#!/usr/bin/env python3
"""verify_claims.py - lint a context file: does everything it quotes still resolve?

Every inline code span and every shell fence is extracted, split into commands, and
resolved against the repository (D16). A positive miss is STALE. A form with no
resolver is UNVERIFIED, never STALE, because contextify would rather say "I cannot
prove this" than accuse a working command.

--budget additionally enforces the line ceilings (150 for AGENTS.md, 30 for CLAUDE.md).
Exit 0 when nothing is stale and no ceiling is broken, 1 otherwise, 2 on bad arguments.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ctxlib  # noqa: E402

USAGE = """Usage: verify_claims.py [--root PATH] [--budget] [--json] [--strict] FILE...

Prints one line per claim: OK|STALE|UNVERIFIED  file:line  text  (reason)
Exit 0 clean, 1 a stale claim or a broken ceiling, 2 bad arguments.
"""


def parse_args(argv):
    opts = {"root": None, "budget": False, "json": False, "strict": False, "files": []}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            raise SystemExit(0)
        if arg == "--root":
            i += 1
            opts["root"] = argv[i] if i < len(argv) else None
        elif arg.startswith("--root="):
            opts["root"] = arg.split("=", 1)[1]
        elif arg == "--budget":
            opts["budget"] = True
        elif arg == "--json":
            opts["json"] = True
        elif arg == "--strict":
            opts["strict"] = True
        elif arg.startswith("-"):
            pass
        else:
            opts["files"].append(arg)
        i += 1
    return opts


def main(argv):
    opts = parse_args(argv)
    if not opts["files"]:
        sys.stderr.write(USAGE)
        return 2

    first = os.path.abspath(opts["files"][0])
    start = opts["root"] or os.path.dirname(first) or os.getcwd()
    root = ctxlib.repo_root(start) or os.path.abspath(start)

    rows = []
    budget_problems = []
    stale = 0
    unverified = 0

    for arg in opts["files"]:
        path = arg if os.path.isabs(arg) else os.path.join(os.getcwd(), arg)
        if not os.path.isfile(path):
            path = os.path.join(root, arg)
        text = ctxlib.read_text(path)
        if text is None:
            sys.stderr.write("contextify: cannot read %s\n" % arg)
            return 2
        rel = ctxlib.relpath_inside(root, path) or os.path.basename(path)
        if opts["budget"]:
            budget_problems.extend(ctxlib.budget_report(root, rel, text))
        for claim in ctxlib.extract_claims(text, rel, "."):
            ctxlib.resolve_claim(claim, root)
            status = {"verified": "OK", "stale": "STALE",
                      "unverified": "UNVERIFIED"}[claim.status]
            if claim.status == "stale":
                stale += 1
            elif claim.status == "unverified":
                unverified += 1
            rows.append({
                "status": status,
                "file": claim.file,
                "line": claim.line,
                "text": claim.text,
                "kind": claim.kind,
                "resolver": claim.resolver,
                "reason": claim.reason,
            })

    failed = stale > 0 or bool(budget_problems) or (opts["strict"] and unverified > 0)

    if opts["json"]:
        sys.stdout.write(json.dumps({
            "root": root,
            "claims": rows,
            "total": len(rows),
            "stale": stale,
            "unverified": unverified,
            "budget": budget_problems,
            "ok": not failed,
        }, ensure_ascii=False) + "\n")
        return 1 if failed else 0

    for row in rows:
        line = "%-11s %s:%s  %s" % (row["status"], row["file"], row["line"], row["text"])
        if row["reason"]:
            line += "  (%s)" % row["reason"]
        sys.stdout.write(line + "\n")
    for problem in budget_problems:
        sys.stdout.write("BUDGET      %s\n" % problem)
    sys.stdout.write("%d claims, %d stale, %d unverified\n" % (len(rows), stale, unverified))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
