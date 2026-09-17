# Dogfood: Codex continuation, 17 September 2026

These are new runs against isolated copies of real repositories. Codex read the skill and primary
files, drafted the managed bodies, and an independent Codex agent re-derived every factual line
before the writer applied them. No Claude model was called. This proves the adapted Codex
workflow, not Claude generation behavior or agreement between different model families.

The final strict runs passed: three generated outputs, no dead commands, no unverified claims
or unsupported managed lines, silent freshness, byte-and-mtime idempotence, human-note
preservation and real drift detection. Two original human-context migrations were safely
refused for exceeding the line ceilings. Those refusals are not successful migrations.

## Isolation and provenance

Only tracked files from each working tree were copied into independent temporary Git
repositories. No original repository was edited. The copies have an index but no synthetic
commit, so their generated stamps record a null commit. Original source revisions are recorded
separately in [source-snapshots.json](dogfood-evidence/source-snapshots.json).

| Source | Source HEAD | Tracked files copied | Initial context |
| --- | --- | ---: | --- |
| 10x | `451ddc695d899374431814cc646c70c2a929a07a` | 49 | AGENTS 66 lines, CLAUDE 116 lines |
| HazeLab | `852985b98dd80b0aceecc4b133ed3c9e74145277` | 67 | None |
| secure-my-app | `21cbf590166fc0f4faed9fce2a2d806dafea0436` | 56 | AGENTS 161 lines |

HazeLab's existing untracked work was neither copied nor touched. The timestamped
[original-file comparison](dogfood-evidence/originals-check.json) rehashed all 172 copied source
files after the first runs and found no change in their original locations. Later authorized
edits by other delivery lanes are outside that comparison.

10x and secure-my-app also have separately named `fresh-context` variants. These omit the old
root instruction files only in a new scratch copy. Their measurements do not claim successful
migration or condensation of the original human files. Final runs used newly rebuilt copies,
not the already-stamped first-pass trees.

## Procedure and independent review

Each copy was resolved as its own Git root. The detector ran first; package manifests, CI,
configuration, scripts and existing instructions were then read. Every factual draft line has
an explicit SHA-256 to source-location mapping. The
[independent review](dogfood-evidence/independent-review.md) confirmed all factual lines. The
10x read-when mapping was tightened to its direct primary source, docs/SYNC.md:1, and independently
confirmed again. No draft claim was approved by its author.

The final writer ran with `--strict`. The source mappings are persisted in both evidence.json
and stamp.json, with no unsupported managed line. Temporary drafts are excluded from context
files. Generated snapshots are named `AGENTS.generated.md` and `CLAUDE.generated.md` in this
report's artifacts so they do not become active nested instructions in the Contextify repository.
The snapshot metadata retains the original filenames from the measured repository.

The commands used local scripts by absolute path. Shareable records replace machine-specific
prefixes with `$SCRIPTS` and `$SCRATCH`:

```sh
python3 "$SCRIPTS/ctx_write.py" --root "$SCRATCH/hazelab" \
  --draft "$SCRATCH/hazelab/.contextify/draft" --targets codex,claude \
  --generated-by codex --strict --dry-run
python3 "$SCRIPTS/ctx_write.py" --root "$SCRATCH/hazelab" \
  --draft "$SCRATCH/hazelab/.contextify/draft" --targets codex,claude \
  --generated-by codex --strict --yes
python3 "$SCRIPTS/verify_claims.py" --root "$SCRATCH/hazelab" \
  --budget "$SCRATCH/hazelab/AGENTS.md" "$SCRATCH/hazelab/CLAUDE.md"
sh "$SCRIPTS/ctx-check" "$SCRATCH/hazelab"
```

The other runs use their corresponding copy names. Each operation's exit status, stdout and
stderr is saved beside its generated snapshots. Fresh checks omit `--ci`: all returned exit 0
with empty stdout. A later check also compared every copy file before and after and confirmed
no write. No dependency install, application build or application test is implied by these checks.

## Final generated-only measurements

Counts describe files before the preservation probe added a human note. Approximate tokens are
UTF-8 bytes divided by four, not tokenizer measurements. Evidence counts are normalized records;
provenance counts are persisted factual-line mappings. Full measurements, timestamps, TSV hashes
and exact core script digests are in [measurements.json](dogfood-evidence/measurements.json).

| Copy | AGENTS lines | Bytes | Approx. tokens | CLAUDE lines | Evidence | Provenance | Unverified |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HazeLab | 15 | 732 | 183 | 4 | 5 | 6 | 0 |
| 10x, fresh context | 16 | 769 | 192.25 | 4 | 3 | 6 | 0 |
| secure-my-app, fresh context | 13 | 626 | 156.5 | 4 | 2 | 4 | 0 |

- HazeLab: dead commands: 0; dead paths: 0; unsupported managed lines: 0.
- 10x fresh context: dead commands: 0; dead paths: 0; unsupported managed lines: 0.
- secure-my-app fresh context: dead commands: 0; dead paths: 0; unsupported managed lines: 0.

