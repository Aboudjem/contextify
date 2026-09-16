#!/usr/bin/env python3
"""ctx_stamp.py - write .contextify/evidence.json and .contextify/stamp.json.

Recomputes every normalizer and every claim over the current tree and the context
files that exist, then writes both JSON files. No context file is ever touched.

--accept (D17) is the after-a-refactor verb: the prose is still right, only the
evidence moved. It refuses on a stale claim or a budget violation, keeps every
context file byte-identical, and records generatedBy as "accept".
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ctxlib  # noqa: E402

USAGE = """Usage: ctx_stamp.py --root PATH [--accept] [--generated-by NAME]
                    [--tool-version X] [--scope PATH] [--json]

Writes .contextify/evidence.json and .contextify/stamp.json from the current tree.
Exit: 0 written or already current, 3 no stamp (with --accept), 4 a refusal.
"""


def parse_args(argv):
    opts = {"root": None, "accept": False, "generated_by": None, "tool_version": None,
            "scope": ".", "json": False}
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
        elif arg == "--accept":
            opts["accept"] = True
        elif arg == "--generated-by":
            i += 1
            opts["generated_by"] = argv[i] if i < len(argv) else None
        elif arg.startswith("--generated-by="):
            opts["generated_by"] = arg.split("=", 1)[1]
        elif arg == "--tool-version":
            i += 1
            opts["tool_version"] = argv[i] if i < len(argv) else None
        elif arg == "--scope":
            i += 1
            opts["scope"] = argv[i] if i < len(argv) else "."
        elif arg == "--json":
            opts["json"] = True
        elif not arg.startswith("-") and opts["root"] is None:
            opts["root"] = arg
        i += 1
    return opts


def main(argv):
    opts = parse_args(argv)
    start = opts["root"] or os.getcwd()
    root = ctxlib.repo_root(start)
    if root is None:
        sys.stderr.write("contextify: %s is not inside a git repository\n" % start)
        return 1

    existing = ctxlib.load_json_file(os.path.join(root, ctxlib.STAMP_REL))
    if opts["accept"] and existing is None:
        sys.stdout.write(ctxlib.NOSTAMP_LINE + "\n")
        return 3

    generated_by = opts["generated_by"] or ("accept" if opts["accept"] else "unknown")
    meta = ctxlib.Meta(opts["tool_version"] or ctxlib.tool_version(), generated_by,
                       ctxlib.now_rfc3339(), ctxlib.head_commit(root))

    before = {}
    for rel in ctxlib.present_context_files(root):
        before[rel] = ctxlib.read_text(os.path.join(root, rel))

    stamp, evidence, claims = ctxlib.stamp_now(root, generated_by, opts["scope"], meta)

    if opts["accept"]:
        stale = [c for c in claims if c.status == "stale"]
        if stale:
            for claim in stale:
                sys.stderr.write("contextify: refused: %s:%s quotes %s, which no longer "
                                 "resolves (%s)\n"
                                 % (claim.file, claim.line, claim.text, claim.reason))
            sys.stderr.write("contextify: accept refuses while a quoted command is dead; "
                             "run /contextify update instead\n")
            return 4
        problems = []
        for rel in before:
            text = before[rel] or ""
            problems.extend(ctxlib.budget_report(root, rel, text))
        if problems:
            for problem in problems:
                sys.stderr.write("contextify: refused: %s\n" % problem)
            return 4

    wrote = ctxlib.persist_stamp(root, stamp, evidence)

    for rel, text in before.items():
        after = ctxlib.read_text(os.path.join(root, rel))
        if after != text:
            sys.stderr.write("contextify: internal: %s changed during stamping\n" % rel)
            return 1

    if opts["json"]:
        import json
        sys.stdout.write(json.dumps({
            "written": wrote,
            "generatedBy": stamp["generatedBy"],
            "evidence": len(stamp["evidence"]),
            "claims": len(claims),
            "unverified": len([c for c in claims if c.status == "unverified"]),
        }, ensure_ascii=False) + "\n")
        return 0

    verb = "accept" if opts["accept"] else "stamp"
    lines = [
        "contextify %s" % verb,
        "",
        ctxlib.label("Result") + ("written" if wrote else "already current"),
        ctxlib.label("Scope") + opts["scope"],
        ctxlib.label("Prose") + "unchanged",
        "",
        ctxlib.label("Evidence") + "%d records" % len(stamp["evidence"]),
        ctxlib.label("Claims") + "%d checked" % len(claims),
        ctxlib.label("Unverified") + "%d claims"
        % len([c for c in claims if c.status == "unverified"]),
        ctxlib.label("Next") + "/contextify check",
    ]
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
