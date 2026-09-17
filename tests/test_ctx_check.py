#!/usr/bin/env python3
"""
Behaviour tests for contextify's deterministic layer (a release gate; runs in CI).

Every check builds a throwaway git repository under tempfile.mkdtemp(), drives the real
scripts as subprocesses, and asserts what a user would observe: exit codes, stdout bytes,
stderr bytes, wall time and the bytes left on disk. Nothing here asserts that a file
exists and stops there.

Numbered cases, in order:
   1  a fresh stamped repo is silent through both the shell entry and ctx_check.py
   2  a dependency bump plus a key reorder is evaluated by the complete checker and is still fresh
   3  a removed script drifts, names the key and the script, and stays inside the bounds
   4  an added dependency drifts on package.json#deps
   5  a quoted command whose script was deleted is Stale, and dead claims come first
   6  no stamp is exit 3 and exactly one line naming /contextify init
   7  a directory that is not a git repository is silent at exit 0
   8  --hook claude, --hook cursor and the stdin cwd field
   9  --ci, --ci --strict and --ci when fresh
  10  the checker's wall time
  11  a second write is byte-identical, and a human sentinel survives the third
  12  the line ceiling, in the linter and in the writer
  13  the Codex byte ceiling refuses before any write
  14  an interrupted write leaves no partial file and can be recovered
  15  the two DISCOVERY_GLOBS lists are the same list
  16  normalizer noise: what is ignored and what is caught
  17  no .env.example value is ever stored
  18  the pointer files and the no-duplication rule
  19  size scaling
  20  a path that resolves outside the scope
  21  accept after a version-only commit, and accept with a dead claim
  22  install_hooks.sh writes five snippets and is idempotent

Standard library only. Run: python3 tests/test_ctx_check.py   (exit 0 = all pass)

Deviations from docs/design/SCRIPTS-SPEC.md, and why, are listed at the bottom of this
docstring.

DEVIATIONS

  a. Drift notice ordering. D11's literal example prints Changed and Removed before
     Stale, but D11's own text and SCRIPTS-SPEC both say "dead claims first", and the
     test contract for case 5 requires dead claims before changed evidence. The
     implementation puts Stale first; every other row of D11 is reproduced literally.

  b. The no-stamp branch. SCRIPTS-SPEC step 3 puts the exit-3 line in ctx-check itself.
     ctx-check instead execs ctx_check.py for it, so the line, the four hook envelopes
     and the --ci and --strict variants have exactly one implementation. Observable
     behaviour is identical: one line on stdout naming /contextify init, exit 3.

  c. The summary block carries one extra row, Size, which D10's example fixture does not
     show. SCRIPTS-SPEC step 1 requires the writer to print the size class, and the
     summary block is the only report it prints.

  d. install_hooks.sh embeds its five snippets as heredocs, but no check compares them
     against skills/contextify/references/hooks-and-ci.md: that reference file belongs to
     another lane and does not exist yet. The comparison test goes in with the file.

  e. Claim liveness carries a tight negation guard: a stale claim on a line that
     documents an absence ("there is no npm run lint:css") is demoted to unverified.
     D16 does not mention it; documenting an absence is a feature of a good AGENTS.md,
     and accusing it of being a hallucination would be the wrong answer.
"""

import json
import hashlib
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "contextify", "scripts")
CTX_CHECK = os.path.join(SCRIPTS, "ctx-check")
CTX_CHECK_PY = os.path.join(SCRIPTS, "ctx_check.py")
CTX_WRITE = os.path.join(SCRIPTS, "ctx_write.py")
CTX_STAMP = os.path.join(SCRIPTS, "ctx_stamp.py")
CTXLIB = os.path.join(SCRIPTS, "ctxlib.py")
INSTALL_HOOKS = os.path.join(SCRIPTS, "install_hooks.sh")
VERIFY_CLAIMS = os.path.join(SCRIPTS, "verify_claims.py")

failures = []
_total = 0
_tempdirs = []

GIT_ENV = {
    "GIT_AUTHOR_NAME": "contextify tests",
    "GIT_AUTHOR_EMAIL": "tests@example.invalid",
    "GIT_COMMITTER_NAME": "contextify tests",
    "GIT_COMMITTER_EMAIL": "tests@example.invalid",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
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


def run(cmd, cwd=None, env=None, stdin=""):
    environment = dict(os.environ)
    environment.update(GIT_ENV)
    environment.pop("CONTEXTIFY_TRACE", None)
    environment.pop("CONTEXTIFY_TEST_CRASH_AFTER", None)
    if env:
        environment.update(env)
    return subprocess.run(cmd, cwd=cwd, input=stdin, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, env=environment)


def git(repo, *args):
    return run(["git", "-c", "commit.gpgsign=false", *args], cwd=repo)


def write(repo, rel, text):
    path = os.path.join(repo, rel)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def read(repo, rel):
    with open(os.path.join(repo, rel), "r", encoding="utf-8") as fh:
        return fh.read()


def new_repo(files, commit=True):
    repo = tempfile.mkdtemp(prefix="ctxtest-repo-")
    _tempdirs.append(repo)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "contextify tests")
    git(repo, "config", "user.email", "tests@example.invalid")
    for rel, text in files.items():
        write(repo, rel, text)
    if commit:
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "fixture")
    return repo


