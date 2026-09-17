# contextify scripts: the contract between the skill and the deterministic layer

Design: 2026-09-16. Implementation corrections: 2026-09-17. This document binds `docs/design/DECISIONS.md` (the design) to concrete files under `skills/contextify/scripts/`. Where DECISIONS.md and this file disagree, this file wins for implementation details; the run brief's locked constraints win over both. Everything here is zero-dependency: POSIX `sh` (bash 3.2 safe) and python3 standard library only (python3 >= 3.11 assumed for `tomllib`; when `tomllib` is missing, the pyproject normalizer falls back to a bounded regex over `[project.scripts]` and marks the rest `unverified`).

## Division of labour

The skill (SKILL.md, run by the model) does the reading and the prose. The scripts do everything deterministic: discovery, evidence normalizing, claim extraction and liveness, budgets, ceilings, managed-block merging, atomic writes, the stamp, the drift check and the hook envelopes. The model never writes a context file directly; it writes a draft and hands it to `ctx_write.py`, which is the only thing that touches the targets.

## Files

| File | Language | Role |
|---|---|---|
| `detect_repo.sh` | bash 3.2 | read-only fact sheet of a repo (seed: agent-context's `detect_repo.sh`, extended) |
| `ctx-check` | POSIX sh | resolves its own installation path and delegates to the complete checker |
| `ctxlib.py` | python3 | shared library: digests, discovery globs, normalizers, claim extraction and resolvers, stamp and evidence IO, managed-block parsing, sizing, budgets, ceilings, journal, atomic writes, envelopes |
| `ctx_check.py` | python3 | slow path: recompute evidence, compare, claim liveness, print the notice, `--hook`, `--ci`, `--strict`, `--json` |
| `ctx_write.py` | python3 | the writer: takes a draft dir, merges managed blocks into every target, preflight, `--dry-run` cost report, diff, journaled atomic write, then stamps and self-checks |
| `ctx_stamp.py` | python3 | writes `.contextify/evidence.json` + `.contextify/stamp.json` from the current tree and context files; `--accept` mode |
| `verify_claims.py` | python3 | lint a context file: every quoted command and path resolves; `--budget` enforces line ceilings; exit 1 on a miss |
| `install_hooks.sh` | bash 3.2 | opt-in writer of the Codex / Gemini / Cursor / git pre-commit / GitHub Action snippets; idempotent; diff first; `--yes` |

Every script accepts `--help` and prints a usage block. Every script is executable (`chmod +x`) and has the right shebang (`#!/bin/sh` for ctx-check, `#!/usr/bin/env bash` for the two bash scripts, `#!/usr/bin/env python3` for the rest). No script imports anything outside the standard library.

## State directory: `.contextify/` in the target repo

| Path | Committed? | Content |
|---|---|---|
| `stamp.json` | yes (recommended) | DECISIONS.md D14 schema, `version: 2` |
| `evidence.json` | yes (recommended) | `{ "version": 1, "generatedAt": ..., "records": [ { "key": "package.json#scripts", "source": {"file": "package.json", "line": 5}, "value": <normalized value or digest>, "claims": ["<claim id>", ...] } ] }` |
| `draft/` | no (gitignored by the writer's `.gitignore` block) | the model's drafts: `AGENTS.md`, optional `CLAUDE.md` addendum, optional nested `<pkg>/AGENTS.md` |
| `journal.json` | no | present only during a write (D7); its presence makes `ctx-check` exit 1 |
| `mistakes.md` | user's choice | optional bounded log (D18) |

`ctx_write.py` maintains an idempotent block in the target repo's `.gitignore`:

```
# START contextify
.contextify/draft/
.contextify/journal.json
# END contextify
```

## Discovery globs (the evidence surface)

The complete checker uses `DISCOVERY_GLOBS` in `ctxlib.py` as the normalizer discovery surface, alongside quoted paths and explicit provenance sources:

```
package.json */package.json packages/*/package.json apps/*/package.json
package-lock.json pnpm-lock.yaml yarn.lock bun.lockb bun.lock pnpm-workspace.yaml lerna.json nx.json turbo.json
tsconfig.json tsconfig.*.json
Makefile makefile GNUmakefile justfile Justfile .justfile
pyproject.toml setup.py setup.cfg requirements.txt Pipfile poetry.lock uv.lock tox.ini noxfile.py
Cargo.toml Cargo.lock go.mod go.work Gemfile pom.xml build.gradle build.gradle.kts settings.gradle settings.gradle.kts
Dockerfile */Dockerfile docker-compose.yml docker-compose.yaml compose.yml compose.yaml
.github/workflows/*.yml .github/workflows/*.yaml .gitlab-ci.yml
.env.example .env.sample .env.template
vercel.json netlify.toml fly.toml render.yaml Procfile serverless.yml amplify.yml apprunner.yaml cdk.json
AGENTS.md CLAUDE.md GEMINI.md .github/copilot-instructions.md .cursor/rules/contextify.mdc
```

Plus the tree at depth two (`tree#depth2`), computed from `git ls-files` names only.

## `ctx-check` (POSIX sh)

Usage: `ctx-check [--hook claude|codex|gemini|cursor] [--ci] [--strict] [--json] [--quiet-if-fresh] [PATH]`

The entry point resolves its script directory before changing working directory and delegates to `ctx_check.py`. The earlier index-only shortcut missed deleted quoted sources, nested context and untracked evidence; it is not used to certify freshness. Every check uses the complete evidence and claim evaluation. Git-list caching is limited to one read-only check invocation.

Under a hook, input reads are bounded and JSON `cwd` selects the repository. A missing or incomplete input falls back to the environment/current directory. Check worktree selection and open-pipe behavior in `tests/test_regressions.py`.

The warm-cache runtime target remains below 100 ms; the timing regression allows 250 ms to tolerate CI variability. Quote actual measurements from a current run, not this target.

## `ctx_check.py`

Same flags. Steps: load stamp and evidence; recompute every normalizer over the working tree; diff evidence keys (added / removed / changed); re-extract claims from every context file listed in `contextFiles` (managed and human lines alike); resolve each claim; a claim that no longer resolves is `stale`; a context file whose `managedBlockDigest` differs from the stamp is `edited` (reported once, not as drift). Decide:

- No evidence change, no stale claim, no missing context file: fresh. Exit 0, stdout empty (even if the fast key mismatched, which happens after a dependency bump; the stamp is NOT rewritten by check).
- Otherwise: the drift notice (D11), max 12 lines and 2,048 bytes, dead claims first. Exit 0 with the notice on stdout.
- With `--hook claude` or `--hook gemini`: wrap the notice as `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<notice>"}}` on one line; with `--hook codex`: `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<notice>"}}` as well (same shape, kept separate in code so it can diverge); with `--hook cursor`: `{"additional_context": "<notice>"}`. Fresh prints nothing under every envelope.
- `--json`: one line of JSON `{"status": "fresh|drift|nostamp|broken", "changed": [...], "removed": [...], "added": [...], "stale": [{"file","line","text","reason"}], "next": "..."}`; fresh still prints nothing unless `--ci`.
- `--ci`: print the notice (or `contextify: fresh` when fresh) to stdout, and also append the same to `$GITHUB_STEP_SUMMARY` if that variable is set. Exit 0 always, except with `--strict`: exit 1 on drift or no stamp.
- Any internal exception: one line on stderr `contextify: check failed: <reason>`, stdout empty, exit 1.

## Evidence normalizers (D15, condensed to what ships in 0.1.0)

Each normalizer is a function `normalize_<name>(root) -> dict[key, value]` where `value` is a JSON-serializable canonical structure; the stored digest is `sha256` over canonical JSON (sorted keys, compact separators). Keys:

`package.json#scripts` (script name -> body), `package.json#deps` (names only, per group), `package.json#packageManager` (name only), `package.json#workspaces`, `package.json#engines` (names only), `lockfile#present` (sorted list of present lockfile names), `ci#jobs` (per workflow: job ids, `run:` strings in order, `working-directory`), `dockerfile#from+expose`, `compose#services`, `tsconfig#paths+strict+target+module`, `env.example#keys` (names only; the value after `=` is never read into memory as a string that is stored), `tree#depth2`, `makefile#targets`, `justfile#recipes`, `pyproject#scripts`, `cargo#bins`, `go.mod#module+go`, `gemfile#present`, `jvm#present`, `deploy#files` (which deploy config files exist). Nested `packages/*/package.json` produce keys prefixed by the relative dir, e.g. `packages/web/package.json#scripts`.

YAML is parsed with a bounded line-based reader (jobs, steps, `run:` scalars including `|` and `>` blocks, `working-directory`); anything the reader cannot follow yields `unverified` rather than a wrong value. No YAML library.

## Claim extraction and resolvers (D16)

Extract from every context file: inline code spans and fenced `sh`/`bash`/`shell`/unlabelled blocks. Split commands on `&&`, `||`, `;`, `|`; strip leading `VAR=value`; track `cd DIR &&`. Forms and resolvers exactly as in D16's table, plus `npx <bin>` (resolves to a dependency name or a bin in `node_modules/.bin` when present, otherwise `unverified`), `pnpm exec <bin>` / `pnpm dlx` (unverified in 0.1.0), `uv run X` / `poetry run X` (unverified in 0.1.0), and a backticked relative path (must contain `/` or an extension, and not look like a URL, flag, or version). A token that looks like a command but matches no resolver is `unverified`, never `stale`. Only a positive miss (the script name, target, recipe, module or path is provably absent) is `stale`.

## Managed blocks (D5)

`<!-- contextify:begin v1 -->` ... `<!-- contextify:end -->`, single-line markers. Zero or one pair per file; anything else is a conflict (exit 2 from `ctx_write.py`, which is NOT a hook and may use exit 2). Header line as D5. Footer line as D5, plain text: `verified on YYYY-MM-DD against <short sha>`. The header and footer are rewritten only when the bytes between them change; a byte-identical draft leaves the file untouched (no mtime change either: the writer compares before writing).

`CLAUDE.md`: line 1 is `@AGENTS.md` (outside the block, owned by contextify: `ctx_check` reports `CLAUDE.md:1 no longer imports AGENTS.md` if missing). `GEMINI.md`: exactly three lines as D6. Cursor rule and Copilot pointer as D6.

## `ctx_write.py`

Usage: `ctx_write.py --root PATH --draft DIR [--targets LIST] [--dry-run] [--yes] [--json] [--symlink] [--generated-by NAME]`

`DIR` also accepts `evidence.tsv`: SHA-256 of the complete draft line, a tab, then a repository source path and line number (`file:line`). Supplied rows must resolve; unknown hashes or malformed sources refuse. Evidence JSON persists those line identities and source digests across updates and acceptance. A separate agent still checks that the source actually supports the prose.

`DIR` holds `AGENTS.md` (the managed body: no markers, no header, no footer; the writer adds them), optional `CLAUDE.md` (Claude-only addendum body, may be empty or absent), optional nested `<dir>/AGENTS.md` bodies. Steps, in order, failing closed at the first problem:

1. Size and budget: classify the repo (D2: tiny / medium / monorepo) and print the class; count final merged lines including human content; refuse (exit 4, message names the count and the ceiling) if `AGENTS.md` would exceed 150 rendered lines or `CLAUDE.md` 30; warn (not refuse) above the size-class target.
2. Content rules (D3): refuse a fenced code block inside the AGENTS.md draft (exit 4, names the line).
3. Preflight per target (D12): final merged lines and bytes; each actual Codex root-to-leaf instruction chain vs 32,768 (or `project_doc_max_bytes` found in `.codex/config.toml`); refuse (exit 4) when the AGENTS.md chain would exceed the Codex ceiling and `codex` is among the targets; report `AGENTS.override.md` shadowing when present at any level.
4. Claims: run the extractor + resolvers over the rendered AGENTS.md; a `stale` claim refuses (exit 4, names file:line); `unverified` claims are counted and, with `--strict`, refused.
5. Path safety: every output path resolves inside `--root` and is not a symlink pointing outside; refuse (exit 5, same error class for every target).
6. Merge: for each target, read the existing file (if any), find the managed pair, replace only the block; a file with human content and no markers: insert the block after the first H1 (or at the top when there is none) and report `migration pending`; a managed block whose digest differs from the stamp is a conflict (exit 2) unless `--yes` AND `--force-managed` are both present after explicit review. All merged claims and budgets are revalidated before writing.
7. `--dry-run`, or no `--yes`: print the unified diff per target and the cost table (D12), write nothing, exit 0. Applying text mode displays the diff before mutation; JSON mode returns structured changes.
8. Write: create `.contextify/journal.json` (targets, expected pre-write digests, new digests); for each target, `tempfile` in the same directory + `os.replace`; write evidence.json and stamp.json through the same journal. Keep the journal while `ctxlib.run_check` checks the generated state. If it reports drift, restore every recorded target, including the previous metadata, remove the journal after restoration, and exit 6 with the notice on stderr. If the check is fresh, remove the journal. An interruption or exception before completion leaves the journal for recovery.
9. Print the summary block (D10). Exit 0.

An interrupted write (a test raises inside the loop) leaves the journal and either the old or the new version of each file, never a partial file; the next `ctx_write.py --recover` restores the old generation from the journal's `previous` field.

## `ctx_stamp.py`

Usage: `ctx_stamp.py --root PATH [--accept] [--generated-by NAME] [--tool-version X]`. Recomputes evidence and claims over the current tree and the existing context files, and writes both JSON files. `--accept` (D17): refuses on a stale claim, a changed managed block also refuses, a budget violation refuses; every context file stays byte-identical; `generatedBy` becomes `accept`. Without a stamp, `--accept` exits 3.

## `verify_claims.py`

Usage: `verify_claims.py [--root PATH] [--budget] [--json] FILE...`. For each file: extract claims, resolve, print one line per claim `OK|STALE|UNVERIFIED  file:line  text  (reason)`, a summary `N claims, M stale, K unverified`, exit 1 if any stale. `--budget`: also fail with `AGENTS.md is 160 lines; the ceiling is 150 (Claude Code guidance: keep context files under 200 lines)` style messages when AGENTS.md > 150 or CLAUDE.md > 30.

## `install_hooks.sh`

Usage: `install_hooks.sh [--yes] [--targets codex,gemini,cursor,git,github] [PATH]`. For each requested target, render the documented hook shape, show a diff against the existing file, propose without applying unless `--yes`, and merge idempotently (JSON merges add the hook entry once; a second run changes nothing). Targets: `.codex/hooks.json`, `.gemini/settings.json` (hooks + offers the `context.fileName` switch separately), `.cursor/hooks.json`, `.githooks/pre-commit` + prints the `git config core.hooksPath .githooks` line, `.github/workflows/contextify-check.yml`. The local Codex, Gemini, Cursor and git snippets call the installed plugin's `ctx-check` by its absolute path. The GitHub workflow instead clones release tag `v0.1.0` into `$RUNNER_TEMP/contextify` and runs that checkout's checker; it requires the tag to be published. Both git and GitHub checks are advisory by default; adding `--strict` makes drift block the commit or CI job.

## Terminal output rules

Plain text, aligned with spaces, no ANSI output or color flag, one final summary block, every finding names its evidence path. `--json` suppresses all prose.

## Optional mode not implemented

The regular pointer-file workflow is supported. `ctx_write.py --symlink` refuses without changing files in 0.1.0; the original design described this optional future mode.
