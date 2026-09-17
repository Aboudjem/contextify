#!/usr/bin/env python3
"""
Behaviour tests for verify_claims.py, contextify's claim linter (a release gate).

The linter's whole value is the line it draws between two kinds of miss. A command or a
path the repository provably does not have is STALE and fails the run. A form no
resolver covers is UNVERIFIED and does not: contextify would rather say "I cannot prove
this" than accuse a working command of being a hallucination.

Checks:
  1  a file quoting a live script, a missing make target and a missing path exits 1 and
     names both misses, and calls the live script OK
  2  a clean file exits 0 and says so
  3  npx with an unresolvable binary is UNVERIFIED, never STALE
  4  --json parses, and its fields agree with the prose output
  5  --budget adds the line ceiling to the same verdict
  6  a path that exists resolves, and the summary line counts what it printed

Standard library only. Run: python3 tests/test_verify_claims.py   (exit 0 = all pass)
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFY = os.path.join(ROOT, "skills", "contextify", "scripts", "verify_claims.py")

failures = []
_total = 0
_tempdirs = []

GIT_ENV = {
    "GIT_AUTHOR_NAME": "contextify tests",
    "GIT_AUTHOR_EMAIL": "tests@example.invalid",
    "GIT_COMMITTER_NAME": "contextify tests",
    "GIT_COMMITTER_EMAIL": "tests@example.invalid",
    "GIT_CONFIG_NOSYSTEM": "1",
}


def check(name, ok, detail=""):
    global _total
    _total += 1
    tag = "PASS" if ok else "FAIL"
    msg = "%s: %s" % (tag, name)
    if detail and not ok:
        msg += "  (%s)" % detail
    print(msg)
    if not ok:
        failures.append(name)


def run(cmd, cwd=None):
    environment = dict(os.environ)
    environment.update(GIT_ENV)
    return subprocess.run(cmd, cwd=cwd, input="", stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, env=environment)


def new_repo(files):
    repo = tempfile.mkdtemp(prefix="ctxclaims-")
    _tempdirs.append(repo)
    run(["git", "init", "-q"], cwd=repo)
    for rel, text in files.items():
        path = os.path.join(repo, rel)
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    run(["git", "add", "-A"], cwd=repo)
    run(["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "fixture"], cwd=repo)
    return repo


PACKAGE = """{
  "name": "claims-fixture",
  "scripts": {
    "build": "tsc -p .",
    "test": "vitest run"
  },
  "devDependencies": {
    "typescript": "5.4.0"
  }
}
"""

MAKEFILE = """.PHONY: bootstrap
bootstrap:
\tnpm ci

check:
\tnpm run test
"""

DIRTY_AGENTS = """# claims fixture

## Commands
- Build the bundle with `npm run build`.
- Ship a release with `make deploy`.

## Architecture
- The router lives in `src/app/page.tsx` and it renders the shell.
- The entry point is `src/index.ts`.
"""

CLEAN_AGENTS = """# claims fixture

## Commands
- Build the bundle with `npm run build`.
- Bootstrap the checkout with `make bootstrap`.

## Architecture
- The entry point is `src/index.ts`.
"""

FILES = {
    "package.json": PACKAGE,
    "Makefile": MAKEFILE,
    "src/index.ts": "export const main = () => 0;\n",
}


# ======================================================================================
print("--- 1. a file with two real misses ---")
repo1 = new_repo(dict(FILES, **{"AGENTS.md": DIRTY_AGENTS}))
r = run([sys.executable, VERIFY, "AGENTS.md"], cwd=repo1)
out1 = r.stdout

check("1a a file with a dead command and a dead path exits 1", r.returncode == 1,
      "exit %d stdout=%r" % (r.returncode, out1))
check("1b the dead make target is reported STALE and named",
      any(l.startswith("STALE") and "make deploy" in l for l in out1.splitlines()),
      "stdout=%r" % out1)
check("1c the dead path is reported STALE and named",
      any(l.startswith("STALE") and "src/app/page.tsx" in l for l in out1.splitlines()),
      "stdout=%r" % out1)
check("1d the live script is reported OK",
      any(l.startswith("OK") and "npm run build" in l for l in out1.splitlines()),
      "stdout=%r" % out1)
check("1e the live path is reported OK",
      any(l.startswith("OK") and "src/index.ts" in l for l in out1.splitlines()),
      "stdout=%r" % out1)
check("1f every finding carries file:line",
      all(":" in l.split()[1] for l in out1.splitlines()
          if l.split() and l.split()[0] in ("OK", "STALE", "UNVERIFIED")),
      "stdout=%r" % out1)
check("1g the summary line counts two stale claims",
      any(l.endswith("unverified") and ", 2 stale," in l for l in out1.splitlines()),
      "stdout=%r" % out1)
check("1h the STALE lines give a reason",
      all("(" in l for l in out1.splitlines() if l.startswith("STALE")),
      "stdout=%r" % out1)


# ======================================================================================
print("--- 2. a clean file ---")
repo2 = new_repo(dict(FILES, **{"AGENTS.md": CLEAN_AGENTS}))
r = run([sys.executable, VERIFY, "AGENTS.md"], cwd=repo2)
check("2a a file whose every claim resolves exits 0", r.returncode == 0,
      "exit %d stdout=%r" % (r.returncode, r.stdout))
check("2b and reports no stale claims", ", 0 stale," in r.stdout,
      "stdout=%r" % r.stdout)
check("2c and it did check something (the summary is not 0 claims)",
      not r.stdout.strip().startswith("0 claims"), "stdout=%r" % r.stdout)


# ======================================================================================
print("--- 3. an unresolvable form is unverified, never stale ---")
NPX_AGENTS = """# claims fixture

