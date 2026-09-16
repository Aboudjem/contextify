#!/usr/bin/env python3
"""
contextify skill eval: machine-checkable static assertions on skills/contextify/SKILL.md.

This is the deterministic half of the eval suite. It encodes the house contract and the
contextify design lock (docs/design/DECISIONS.md, docs/design/SCRIPTS-SPEC.md) as pass/fail
checks, so a regression is caught in CI rather than in someone's repository. It was written
BEFORE the skill existed and run once against the missing file (RED: not found, exit 1); see
evals/RED-baseline.md. The behavioral half, a cold model asked to write an AGENTS.md with no
skill installed, is recorded in the same file.

What it enforces:
  - frontmatter keys present and well-formed (name, description, license, metadata.version,
    argument-hint), with the version quoted and never at the top level;
  - the description is WHEN-only, carries the story sentence verbatim, names the trigger
    words, promises evidence, promises a zero-token check that never rewrites, and contrasts
    with Claude Code's own /init;
  - the required section headings are all present and in the right order;
  - no emoji in any heading, and no em dash anywhere in the file;
  - the body stays under 600 lines, so the depth lives in references/;
  - every references/*.md path the body mentions exists on disk, and all ten are named;
  - the control sections give orders, not advice ("you should" and friends are banned there);
  - the design numbers that a careless edit would duplicate or drift: the line target, the
    ceiling, the CLAUDE.md cap, the check's exit contract, the free-form clause, the pointer
    template, and the names of the five scripts the skill drives.

Usage:
    python3 evals/check_skill.py [path-to-SKILL.md]   # default: skills/contextify/SKILL.md
Exit code 0 = all checks pass, 1 = at least one failed. Standard library only.
"""
import os
import re
import sys

NAME = "contextify"
DEFAULT_PATH = os.path.join("skills", NAME, "SKILL.md")

# Locked byte-identical across the whole repo (README, plugin.json, both editor mirrors,
# marketplace.json, SKILL.md). Compared against the RAW text: the point of locking it is that
# the wording does not drift. tests/test_manifests.py parses the assignment below with
# `^STORY = (.*?)\n\n`, so it stays one line followed by one blank line.
STORY = "Tell every coding agent how your repo works. Then prove it is still true."

# The house section skeleton, in order. Each entry is (what the section DOES, the heading
# prefixes that count as it). Matched on the lowercased heading with backticks stripped, so a
# heading may carry a parenthetical tail, and a skill may use its own domain name for a section
# as long as the function is there. The order is the contract: the story, then how to call it,
# then when not to, then the procedure, then the rules, then the artifact, then the depth, then
# the failure modes.
REQUIRED_SECTIONS = [
    ("the overview", ["## overview"]),
    ("how it is invoked", ["## invocation"]),
    ("when to use it and when not", ["## when to use"]),
    ("the procedure", ["## the run", "## procedure"]),
    ("the hard rules", ["## hard rules", "## what this refuses to do"]),
    ("the output artifact and handoff", ["## the output", "## handoff format"]),
    ("the depth pointer", ["## reference files"]),
    ("the failure modes", ["## common mistakes"]),
]

# House signatures that are required but whose position is not pinned.
UNORDERED_SECTIONS = [
    ("honest limits (what the skill does NOT promise)", ["## honest limits", "## limits"]),
    ("cross-harness (what travels to other agents)",
     ["## cross-harness", "## other agents", "## works in your editor"]),
]

# The sections that give the agent orders. Advice-shaped wording in them is a bug: a hedge in a
# control section is what a model reads as permission to skip the step.
CONTROL_SECTION_LABELS = {"the procedure", "the hard rules", "the failure modes"}
ADVICE_PHRASES = [
    "you should",
    "you may want to",
    "you might want to",
    "it is recommended",
    "it's recommended",
    "if desired",
]
# Quoted specimens: a line that quotes the banned wording in order to ban it. Pinned so the
# hatch cannot widen silently.
EXPECTED_SPECIMENS = 1
QUOTED_RE_TMPL = r'["“‘][^"”’]*{}[^"”’]*["”’]'