All three initial strict writes succeeded. A second identical run preserved both bytes and
mtime for AGENTS.md, CLAUDE.md, .gitignore, stamp.json and evidence.json. A human suffix with CRLF
then survived a subsequent writer run byte for byte. Each deliberate source break produced a
stale-claim notice, and restoring the source returned the check to silence. The final script
hashes still matched at the end of all probes.

## Exact final writer summaries

HazeLab:

```text
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -0,0 +1,15 @@
+<!-- contextify:begin v1 -->
+<!-- Generated by contextify 0.1.0; writer=codex; at=2026-09-17T08:04:53Z; commit=none; regenerate: /contextify update -->
+# HazeLab
+## Commands
+- Development from the repository root: `pnpm run dev`.
+- Build: `pnpm run build`; this generates the Prisma client before building Next.js.
+- Lint: `pnpm run lint`.
+## Testing
+- No test script is declared in `package.json`; do not assume a package-manager test command exists.
+- `vitest.config.ts` selects jsdom and discovers TypeScript tests under the tests directory.
+## Read when relevant
+- `prisma.config.ts` sets the schema and migration locations; read it before changing database tooling.
+
+verified on 2026-09-17 against none
+<!-- contextify:end -->
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -0,0 +1,4 @@
+@AGENTS.md
+<!-- contextify:begin v1 -->
+<!-- Generated by contextify 0.1.0; writer=codex; at=2026-09-17T08:04:53Z; commit=none; regenerate: /contextify update -->
+<!-- contextify:end -->
contextify init

Result   written
Scope    .
Size     medium
Targets  claude, codex

Files written                               Lines
AGENTS.md                                      15
CLAUDE.md                                       4
.contextify/evidence.json                     184
.contextify/stamp.json                        180

Evidence      5 records
Unverified    0 claims
Next         /contextify check
Note     Codex root-to-leaf chains fit 32,768 bytes (.codex/config.toml project_doc_max_bytes not set)
Note     created
Note     created
```

10x, fresh context:

```text
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -0,0 +1,16 @@
+<!-- contextify:begin v1 -->
+<!-- Generated by contextify 0.1.0; writer=codex; at=2026-09-17T08:04:56Z; commit=none; regenerate: /contextify update -->
+# 10x marketplace
+## Commands
+- Test from the repository root: `npm test`.
+- Validate the marketplace structure: `npm run validate`.
+- Check upstream version pins: `npm run sync:check`.
+## Architecture
+- `scripts/sync-plugins.mjs` reads `.claude-plugin/marketplace.json` and updates its version pins only in write mode.
+## Boundaries
+- Keep the marketplace manifest free of a top-level version and metadata keywords; `scripts/validate-marketplace.mjs` rejects both.
+## Read when relevant
+- `docs/SYNC.md` explains the version-pin synchronization workflow.
+
+verified on 2026-09-17 against none
+<!-- contextify:end -->
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -0,0 +1,4 @@
+@AGENTS.md
+<!-- contextify:begin v1 -->
+<!-- Generated by contextify 0.1.0; writer=codex; at=2026-09-17T08:04:56Z; commit=none; regenerate: /contextify update -->
+<!-- contextify:end -->
--- a/.gitignore
+++ b/.gitignore
@@ -13,2 +13,7 @@
 # goalify briefs + conditions (local)
 .goal/
+
+# START contextify
+.contextify/draft/
+.contextify/journal.json
+# END contextify
contextify init

Result   written
Scope    .
Size     medium
Targets  claude, codex

Files written                               Lines
AGENTS.md                                      16
CLAUDE.md                                       4
.gitignore                                     19
.contextify/evidence.json                     166
.contextify/stamp.json                        195

Evidence      3 records
Unverified    0 claims
Next         /contextify check
Note     Codex root-to-leaf chains fit 32,768 bytes (.codex/config.toml project_doc_max_bytes not set)
Note     created
Note     created
```

secure-my-app, fresh context:

```text
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -0,0 +1,13 @@
+<!-- contextify:begin v1 -->
+<!-- Generated by contextify 0.1.0; writer=codex; at=2026-09-17T08:04:58Z; commit=none; regenerate: /contextify update -->
+# secure-my-app
+## Commands
+- Validate the skill from the repository root: `python3 evals/check_skill.py skills/secure-my-app/SKILL.md`.
+- Run release checks: `python3 tests/test_manifests.py`.
+## Boundaries
+- When invoking the skill, remain read-only until the user approves a fix.
+## Read when relevant
+- `skills/secure-my-app/references/controls.md` contains the DETECT and VERIFY catalogue used by the skill.
+
+verified on 2026-09-17 against none
+<!-- contextify:end -->
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -0,0 +1,4 @@
+@AGENTS.md
+<!-- contextify:begin v1 -->
+<!-- Generated by contextify 0.1.0; writer=codex; at=2026-09-17T08:04:58Z; commit=none; regenerate: /contextify update -->
+<!-- contextify:end -->
--- a/.gitignore
+++ b/.gitignore
@@ -30,2 +30,7 @@
 # build journal (local resumability only)
 docs/audit/
+
+# START contextify
+.contextify/draft/
+.contextify/journal.json
+# END contextify
contextify init

Result   written
Scope    .
Size     medium
Targets  claude, codex

Files written                               Lines
AGENTS.md                                      13
CLAUDE.md                                       4
.gitignore                                     36
.contextify/evidence.json                     138
.contextify/stamp.json                        118

Evidence      2 records
Unverified    0 claims
Next         /contextify check
Note     Codex root-to-leaf chains fit 32,768 bytes (.codex/config.toml project_doc_max_bytes not set)
Note     created
Note     created
```

