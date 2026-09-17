#!/usr/bin/env python3
"""ctx_write.py - the only thing in contextify that writes a context file.

Takes a draft directory, merges its bodies into the managed block of every target,
fails closed at the first problem, then writes through a recovery journal and
stamps what it wrote. Finishes by running the check against its own output: a
generated file that cannot pass its own check never survives on disk (D7).

Exit codes:
  0  written, or nothing to write
  2  a managed-block conflict (--yes alone cannot override it)
  4  a refusal: a ceiling, a content rule, a dead claim
  5  a path that resolves outside the scope
  6  the post-write self-check failed and everything was rolled back
"""

import difflib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ctxlib  # noqa: E402

USAGE = """Usage: ctx_write.py --root PATH --draft DIR [--targets LIST] [--dry-run] [--yes]
                    [--json] [--symlink] [--strict] [--force-managed]
                    [--generated-by NAME] [--scope PATH]
       ctx_write.py --root PATH --recover

Targets: claude, codex, gemini, cursor, cursor-rule, copilot. AGENTS.md is always
generated. codex and cursor read AGENTS.md natively, so they add no file; naming them
only turns on their preflight ceilings.
"""


def parse_args(argv):
    opts = {"root": None, "draft": None, "targets": None, "dry_run": False, "yes": False,
            "json": False, "symlink": False, "strict": False, "force": False,
            "generated_by": None, "scope": ".", "recover": False}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--root", "--draft", "--targets", "--generated-by", "--tool-version", "--scope", "--hook") and (i + 1 >= len(argv) or argv[i + 1].startswith("--")):
            raise ctxlib.CtxError("missing value for %s" % arg, 4)
        if arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            raise SystemExit(0)
        if arg == "--root":
            i += 1
            opts["root"] = argv[i] if i < len(argv) else None
        elif arg.startswith("--root="):
            opts["root"] = arg.split("=", 1)[1]
        elif arg == "--draft":
            i += 1
            opts["draft"] = argv[i] if i < len(argv) else None
        elif arg.startswith("--draft="):
            opts["draft"] = arg.split("=", 1)[1]
        elif arg == "--targets":
            i += 1
            opts["targets"] = argv[i] if i < len(argv) else None
        elif arg.startswith("--targets="):
            opts["targets"] = arg.split("=", 1)[1]
        elif arg == "--generated-by":
            i += 1
            opts["generated_by"] = argv[i] if i < len(argv) else None
        elif arg.startswith("--generated-by="):
            opts["generated_by"] = arg.split("=", 1)[1]
        elif arg == "--scope":
            i += 1
            opts["scope"] = argv[i] if i < len(argv) else "."
        elif arg == "--dry-run":
            opts["dry_run"] = True
        elif arg == "--yes":
            opts["yes"] = True
        elif arg == "--json":
            opts["json"] = True
        elif arg == "--symlink":
            opts["symlink"] = True
        elif arg == "--strict":
            opts["strict"] = True
        elif arg == "--force-managed":
            opts["force"] = True
        elif arg == "--recover":
            opts["recover"] = True
        else:
            raise ctxlib.CtxError("unsupported argument: %s" % arg, 4)
        i += 1
    return opts


def fail(message, code):
    sys.stderr.write("contextify: %s\n" % message)
    return code


