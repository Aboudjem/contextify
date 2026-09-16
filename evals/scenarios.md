# contextify behavioural eval scenarios

Scenarios that exercise `init`, `update`, `check` and `accept`, plus the traps a confident model
falls into. Each names a setup, the prompt or command, what a correct run does,
what a failing run looks like, and how to judge it. Judge mechanically wherever a deterministic
script already covers the same shape; use a separate reader otherwise, never the model that
produced the transcript.

The deterministic, in-CI half of the suite is [`check_skill.py`](check_skill.py),
`../tests/test_ctx_check.py`, `../tests/test_verify_claims.py` and `../tests/test_manifests.py`.
Numbers below that come from the design lock are cited with a pointer into
[`../docs/design/DECISIONS.md`](../docs/design/DECISIONS.md).

---

**S1. init on a tiny repo**
Setup: a fixture with about ten tracked files, one manifest, no test runner, no CI, no existing
context file (DECISIONS.md D2: tiny is at most 10 eligible files, one build unit).
Prompt: `/contextify init`.
Correct run: classifies tiny, targets the tiny line budget, drops Architecture, Conventions,
Testing and Repository workflow entirely, writes no placeholder for any of them.
Failing run: writes an `## Architecture` heading built from a directory listing instead of a real
relation between files, or pads the file to look complete.
Judge: mechanical. Grep the generated `AGENTS.md` for `## Architecture`; it must be absent. Maps
to beat-them-here claim 8 in DECISIONS.md.

**S2. init on a Next.js app**
Setup: the same shape of fixture `RED-baseline.md` used, a real Next.js app with `dev`, `build`,
`postinstall`, `start` and `lint` scripts and no `test` script.
Prompt: `/contextify init`.
Correct run: Commands section first, every quoted command resolves against the real scripts, no
code blocks, no invented test command, a single-test line only when a real test path exists.
Failing run: writes `pnpm test` because it looks idiomatic, fences the commands, or duplicates the
README's product description.
Judge: mechanical. Diff quoted commands against `package.json#scripts`. Must beat RED-baseline.md
on the same fixture shape: 0 dead commands, 0 missing paths (hold), generic lines under 1, total
lines under 72, tokens under about 1693.

**S3. init on a monorepo**
Setup: two build units joined by workspace config, each with its own manifest and a different
test command.
Prompt: `/contextify init`.
Correct run: classifies monorepo, writes a root `AGENTS.md`, writes a nested `AGENTS.md` only for
the build unit whose commands actually differ from the root's.
Failing run: writes a nested file for every subdirectory regardless of whether it has its own
build, or repeats the root commands verbatim in the nested file.
Judge: rubric, cross-checked against DECISIONS.md claim 8's monorepo half: targets the monorepo
budget and includes evidenced cross-package architecture.

**S4. init with an existing hand-written CLAUDE.md**
Setup: a hand-written `CLAUDE.md` with real prose and no contextify markers, no `AGENTS.md` yet.
Prompt: `/contextify init`.
Correct run: shows the insertion as a diff before writing, inserts the managed block after the
first H1, preserves every other byte, reports migration pending until the human content is moved.
Failing run: overwrites the file, or silently adopts the human prose as generated content.
Judge: mechanical. Byte-diff the file outside the markers before and after. Maps to beat-them-here
claim 10 in DECISIONS.md.

**S5. update after a script rename**
Setup: a stamped repo whose `AGENTS.md` quotes one script name; that script is renamed in the
manifest, nothing else changes.
Prompt: `/contextify update`, run after `ctx-check` reports drift.
Correct run: re-reads only the moved evidence, revises only the one affected line, keeps every
other managed line and any human sentinel outside the block byte-identical, shows the diff before
writing.
Failing run: regenerates the whole file, drops the human sentinel, or writes without a diff.
Judge: mechanical. Matches `test_ctx_check.py` case 3 (a removed script drifts, names the key and
the script) together with case 11 (a human sentinel survives a further write).

**S6. check when fresh**
Setup: a freshly stamped repo, nothing changed since. Prompt: `/contextify check`.
Correct run: exit 0, empty output, one line telling the user it is fresh.
Failing run: prints anything, calls a model, or touches any file.
Judge: mechanical. Matches `test_ctx_check.py` case 1.

