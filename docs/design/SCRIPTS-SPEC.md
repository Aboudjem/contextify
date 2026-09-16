# contextify scripts: the contract between the skill and the deterministic layer

Date: 2026-09-16. This document binds `docs/design/DECISIONS.md` (the design) to concrete files under `skills/contextify/scripts/`. Where DECISIONS.md and this file disagree, this file wins for implementation details; the run brief's locked constraints win over both. Everything here is zero-dependency: POSIX `sh` (bash 3.2 safe) and python3 standard library only (python3 >= 3.11 assumed for `tomllib`; when `tomllib` is missing, the pyproject normalizer falls back to a bounded regex over `[project.scripts]` and marks the rest `unverified`).

## Division of labour

The skill (SKILL.md, run by the model) does the reading and the prose. The scripts do everything deterministic: discovery, evidence normalizing, claim extraction and liveness, budgets, ceilings, managed-block merging, atomic writes, the stamp, the drift check and the hook envelopes. The model never writes a context file directly; it writes a draft and hands it to `ctx_write.py`, which is the only thing that touches the targets.

## Files

| File | Language | Role |
|---|---|---|
| `detect_repo.sh` | bash 3.2 | read-only fact sheet of a repo (seed: agent-context's `detect_repo.sh`, extended) |
| `ctx-check` | POSIX sh | hook entry point and fast path; `exec`s `ctx_check.py` on any miss |
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

The fast path and the slow path share one list, `DISCOVERY_GLOBS`, defined once in `ctxlib.py` and mirrored literally in `ctx-check` (a test asserts the two lists are identical):

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

1. Resolve the working tree. Under a hook, read stdin (non-blocking: only if stdin is not a TTY and has data) and extract the `cwd` field with a bounded `sed`; fall back to `$CLAUDE_PROJECT_DIR`, then `$PWD`, then `PATH` if given. `cd` there.
2. `git rev-parse --show-toplevel` fails: exit 0, no output (not a repo is not an error).
3. No `.contextify/stamp.json`: print exactly one line `contextify: no stamp yet. Run /contextify init` to stdout (envelope-wrapped under `--hook`), exit 3. Under `--ci` without `--strict` the line is printed and exit is 0; with `--strict` exit 1.
4. `.contextify/journal.json` exists: write `contextify: an interrupted write left .contextify/journal.json; run /contextify update to recover` to stderr, exit 1, stdout empty.
5. Fast path: `git ls-files -s -z -- <DISCOVERY_GLOBS>` piped to `shasum -a 256` (or `sha256sum`, whichever exists; both tried). Read `fastKey` from the stamp with a bounded regex (`"fastKey": "sha256:<64 hex>"`), never `eval`. If the digest equals the stamp's key AND `git diff --quiet -- <DISCOVERY_GLOBS>` succeeds (no unstaged change on evidence paths) AND `git diff --quiet -- AGENTS.md CLAUDE.md GEMINI.md` succeeds AND every file listed in the stamp's `contextFiles` exists: exit 0, print nothing.
6. Otherwise: `exec python3 "$(dirname "$0")/ctx_check.py" "$@"`, passing the resolved tree as `--root`.

The fast path must complete in under 100 ms on a warm cache (a test measures it and asserts under 250 ms to be tolerant of CI).

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

Extract from every context file: inline code spans and fenced `sh`/`bash`/`shell`/unlabelled blocks. Split commands on `&&`, `||`, `;`, `|`; strip leading `VAR=value`; track `cd DIR &&`. Forms and resolvers exactly as in D16's table, plus `npx <bin>` / `pnpm exec <bin>` / `pnpm dlx` (resolve to a dependency name or a bin in `node_modules/.bin` when present, else `unverified`, never `stale`), `uv run X` / `poetry run X` (unverified in 0.1.0), and a backticked relative path (must contain `/` or an extension, and not look like a URL, flag, or version). A token that looks like a command but matches no resolver is `unverified`, never `stale`. Only a positive miss (the script name, target, recipe, module or path is provably absent) is `stale`.

## Managed blocks (D5)

`<!-- contextify:begin v1 -->` ... `<!-- contextify:end -->`, single-line markers. Zero or one pair per file; anything else is a conflict (exit 2 from `ctx_write.py`, which is NOT a hook and may use exit 2). Header line as D5. Footer line as D5, plain text: `verified on YYYY-MM-DD against <short sha>`. The header and footer are rewritten only when the bytes between them change; a byte-identical draft leaves the file untouched (no mtime change either: the writer compares before writing).

`CLAUDE.md`: line 1 is `@AGENTS.md` (outside the block, owned by contextify: `ctx_check` reports `CLAUDE.md:1 no longer imports AGENTS.md` if missing). `GEMINI.md`: exactly three lines as D6. Cursor rule and Copilot pointer as D6.

## `ctx_write.py`

Usage: `ctx_write.py --root PATH --draft DIR [--targets LIST] [--dry-run] [--yes] [--json] [--symlink] [--generated-by NAME]`

`DIR` holds `AGENTS.md` (the managed body: no markers, no header, no footer; the writer adds them), optional `CLAUDE.md` (Claude-only addendum body, may be empty or absent), optional nested `<dir>/AGENTS.md` bodies. Steps, in order, failing closed at the first problem:

1. Size and budget: classify the repo (D2: tiny / medium / monorepo) and print the class; count draft lines; refuse (exit 4, message names the count and the ceiling) if `AGENTS.md` would exceed 150 rendered lines or `CLAUDE.md` 30; warn (not refuse) above the size-class target.
2. Content rules (D3): refuse a fenced code block inside the AGENTS.md draft (exit 4, names the line).
3. Preflight per target (D12): rendered lines and bytes; Codex chain bytes vs 32,768 (or `project_doc_max_bytes` found in `.codex/config.toml`); refuse (exit 4) when the AGENTS.md chain would exceed the Codex ceiling and `codex` is among the targets; report `AGENTS.override.md` shadowing when present at any level.
4. Claims: run the extractor + resolvers over the rendered AGENTS.md; a `stale` claim refuses (exit 4, names file:line); `unverified` claims are counted and, with `--strict`, refused.
5. Path safety: every output path resolves inside `--root` and is not a symlink pointing outside; refuse (exit 5, same error class for every target).
6. Merge: for each target, read the existing file (if any), find the managed pair, replace only the block; a file with human content and no markers: insert the block after the first H1 (or at the top when there is none) and report `migration pending`; a managed block whose digest differs from the stamp is a conflict (exit 2) unless `--yes` AND `--force-managed` are both present.
7. `--dry-run`: print the unified diff per target and the cost table (D12), write nothing, exit 0.
8. Write: create `.contextify/journal.json` (targets, expected pre-write digests, new digests); for each target, `tempfile` in the same directory + `os.replace`; then `ctx_stamp.py` logic writes evidence.json and stamp.json; remove the journal; run the check (`ctx_check.py --root`); if the check is not exit 0 with empty stdout, restore every target from the journal's recorded previous content, remove the stamp change, and exit 6 with the notice on stderr.
9. Print the summary block (D10). Exit 0.

An interrupted write (a test raises inside the loop) leaves the journal and either the old or the new version of each file, never a partial file; the next `ctx_write.py --recover` restores the old generation from the journal's `previous` field.

## `ctx_stamp.py`

Usage: `ctx_stamp.py --root PATH [--accept] [--generated-by NAME] [--tool-version X]`. Recomputes evidence and claims over the current tree and the existing context files, and writes both JSON files. `--accept` (D17): refuses on a stale claim, an edited managed block is fine (accept re-digests it), a budget violation refuses; every context file stays byte-identical; `generatedBy` becomes `accept`. Without a stamp, `--accept` exits 3.

## `verify_claims.py`

Usage: `verify_claims.py [--root PATH] [--budget] [--json] FILE...`. For each file: extract claims, resolve, print one line per claim `OK|STALE|UNVERIFIED  file:line  text  (reason)`, a summary `N claims, M stale, K unverified`, exit 1 if any stale. `--budget`: also fail with `AGENTS.md is 160 lines; the ceiling is 150 (Claude Code guidance: keep context files under 200 lines)` style messages when AGENTS.md > 150 or CLAUDE.md > 30.

## `install_hooks.sh`

Usage: `install_hooks.sh [--yes] [--targets codex,gemini,cursor,git,github] [PATH]`. For each requested target, render the snippet from `skills/contextify/references/hooks-and-ci.md` (embedded in the script as heredocs, kept byte-identical with the reference by a test), show a diff against the existing file, ask unless `--yes`, merge idempotently (JSON merges add the hook entry once; a second run changes nothing). Targets: `.codex/hooks.json`, `.gemini/settings.json` (hooks + offers the `context.fileName` switch separately), `.cursor/hooks.json`, `.githooks/pre-commit` + prints the `git config core.hooksPath .githooks` line, `.github/workflows/contextify-check.yml`. Each snippet calls `ctx-check` through a path the user's install provides: the script writes the absolute path of the installed plugin's `ctx-check` and says so.

## Terminal output rules

Plain text, aligned with spaces, no ANSI unless `--color` and `NO_COLOR` is empty, one final summary block, every finding names its evidence path. `--json` suppresses all prose.
