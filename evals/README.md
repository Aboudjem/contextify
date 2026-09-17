# contextify evals

The reason this repo carries an eval suite at all: contextify writes files other coding agents
read as fact, and every line in them is supposed to be evidence-backed, omitted, or labelled
`unverified`. A skill that invents a command, or a script that reports a repo fresh when a claim
already died, fails silently in someone else's project. CI here is the only place that gets caught
before it ships.

## a. `check_skill.py`: the design lock as assertions on `SKILL.md`

```bash
python3 evals/check_skill.py skills/contextify/SKILL.md
```

It was written before `skills/contextify/SKILL.md` existed, so its first real run had to be
against the missing file: exit 1, `0 checks passed for <path> (nothing to check: RED)`. Reproduce
that RED any time with `python3 evals/check_skill.py /nonexistent/contextify/SKILL.md`. What it
asserts, by family:

- **Frontmatter and the description contract.** `name` matches the slug pattern and the parent
  directory; `description` sits between the house floor and the Agent Skills spec cap, opens on
  the story sentence verbatim, names the trigger word and every documented trigger phrase,
  promises evidence-or-omit-or-`unverified`, states the check spends zero tokens and never
  rewrites a file on its own, and identifies the intended use. `metadata.version` is
  quoted, `license` is MIT, `argument-hint` names every mode.
- **Structure, references and the pinned design numbers.** The H1 is the bare slug, the house
  sections appear in the house order, honest limits and cross-harness are present, no emoji or em
  dash anywhere, the body stays under the line cap, the `CLAUDE.md` pointer template is fenced as
  one markdown block carrying `@AGENTS.md`, every `references/*.md` path named exists on disk, and
  the line target, line ceiling, `CLAUDE.md` cap, `ctx-check` exit contract, free-form Markdown
  clause and script names are each pinned so a careless edit cannot let them drift.
- **Control sections give orders, not advice.** `you should`, `it is recommended` and their
  neighbours are banned inside the procedure, the hard rules and the failure-modes sections. A
  quoted specimen that bans the wording on purpose is exempt, and the specimen count is pinned.

## b. `test_ctx_check.py` and `test_verify_claims.py`: behaviour tests on the scripts

```bash
python3 tests/test_ctx_check.py
python3 tests/test_verify_claims.py
```

`test_ctx_check.py` builds a throwaway git repository for every case, drives the real scripts as
subprocesses, and asserts what a user would observe: exit codes, stdout bytes, stderr bytes, wall
time, and what is left on disk. It covers the exit contract on a fresh repo and one with no stamp,
noise suppression on a dependency bump, stale claims sorted first when a script is deleted, the
hook envelopes for `claude`, `codex`, `gemini` and `cursor` plus the stdin `cwd` field, `--ci` and
`--ci --strict`, the complete checker's wall time, idempotency, the line-ceiling budget gate, the Codex
byte preflight, an atomic write with no partial file on interruption, and `accept` after a
version-only commit versus `accept` with a dead claim. `test_verify_claims.py` covers the standalone
linter the same way: every quoted command and path resolves or is stale or unverified, `--budget`
fails an oversized file, exit is 1 on any stale claim.

## c. `test_manifests.py`: the release gate

```bash
python3 tests/test_manifests.py
python3 tests/test_regressions.py
python3 tests/test_hooks.py
```

Every manifest parses and agrees on one version, every required repo file exists, `SKILL.md`'s
frontmatter matches `plugin.json`, every relative link in `README.md` resolves, every
`references/*.md` the skill names exists, the translated READMEs carry the may-lag marker, and no
tracked file matches a credential pattern.

## d. The RED baseline: what the built-in `/init` commands produced

[`RED-baseline.md`](RED-baseline.md) records Claude Code's, Codex's and Gemini CLI's own `/init`
against one fixture, a real Next.js app with no existing context file. Gemini failed outright:
exit 55, no file written. Claude wrote a 72-line `CLAUDE.md`, about 1693 tokens by the bytes/4
approximation used there; Codex wrote a 46-line `AGENTS.md`, about 975 tokens; both already hit 0
dead commands and 0 missing paths, with exactly 1 generic line each. Neither carries a timestamp, a
commit hash, or any drift-detection mechanism, and neither wrote anything for another agent. Those
are the numbers contextify has to beat, and the two zeros are floors it has no room to regress
below.

## e. The behavioural scenarios: judged by a human or a separate model

[`scenarios.md`](scenarios.md) covers `init`, `update`, `check`, `accept`, and the traps a
confident model falls into: inventing a test command that does not exist, inferring a deploy model
from a branch name. Each scenario names its setup, the correct run, the failing run, and how to
judge it, mechanically where the deterministic suite already covers the shape, by rubric otherwise.

## f. The dogfood record: measured, not promised

[dogfood.md](dogfood.md) records the current Codex runs on isolated copies of maintained repositories. It distinguishes measured script behavior, independently reviewed drafts, initial failures and any remaining host-specific validation. The [RED baseline](RED-baseline.md) remains the historical Claude/Codex/Gemini experiment from 2026-09-16.

The independent Codex review also led to adversarial cases in `tests/test_regressions.py` and hook-installation cases in `tests/test_hooks.py`. These test boundary escapes, byte preservation, budgets after merging, provenance, previews, and portable hook installation.

Run the checks locally:


```bash
python3 evals/check_skill.py skills/contextify/SKILL.md
python3 tests/test_ctx_check.py
python3 tests/test_verify_claims.py
python3 tests/test_manifests.py
python3 tests/test_regressions.py
python3 tests/test_hooks.py
```

## What a green run proves, and what it does not

A green run proves the file's shape matches the house contract, the scripts hold their exit codes
and claimed behaviour on synthetic repositories, and the release manifests agree with each other.
The suite prints N/N checks passed each time; that number moves as checks grow, so never quote the
current figure as fixed.

None of it proves a real `init` run produces prose worth reading, or that a "verified" command
works. Verified means the script name, target or path resolves where the line says it does.
Nothing was executed. A resolved command can still be broken; only the scenarios and the dogfood
record speak to that.