# Specimens for the self-tests at the end: the advice gate has to fire on the wrong form and
# stay quiet on an order, because a gate nobody has watched fail is not a gate.
ADVICE_UNQUOTED_SPECIMEN = "You should run the tests before pushing."
ADVICE_QUOTED_SPECIMEN = ('A line that reads "you should run the tests before pushing" is what '
                          "the agent already assumed.")
ORDER_SPECIMEN = "Run the tests before pushing. Never invent a filter flag."

# --- domain invariants ------------------------------------------------------------------
# The contextify design lock. Each of these reads as fine when it is wrong, so it is pinned
# here rather than trusted to review.

# 1. The budget numbers (DECISIONS.md D2). Each appears in the body exactly once, in one place,
#    and every later mention refers back. Two copies of a number is how one of them goes stale.
BUDGET_PATTERNS = [
    ("the line target (60)", r"target (?:of )?60"),
    ("the hard ceiling (150)", r"ceiling (?:of )?150"),
    ("the CLAUDE.md cap (30)", r"under 30"),
]

# 2. The ctx-check exit contract (D9). Exit 2 is reserved for ctx_write.py, which is not a hook.
#    A check that exits 2 from a SessionStart hook is a check the user switches off.
EXIT_CONTRACT = "never exit 2"

# 3. The agents.md convention has no schema (seed skill's Iron rule). A skill that quietly
#    prescribes one produces empty headings, which read as facts.
FREE_FORM_CLAUSE = "AGENTS.md is free-form Markdown"

# 4. The hook's whole promise (D11 plus hooks/hooks.json): a fresh repo costs zero tokens.
FRESH_IS_SILENT = "prints nothing"

# 5. The pointer template. CLAUDE.md line 1 is owned by contextify; if the import goes, Claude
#    Code reads none of this.
POINTER_IMPORT = "@AGENTS.md"

# 6. The ten reference files (the depth lives there, and the body is the only index of them).
REFERENCE_FILES = [
    "agents-and-files.md",
    "section-template.md",
    "detection-signals.md",
    "budget-and-style.md",
    "update-in-place.md",
    "verification.md",
    "hooks-and-ci.md",
    "monorepo.md",
    "comparison.md",
    "init-prompts.md",
]

# 7. The deterministic layer (SCRIPTS-SPEC.md). The skill drives these by name; a rename that
#    reaches only the scripts directory leaves the body telling the model to run nothing.
SCRIPTS = ["detect_repo.sh", "ctx-check", "ctx_write.py", "ctx_stamp.py", "verify_claims.py"]

EM_DASH = "\u2014"  # written as an escape so this file itself carries no em dash

# Emoji blocks. Arrows (U+2190-U+21FF), the middle dot and the maths operators the house style
# uses on purpose are deliberately NOT in here.
EMOJI_RANGES = [
    (0x1F000, 0x1FAFF),
    (0x1F1E6, 0x1F1FF),
    (0x2600, 0x26FF),
    (0x2700, 0x27BF),
    (0xFE0F, 0xFE0F),
    (0x2B00, 0x2BFF),
]


def has_emoji(s):
    return any(any(lo <= ord(ch) <= hi for lo, hi in EMOJI_RANGES) for ch in s)


def advice_hit(line, phrase):
    """(is an unquoted hit, is a quoted specimen) for one line and one banned phrase."""
    if phrase not in line.lower():
        return (False, False)
    if re.search(QUOTED_RE_TMPL.format(re.escape(phrase)), line, re.I):
        return (False, True)
    return (True, False)


def parse_frontmatter(block):
    """Minimal YAML parse for top-level scalars + folded/literal block scalars."""
    data = {}
    lines = block.split("\n")
    i = 0
    key_re = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#") or line[:1] in (" ", "\t"):
            i += 1
            continue
        km = key_re.match(line)
        if not km:
            i += 1
            continue
        key, rest = km.group(1), km.group(2).strip()
        if rest.startswith(("|", ">")):
            collected = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() == "":
                    collected.append("")
                    i += 1
                    continue
                if nxt[:1] in (" ", "\t"):
                    collected.append(nxt.strip())
                    i += 1
                else:
                    break
            data[key] = " ".join(c for c in collected if c != "").strip()
            continue
        val = rest
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        data[key] = val
        i += 1
    return data