## Real drift probes

HazeLab: removed the actual lint script from the copied package manifest. Exact exit-0 notice:

```text
contextify: drift
Scope    .
Stale    AGENTS.md:7 references pnpm run lint
Changed  package.json#scripts
Changed  provenance:package.json:10
Removed  script lint
Files    0 written
Next     /contextify update
Accept   unavailable until the stale command is corrected
```

10x fresh context: removed validate from its copied package manifest. The notice names
`AGENTS.md:6 references npm run validate`, package scripts and the corresponding provenance line.
secure-my-app fresh context: moved the declared Python check out of its path; the notice names
`AGENTS.md:6 references python3 tests/test_manifests.py` and tree#depth2. Exact notices are in
[10x drift](dogfood-evidence/10x-fresh-context/drift.json) and
[secure-my-app drift](dogfood-evidence/secure-my-app-fresh-context/drift.json). Every mutation was
reversed afterwards; all three restored checks were silent.

## Existing human context: preserved and refused

The final writer refused both dry-run and apply for the original-context copies, with exit 4:

```text
contextify: refused: CLAUDE.md is 120 lines; the ceiling is 30
contextify: refused: AGENTS.md is 174 lines; the ceiling is 150 (Claude Code guidance: keep context files under 200 lines)
```

All bytes in each copy, including its index and human instructions, remained unchanged. Neither
copy gained a stamp. See [preservation-refusals.json](dogfood-evidence/preservation-refusals.json).
The user must decide how to shorten or relocate the original human material; the writer never
silently condenses it to make the budget pass.

The first-pass linter also reported 7 stale and 22 unverified claims in 10x's human context, and
20 stale and 13 unverified in secure-my-app. These are not counts of dead commands. Some prose
shorthand was interpreted as a root-relative path: repository slugs, N/A and filenames named
after their parent directory can be false positives. The 10x human text also named a root
gitleaks configuration absent from the snapshot. The budgets are unambiguous; the path findings
need interpretation. Original outputs remain in `*-existing-context-verify.json`, explicitly
first-pass evidence rather than a current resolver score.

## Findings that changed the implementation

The initial runs found two defects. Preflight checked the generated block before merging human
content, so it accepted over-budget proposals. The initial stamp also included the temporary
draft, which disappeared after the writer installed ignore rules and broke first-to-second
idempotence. Both failed observations are retained under
[first-pass evidence](dogfood-evidence/first-pass/measurements.json). The final runs above prove
merged-budget refusal and idempotence with newly created copies after the corrections.

The generated HazeLab text distinguishes an absent package test script from its existing Vitest
configuration. It does not invent a test command or say no test runner exists. The other drafts
avoid repeating product catalogs and retain sourced commands and operational boundaries.
No human has hand-tightened these new external drafts; independent Codex review is not presented
as human approval.

## Contextify self-dogfood

The repository's own instructions were written through the strict writer and independently
reviewed with Codex. The [self-run record](dogfood-evidence/self-results.json), captured on
2026-09-17 at 08:12 UTC, records 27 lines in AGENTS.md and 4 in CLAUDE.md. AGENTS.md contains
1,722 UTF-8 bytes, approximately 430.5 tokens by bytes/4; the stamp has 2 normalized evidence
records. The recorded hashes matched the local files when these measurements were added.

The no-op writer preserved the bytes of both instruction files, both metadata files and
.gitignore. This self-run records byte identity; it does not assert mtime identity. The ordinary
checker exited 0 with empty stdout and stderr. The strict claim-and-budget check exited 0:

```text
17 claims, 0 stale, 0 unverified
```

The external real-drift and CRLF preservation probes are described separately above. No fresh
Claude model session, human hand-tightening or successful published CI run is implied by this
self-run.

## Validation boundaries

- Installation validation is separate; no installation result is inferred from these runs.
- Claude's weekly limit prevents a fresh Claude model generation run. An independent Codex
  agent is not a different model family; neither unperformed validation is claimed.
- A resolved command means its declaration or target exists, not that it passed execution.
- Smaller instruction files do not establish better task success, lower model cost or better
  editorial quality. No such advantage is claimed.