def new_draft(agents_body, claude_body=None, nested=None):
    draft = tempfile.mkdtemp(prefix="ctxtest-draft-")
    _tempdirs.append(draft)
    with open(os.path.join(draft, "AGENTS.md"), "w", encoding="utf-8") as fh:
        fh.write(agents_body)
    if claude_body is not None:
        with open(os.path.join(draft, "CLAUDE.md"), "w", encoding="utf-8") as fh:
            fh.write(claude_body)
    for rel, body in (nested or {}).items():
        path = os.path.join(draft, rel, "AGENTS.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
    return draft


def ctx_write(repo, draft, targets=None, extra=None, env=None):
    cmd = [sys.executable, CTX_WRITE, "--root", repo, "--draft", draft, "--yes"]
    if targets:
        cmd += ["--targets", targets]
    cmd += extra or []
    return run(cmd, cwd=repo, env=env)


def ctx_check(repo, args=None, cwd=None, stdin="", env=None):
    return run(["sh", CTX_CHECK, *(args or [])], cwd=cwd or repo, stdin=stdin, env=env)


def snapshot(repo):
    """Every file under repo except .git, as {relative path: bytes}."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, repo)
            if os.path.islink(path):
                out[rel] = b"symlink:" + os.readlink(path).encode()
                continue
            try:
                with open(path, "rb") as fh:
                    out[rel] = fh.read()
            except OSError:
                pass
    return out


PKG = {
    "name": "fixture",
    "version": "1.0.0",
    "scripts": {
        "build": "tsc -p .",
        "test": "vitest run",
        "lint:css": "stylelint 'src/**/*.css'",
        "docs": "typedoc src",
    },
    "dependencies": {"left-pad": "1.3.0"},
}


def pkg_json(data):
    return json.dumps(data, indent=2) + "\n"


BASIC_FILES = {
    "package.json": pkg_json(PKG),
    "src/index.ts": "import './styles.css';\nexport const main = () => 0;\n",
    "src/styles.css": "body { margin: 0; }\n",
    "README.md": "# fixture\n\nA throwaway repository.\n"
                 "- Build the bundle: `npm run build`\n"
                 "- Run the suite: `npm run test`\n"
                 "- Lint the stylesheets: `npm run lint:css`\n",
}

DRAFT_BODY = """# fixture

## Commands
- Build the bundle: `npm run build`
- Run the suite: `npm run test`
- Lint the stylesheets: `npm run lint:css`

## Architecture
- `src/index.ts` imports `src/styles.css`.
"""


def basic_repo():
    repo = new_repo(dict(BASIC_FILES))
    draft = new_draft(DRAFT_BODY)
    evidence_rows = []
    for line in DRAFT_BODY.splitlines():
        if line.startswith("- Build"):
            source = "README.md:4"
        elif line.startswith("- Run"):
            source = "README.md:5"
        elif line.startswith("- Lint"):
            source = "README.md:6"
        elif line.startswith("- `src/index.ts`"):
            source = "src/index.ts:1"
        else:
            continue
        evidence_rows.append(hashlib.sha256(line.encode()).hexdigest() + "\t" + source)
    write(draft, "evidence.tsv", "\n".join(evidence_rows) + "\n")
    result = ctx_write(repo, draft, targets="claude,gemini")
    if result.returncode != 0:
        raise AssertionError("fixture write failed: %s%s" % (result.stdout, result.stderr))
    return repo, draft


# ======================================================================================
print("--- 1. a fresh stamped repo is silent, through both paths ---")
repo1, draft1 = basic_repo()

r = ctx_check(repo1)
check("1a shell entry on a fresh repo exits 0", r.returncode == 0,
      "exit %d stderr=%r" % (r.returncode, r.stderr))
check("1b shell entry on a fresh repo prints nothing on stdout", r.stdout == "",
      "stdout=%r" % r.stdout)
check("1c shell entry on a fresh repo prints nothing on stderr", r.stderr == "",
      "stderr=%r" % r.stderr)

r = ctx_check(repo1, env={"CONTEXTIFY_TRACE": "1"})
check("1d the shell delegates to the authoritative checker until a complete cache exists",
      "contextify-trace" in r.stderr, "stderr=%r" % r.stderr)

r = run([sys.executable, CTX_CHECK_PY, "--root", repo1], cwd=repo1)
check("1e ctx_check.py on a fresh repo exits 0 with empty stdout",
      r.returncode == 0 and r.stdout == "",
      "exit %d stdout=%r stderr=%r" % (r.returncode, r.stdout, r.stderr))


# ======================================================================================
print("--- 2. a dependency bump plus a key reorder is noise, not drift ---")
repo2, draft2 = basic_repo()
reordered = {
    "name": "fixture",
    "version": "1.0.0",
    "dependencies": {"left-pad": "1.3.1"},
    "scripts": {
        "docs": "typedoc src",
        "test": "vitest run",
        "build": "tsc -p .",
        "lint:css": "stylelint 'src/**/*.css'",
    },
}
write(repo2, "package.json", pkg_json(reordered))
git(repo2, "add", "-A")
git(repo2, "commit", "-q", "-m", "bump left-pad and reorder scripts")

r = ctx_check(repo2, env={"CONTEXTIFY_TRACE": "1"})
check("2a the bump moves the index blob; complete checker still resolves freshness",
      "contextify-trace" in r.stderr, "stderr=%r" % r.stderr)
check("2b the normalizer suppresses the noise: exit 0", r.returncode == 0,
      "exit %d" % r.returncode)
check("2c the normalizer suppresses the noise: no stdout at all", r.stdout == "",
      "stdout=%r" % r.stdout)


# ======================================================================================
print("--- 3. a removed script is drift, named ---")
repo3, draft3 = basic_repo()
without_docs = json.loads(pkg_json(PKG))
del without_docs["scripts"]["docs"]
write(repo3, "package.json", pkg_json(without_docs))

r = ctx_check(repo3)
out3 = r.stdout
check("3a removing a script exits 0 (a stale doc never blocks a session)",
      r.returncode == 0, "exit %d" % r.returncode)
check("3b the notice names the evidence key package.json#scripts",
      "package.json#scripts" in out3, "stdout=%r" % out3)
check("3c the notice names the script that went away",
      re.search(r"Removed\s+script docs", out3) is not None, "stdout=%r" % out3)
check("3d the notice is at most 12 lines", len(out3.rstrip("\n").splitlines()) <= 12,
      "%d lines" % len(out3.rstrip("\n").splitlines()))
check("3e the notice is at most 2048 bytes", len(out3.encode("utf-8")) <= 2048,
      "%d bytes" % len(out3.encode("utf-8")))
check("3f the notice opens on the locked first line",
      out3.startswith("contextify: drift\n"), "stdout=%r" % out3[:40])
check("3g the last line names the next command",
      out3.rstrip("\n").splitlines()[-1].startswith("Next"),
      "last line=%r" % out3.rstrip("\n").splitlines()[-1])

# The notice is bounded however much moved, which is the point of injecting it at
# session start: an unbounded report becomes the bloat contextify exists to prevent.
repo3b, _ = basic_repo()
flood = json.loads(pkg_json(PKG))
flood["scripts"] = {"kept": "true"}
flood["dependencies"] = {"dep-%02d" % n: "1.0.0" for n in range(20)}
write(repo3b, "package.json", pkg_json(flood))
write(repo3b, ".env.example", "\n".join("KEY_%02d=value" % n for n in range(12)) + "\n")
r = ctx_check(repo3b)
out3b = r.stdout
lines3b = out3b.rstrip("\n").splitlines()
check("3h a flood of findings still fits in 12 lines", len(lines3b) <= 12,
      "%d lines: %r" % (len(lines3b), out3b))
check("3i and in 2048 bytes", len(out3b.encode("utf-8")) <= 2048,
      "%d bytes" % len(out3b.encode("utf-8")))
check("3j the excess is collapsed into a count rather than dropped silently",
      any(l.startswith("More") for l in lines3b), "stdout=%r" % out3b)
check("3k a flooded notice still exits 0 and still names the next command",
      r.returncode == 0 and lines3b[-1].startswith(("Next", "Accept")),
      "exit %d last=%r" % (r.returncode, lines3b[-1]))


# ======================================================================================
print("--- 4. an added dependency is drift on package.json#deps ---")
repo4, draft4 = basic_repo()
with_dep = json.loads(pkg_json(PKG))
with_dep["dependencies"]["right-pad"] = "2.0.0"
write(repo4, "package.json", pkg_json(with_dep))

r = ctx_check(repo4)
check("4a adding a dependency exits 0", r.returncode == 0, "exit %d" % r.returncode)
check("4b the notice names package.json#deps", "package.json#deps" in r.stdout,
      "stdout=%r" % r.stdout)
check("4c the notice names the dependency that arrived",
      "right-pad" in r.stdout, "stdout=%r" % r.stdout)
check("4d a dependency change does not claim the scripts moved",
      "package.json#scripts" not in r.stdout, "stdout=%r" % r.stdout)


# ======================================================================================
print("--- 5. a quoted command whose script was deleted is Stale, first ---")
repo5, draft5 = basic_repo()
without_lint = json.loads(pkg_json(PKG))
del without_lint["scripts"]["lint:css"]
write(repo5, "package.json", pkg_json(without_lint))

r = ctx_check(repo5)
out5 = r.stdout
lines5 = out5.rstrip("\n").splitlines()
stale_idx = next((i for i, l in enumerate(lines5) if l.startswith("Stale")), None)
changed_idx = next((i for i, l in enumerate(lines5) if l.startswith("Changed")), None)

check("5a the notice carries a Stale row", stale_idx is not None, "stdout=%r" % out5)
if stale_idx is not None:
    stale_line = lines5[stale_idx]
    agents_line = None
    for n, text in enumerate(read(repo5, "AGENTS.md").splitlines(), 1):
        if "lint:css" in text:
            agents_line = n
            break
    check("5b the Stale row names AGENTS.md and the exact line number",
          ("AGENTS.md:%d" % agents_line) in stale_line,
          "line=%r expected AGENTS.md:%s" % (stale_line, agents_line))
    check("5c the Stale row quotes the command text",
          "npm run lint:css" in stale_line, "line=%r" % stale_line)
check("5d dead claims are listed before changed evidence",
      stale_idx is not None and changed_idx is not None and stale_idx < changed_idx,
      "stale at %s, changed at %s" % (stale_idx, changed_idx))
check("5e a dead claim disables accept in the notice",
      any(l.startswith("Accept") for l in lines5), "stdout=%r" % out5)
check("5f a stale claim still exits 0", r.returncode == 0, "exit %d" % r.returncode)
check("5g the notice stays inside both bounds",
      len(lines5) <= 12 and len(out5.encode("utf-8")) <= 2048,
      "%d lines, %d bytes" % (len(lines5), len(out5.encode("utf-8"))))


# ======================================================================================
print("--- 6. no stamp ---")
repo6 = new_repo(dict(BASIC_FILES))
r = ctx_check(repo6)
check("6a an unstamped repo exits 3", r.returncode == 3, "exit %d" % r.returncode)
check("6b an unstamped repo prints exactly one line",
      len(r.stdout.rstrip("\n").splitlines()) == 1, "stdout=%r" % r.stdout)
check("6c that line names /contextify init", "/contextify init" in r.stdout,
      "stdout=%r" % r.stdout)


# ======================================================================================
print("--- 7. not a git repository ---")
plain = tempfile.mkdtemp(prefix="ctxtest-plain-")
_tempdirs.append(plain)
with open(os.path.join(plain, "notes.txt"), "w") as fh:
    fh.write("nothing to see\n")
r = ctx_check(plain, cwd=plain)
check("7a a directory outside git exits 0", r.returncode == 0, "exit %d" % r.returncode)
check("7b a directory outside git prints nothing on stdout", r.stdout == "",
      "stdout=%r" % r.stdout)
check("7c a directory outside git prints nothing on stderr", r.stderr == "",
      "stderr=%r" % r.stderr)


# ======================================================================================
print("--- 8. hook envelopes and the stdin cwd field ---")
elsewhere = tempfile.mkdtemp(prefix="ctxtest-elsewhere-")
_tempdirs.append(elsewhere)

r = ctx_check(repo5, args=["--hook", "claude"], cwd=elsewhere,
              stdin=json.dumps({"cwd": repo5, "hook_event_name": "SessionStart"}))
check("8a --hook claude prints exactly one line",
      len(r.stdout.rstrip("\n").splitlines()) == 1, "stdout=%r" % r.stdout)
payload = None
try:
    payload = json.loads(r.stdout)
except ValueError:
    payload = None
check("8b that line is valid JSON", payload is not None, "stdout=%r" % r.stdout)
if payload:
    hook_out = payload.get("hookSpecificOutput") or {}
    check("8c hookSpecificOutput.hookEventName is SessionStart",
          hook_out.get("hookEventName") == "SessionStart", "payload=%r" % payload)
    check("8d additionalContext carries the drift notice",
          "contextify: drift" in (hook_out.get("additionalContext") or "")
          and "lint:css" in (hook_out.get("additionalContext") or ""),
          "additionalContext=%r" % hook_out.get("additionalContext"))
check("8e the stdin cwd field is honoured when the process cwd is somewhere else",
      r.returncode == 0 and r.stdout != "", "exit %d stdout=%r" % (r.returncode, r.stdout))

r = ctx_check(repo1, args=["--hook", "claude"], cwd=elsewhere,
              stdin=json.dumps({"cwd": repo1}))
check("8f a fresh repo prints nothing at all under --hook claude",
      r.stdout == "" and r.returncode == 0,
      "exit %d stdout=%r" % (r.returncode, r.stdout))

r = ctx_check(repo5, args=["--hook", "cursor"], cwd=elsewhere,
              stdin=json.dumps({"cwd": repo5}))
cursor_payload = None
try:
    cursor_payload = json.loads(r.stdout)
except ValueError:
    cursor_payload = None
check("8g --hook cursor uses the snake_case additional_context envelope",
      isinstance(cursor_payload, dict) and "additional_context" in cursor_payload
      and "hookSpecificOutput" not in cursor_payload,
      "stdout=%r" % r.stdout)


# ======================================================================================
print("--- 9. the CI adapter ---")
r = ctx_check(repo5, args=["--ci"])
check("9a --ci on drift prints the notice", "contextify: drift" in r.stdout,
      "stdout=%r" % r.stdout)
check("9b --ci alone stays exit 0 on drift", r.returncode == 0, "exit %d" % r.returncode)

r = ctx_check(repo5, args=["--ci", "--strict"])
check("9c --ci --strict turns drift into exit 1", r.returncode == 1,
      "exit %d" % r.returncode)
check("9d --ci --strict still prints the notice", "contextify: drift" in r.stdout,
      "stdout=%r" % r.stdout)

r = ctx_check(repo1, args=["--ci"])
check("9e --ci when fresh says so on stdout", r.stdout.strip() == "contextify: fresh",
      "stdout=%r" % r.stdout)
check("9f --ci when fresh exits 0", r.returncode == 0, "exit %d" % r.returncode)

r = ctx_check(repo1, args=["--ci", "--strict"])
check("9g --ci --strict when fresh exits 0", r.returncode == 0, "exit %d" % r.returncode)


# ======================================================================================
print("--- 10. the checker's wall time ---")
for _ in range(2):
    ctx_check(repo1)  # the spec's budget is a warm cache, so warm it before measuring
samples = []
for _ in range(5):
    start = time.perf_counter()
    r = ctx_check(repo1)
    samples.append((time.perf_counter() - start) * 1000.0)
median_ms = statistics.median(samples)
print("       checker samples (ms): %s" % ", ".join("%.1f" % s for s in samples))
print("       checker median (ms):  %.1f" % median_ms)
check("10a the checker's median is under 250 ms (target is 100 ms)", median_ms < 250.0,
      "median %.1f ms" % median_ms)


# ======================================================================================
print("--- 11. idempotency and the human sentinel ---")
repo11, draft11 = basic_repo()
before11 = snapshot(repo11)
stamp_before = json.loads(read(repo11, ".contextify/stamp.json"))

r = ctx_write(repo11, draft11, targets="claude,gemini")
after11 = snapshot(repo11)
stamp_after = json.loads(read(repo11, ".contextify/stamp.json"))

check("11a a second write with the same draft exits 0", r.returncode == 0,
      "exit %d stderr=%r" % (r.returncode, r.stderr))
differing = sorted(k for k in set(before11) | set(after11)
                   if before11.get(k) != after11.get(k))
check("11b every file is byte-identical between the two runs", not differing,
      "changed: %s" % ", ".join(differing))
check("11c the stamp's generatedAt is untouched by a no-op run",
      stamp_before["generatedAt"] == stamp_after["generatedAt"],
      "%r then %r" % (stamp_before["generatedAt"], stamp_after["generatedAt"]))

SENTINEL = "Human sentinel: this line is mine and contextify must not touch it."
with open(os.path.join(repo11, "AGENTS.md"), "a", encoding="utf-8") as fh:
    fh.write("\n" + SENTINEL + "\n")

new_body = DRAFT_BODY.replace("## Architecture",
                              "## Testing\n- The suite runs headless.\n\n## Architecture")
draft11b = new_draft(new_body)
r = ctx_write(repo11, draft11b, targets="claude,gemini")
check("11d a third write with a changed draft exits 0", r.returncode == 0,
      "exit %d stderr=%r" % (r.returncode, r.stderr))
agents11 = read(repo11, "AGENTS.md")
check("11e the human sentinel survives byte for byte",
      agents11.count(SENTINEL) == 1 and agents11.rstrip("\n").endswith(SENTINEL),
      "tail=%r" % agents11[-160:])
check("11f the managed block picked up the new draft body",
      "## Testing" in agents11 and "The suite runs headless." in agents11,
      "AGENTS.md=%r" % agents11[:400])
check("11g the sentinel stayed outside the managed block",
      agents11.index("<!-- contextify:end -->") < agents11.index(SENTINEL),
      "the sentinel was swallowed by the block")
r = ctx_check(repo11)
check("11h the repo is fresh again after the third write",
      r.returncode == 0 and r.stdout == "",
      "exit %d stdout=%r" % (r.returncode, r.stdout))


# ======================================================================================
print("--- 12. the line ceiling ---")
long_lines = "\n".join("- Fact number %d about this repository." % n for n in range(1, 159))
repo12 = new_repo({"package.json": pkg_json(PKG), "AGENTS.md": "# fixture\n" + long_lines
                   + "\n"})
agents_len = len(read(repo12, "AGENTS.md").splitlines())
r = run([sys.executable, VERIFY_CLAIMS, "--budget", "AGENTS.md"], cwd=repo12)
combined12 = r.stdout + r.stderr
check("12a verify_claims --budget fails on an oversized AGENTS.md", r.returncode == 1,
      "exit %d output=%r" % (r.returncode, combined12[:300]))
check("12b the message names the real count (%d) and the ceiling (150)" % agents_len,
      str(agents_len) in combined12 and "150" in combined12,
      "output=%r" % combined12[:300])

over_body = "# fixture\n\n" + "\n".join(
    "- Fact number %d about this repository." % n for n in range(1, 160)) + "\n"
repo12b = new_repo(dict(BASIC_FILES))
draft12 = new_draft(over_body)
r = ctx_write(repo12b, draft12)
check("12c ctx_write refuses a draft that would render over the ceiling",
      r.returncode == 4, "exit %d stderr=%r" % (r.returncode, r.stderr))
rendered_count = len(over_body.splitlines()) + 5
check("12d the refusal names the rendered count (%d) and the ceiling" % rendered_count,
      str(rendered_count) in r.stderr and "150" in r.stderr, "stderr=%r" % r.stderr)
check("12e the refused write created no AGENTS.md",
      not os.path.exists(os.path.join(repo12b, "AGENTS.md")), "AGENTS.md was written")


# ======================================================================================
print("--- 13. the Codex byte ceiling ---")
fat_line = ("- This repository keeps its integration fixtures under a dedicated directory "
            "so that the suite can run them in isolation from the unit tests, and the "
            "runner discovers them by convention rather than by an explicit list. " * 2)
fat_body = "# fixture\n\n" + "\n".join(fat_line for _ in range(100)) + "\n"
repo13 = new_repo(dict(BASIC_FILES))
draft13 = new_draft(fat_body)

rendered_bytes = len(fat_body.encode("utf-8"))
status_before = git(repo13, "status", "--porcelain").stdout
r = ctx_write(repo13, draft13, targets="codex")
status_after = git(repo13, "status", "--porcelain").stdout
check("13a a draft over the Codex ceiling is refused with exit 4", r.returncode == 4,
      "exit %d stderr=%r" % (r.returncode, r.stderr[:300]))
check("13b the refusal names the 32,768-byte ceiling",
      "32768" in r.stderr or "32,768" in r.stderr, "stderr=%r" % r.stderr[:300])
check("13c the refusal happens before any write",
      status_before == status_after
      and not os.path.exists(os.path.join(repo13, "AGENTS.md")),
      "git status moved: %r then %r" % (status_before, status_after))
check("13d the same draft is under the line ceiling, so bytes are the only reason",
      len(fat_body.splitlines()) + 5 < 150 and rendered_bytes > 32768,
      "%d lines, %d bytes" % (len(fat_body.splitlines()) + 5, rendered_bytes))

repo13b = new_repo(dict(BASIC_FILES))
r = ctx_write(repo13b, draft13, targets="claude")
check("13e the same draft is accepted when Codex is not a target", r.returncode == 0,
      "exit %d stderr=%r" % (r.returncode, r.stderr[:300]))


# ======================================================================================
print("--- 14. an interrupted write ---")
repo14, draft14 = basic_repo()
old14 = {rel: read(repo14, rel) for rel in
         ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".contextify/stamp.json",
          ".contextify/evidence.json")}
changed_body = DRAFT_BODY.replace("## Architecture",
                                  "## Boundaries\n- Never: commit a built bundle.\n\n"
                                  "## Architecture")
draft14b = new_draft(changed_body)
r = ctx_write(repo14, draft14b, targets="claude,gemini",
              env={"CONTEXTIFY_TEST_CRASH_AFTER": "1"})
check("14a the injected crash really did abort the run", r.returncode != 0,
      "exit %d" % r.returncode)
journal_path = os.path.join(repo14, ".contextify", "journal.json")
check("14b the journal survives the crash", os.path.exists(journal_path),
      ".contextify/journal.json is gone")
journal = json.loads(read(repo14, ".contextify/journal.json"))
partial = []
for entry in journal["targets"]:
    rel = entry["path"]
    current = read(repo14, rel) if os.path.exists(os.path.join(repo14, rel)) else None
    if current not in (entry["previous"],
                       None if entry["previous"] is None else entry["previous"]):
        # the file moved: it must be exactly the new content, never a fragment of it
        import hashlib
        got = "sha256:" + hashlib.sha256((current or "").encode()).hexdigest()
        if got != entry["newDigest"]:
            partial.append(rel)
check("14c every target is either the whole old file or the whole new one", not partial,
      "partial: %s" % ", ".join(partial))

r = ctx_check(repo14)
check("14d ctx-check exits 1 while a journal is on disk", r.returncode == 1,
      "exit %d" % r.returncode)
check("14e ctx-check keeps stdout empty and speaks on stderr only",
      r.stdout == "" and "journal.json" in r.stderr,
      "stdout=%r stderr=%r" % (r.stdout, r.stderr))

r = run([sys.executable, CTX_WRITE, "--root", repo14, "--recover"], cwd=repo14)
check("14f --recover exits 0", r.returncode == 0,
      "exit %d stderr=%r" % (r.returncode, r.stderr))
check("14g --recover removes the journal", not os.path.exists(journal_path),
      "the journal is still there")
restored = {rel: read(repo14, rel) for rel in old14}
check("14h --recover restores the previous generation byte for byte", restored == old14,
      "differs: %s" % ", ".join(k for k in old14 if old14[k] != restored[k]))

r = ctx_check(repo14)
check("14i the recovered repo is fresh again", r.returncode == 0 and r.stdout == "",
      "exit %d stdout=%r stderr=%r" % (r.returncode, r.stdout, r.stderr))


# ======================================================================================
print("--- 15. one discovery list, two languages ---")
sh_source = open(CTX_CHECK, encoding="utf-8").read()
py_source = open(CTXLIB, encoding="utf-8").read()
sh_block = re.search(r"# DISCOVERY_GLOBS_BEGIN\n(.*?)# DISCOVERY_GLOBS_END", sh_source,
                     re.DOTALL)
py_block = re.search(r"# DISCOVERY_GLOBS_BEGIN\n(.*?)# DISCOVERY_GLOBS_END", py_source,
                     re.DOTALL)
sh_globs = []
py_globs = []
if sh_block:
    body = sh_block.group(1)
    body = body[body.index("'") + 1:body.rindex("'")]
    sh_globs = body.split()
if py_block:
    py_globs = re.findall(r'"([^"]+)"', py_block.group(1))
check("15a ctx-check declares a DISCOVERY_GLOBS block", bool(sh_globs), "not found")
check("15b ctxlib.py declares a DISCOVERY_GLOBS block", bool(py_globs), "not found")
check("15c the two lists are the same list, in the same order", sh_globs == py_globs,
      "sh has %d entries, python has %d; first difference: %s"
      % (len(sh_globs), len(py_globs),
         next((("%r vs %r" % (a, b)) for a, b in zip(sh_globs, py_globs) if a != b),
              "length only")))


# ======================================================================================
print("--- 16. normalizer noise ---")
RICH_FILES = dict(BASIC_FILES)
RICH_FILES[".github/workflows/ci.yml"] = """name: ci

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build
        working-directory: .
"""
RICH_FILES["Dockerfile"] = """# the runtime image
FROM node:20
WORKDIR /app
EXPOSE 3000
"""
RICH_FILES[".env.example"] = """# copy to .env before running
DATABASE_URL=postgres://localhost/fixture
API_TOKEN=SECRET_VALUE_XYZ123
"""


def rich_repo():
    repo = new_repo(dict(RICH_FILES))
    draft = new_draft(DRAFT_BODY)
    evidence_rows = []
    for line in DRAFT_BODY.splitlines():
        if line.startswith("- Build"):
            source = "README.md:4"
        elif line.startswith("- Run"):
            source = "README.md:5"
        elif line.startswith("- Lint"):
            source = "README.md:6"
        elif line.startswith("- `src/index.ts`"):
            source = "src/index.ts:1"
        else:
            continue
        evidence_rows.append(hashlib.sha256(line.encode()).hexdigest() + "\t" + source)
    write(draft, "evidence.tsv", "\n".join(evidence_rows) + "\n")
    result = ctx_write(repo, draft, targets="claude")
    if result.returncode != 0:
        raise AssertionError("rich fixture failed: %s%s" % (result.stdout, result.stderr))
    return repo


def edit(repo, rel, old, new):
    text = read(repo, rel)
    if old not in text:
        raise AssertionError("fixture text %r not found in %s" % (old, rel))
    write(repo, rel, text.replace(old, new, 1))


repo16a = rich_repo()
edit(repo16a, ".github/workflows/ci.yml", "actions/checkout@v4", "actions/checkout@v5")
r = ctx_check(repo16a)
check("16a a uses: pin bump is not drift", r.returncode == 0 and r.stdout == "",
      "exit %d stdout=%r" % (r.returncode, r.stdout))

repo16b = rich_repo()
edit(repo16b, "Dockerfile", "# the runtime image", "# the runtime image, pinned by hand")
r = ctx_check(repo16b)
check("16b a Dockerfile comment is not drift", r.returncode == 0 and r.stdout == "",
      "exit %d stdout=%r" % (r.returncode, r.stdout))

repo16c = rich_repo()
edit(repo16c, ".env.example", "postgres://localhost/fixture", "postgres://elsewhere/db")
r = ctx_check(repo16c)
check("16c an .env.example value is not drift", r.returncode == 0 and r.stdout == "",
      "exit %d stdout=%r" % (r.returncode, r.stdout))

repo16d = rich_repo()
edit(repo16d, ".github/workflows/ci.yml", "- run: npm ci", "- run: npm ci --ignore-scripts")
r = ctx_check(repo16d)
check("16d a changed run: line is drift, and the notice names ci#jobs",
      r.returncode == 0 and "ci#jobs" in r.stdout,
      "exit %d stdout=%r" % (r.returncode, r.stdout))

repo16e = rich_repo()
edit(repo16e, "Dockerfile", "FROM node:20", "FROM python:3.12")
r = ctx_check(repo16e)
check("16e a changed FROM image name is drift, named dockerfile#from+expose",
      r.returncode == 0 and "dockerfile#from+expose" in r.stdout,
      "exit %d stdout=%r" % (r.returncode, r.stdout))

repo16f = rich_repo()
edit(repo16f, ".env.example", "API_TOKEN=", "API_KEY=")
r = ctx_check(repo16f)
check("16f a renamed .env.example key is drift, named env.example#keys",
      r.returncode == 0 and "env.example#keys" in r.stdout,
      "exit %d stdout=%r" % (r.returncode, r.stdout))
check("16g the notice names the key that went away and the one that arrived",
      "API_TOKEN" in r.stdout and "API_KEY" in r.stdout, "stdout=%r" % r.stdout)

repo16h = rich_repo()
edit(repo16h, "Dockerfile", "FROM node:20", "FROM node:22")
r = ctx_check(repo16h)
check("16h a FROM tag bump is not drift (the tag is deliberately dropped)",
      r.returncode == 0 and r.stdout == "",
      "exit %d stdout=%r" % (r.returncode, r.stdout))


# ======================================================================================
print("--- 17. no .env.example value ever reaches the state directory ---")
repo17 = rich_repo()
leaks = []
state = os.path.join(repo17, ".contextify")
for dirpath, _dirnames, filenames in os.walk(state):
    for name in filenames:
        path = os.path.join(dirpath, name)
        with open(path, "rb") as fh:
            if b"SECRET_VALUE_XYZ123" in fh.read():
                leaks.append(os.path.relpath(path, repo17))
check("17a the value written in .env.example appears nowhere under .contextify/",
      not leaks, "leaked into: %s" % ", ".join(leaks))
evidence17 = read(repo17, ".contextify/evidence.json")
check("17b evidence.json still records the key names it is supposed to record",
      "API_TOKEN" in evidence17 and "DATABASE_URL" in evidence17,
      "env.example#keys is missing its names")
check("17c and it records no value for any of them",
      "postgres://localhost/fixture" not in evidence17,
      "a value from .env.example is stored")


# ======================================================================================
print("--- 18. pointer files carry no duplicated instructions ---")
UNIQUE = "Fixture ownership rule 17 governs every change to this repository."
body18 = DRAFT_BODY.replace("## Architecture", "## Conventions\n- %s\n\n## Architecture"
                            % UNIQUE)
repo18 = new_repo(dict(BASIC_FILES))
draft18 = new_draft(body18)
r = ctx_write(repo18, draft18, targets="claude,gemini,copilot,cursor-rule")
check("18a a four-pointer write exits 0", r.returncode == 0,
      "exit %d stderr=%r" % (r.returncode, r.stderr))

claude18 = read(repo18, "CLAUDE.md")
check("18b CLAUDE.md line 1 is exactly @AGENTS.md",
      claude18.splitlines()[0] == "@AGENTS.md",
      "line 1 = %r" % claude18.splitlines()[0])
gemini18 = read(repo18, "GEMINI.md")
check("18c GEMINI.md is exactly three lines",
      len(gemini18.rstrip("\n").splitlines()) == 3,
      "%d lines: %r" % (len(gemini18.rstrip("\n").splitlines()), gemini18))
mdc18 = read(repo18, ".cursor/rules/contextify.mdc")
desc = re.search(r"^description:\s*(.+)$", mdc18, re.MULTILINE)
check("18d the cursor rule declares alwaysApply: true",
      re.search(r"^alwaysApply:\s*true\s*$", mdc18, re.MULTILINE) is not None,
      "mdc=%r" % mdc18)
check("18e the cursor rule carries a non-empty description",
      desc is not None and desc.group(1).strip() != "", "mdc=%r" % mdc18)
copilot18 = read(repo18, ".github/copilot-instructions.md")
check("18f the copilot pointer links ../AGENTS.md", "../AGENTS.md" in copilot18,
      "copilot=%r" % copilot18)

generated18 = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursor/rules/contextify.mdc",
               ".github/copilot-instructions.md"]
occurrences = sum(read(repo18, rel).count(UNIQUE) for rel in generated18)
check("18g the unique sentence occurs exactly once across every generated file",
      occurrences == 1, "%d occurrences" % occurrences)


# ======================================================================================
print("--- 19. size scaling ---")


def size_of(repo):
    draft = new_draft("# fixture\n\n## Commands\n- Nothing to declare yet.\n")
    result = run([sys.executable, CTX_WRITE, "--root", repo, "--draft", draft, "--dry-run"],
                 cwd=repo)
    m = re.search(r"^Size\s+(\w+)$", result.stdout, re.MULTILINE)
    return (m.group(1) if m else "?"), result


repo19a = new_repo({"README.md": "# tiny\n", "main.py": "print(1)\n",
                    ".gitignore": "__pycache__/\n"})
size_a, res_a = size_of(repo19a)
print("       3-file repo classified: %s" % size_a)
check("19a a three-file single-unit repo is tiny", size_a == "tiny",
      "got %r; stdout=%r" % (size_a, res_a.stdout[-400:]))

mono = {
    "package.json": pkg_json({"name": "root", "private": True,
                              "workspaces": ["packages/*"], "scripts": {"build": "turbo"}}),
    "packages/web/package.json": pkg_json({"name": "web", "scripts": {"build": "vite"}}),
    "packages/api/package.json": pkg_json({"name": "api", "scripts": {"build": "tsc"}}),
    "packages/web/src/main.ts": "export default 1;\n",
    "packages/api/src/main.ts": "export default 2;\n",
    "README.md": "# mono\n",
}
repo19b = new_repo(mono)
size_b, res_b = size_of(repo19b)
print("       two-workspace repo classified: %s" % size_b)
check("19b two workspace packages make a monorepo", size_b == "monorepo",
      "got %r; stdout=%r" % (size_b, res_b.stdout[-400:]))

medium = {"package.json": pkg_json(PKG), "README.md": "# medium\n"}
for n in range(14):
    medium["src/module_%02d.ts" % n] = "export const v%d = %d;\n" % (n, n)
repo19c = new_repo(medium)
size_c, res_c = size_of(repo19c)
print("       16-file single-unit repo classified: %s" % size_c)
check("19c a single-unit repo past the tiny threshold is medium", size_c == "medium",
      "got %r; stdout=%r" % (size_c, res_c.stdout[-400:]))


# ======================================================================================
print("--- 20. a path that resolves outside the scope ---")
outside = tempfile.mkdtemp(prefix="ctxtest-outside-")
_tempdirs.append(outside)
outside_file = os.path.join(outside, "AGENTS.md")

repo20 = new_repo(dict(BASIC_FILES))
os.symlink(outside_file, os.path.join(repo20, "AGENTS.md"))
draft20 = new_draft("# fixture\n\n## Commands\n- Nothing to declare yet.\n")
r = ctx_write(repo20, draft20, targets="claude")
check("20a a target symlinked outside the root is refused with exit 5",
      r.returncode == 5, "exit %d stderr=%r" % (r.returncode, r.stderr))
check("20b nothing is created outside the root",
      not os.path.exists(outside_file), "%s was created" % outside_file)

outside_pkg = os.path.join(outside, "pkg")
os.makedirs(outside_pkg, exist_ok=True)
repo20b = new_repo(dict(BASIC_FILES))
os.symlink(outside_pkg, os.path.join(repo20b, "pkg"))
draft20b = new_draft("# fixture\n\n## Commands\n- Nothing to declare yet.\n",
                     nested={"pkg": "# pkg\n\n## Commands\n- Nothing here either.\n"})
r = ctx_write(repo20b, draft20b, targets="claude")
check("20c a nested draft path that resolves outside the root is refused with exit 5",
      r.returncode == 5, "exit %d stderr=%r" % (r.returncode, r.stderr))
check("20d and the outside directory stays empty", not os.listdir(outside_pkg),
      "contents: %s" % os.listdir(outside_pkg))
check("20e both refusals use the same error class",
      "outside the scope" in r.stderr, "stderr=%r" % r.stderr)


# ======================================================================================
print("--- 21. accept ---")
repo21, draft21 = basic_repo()
before21 = {rel: read(repo21, rel) for rel in ("AGENTS.md", "CLAUDE.md", "GEMINI.md")}
bumped = json.loads(pkg_json(PKG))
bumped["dependencies"]["left-pad"] = "1.3.9"
write(repo21, "package.json", pkg_json(bumped))
git(repo21, "add", "-A")
git(repo21, "commit", "-q", "-m", "bump left-pad")

r = run([sys.executable, CTX_STAMP, "--root", repo21, "--accept"], cwd=repo21)
check("21a accept after a version-only commit exits 0", r.returncode == 0,
      "exit %d stderr=%r" % (r.returncode, r.stderr))
after21 = {rel: read(repo21, rel) for rel in before21}
check("21b every context file stays byte-identical", after21 == before21,
      "changed: %s" % ", ".join(k for k in before21 if before21[k] != after21[k]))
stamp21 = json.loads(read(repo21, ".contextify/stamp.json"))
check("21c the stamp records generatedBy == accept",
      stamp21.get("generatedBy") == "accept", "got %r" % stamp21.get("generatedBy"))
r = ctx_check(repo21)
check("21d the repo is fresh after accept", r.returncode == 0 and r.stdout == "",
      "exit %d stdout=%r" % (r.returncode, r.stdout))

repo21b, _ = basic_repo()
broken = json.loads(pkg_json(PKG))
del broken["scripts"]["lint:css"]
write(repo21b, "package.json", pkg_json(broken))
r = run([sys.executable, CTX_STAMP, "--root", repo21b, "--accept"], cwd=repo21b)
combined21 = r.stdout + r.stderr
check("21e accept refuses while a quoted command is dead", r.returncode != 0,
      "exit %d" % r.returncode)
check("21f the refusal names the dead claim", "lint:css" in combined21,
      "output=%r" % combined21[:300])


# ======================================================================================
print("--- 22. install_hooks.sh ---")
repo22 = new_repo({"README.md": "# hooks fixture\n"})
r = run(["bash", INSTALL_HOOKS, "--yes", "--targets", "codex,gemini,cursor,git,github",
         repo22], cwd=repo22)
check("22a install_hooks.sh exits 0", r.returncode == 0,
      "exit %d stderr=%r" % (r.returncode, r.stderr))
expected22 = [".codex/hooks.json", ".gemini/settings.json", ".cursor/hooks.json",
              ".githooks/pre-commit", ".github/workflows/contextify-check.yml"]
missing22 = [rel for rel in expected22
             if not os.path.isfile(os.path.join(repo22, rel))]
check("22b all five snippets are written", not missing22,
      "missing: %s" % ", ".join(missing22))

bad_json = []
for rel in expected22[:3]:
    try:
        json.loads(read(repo22, rel))
    except ValueError as exc:
        bad_json.append("%s (%s)" % (rel, exc))
check("22c every JSON snippet parses as JSON", not bad_json, "; ".join(bad_json))

no_path = [rel for rel in expected22[:-1] if CTX_CHECK not in read(repo22, rel)]
workflow22 = read(repo22, expected22[-1])
portable22 = (CTX_CHECK not in workflow22 and '--branch v0.1.0' in workflow22
              and '$RUNNER_TEMP/contextify/skills/contextify/scripts/ctx-check' in workflow22)
check("22d local hooks use this installation and CI fetches a portable release",
      not no_path and portable22, "local missing: %s; portable CI=%s" % (no_path, portable22))

first22 = snapshot(repo22)
r = run(["bash", INSTALL_HOOKS, "--yes", "--targets", "codex,gemini,cursor,git,github",
         repo22], cwd=repo22)
second22 = snapshot(repo22)
check("22e a second run exits 0", r.returncode == 0, "exit %d" % r.returncode)
moved22 = sorted(k for k in set(first22) | set(second22)
                 if first22.get(k) != second22.get(k))
check("22f a second run changes nothing", not moved22, "changed: %s" % ", ".join(moved22))


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