def headings(body):
    """(line number, raw heading) for every ATX heading outside fenced code blocks."""
    out, fence = [], None
    fence_re = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
    for n, line in enumerate(body.split("\n"), 1):
        fm = fence_re.match(line)
        if fm:
            if fence is None:
                fence = fm.group(1)[0]
            elif fm.group(1)[0] == fence and not fm.group(2).strip():
                fence = None
            continue
        if fence is None and re.match(r"^#{1,6}\s", line):
            out.append((n, line.rstrip()))
    return out


def section_slices(body):
    """{lowercased `## ` heading: section text} for every H2, heading line included."""
    slices, current, buf = {}, None, []
    for line in body.split("\n"):
        if line.startswith("## "):
            if current is not None:
                slices[current] = "\n".join(buf)
            current = line.strip().replace("`", "").lower()
            buf = [line]
        elif current is not None:
            buf.append(line)
    if current is not None:
        slices[current] = "\n".join(buf)
    return slices


def fenced_blocks(body, lang):
    """Bodies of every ```<lang> fenced block."""
    out, buf, inside = [], [], False
    for line in body.split("\n"):
        if not inside and re.match(r"^\s{0,3}```" + lang + r"\s*$", line):
            inside, buf = True, []
            continue
        if inside and re.match(r"^\s{0,3}```\s*$", line):
            out.append("\n".join(buf))
            inside = False
            continue
        if inside:
            buf.append(line)
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    if not os.path.exists(path):
        print(f"FAIL: {path} not found")
        print("-" * 60)
        print(f"0 checks passed for {path} (nothing to check: RED)")
        return 1

    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not m:
        print(f"FAIL: no YAML frontmatter in {path}")
        print("-" * 60)
        print(f"0 checks passed for {path} (nothing to check: no frontmatter)")
        return 1

    block = m.group(1)
    body = text[m.end():]
    fm = parse_frontmatter(block)
    # `flat` keeps the casing and folds the line wrapping away, so a pinned phrase is found
    # whether or not the author's editor broke it across two lines.
    flat = re.sub(r"\s+", " ", body)
    low = flat.replace("`", "").replace("*", "").lower()
    checks = []

    # --- frontmatter ---
    fm_name = fm.get("name", "")
    parent = os.path.basename(os.path.dirname(os.path.abspath(path)))
    checks.append(("frontmatter: name matches ^[a-z0-9]+(-[a-z0-9]+)*$ and is <= 64 chars",
                   bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fm_name)) and len(fm_name) <= 64,
                   f"got {fm_name!r}"))
    checks.append((f"frontmatter: name equals the parent directory ({parent})", fm_name == parent,
                   f"name={fm_name!r}, directory={parent!r}"))
    desc = fm.get("description", "")
    checks.append(("frontmatter: description is present and non-empty", bool(desc.strip()), ""))
    checks.append(("frontmatter: description is <= 1024 chars (the Agent Skills spec cap)",
                   len(desc) <= 1024, f"{len(desc)} chars, {max(0, len(desc) - 1024)} over"))
    checks.append(("frontmatter: description is >= 400 chars (the house floor)",
                   len(desc) >= 400, f"{len(desc)} chars"))
    checks.append(("frontmatter: description is a folded block scalar (>-)",
                   bool(re.search(r"^description:\s*>-\s*$", block, re.MULTILINE)),
                   "a one-line description this long wraps badly in every reader"))
    checks.append(("frontmatter: metadata.version is present AND quoted",
                   bool(re.search(r"^\s+version:\s*[\"']\d+\.\d+\.\d+[\"']\s*$", block,
                                  re.MULTILINE)),
                   "needs `metadata:` then an indented `version: \"x.y.z\"`, quotes included"))
    checks.append(("frontmatter: no bare top-level version:",
                   not re.search(r"^version:", block, re.MULTILINE),
                   "the version belongs under metadata:"))
    checks.append(("frontmatter: license is MIT",
                   bool(re.search(r"^license:\s*[\"']?MIT[\"']?\s*$", block, re.MULTILINE)), ""))
    checks.append(("frontmatter: argument-hint is declared",
                   bool(re.search(r"^argument-hint:\s*\S", block, re.MULTILINE)), ""))
    checks.append(("frontmatter: argument-hint names the four modes",
                   all(mode in fm.get("argument-hint", "")
                       for mode in ("init", "update", "check", "accept")),
                   f"got {fm.get('argument-hint', '')!r}"))

    # --- description contract (WHEN-only) ---
    checks.append(("description: carries the story sentence verbatim", STORY in desc,
                   "the first sentences must be byte-identical to plugin.json and the README"))
    checks.append(("description: opens on the story sentence", desc.startswith(STORY),
                   f"starts {desc[:60]!r}"))
    checks.append((f"description: names the trigger word {NAME!r}", NAME in desc.lower(), ""))
    trigger_phrases = ["contextify this repo", "write an agents.md", "generate claude.md",
                       "agent context", "context file is stale"]
    missing_triggers = [t for t in trigger_phrases if t not in desc.lower()]
    checks.append(("description: names every documented trigger phrase", not missing_triggers,
                   "missing: " + ", ".join(repr(t) for t in missing_triggers)))
    checks.append(("description: says an unsupported line is labelled unverified",
                   "unverified" in desc.lower(),
                   "evidence-backed, or omitted, or labelled unverified: say so where the "
                   "model reading the description will see it"))
    checks.append(("description: says the drift check spends zero tokens",
                   "zero token" in desc.lower(), ""))
    checks.append(("description: says the check never rewrites a file on its own",
                   "never rewrites" in desc.lower(), ""))
    checks.append(("description: contrasts with Claude Code's own /init", "/init" in desc,
                   "the nearest built-in is the thing a reader has to be able to tell it from"))
    checks.append(("description: is WHEN-only (no numbered procedure steps)",
                   not re.search(r"\b[1-9]\.\s", desc),
                   "a numbered summary in the description becomes a shortcut models follow "
                   "instead of reading the body"))

    # --- structure: the H1 and the ordered section skeleton ---
    hs = headings(body)
    h1 = next((h for _, h in hs if h.startswith("# ")), "")
    checks.append((f"structure: the H1 is `# {NAME}`", h1.strip() == f"# {NAME}", f"got {h1!r}"))

    h2s = [h.strip().replace("`", "").lower() for _, h in hs if h.startswith("## ")]

    def find_section(prefixes):
        for i, h in enumerate(h2s):
            if any(h.startswith(p) for p in prefixes):
                return i
        return None

    found = []
    for label, prefixes in REQUIRED_SECTIONS:
        idx = find_section(prefixes)
        checks.append((f"structure: a section for {label} is present", idx is not None,
                       f"{path} has no H2 starting " + " or ".join(repr(p) for p in prefixes)))
        if idx is not None:
            found.append((label, idx))
    ordered = all(found[k][1] < found[k + 1][1] for k in range(len(found) - 1))
    checks.append(("structure: the required sections appear in the house order", ordered,
                   " then ".join(f"{lbl}@{i}" for lbl, i in found)))

    for label, prefixes in UNORDERED_SECTIONS:
        checks.append((f"structure: a section for {label} is present",
                       find_section(prefixes) is not None,
                       f"{path} has no H2 starting " + " or ".join(repr(p) for p in prefixes)))

    bad_headings = [f"line {n}: {h}" for n, h in hs if has_emoji(h)]
    checks.append(("structure: no emoji in any heading", not bad_headings,
                   "; ".join(bad_headings[:4])))
    checks.append(("structure: no emoji anywhere in the body", not has_emoji(body), ""))

    em_lines = [str(n) for n, line in enumerate(text.split("\n"), 1) if EM_DASH in line]
    checks.append((f"style: no em dash anywhere in {os.path.basename(path)}", not em_lines,
                   f"{path}: em dash on line(s) " + ", ".join(em_lines[:8])
                   + " (use a comma, a full stop, or parentheses)"))

    line_count = body.count("\n")
    checks.append(("structure: body is under 600 lines (the depth lives in references/)",
                   line_count < 600, f"{line_count} lines"))
    checks.append((f"structure: the body documents /{NAME}", f"/{NAME}" in body, ""))
    checks.append(("structure: the body documents $ARGUMENTS", "$ARGUMENTS" in body, ""))
    checks.append(("structure: the body documents all four modes as $ARGUMENTS values",
                   "[init|update|check|accept]" in body,
                   "the argument grammar has to appear in the body, not only in the hint"))
    checks.append((f"structure: the body names the .{NAME}/ state directory",
                   f".{NAME}/" in body, ""))
    checks.append(("structure: the body quotes the story sentence too", STORY in body,
                   "the overview opens on the same sentence the description carries"))

    # --- the pointer template: one fenced ```markdown block, and the import line in it ---
    md_blocks = fenced_blocks(body, "markdown")
    checks.append(("structure: a ```markdown template block is fenced in the body",
                   bool(md_blocks),
                   "the CLAUDE.md pointer must be shown as one fenced ```markdown block"))
    checks.append((f"pointer: the ```markdown block carries the literal line {POINTER_IMPORT!r}",
                   any(POINTER_IMPORT in b.split("\n") for b in md_blocks),
                   "CLAUDE.md line 1 is the import; without it Claude Code reads none of this"))

    # --- references: every path the body names has to exist, and all ten are named ---
    ref_dir = os.path.join(os.path.dirname(os.path.abspath(path)), "references")
    refs = sorted(set(re.findall(r"(?:skills/" + NAME + r"/)?references/([A-Za-z0-9._\-]+\.md)",
                                 body)))
    checks.append(("references: the body names at least one references/*.md file", bool(refs),
                   "a body under 600 lines needs the depth to live somewhere"))
    for ref in REFERENCE_FILES:
        checks.append((f"references: the body names references/{ref}", ref in refs,
                       "the body is the only index of the references directory"))
    for ref in refs:
        target = os.path.join(ref_dir, ref)
        checks.append((f"references: references/{ref} exists on disk", os.path.isfile(target),
                       f"{target} is missing"))

    # --- domain invariants: the design numbers and the locked phrases ---
    for label, pattern in BUDGET_PATTERNS:
        hits = re.findall(pattern, flat)
        checks.append((f"budget: {label} is stated exactly once in the body", len(hits) == 1,
                       f"{len(hits)} match(es) for /{pattern}/; state the budget in one place "
                       "and refer back, or the copies drift apart"))
    checks.append((f"check contract: the body says {EXIT_CONTRACT!r}", EXIT_CONTRACT in flat,
                   "exit 2 belongs to ctx_write.py; a hook that exits 2 gets switched off"))
    checks.append(("check contract: the body names the other exit codes",
                   all(code in low for code in ("exit 0", "exit 3", "exit 1")),
                   "0 fresh, 0 with a notice drift, 3 no stamp, 1 the check itself breaking"))
    checks.append((f"check contract: the body says the hook {FRESH_IS_SILENT!r} when fresh",
                   FRESH_IS_SILENT in flat,
                   "a fresh repo costing zero tokens is the hook's whole promise"))
    checks.append((f"schema: the body states {FREE_FORM_CLAUSE!r}", FREE_FORM_CLAUSE in flat,
                   "the agents.md convention has no required schema; prescribing one is how "
                   "empty headings get written and then read as facts"))
    checks.append(("evidence rule: the body bans code blocks in the generated file",
                   "no code blocks in the generated agents.md" in low, ""))
    checks.append(("evidence rule: the body states the omit-or-label rule",
                   "unverified" in low and "omit" in low, ""))
    checks.append(("evidence rule: the body forbids writing secret values",
                   ".env.example" in body and "secret" in low, ""))
    checks.append(("evidence rule: the body requires a separate verification pass",
                   "separate" in low and "verif" in low, ""))
    for script in SCRIPTS:
        checks.append((f"scripts: the body drives {script}", script in body,
                       "the deterministic layer is only reachable if the body names it"))
    checks.append(("scripts: the body resolves them through ${CLAUDE_SKILL_DIR}",
                   "${CLAUDE_SKILL_DIR}" in body, ""))
    checks.append(("cross-harness: the body says what ${CLAUDE_SKILL_DIR} means elsewhere",
                   "scripts directory next to this file" in low, ""))
    checks.append(("cross-harness: the body names the npx skills add install line",
                   "npx skills add" in body, ""))
    checks.append(("cross-harness: the body says the SessionStart hook is not shipped elsewhere",
                   "install_hooks.sh" in body and "not installed" in low, ""))
    checks.append(("honest limits: the ETH finding is quoted exactly, with no invented figure",
                   "do not generally improve task success rates, while increasing inference "
                   "cost by over 20% on average" in flat and "2602.11988" in body, ""))

    # --- control sections give orders, not advice ---
    # A phrase inside quotation marks is a specimen: the line is quoting the wrong form in order
    # to ban it, which is the only legitimate use. Those are counted and the count is pinned, so
    # the hatch cannot be widened silently. Bumping it is a deliberate act: confirm the line
    # really TEACHES the wrong form, then change the constant in the same commit.
    slices = section_slices(body)
    quoted_specimens = 0
    for want_label, want_prefixes in [(lbl, pre) for lbl, pre in REQUIRED_SECTIONS
                                      if lbl in CONTROL_SECTION_LABELS]:
        sec = next((v for k, v in slices.items()
                    if any(k.startswith(p) for p in want_prefixes)), None)
        if sec is None:
            continue
        for phrase in ADVICE_PHRASES:
            hits = []
            for ln, line in enumerate(sec.split("\n"), 1):
                is_hit, is_specimen = advice_hit(line, phrase)
                if is_specimen:
                    quoted_specimens += 1
                if is_hit:
                    hits.append(ln)
            checks.append((f"control section for {want_label} gives orders, not advice: "
                           f"no {phrase!r}", not hits,
                           f"{path}, inside the {want_label} section, relative line(s) "
                           + ", ".join(str(h) for h in hits[:4])))
        checks.append((f"control section for {want_label} is not empty",
                       len(sec.strip().split("\n")) > 2, f"the {want_label} section has no body"))
    checks.append((f"control sections: quoted wrong-form specimens stay pinned at "
                   f"{EXPECTED_SPECIMENS} ({quoted_specimens} in use)",
                   quoted_specimens == EXPECTED_SPECIMENS,
                   "confirm the line TEACHES the wrong form, then change EXPECTED_SPECIMENS "
                   "in evals/check_skill.py in the same commit"))

    # --- self-tests on the advice gate ---
    checks.append(("gate self-test: the advice gate fires on an unquoted specimen",
                   advice_hit(ADVICE_UNQUOTED_SPECIMEN, "you should") == (True, False), ""))
    checks.append(("gate self-test: a quoted specimen counts as a specimen, not a hit",
                   advice_hit(ADVICE_QUOTED_SPECIMEN, "you should") == (False, True), ""))
    checks.append(("gate self-test: an order is not caught",
                   all(advice_hit(ORDER_SPECIMEN, p) == (False, False) for p in ADVICE_PHRASES),
                   ""))

    failed = [c for c in checks if not c[1]]
    for nm, ok, detail in checks:
        tag = "PASS" if ok else "FAIL"
        extra = f"  ({detail})" if detail and not ok else ""
        print(f"{tag}: {nm}{extra}")
    print("-" * 60)
    print(f"{len(checks) - len(failed)}/{len(checks)} checks passed for {path}")
    if failed:
        print(f"{len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