**S7. check after a dependency-version bump only**
Setup: the same fixture, a dependency version bumped in the manifest, no script or key changed.
Prompt: `/contextify check`.
Correct run: still exits 0 with empty output, because the normalizer deliberately ignores
dependency versions.
Failing run: reports drift on a version-only change, training the user to ignore the notice.
Judge: mechanical. Matches `test_ctx_check.py` case 2.

**S8. check after a workflow run: line change**
Setup: a CI workflow whose job step's `run:` line changes to a different command. Prompt: `/contextify check`.
Correct run: reports drift and names `ci#jobs` as the changed evidence key.
Failing run: stays silent on a real command change, or reports drift with no named key.
Judge: mechanical. Grep the notice for `ci#jobs`.

**S9. accept after a refactor that only moved evidence**
Setup: files moved or renamed, but every command and path `AGENTS.md` describes is still
accurate, only the source line moved.
Prompt: `/contextify accept`.
Correct run: revalidates, replaces only `evidence.json` and `stamp.json`, every context file stays
byte-identical, the stamp's `generatedBy` becomes `accept`, the report states plainly that no
prose changed.
Failing run: rewrites prose to freshen it, or accepts without checking for a dead claim first.
Judge: mechanical. Matches `test_ctx_check.py` case 21 and DECISIONS.md D17.

**S10. the hallucination trap**
Setup: a fixture whose README claims `npm test` runs the suite, but the manifest has no `test`
script at all.
Prompt: `/contextify init`.
Correct run: writes "no test runner is configured" or omits the line, never `npm test`.
Failing run: copies the README's claim into `AGENTS.md` as if it were verified.
Judge: mechanical. Grep the generated file for `npm test`; it must be absent.

**S11. the deploy-inference trap**
Setup: a branch named `prod`, no CI workflow, no infrastructure-as-code files. Prompt: `/contextify init`.
Correct run: writes no deploy model at all. A deploy claim needs CI config, infrastructure as
code, deploy config, or a read-only cloud read, never a branch name alone.
Failing run: writes "deploys from prod" or similar, inferred from the branch name.
Judge: mechanical. Grep the generated file for a deploy claim; if present, it must trace to a
source other than the branch name.

**S12. the 12-line notice bound**
Setup: a stamped fixture, then one commit that moves 20 evidence keys and kills 6 claims.
Prompt: `ctx-check` (or `/contextify check`).
Correct run: the notice stays at most 12 lines and 2048 bytes, exit 0, dead claims first, the last
line names the next command.
Failing run: the notice grows past the bound, or drops the next-command line.
Judge: mechanical. Matches DECISIONS.md beat-them-here claim 6 and its stated test.

**S13. the Codex 32 KiB preflight refusal**
Setup: a draft `AGENTS.md` under the line ceiling but large enough in bytes that the Codex
instruction chain would exceed 32,768 bytes, with `codex` selected as a target.
Prompt: `/contextify init --dry-run`, then an attempted write.
Correct run: the dry-run cost table names the actual byte count and the ceiling, the write
refuses, nothing is written.
Failing run: writes anyway and lets Codex silently truncate the file.
Judge: mechanical. Matches DECISIONS.md beat-them-here claim 9 and `test_ctx_check.py` case 13.

**S14. the mistakes-log promotion rule**
Setup: `.contextify/mistakes.md` exists with one entry describing a single incident. Prompt: `/contextify update`.
Correct run: reads the log, does not promote the single entry into a rule, because promotion
requires the same pattern in more than one entry.
Failing run: promotes a one-off entry into a Do-not rule in `AGENTS.md`.
Judge: rubric. No deterministic script covers `mistakes.md` yet, so this stays a judged transcript
until a test is added.

---

## How to run these scenarios

- **Deterministic (CI), the parts that are mechanical above:**
  ```bash
  python3 evals/check_skill.py skills/contextify/SKILL.md
  python3 tests/test_ctx_check.py
  python3 tests/test_verify_claims.py
  python3 tests/test_manifests.py
  ```
- **Behavioural:** build the fixture the scenario describes, prompt a model with the given
  prompt, and check the produced file and transcript against the correct-run and failing-run
  description. For the rubric scenarios (S3, S14), score with a separate model that did not
  produce the transcript.
- **Record what you run.** [`RED-baseline.md`](RED-baseline.md) is the recorded pattern to follow.
  Redact hosts, paths and tokens before a transcript goes anywhere near this repo.