## Commands
- Build the bundle with `npm run build`.
- Generate the client with `npx some-unlisted-generator`.
- Run a one-off with `uv run migrate`.
"""
repo3 = new_repo(dict(FILES, **{"AGENTS.md": NPX_AGENTS}))
r = run([sys.executable, VERIFY, "AGENTS.md"], cwd=repo3)
out3 = r.stdout
npx_line = next((l for l in out3.splitlines() if "some-unlisted-generator" in l), "")
check("3a npx with a binary nothing declares is UNVERIFIED",
      npx_line.startswith("UNVERIFIED"), "line=%r" % npx_line)
check("3b it is emphatically not STALE", not npx_line.startswith("STALE"),
      "line=%r" % npx_line)
uv_line = next((l for l in out3.splitlines() if "uv run migrate" in l), "")
check("3c uv run is UNVERIFIED too, with a reason",
      uv_line.startswith("UNVERIFIED") and "(" in uv_line, "line=%r" % uv_line)
check("3d a file whose only misses are unverified still exits 0", r.returncode == 0,
      "exit %d stdout=%r" % (r.returncode, out3))
r = run([sys.executable, VERIFY, "--strict", "AGENTS.md"], cwd=repo3)
check("3e --strict is the opt-in that makes unverified fail", r.returncode == 1,
      "exit %d" % r.returncode)


# ======================================================================================
print("--- 4. --json ---")
r = run([sys.executable, VERIFY, "--json", "AGENTS.md"], cwd=repo1)
payload = None
try:
    payload = json.loads(r.stdout)
except ValueError:
    payload = None
check("4a --json emits one parseable object", isinstance(payload, dict),
      "stdout=%r" % r.stdout[:200])
if isinstance(payload, dict):
    check("4b --json counts the same two stale claims the prose does",
          payload.get("stale") == 2, "stale=%r" % payload.get("stale"))
    check("4c --json marks the run as not ok", payload.get("ok") is False,
          "ok=%r" % payload.get("ok"))
    statuses = {row["text"]: row["status"] for row in payload.get("claims", [])}
    check("4d every claim row carries status, file, line and text",
          all({"status", "file", "line", "text"} <= set(row)
              for row in payload.get("claims", [])),
          "rows=%r" % payload.get("claims"))
    check("4e make deploy is STALE in the JSON too",
          statuses.get("make deploy") == "STALE", "statuses=%r" % statuses)
check("4f --json still exits 1 when something is stale", r.returncode == 1,
      "exit %d" % r.returncode)
check("4g --json prints no prose", "claims," not in r.stdout,
      "stdout=%r" % r.stdout[:200])


# ======================================================================================
print("--- 5. --budget ---")
big = "# claims fixture\n\n" + "\n".join(
    "- Fact number %d about this repository." % n for n in range(1, 160)) + "\n"
repo5 = new_repo(dict(FILES, **{"AGENTS.md": big}))
r = run([sys.executable, VERIFY, "--budget", "AGENTS.md"], cwd=repo5)
combined = r.stdout + r.stderr
count = len(big.splitlines())
check("5a --budget fails a file over the line ceiling", r.returncode == 1,
      "exit %d" % r.returncode)
check("5b the message names the count (%d) and the ceiling (150)" % count,
      str(count) in combined and "150" in combined, "output=%r" % combined[-300:])
r = run([sys.executable, VERIFY, "AGENTS.md"], cwd=repo5)
check("5c without --budget the same file passes, because no claim is dead",
      r.returncode == 0, "exit %d stdout=%r" % (r.returncode, r.stdout[-200:]))
r = run([sys.executable, VERIFY, "--budget", "AGENTS.md"], cwd=repo2)
check("5d --budget leaves a file inside the ceiling alone", r.returncode == 0,
      "exit %d stdout=%r" % (r.returncode, r.stdout[-200:]))


# ======================================================================================
print("--- 6. arguments ---")
r = run([sys.executable, VERIFY], cwd=repo2)
check("6a no file argument is a usage error at exit 2", r.returncode == 2,
      "exit %d" % r.returncode)
r = run([sys.executable, VERIFY, "does-not-exist.md"], cwd=repo2)
check("6b an unreadable file is a usage error at exit 2, named on stderr",
      r.returncode == 2 and "does-not-exist.md" in r.stderr,
      "exit %d stderr=%r" % (r.returncode, r.stderr))
r = run([sys.executable, VERIFY, "--help"], cwd=repo2)
check("6c --help prints usage and exits 0",
      r.returncode == 0 and "verify_claims.py" in r.stdout, "exit %d" % r.returncode)


# ======================================================================================
for path in _tempdirs:
    shutil.rmtree(path, ignore_errors=True)

print("-" * 60)
passed = _total - len(failures)
print("%d/%d checks passed" % (passed, _total))
if failures:
    print("%d failed" % len(failures))
    for name in failures:
        print("  - %s" % name)
else:
    print("All checks passed.")
sys.exit(1 if failures else 0)
