#!/usr/bin/env python3
"""ctx_check.py - the slow path of contextify's freshness check.

Recomputes every normalizer over the working tree, compares against the stamp,
re-resolves every claim quoted in the context files and prints the bounded drift
notice (D11). Never writes, never calls a model, never touches the git index.

Exit contract (D9), locked in every mode:
  0 with empty stdout   fresh
  0 with stdout         drift, at most 12 lines and 2,048 bytes
  3                     no stamp yet
  1                     the check itself broke (stderr only, stdout empty)
Never 2. --ci --strict and --git --strict turn drift into exit 1.
"""

import json
import os
import select
import time
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ctxlib  # noqa: E402

USAGE = """Usage: ctx_check.py [--root PATH] [--hook claude|codex|gemini|cursor] [--ci | --git]
                    [--strict] [--json] [--quiet-if-fresh] [PATH]

Prints nothing when the context files are fresh.
"""


def parse_args(argv):
    opts = {"root": None, "hook": None, "ci": False, "strict": False, "json": False,
            "quiet": False, "path": None, "git": False}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--root", "--draft", "--targets", "--generated-by", "--tool-version", "--scope", "--hook") and (i + 1 >= len(argv) or argv[i + 1].startswith("--")):
            raise ctxlib.CtxError("missing value for %s" % arg, 4)
        if arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            raise SystemExit(0)
        elif arg == "--root":
            i += 1
            opts["root"] = argv[i] if i < len(argv) else None
        elif arg.startswith("--root="):
            opts["root"] = arg.split("=", 1)[1]
        elif arg == "--hook":
            i += 1
            opts["hook"] = argv[i] if i < len(argv) else None
        elif arg.startswith("--hook="):
            opts["hook"] = arg.split("=", 1)[1]
        elif arg == "--ci":
            opts["ci"] = True
        elif arg == "--git":
            opts["git"] = True
        elif arg == "--strict":
            opts["strict"] = True
        elif arg == "--json":
            opts["json"] = True
        elif arg == "--quiet-if-fresh":
            opts["quiet"] = True
        elif arg.startswith("-"):
            raise ctxlib.CtxError("unsupported argument: %s" % arg, 1)
        elif opts["path"] is None:
            opts["path"] = arg
        i += 1
    if opts["git"] and (opts["ci"] or opts["hook"] or opts["json"]):
        raise ctxlib.CtxError("--git cannot be combined with --ci, --hook or --json", 1)
    return opts


def read_hook_cwd():
    """The hook writes one JSON object on stdin. A missing or unreadable one is fine."""
    if sys.stdin is None or sys.stdin.isatty():
        return None
    try:
        fd = sys.stdin.fileno()
        raw_bytes = b""
        deadline = time.monotonic() + 0.05
        while len(raw_bytes) < 8192:
            ready, _, _ = select.select([fd], [], [], max(0, deadline - time.monotonic()))
            if not ready:
                break
            chunk = os.read(fd, 8192 - len(raw_bytes))
            if not chunk:
                break
            raw_bytes += chunk
            try:
                json.loads(raw_bytes)
                break
            except (ValueError, UnicodeDecodeError):
                pass
            if time.monotonic() >= deadline:
                break
        raw = raw_bytes.decode("utf-8")
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    cwd = data.get("cwd") if isinstance(data, dict) else None
    return cwd if isinstance(cwd, str) and cwd else None


def emit(out, text, hook):
    if not text:
        return
    if hook:
        out.write(ctxlib.envelope(hook, text) + "\n")
    else:
        out.write(text + "\n")


def main(argv):
    opts = parse_args(argv)
    ctxlib.trace("slow path ctx_check.py")

    start = opts["root"] or opts["path"]
    if start is None and opts["hook"]:
        start = read_hook_cwd()
    if start is None:
        start = os.getcwd() if opts["git"] else os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not os.path.isdir(start):
        if opts["git"]:
            sys.stderr.write("contextify: check failed: directory does not exist\n")
            return 1
        return 0

    root = ctxlib.repo_root(start)
    if root is None:
        if opts["git"]:
            sys.stderr.write("contextify: check failed: not a Git repository\n")
            return 1
        return 0

    if os.path.exists(os.path.join(root, ctxlib.JOURNAL_REL)):
        sys.stderr.write("contextify: an interrupted write left .contextify/journal.json; "
                         "run /contextify update to recover\n")
        return 1

    try:
        result = ctxlib.run_check(root, strict=opts["strict"])
    except ctxlib.CtxError as exc:
        sys.stderr.write("contextify: check failed: %s\n" % exc.message)
        return 1
    except Exception as exc:  # a broken check must stay a warning, never a blocker
        sys.stderr.write("contextify: check failed: %s: %s\n"
                         % (exc.__class__.__name__, exc))
        return 1

    if result.status == "nostamp":
        text = ctxlib.NOSTAMP_LINE
        if opts["json"]:
            sys.stdout.write(json.dumps(ctxlib.json_report(result),
                                        ensure_ascii=False) + "\n")
        else:
            emit(sys.stderr if opts["git"] else sys.stdout, text, opts["hook"])
        if opts["ci"]:
            append_summary(text)
            return 1 if opts["strict"] else 0
        if opts["git"]:
            return 1 if opts["strict"] else 0
        return 3

    if result.status == "fresh":
        if opts["ci"]:
            text = "contextify: fresh"
            if opts["json"]:
                sys.stdout.write(json.dumps(ctxlib.json_report(result),
                                            ensure_ascii=False) + "\n")
            else:
                sys.stdout.write(text + "\n")
            append_summary(text)
        return 0

    text = ctxlib.notice_text(result)
    if opts["json"]:
        sys.stdout.write(json.dumps(ctxlib.json_report(result), ensure_ascii=False) + "\n")
    else:
        emit(sys.stderr if opts["git"] else sys.stdout, text, opts["hook"])
    if opts["ci"]:
        append_summary(text)
        return 1 if opts["strict"] else 0
    if opts["git"] and opts["strict"]:
        return 1
    return 0


def append_summary(text):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ctxlib.CtxError as exc:
        sys.stderr.write("contextify: " + exc.message + "\n")
        sys.exit(1)