def read_draft(draft_dir):
    """Root bodies, nested instructions and optional allowlisted supporting drafts."""
    agents_path = os.path.join(draft_dir, ctxlib.AGENTS_MD)
    agents = ctxlib.read_text(agents_path)
    if agents is None:
        raise ctxlib.CtxError("draft %s is missing AGENTS.md" % draft_dir, 4)
    claude = ctxlib.read_text(os.path.join(draft_dir, ctxlib.CLAUDE_MD))
    supporting = {}
    support_dir = os.path.join(draft_dir, "docs", "context")
    if os.path.lexists(support_dir):
        ctxlib.safe_path(draft_dir, "docs/context")
        if not os.path.isdir(support_dir):
            raise ctxlib.CtxError("refused: draft docs/context must be a directory", 4)
        for name in os.listdir(support_dir):
            rel = "docs/context/" + name
            if rel not in ctxlib.SUPPORTING_DOCS:
                raise ctxlib.CtxError("refused: unknown supporting draft %s" % rel, 4)
            path = ctxlib.safe_path(draft_dir, rel)
            if not os.path.isfile(path):
                raise ctxlib.CtxError("refused: supporting draft %s must be a file" % rel, 4)
            text = ctxlib.read_text(path)
            if text is None:
                raise ctxlib.CtxError("refused: unreadable supporting draft %s" % rel, 4)
            supporting[rel] = text.splitlines()
    nested = {}
    for dirpath, dirnames, filenames in os.walk(draft_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if os.path.abspath(dirpath) == os.path.abspath(draft_dir):
            continue
        if ctxlib.AGENTS_MD in filenames:
            rel = os.path.relpath(dirpath, draft_dir).replace(os.sep, "/")
            nested[rel] = ctxlib.read_text(os.path.join(dirpath, ctxlib.AGENTS_MD))
    return (agents.splitlines(),
            claude.splitlines() if claude is not None else None,
            {k: (v or "").splitlines() for k, v in nested.items()}, supporting)


def check_content_rules(body_lines, rel):
    for idx, line in enumerate(body_lines, 1):
        if ctxlib.FENCE_RE.match(line):
            raise ctxlib.CtxError(
                "refused: %s draft line %d opens a fenced code block; a generated "
                "context document carries no code blocks" % (rel, idx), 4)


def resolve_targets(spec):
    if not spec:
        return ["claude"]
    ids = [t.strip() for t in spec.split(",") if t.strip()]
    unknown = [t for t in ids if t not in ctxlib.TARGET_IDS]
    if unknown:
        raise ctxlib.CtxError(
            "refused: unknown target id %s; supported ids are %s"
            % (", ".join(unknown), ", ".join(ctxlib.TARGET_IDS)), 4)
    return ids


def build_outputs(root, targets, agents_body, claude_body, nested, meta, supporting=None):
    """Ordered [(rel, rendered_text)] for every file this run would produce."""
    out = [(ctxlib.AGENTS_MD, ctxlib.render_agents(agents_body, meta))]
    for rel in sorted(nested):
        out.append((rel + "/" + ctxlib.AGENTS_MD,
                    ctxlib.render_agents(nested[rel], meta)))
    for rel, body in sorted((supporting or {}).items()):
        out.append((rel, ctxlib.render_agents(body, meta)))
    if "claude" in targets:
        out.append((ctxlib.CLAUDE_MD, ctxlib.render_claude(claude_body or [], meta)))
    if "gemini" in targets:
        out.append((ctxlib.GEMINI_MD, ctxlib.render_gemini(meta)))
    if "cursor-rule" in targets:
        out.append((ctxlib.CURSOR_RULE, ctxlib.render_cursor_rule(meta)))
    if "copilot" in targets:
        out.append((ctxlib.COPILOT_MD, ctxlib.render_copilot(meta)))
    return out


def check_budgets(outputs, size_class):
    problems = []
    for rel, text in outputs:
        problems.extend(ctxlib.budget_report(None, rel, text))
    if problems:
        raise ctxlib.CtxError(
            "refused: %s" % problems[0] + (
                "" if len(problems) == 1 else " (and %d more)" % (len(problems) - 1)), 4)
    warnings = []
    target_lines = ctxlib.SIZE_TARGETS[size_class]
    agents = dict(outputs).get(ctxlib.AGENTS_MD, "")
    count = len(agents.splitlines())
    if count > target_lines:
        warnings.append("AGENTS.md is %d lines; the %s target is %d, the ceiling is %d"
                        % (count, size_class, target_lines, ctxlib.AGENTS_LINE_CEILING))
    return warnings


def codex_chain(outputs):
    total = 0
    for rel, text in outputs:
        if os.path.basename(rel) == ctxlib.AGENTS_MD:
            total += len(text.encode("utf-8")) + 2  # the separator between chained docs
    return total


def check_preflight(root, targets, outputs):
    notes = []
    ceiling, source = ctxlib.codex_ceiling(root)
    if "codex" in targets:
        problems = ctxlib.codex_chain_problems(root, outputs)
        if problems:
            raise ctxlib.CtxError("refused: " + problems[0], 4)
        notes.append("Codex root-to-leaf chains fit %s bytes (%s)" % (fmt(ceiling), source))
    shadows = ctxlib.override_shadows(root)
    for shadow in shadows:
        notes.append("%s shadows the generated AGENTS.md at that level" % shadow)
    return notes


def fmt(n):
    return "{:,}".format(n)


def check_claims(root, outputs, scope, strict):
    stale = []
    unverified = []
    for rel, text in outputs:
        if os.path.basename(rel) != ctxlib.AGENTS_MD and ctxlib.supporting_scope(rel) is None:
            continue
        for claim in ctxlib.extract_claims(text, rel, "."):
            if scope != ".":
                owner_root = ctxlib.safe_path(root, scope)
                ctxlib.safe_path(owner_root, os.path.relpath(os.path.join(root, claim.cwd), owner_root))
            ctxlib.resolve_claim(claim, root)
            if claim.status == "stale":
                stale.append(claim)
            elif claim.status == "unverified":
                unverified.append(claim)
    if stale:
        first = stale[0]
        raise ctxlib.CtxError(
            "refused: %s:%d quotes %s, which does not resolve (%s)%s"
            % (first.file, first.line, first.text, first.reason,
               "" if len(stale) == 1 else "; %d more dead claims" % (len(stale) - 1)), 4)
    if strict and unverified:
        first = unverified[0]
        raise ctxlib.CtxError(
            "refused under --strict: %s:%d quotes %s, which cannot be verified (%s); "
            "%d unverified claims in all"
            % (first.file, first.line, first.text, first.reason, len(unverified)), 4)
    return unverified


def check_paths(root, outputs):
    ctxlib.validate_state_paths(root)
    for rel, _text in outputs:
        ctxlib.safe_path(root, rel)


def merge_all(root, outputs, stamp, yes, force):
    """[(rel, new_text, old_text, note)] after merging into whatever is on disk."""
    merged = []
    context_files = (stamp or {}).get("contextFiles") or {}
    for rel, rendered in outputs:
        path = ctxlib.safe_path(root, rel)
        existing = ctxlib.read_text(path) if os.path.exists(path) else None
        if existing is not None:
            recorded = (context_files.get(rel) or {}).get("managedBlockDigest")
            if recorded:
                try:
                    body = ctxlib.managed_body_of(existing)
                except ctxlib.CtxError:
                    body = None
                if body is None or ctxlib.block_digest(body) != recorded:
                    if not (yes and force):
                        raise ctxlib.CtxError(
                            "conflict: the managed block in %s was edited since it was "
                            "stamped; restore the block, or review its draft and rerun with "
                            "--yes --force-managed to replace it" % rel, 2)
        keep = "@AGENTS.md" if os.path.basename(rel) == ctxlib.CLAUDE_MD else None
        new_text, note = ctxlib.merge_block(existing, rendered, None, keep_first_line=keep)
        merged.append((rel, new_text, existing, note))
    return merged


def diff_text(rel, old, new):
    old_lines = (old or "").splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    return "".join(difflib.unified_diff(
        old_lines, new_lines, fromfile="a/" + rel, tofile="b/" + rel, n=2))


def cost_table(merged, targets, notes):
    lines = ["", "Target                                  Lines      Bytes  Ceiling"]
    for rel, new_text, _old, _note in merged:
        count = len(new_text.splitlines())
        size = len(new_text.encode("utf-8"))
        base = os.path.basename(rel)
        if base == ctxlib.AGENTS_MD:
            ceiling = "%d lines" % ctxlib.AGENTS_LINE_CEILING
        elif ctxlib.supporting_scope(rel) is not None:
            ceiling = "%d lines" % ctxlib.SUPPORTING_LINE_CEILING
        elif base == ctxlib.CLAUDE_MD:
            ceiling = "%d lines" % ctxlib.CLAUDE_LINE_CEILING
        else:
            ceiling = "none"
        lines.append("%-36s %7d %10s  %s" % (rel, count, fmt(size), ceiling))
    if "claude" in targets:
        lines.append("")
        lines.append("Claude    CLAUDE.md plus the AGENTS.md it imports, against the "
                     "%d-line guidance (guidance, not a cap)" % ctxlib.CLAUDE_LINE_GUIDANCE)
    for note in notes:
        lines.append("          " + note)
    return lines


def summary_block(verb, scope, size_class, targets, written, evidence_count,
                  unverified_count, next_command, verb_result=None):
    lines = ["contextify %s" % verb, ""]
    lines.append(ctxlib.label("Result")
                 + (verb_result or ("written" if written else "unchanged")))
    lines.append(ctxlib.label("Scope") + scope)
    lines.append(ctxlib.label("Size") + size_class)
    lines.append(ctxlib.label("Targets") + ", ".join(targets))
    lines.append("")
    heading = "Files proposed" if verb_result == "proposed" else "Files written"
    lines.append("%-42s %6s" % (heading, "Lines"))
    for rel, count in written:
        lines.append("%-42s %6d" % (rel, count))
    if not written:
        lines.append("%-42s %6s" % ("(nothing changed)", "-"))
    lines.append("")
    lines.append(ctxlib.label_wide("Evidence") + "%2d records" % evidence_count)
    lines.append(ctxlib.label_wide("Unverified") + "%2d claims" % unverified_count)
    lines.append(ctxlib.label_wide("Next") + next_command)
    return lines


def do_recover(root):
    journal_path = ctxlib.safe_path(root, ctxlib.JOURNAL_REL)
    journal = ctxlib.load_json_file(journal_path)
    if journal is None:
        sys.stdout.write("contextify: nothing to recover; there is no "
                         ".contextify/journal.json\n")
        return 0
    entries = validate_journal(root, journal)
    for entry in entries:
        rel = entry.get("path")
        path = ctxlib.safe_path(root, rel)
        current = ctxlib.read_text(path) if os.path.exists(path) else None
        current_digest = ctxlib.digest_bytes(current) if current is not None else None
        if current_digest not in (entry.get("previousDigest"), entry.get("newDigest")):
            return fail("recovery stopped: %s changed since the interrupted write; "
                        "nothing was restored" % rel, 6)
    restored = []
    for entry in entries:
        rel = entry.get("path")
        path = ctxlib.safe_path(root, rel)
        previous = entry.get("previous")
        if previous is None:
            if os.path.exists(path):
                os.unlink(path)
                restored.append(rel)
            continue
        if ctxlib.read_text(path) != previous:
            ctxlib.safe_write(root, rel, previous)
            restored.append(rel)
    os.unlink(journal_path)
    lines = ["contextify recover", "",
             ctxlib.label("Result") + "previous generation restored",
             ctxlib.label("Files") + (", ".join(restored) if restored else "none changed"),
             ctxlib.label("Next") + "/contextify check"]
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


def main(argv):
    opts = parse_args(argv)
    start = opts["root"] or os.getcwd()
    root = ctxlib.repo_root(start)
    if root is None:
        return fail("%s is not inside a git repository" % start, 1)

    ctxlib.validate_state_paths(root)
    opts["scope"] = ctxlib.selected_scope(root, start, opts["scope"])
    if opts["symlink"]:
        return fail("--symlink is not implemented; no files changed", 4)
    if opts["recover"]:
        if opts["dry_run"] or opts["json"]:
            return fail("recovery does not support --dry-run or --json", 4)
        return do_recover(root)

    if not opts["draft"]:
        sys.stderr.write(USAGE)
        return fail("--draft DIR is required", 4)

    journal_path = os.path.join(root, ctxlib.JOURNAL_REL)
    if os.path.exists(journal_path) and not opts["dry_run"]:
        return fail("an interrupted write left .contextify/journal.json; run "
                    "ctx_write.py --root %s --recover first" % root, 6)

    try:
        return run(root, opts)
    except ctxlib.CtxError as exc:
        return fail(exc.message, exc.code)


def run(root, opts):
    draft = read_draft(opts["draft"])
    scope = opts["scope"]
    previous = ctxlib.load_json_file(ctxlib.safe_path(root, ctxlib.STAMP_REL)) or {}
    targets = set(resolve_targets(opts["targets"])) | set(previous.get("targets", []))
    relatives = {ctxlib.AGENTS_MD, *draft[3]}
    relatives.update(rel + "/" + ctxlib.AGENTS_MD for rel in draft[2])
    relatives.update(path for target, path in (("claude", ctxlib.CLAUDE_MD), ("gemini", ctxlib.GEMINI_MD),
                                              ("cursor-rule", ctxlib.CURSOR_RULE), ("copilot", ctxlib.COPILOT_MD)) if target in targets)
    planned = {rel if scope == "." else scope + "/" + rel for rel in relatives}
    # Excluding exactly the proposed outputs gives identical evidence before/after write.
    with ctxlib.planned_outputs(root, planned):
        return run_with_draft(root, opts, draft)


def run_with_draft(root, opts, draft):
    scope = opts["scope"]
    size_class, file_count, unit_count = ctxlib.classify(root)
    previous_stamp = ctxlib.load_json_file(ctxlib.safe_path(root, ctxlib.STAMP_REL)) or {}
    targets = sorted(set(resolve_targets(opts["targets"])) | set(previous_stamp.get("targets", [])))
    agents_body, claude_body, nested, supporting = draft

    check_content_rules(agents_body, ctxlib.AGENTS_MD)
    for rel, body in nested.items():
        check_content_rules(body, rel + "/" + ctxlib.AGENTS_MD)
    for rel, body in supporting.items():
        check_content_rules(body, rel)

    meta = ctxlib.Meta(ctxlib.tool_version(), opts["generated_by"] or "unknown",
                       ctxlib.now_rfc3339(), ctxlib.head_commit(root))
    outputs = build_outputs(root, targets, agents_body, claude_body, nested, meta, supporting)
    if scope != ".":
        outputs = [(scope + "/" + rel, text) for rel, text in outputs]

    check_paths(root, outputs)
    if scope != ".":
        for rel, _text in outputs:
            ctxlib.safe_path(ctxlib.safe_path(root, scope), os.path.relpath(os.path.join(root, rel), os.path.join(root, scope)))

    stamp = ctxlib.load_json_file(os.path.join(root, ctxlib.STAMP_REL))
    for rel, entry in (stamp or {}).get("contextFiles", {}).items():
        if ctxlib.supporting_scope(rel) is None or rel in dict(outputs):
            continue
        text = ctxlib.read_text(ctxlib.safe_path(root, rel))
        if text is None:
            raise ctxlib.CtxError("refused: previously generated %s is missing; include its reviewed draft to restore it" % rel, 4)
        body = ctxlib.managed_body_of(text)
        recorded = entry.get("managedBlockDigest")
        if recorded and (body is None or ctxlib.block_digest(body) != recorded):
            raise ctxlib.CtxError("conflict: omitted supporting document %s has an edited managed block; include a reviewed draft before replacing it" % rel, 2)
        problems = ctxlib.budget_report(root, rel, text)
        if problems:
            raise ctxlib.CtxError("refused: " + problems[0], 4)
    merged = merge_all(root, outputs, stamp, opts["yes"], opts["force"])
    merged.append((".gitignore", ctxlib.gitignore_merged_text(root),
                   ctxlib.read_text(os.path.join(root, ".gitignore")), ""))

    final_outputs = [(rel, text) for rel, text, _old, _note in merged if rel != ".gitignore"]
    warnings = check_budgets(final_outputs, size_class)
    notes = check_preflight(root, targets, final_outputs)
    notes.extend(note for _, _, _, note in merged if note)
    unverified = check_claims(root, final_outputs, scope, opts["strict"])
    all_context_texts = {rel: ctxlib.read_text(ctxlib.safe_path(root, rel)) or ""
                         for rel in ctxlib.present_context_files(root)}
    all_context_texts.update(dict(final_outputs))
    provenance, missing_provenance = ctxlib.provenance_for(root, all_context_texts, opts["draft"], scope,
                                                         updated_files=set(dict(final_outputs)))
    if opts["strict"] and missing_provenance:
        raise ctxlib.CtxError("refused under --strict: %d managed lines lack provenance" % len(missing_provenance), 4)
    unverified.extend(missing_provenance)
    patches = [diff_text(rel, old, new_text) for rel, new_text, old, _note in merged if new_text != old]
    if opts["dry_run"] or not opts["yes"]:
        if opts["json"]:
            sys.stdout.write(json.dumps({"result": "proposed", "scope": scope, "diff": patches, "notes": notes,
                                        "unverified": len(unverified), "warnings": warnings}) + "\n")
            return 0
        out = []
        for rel, new_text, old, _note in merged:
            patch = diff_text(rel, old, new_text)
            if patch:
                out.append(patch.rstrip("\n"))
        out.extend(cost_table(merged, targets, notes))
        out.append("")
        proposed = [(rel, len(new_text.splitlines()))
                    for rel, new_text, old_text, _n in merged if new_text != old_text]
        out.extend(summary_block("init --dry-run", scope, size_class, targets, proposed,
                                 len(ctxlib.collect_evidence(root)), len(unverified),
                                 "/contextify init --yes", verb_result="proposed"))
        for warning in warnings:
            out.append(ctxlib.label("Warning") + warning)
        sys.stdout.write("\n".join(out) + "\n")
        return 0

    changed = [(rel, new_text, old) for rel, new_text, old, _n in merged if new_text != old]

    written_texts = {rel: new_text for rel, new_text, _old, _n in merged}
    new_stamp, new_evidence = stamp_for(root, written_texts, meta, scope)
    ctxlib.attach_provenance(new_stamp, new_evidence, provenance, missing_provenance)
    new_stamp["targets"] = targets

    stamp_path = os.path.join(root, ctxlib.STAMP_REL)
    evidence_path = os.path.join(root, ctxlib.EVIDENCE_REL)
    old_stamp_text = ctxlib.read_text(stamp_path) if os.path.exists(stamp_path) else None
    old_evidence_text = (ctxlib.read_text(evidence_path)
                         if os.path.exists(evidence_path) else None)

    stamp_is_current = (
        stamp is not None
        and ctxlib.stamp_signature(stamp) == ctxlib.stamp_signature(new_stamp))
    if not changed and stamp_is_current:
        if opts["json"]:
            sys.stdout.write(json.dumps({"result": "unchanged", "scope": scope, "diff": [], "unverified": len(unverified)}) + "\n")
            return 0
        sys.stdout.write("\n".join(summary_block(
            "update", scope, size_class, targets, [], len(new_stamp["evidence"]),
            len(unverified), "/contextify check")) + "\n")
        return 0

    if stamp_is_current and old_stamp_text is not None:
        new_stamp["generatedAt"] = stamp["generatedAt"]

    state_targets = [
        (ctxlib.EVIDENCE_REL, ctxlib.dump_json(ctxlib.EVIDENCE_REL, new_evidence),
         old_evidence_text),
        (ctxlib.STAMP_REL, ctxlib.dump_json(ctxlib.STAMP_REL, new_stamp), old_stamp_text),
    ]
    to_write = changed + [t for t in state_targets if t[1] != t[2]]

    journal = {
        "version": 1,
        "startedAt": meta.generated_at,
        "root": root,
        "targets": [{"path": rel,
                     "previous": old,
                     "previousDigest": ctxlib.digest_bytes(old) if old is not None else None,
                     "newDigest": ctxlib.digest_bytes(new_text)}
                    for rel, new_text, old in to_write],
    }
    if not opts["json"]:
        sys.stdout.write("".join(patches))
        sys.stdout.flush()
    check_paths(root, [(rel, text) for rel, text, _old in to_write])
    os.makedirs(ctxlib.safe_path(root, ctxlib.STATE_DIR), exist_ok=True)
    journal_path = os.path.join(root, ctxlib.JOURNAL_REL)
    ctxlib.safe_write(root, ctxlib.JOURNAL_REL, ctxlib.dump_json(ctxlib.JOURNAL_REL, journal))

    crash_after = os.environ.get("CONTEXTIFY_TEST_CRASH_AFTER")
    crash_after = int(crash_after) if crash_after and crash_after.isdigit() else 0

    written = []
    for index, (rel, new_text, _old) in enumerate(to_write, 1):
        path = ctxlib.safe_path(root, rel)
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)
        ctxlib.safe_write(root, rel, new_text)
        written.append((rel, len(new_text.splitlines())))
        if crash_after and index >= crash_after:
            raise RuntimeError(
                "CONTEXTIFY_TEST_CRASH_AFTER=%d: interrupted after %s" % (crash_after, rel))

    result = ctxlib.run_check(root, strict=False)
    if result.status != "fresh":
        rollback(root, journal)
        sys.stderr.write(ctxlib.notice_text(result) + "\n")
        return fail("the generated files did not pass their own check; the previous "
                    "generation was restored", 6)

    os.unlink(ctxlib.safe_path(root, ctxlib.JOURNAL_REL))

    lines = summary_block("init", scope, size_class, targets, written,
                          len(new_stamp["evidence"]), len(unverified),
                          "/contextify check")
    for warning in warnings:
        lines.append(ctxlib.label("Warning") + warning)
    for note in notes:
        lines.append(ctxlib.label("Note") + note)
    if opts["json"]:
        sys.stdout.write(json.dumps({
            "result": "written",
            "diff": patches,
            "notes": notes,
            "scope": scope,
            "size": size_class,
            "files": [{"path": rel, "lines": n} for rel, n in written],
            "evidence": len(new_stamp["evidence"]),
            "unverified": len(unverified),
        }, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write("\n".join(lines) + "\n")
    return 0


def validate_journal(root, journal):
    if not isinstance(journal, dict) or journal.get("version") != 1 or (not isinstance(journal.get("root"), str) or os.path.realpath(journal["root"]) != os.path.realpath(root)) or not isinstance(journal.get("targets"), list):
        raise ctxlib.CtxError("refused: malformed recovery journal", 6)
    entries = journal["targets"]
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ctxlib.CtxError("refused: malformed recovery target", 6)
        rel = entry.get("path")
        ctxlib.safe_path(root, rel)
        allowed = rel in (".gitignore", ctxlib.STAMP_REL, ctxlib.EVIDENCE_REL) or rel in ctxlib.GENERATED_FILES or ctxlib.supporting_scope(rel) is not None or any(rel.endswith("/" + target) for target in ctxlib.GENERATED_FILES)
        previous = entry.get("previous")
        if not allowed or rel in seen or (previous is not None and not isinstance(previous, str)):
            raise ctxlib.CtxError("refused: invalid recovery target", 6)
        seen.add(rel)
        expected = ctxlib.digest_bytes(previous) if previous is not None else None
        if expected != entry.get("previousDigest") or not isinstance(entry.get("newDigest"), str) or not __import__("re").fullmatch(r"sha256:[a-f0-9]{64}", entry["newDigest"]):
            raise ctxlib.CtxError("refused: invalid recovery digest", 6)
    return entries


def rollback(root, journal):
    for entry in validate_journal(root, journal):
        path = ctxlib.safe_path(root, entry["path"])
        if entry["previous"] is None:
            if os.path.exists(path):
                os.unlink(path)
        else:
            ctxlib.safe_write(root, entry["path"], entry["previous"])
    journal_path = ctxlib.safe_path(root, ctxlib.JOURNAL_REL)
    if os.path.exists(journal_path):
        os.unlink(journal_path)


def stamp_for(root, written_texts, meta, scope):
    """The stamp and evidence for a tree where written_texts are already on disk."""
    context_files = {}
    candidates = list(ctxlib.present_context_files(root))
    for rel in sorted(set(list(written_texts) + candidates)):
        if rel == ".gitignore":
            continue
        text = written_texts.get(rel)
        if text is None:
            path = ctxlib.safe_path(root, rel)
            if not os.path.exists(path):
                continue
            text = ctxlib.read_text(path)
        if text is None:
            continue
        context_files[rel] = ctxlib.entry_from_text(text)
    records = ctxlib.collect_evidence(root, extra_paths=sorted(written_texts))
    claims = []
    for rel in sorted(context_files):
        text = written_texts.get(rel) or ctxlib.read_text(os.path.join(root, rel)) or ""
        for claim in ctxlib.extract_claims(text, rel, "."):
            ctxlib.resolve_claim(claim, root)
            claims.append(claim)
    return ctxlib.build_stamp(root, records, claims, context_files, meta, scope)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ctxlib.CtxError as exc:
        sys.exit(fail(exc.message, exc.code))
