# contextify design decisions (locked)

Date: 2026-09-16. Method: a four-CLI dream-team fanout answered one design prompt independently, then an anonymized cross-check graded every answer. Fanout dir: `/Users/adamboudj/projects/10x/.goal/audit/ctx-design/fanout` (A claude, B codex, C kimi, D agy). Verdict: `.../crosscheck/verdict-matrix.json`. **Answer B won**, graded CONFIRMED; A, C and D each took one CORRECTED; nothing was fact-contaminated. This document starts from B and grafts a runner-up element only where it is verifiably better and is not what a grader corrected.

Corrections honoured, so they are not carried forward: A's exit-code changes and its claim that per-file renames give an atomic multi-file update (rejected, see D7 and D9); C's `--strict` drift exit 4, its `CLAUDE.md` missing the first-line import, its five-line `GEMINI.md`; D's accents at hue 284.82 and 282.99, outside the 290 to 315 band, actual ratios 5.96:1 and 7.30:1 (rejected, see D21).

Every number in an output example below is an illustrative fixture rendering, not a measured product result. Anything not established by a primary source is labelled `uncertain`.

## D1. The AGENTS.md section skeleton

**Decision.** Ordered sections with per-section line allowances, counting physical lines including headings, comments and blanks. A section with no evidence is omitted entirely: no heading, no placeholder, no TODO.

| # | Section | Lines | Evidence file(s) that can justify a line |
|---|---|---:|---|
| 1 | H1, managed begin marker, provenance comment | 4 | generator identity, `generatedAt`, `git rev-parse HEAD` |
| 2 | `## Commands` | 14 | `package.json#scripts`, Makefile and justfile targets, `pyproject [project.scripts]`, Cargo bins, CI `run:` lines with working directories |
| 3 | `## Architecture` | 12 | two or more implementation files plus the relation between them, for example entry point to router to persistence |
| 4 | `## Conventions` | 6 | `tsconfig` `paths`/`strict`/`target`, `package.json#type`, existing contributor instructions; never a rule a formatter owns |
| 5 | `## Testing` | 6 | test config, fixtures, setup scripts, CI `services:`, `.env.example` keys a setup file references |
| 6 | `## Repository workflow` | 4 | `CONTRIBUTING.md`, PR template, release workflow, default branch ref |
| 7 | `## Boundaries` | 8 | hazard detectors only (D4) |
| 8 | `## Read when relevant` | 3 | existing doc paths, one task-specific reason to open each |
| 9 | verified-on footer, managed end marker | 3 | stamp `commit` and date |
| | **Total** | **60** | hard ceiling **150** |

Commands come first. There is no purpose or stack section by default: a README already says it and a stack is derivable from a tracked manifest. One stack line is allowed inside Commands when a fact is load-bearing and no tracked manifest states it. Commands carry a single-test invocation when evidence supports it (working directory, exact command, real example test path); with only the runner known, print `Single test: unverified` or omit it, and never invent a filter flag. Architecture means the big picture that needs several files to understand: every bullet names at least two tracked paths and the relation between them, and a directory listing does not qualify.

**Why / Source.** B, primary. Commands-first, the single-test line and the multiple-files framing are what Claude's own stable `/init` prompt asks for and nothing else in the survey does: `/Users/adamboudj/projects/10x/.goal/research/ctx/08-steal-list.md` (stable prompt, items 1 and 2), plus tip 6 in `.../ctx/02-community-intel.md`.

## D2. Size scaling

**Decision.** Count tracked plus non-ignored untracked regular files, excluding generated context files, `.contextify/`, vendored dependencies and build outputs named by repository configuration. A **build unit** is a directory with a manifest and an independently declared build, test or executable entry point.

- **Tiny**: at most 10 eligible files, at most one build unit, no declared workspace. Target 20.
- **Monorepo**: at least two build units joined by workspace configuration, or documented as separately operated projects. Target 60.
- **Medium**: everything else. Target 40.

Scaling only goes down: 60 caps the target, 150 caps the file. Tiny drops Architecture, Conventions, Testing and Repository workflow, folding necessary test detail into Commands. Boundaries survive at any size when a hazard fires. Human content counts toward the ceiling, and going over demands a reviewed reduction, never a silent truncation.

**Why / Source.** B, primary. One fixed template is the clearest failure in the survey and the cheapest thing to beat with a measurable rule: `08-steal-list.md` section 5 (`AGENTS.md.template`).

## D3. The evidence rule and what earns a line

**Decision.** Every command, path, port, branch and deploy fact traces to a file the run read, or it is omitted, or it is labelled `unverified`. Evidence lives in `.contextify/evidence.json`, keyed by a hash of the line text rather than by line number. An inline `<!-- src: path:line -->` comment is written only when the section is still inside budget after adding it. Three content rules, enforced by `lint`: **no code blocks in the generated AGENTS.md** (the agent greps faster than it reads, and a pasted snippet rots silently); **no README duplication** (if a line does not change agent behaviour, cut it); **only rules the agent has actually got wrong**, so `init` output is deliberately sparse.

**Why / Source.** B, primary. Provenance per line is the gap nobody fills: `.../ctx/03-comparables-and-skills-cli.md` Part C item 2. No code blocks and grep-beats-read: `.../ctx/06b-reddit-browser.md` tips 2 and 12. README duplication: `02-community-intel.md` anti-patterns.

## D4. Boundaries only where the repo shows a hazard

**Decision.** Three labels, empty labels omitted, whole section omitted when nothing fires:

```markdown
## Boundaries
- Always: <evidenced required action>
- Ask first: <evidenced action requiring approval>
- Never: <evidenced prohibited action>
```

Detectors: a gating CI command (a workflow on `pull_request` whose `run` line matches a Commands entry) fires Always. Deploy on push to the default branch, and a tracked migrations directory, fire Ask first. Generated code marked `@generated`, `DO NOT EDIT` or `linguist-generated`, and a tracked `.env.example` with `.env` ignored, fire Never. Every Never line names what to do instead; positive framing over all-caps bans. A deploy script proves deployment exists, not that it needs approval: that permission comes from an existing policy or a recorded human decision.

**Why / Source.** B for the labels and the permission caveat, A for the detector table. Three tiers and the secrets constraint: `02-community-intel.md` tips 11 and 12. Positive framing and literal rule-following: `06b-reddit-browser.md` tips 29, 9 and 12.

## D5. Managed-block markers and the header

**Decision.** Markers are single-line HTML comments so every reader ignores them: `<!-- contextify:begin v1 -->` and `<!-- contextify:end -->`. The line right after the begin marker is the provenance header:

```text
<!-- Generated by contextify {toolVersion}; writer={generatedBy}; at={generatedAt}; commit={commit}; regenerate: /contextify update -->
```

The last managed line of `AGENTS.md` is the footer, plain text rather than a comment so a human reading the rendered file sees it: `verified on {date} against {commit}`.

A file carries zero or one complete pair. An unpaired marker, a nested pair or two pairs is a conflict: the run refuses and names the line numbers. Header and footer are rewritten only when the bytes between the markers change, so a no-op re-run is byte-identical. Use `unknown` for an unavailable writer identity and `none` before the first commit.

**Why / Source.** B for the marker vocabulary and rewrite-only-on-change, A for the fixed header field order. Block-preservation pattern: `08-steal-list.md` section 1 (`src/core/GitignoreUtils.ts`).

## D6. Literal pointer file contents

**Decision.** `CLAUDE.md`, four lines by default, `@AGENTS.md` first:

```markdown
@AGENTS.md
<!-- contextify:begin v1 -->
<!-- Generated by contextify {toolVersion}; writer={generatedBy}; at={generatedAt}; commit={commit}; regenerate: /contextify update -->
<!-- contextify:end -->
```

An optional `## Claude Code` section goes inside the block only when evidenced Claude-specific notes exist (`.claude/settings.json` hooks, `.mcp.json` servers, a gitignored `CLAUDE.local.md`). The file stays under 30 lines. Line 1 sits outside the block but contextify owns it: if it is removed, `check` reports `CLAUDE.md:1 no longer imports AGENTS.md`.

`GEMINI.md`, exactly three lines:

```markdown
<!-- contextify:begin v1; Generated by contextify {toolVersion}; writer={generatedBy}; at={generatedAt}; commit={commit}; regenerate: /contextify update -->
@AGENTS.md
<!-- contextify:end -->
```

The settings switch is offered as a displayed patch, never applied silently: `{"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}}`. When it is taken, line two becomes `Repository instructions: [AGENTS.md](AGENTS.md).` so AGENTS is not discovered and imported twice. Whether a given release deduplicates combined discovery and imports is `uncertain`.

`.cursor/rules/contextify.mdc`, optional, written only with `--targets cursor-rule`:

```markdown
---
description: Repository instructions in AGENTS.md
globs: ""
alwaysApply: true
---
<!-- contextify:begin v1 -->
<!-- Generated by contextify {toolVersion}; writer={generatedBy}; at={generatedAt}; commit={commit}; regenerate: /contextify update -->
Read [AGENTS.md](../../AGENTS.md) before changing this repository.
<!-- contextify:end -->
```

`.github/copilot-instructions.md`:

```markdown
<!-- contextify:begin v1 -->
<!-- Generated by contextify {toolVersion}; writer={generatedBy}; at={generatedAt}; commit={commit}; regenerate: /contextify update -->
Read [AGENTS.md](../AGENTS.md) for repository instructions. Inside a subdirectory the nearest AGENTS.md applies.
<!-- contextify:end -->
```

`description` is non-empty because community reports say an `alwaysApply` rule can fail to register without one; that report is `uncertain` and not in the official docs. Whether a Markdown pointer behaves as a native import across every Copilot feature is also `uncertain`.

**Why / Source.** B, primary. Claude reads CLAUDE.md not AGENTS.md and the docs recommend `@AGENTS.md`: `.../ctx/07-skeptic.md` claims 3b and 3c. Nested Gemini settings key: claim 5 and correction 1. Cursor `.mdc` frontmatter and native AGENTS support: claims 6 and 6b. Copilot nearest-wins: claim 7. Cursor description quirk: `02-community-intel.md` per-tool quirks.

## D7. Existing files, conflicts and write safety

**Decision.** Recognize only complete, unnested marker pairs; duplicate or malformed pairs are conflicts. Preserve every byte outside a managed block, including line endings. If a managed block differs from its stamped digest, stop with a conflict that `--yes` cannot override. For an unmarked human file, propose insertion or migration in a diff and never silently adopt it as generated content; insert after the first H1 when the file opens with one. Generic instructions already living in another agent file must be explicitly migrated into AGENTS before that file is called a thin pointer; until then report `migration pending`. Human lines are read as evidence and their commands and paths get the same liveness check.

Writes go through a recovery journal: render everything, journal the expected pre-write digest of every target, replace files, write `.contextify/stamp.json` last, remove the journal. A surviving journal means the previous run was interrupted, and `check` returns 1 with stderr only until recovery restores the old generation or completes the validated new one. If another process changed a file since the journal was written, recovery stops rather than overwriting it. Per-file replacement alone is not a filesystem-wide transaction. `init` ends by running `ctx-check` on what it just wrote; anything other than exit 0 with empty stdout aborts the run and triggers recovery, so a generated file that cannot pass its own check never survives on disk.

**Why / Source.** B, primary. Partial writes are worse than stale documentation (`08-steal-list.md` section 3, `agent/claude-md-guardian.md`), and the atomic-write mechanism it hardens is `08-steal-list.md` section 4 (`tempfile.mkstemp` plus `os.replace`).

## D8. CLI surface

**Decision.** The slash command invokes the skill; `check` and `accept` delegate to deterministic scripts. No npm package, no standalone binary CLI. `/contextify init|update|check|accept [path] [options]`. An omitted `path` means the repository containing the working directory; an explicit directory scopes the run, and a path outside it can never become an output target.

| Mode | Action | Normal output |
|---|---|---|
| `init` | discover evidence, generate, validate, write | discovery counts, full diff, summary block |
| `update` | re-read evidence, revise affected managed content | named changes, full diff, summary; unchanged files listed |
| `check` | run `ctx-check`, never write | fresh: nothing. drift: at most 12 lines |
| `accept` | revalidate prose, replace metadata only | evidence and stamp diff, then a summary stating prose was unchanged |

| Flag | Modes | Behaviour |
|---|---|---|
| `--dry-run` | all | no writes; init and update show proposed diffs and costs; check stays read-only |
| `--yes` | init, update, accept | skip questions, apply safe validated changes; never bypasses a conflict or a ceiling |
| `--json` | all | structured output only; a fresh check stays silent; a drift object is one physical line |
| `--targets LIST` | init, update | ids `claude,codex,gemini,cursor,cursor-rule,copilot`. AGENTS is always generated; `cursor-rule` explicitly requests the optional `.mdc` |
| `--strict` | all | require zero unverified claims and full resolver coverage. Findings print on stdout. Exit codes do not change |
| `--color` | all | opt into ANSI colour; ignored with `--json` or a non-empty `NO_COLOR` |
| `--symlink` | init, update | explicit Claude-only alternative, not the default. Eligible only with no human content, no Claude addendum and AGENTS under 30 lines; otherwise refuse with a reason |
| `--hook AGENT` | check | pick the output envelope for `claude`, `codex`, `gemini` or `cursor` |

Colour is off by default and a non-empty `NO_COLOR` beats `--color`. An unsupported flag and mode combination is a usage error, never silently ignored.

**Why / Source.** B, primary. The symlink alternative is documented by Claude (`07-skeptic.md` claim 3b); the `--hook` envelope comes from `.../ctx/04-auto-update-mechanics.md`.

## D9. The `ctx-check` exit contract

**Decision.** Locked, in every invocation mode: `0` with empty stdout is fresh; `0` with non-empty stdout is drift or a strict-policy finding, at most 12 lines and 2,048 UTF-8 bytes; `3` is no stamp; `1` is the check itself breaking, stderr only with stdout empty. Never `2`, never a model call, never a write, never a touch of the index. A non-git directory exits 0 silently. CI strictness is a separate opt-in adapter, `ctx-gate`, that turns a missing stamp or a reported finding into a non-zero CI result; it wraps `ctx-check` and does not redefine its codes.

**Why / Source.** B, honouring the locked contract. A session-start hook that blocks or errors gets blamed for everything else and switched off within a week. Exit table and non-git guard: `04-auto-update-mechanics.md`. A and C both proposed exit 4 here and were corrected.

## D10. The `init` summary block

**Decision.** Literal shape; the values are an example fixture rendering.

```text
contextify init

Result   written
Scope    .
Targets  claude, gemini, cursor-rule, copilot

Files written                              Lines
AGENTS.md                                     60
CLAUDE.md                                      4
GEMINI.md                                      3
.cursor/rules/contextify.mdc                   9
.github/copilot-instructions.md                4
.contextify/evidence.json                     84
.contextify/stamp.json                        72

Evidence     18 records
Unverified    0 claims
Next         /contextify check
```

Every file actually written appears, lines measured after serialization, aligned columns, no colour, one final summary block.

**Why / Source.** B, primary. The summary is the product's only report, so it has to name every byte it touched.

## D11. The drift notice

**Decision.** Literal shape, eight lines here, 12 the hard maximum, dead claims first, excess findings collapsed into a count.

```text
contextify: drift
Scope    .
Changed  package.json#scripts
Removed  script lint:css
Stale    AGENTS.md:14 references npm run lint:css
Files    0 written
Next     /contextify update
Accept   unavailable until the stale command is corrected
```

When only moved-evidence rows exist and no claim is dead, the last line reads `Next     /contextify update, or /contextify accept if the docs are still right`. Control characters are escaped. An evidence key that no generated line cites changes silently.

**Why / Source.** B, primary. A bounded notice is the only kind that can be injected at session start without becoming the bloat it prevents. Shape and the roughly 70-token cost target: `04-auto-update-mechanics.md`, SessionStart hook section.

## D12. What `--dry-run` prints per target

**Decision.** For every target: proposed physical lines, UTF-8 bytes, the difference against the current file, and the applicable contextify ceiling. Then per agent: **Claude**, pointer-file lines plus known expanded imported lines, shown against the 200-line guidance and explicitly labelled guidance, not a cap; **Codex**, discovered instruction-chain bytes including separators, against 32,768 bytes or a verified configured `project_doc_max_bytes` override, respecting `AGENTS.override.md` at every directory level and reporting when it shadows the generated file; **Gemini, Cursor, Copilot**, lines and bytes with no invented common budget percentage; `unknown additional context` when user-level or managed instructions cannot be inspected. The two numbers are never presented as interchangeable token limits, and no token estimates are printed.

**Why / Source.** B, primary. Nobody else shows the cost before writing. 200-line guidance: `07-skeptic.md` claim 3c. 32 KiB cap and silent truncation: claims 4b and 4c, correction 9.

## D13. The three `init` questions

**Decision.** At most three, each asked only when its trigger fires, each skippable.

1. `Which agents should get pointer files?` Default: Claude Code plus any agent evidenced by existing repository configuration. AGENTS is unconditional; the Cursor rule file is off.
2. `What must an agent know that the repository does not show, especially a single-test command or an action that needs approval?` Default: skip. A human-supplied technical fact stays `unverified` until a file read during the run supports it.
3. `Apply the displayed changes?` Default: apply safe additions and managed-block replacements, with conflicts excluded and visibly reported.

`init` asks nothing when `--yes` supplies the decisions, when `--dry-run` asks only for a proposal, when every choice is explicit and only new non-conflicting files are created, or when input is not interactive (non-interactive without `--yes` produces a dry-run proposal, not a write). `update`, `check` and `accept` never ask. Nothing is asked about language, framework, package manager or ports when repository evidence answers it.

**Why / Source.** B, primary. An interview that asks what the repo already states is how a generator earns the reputation measured in `02-community-intel.md` tips 10 and 20.

## D14. `.contextify/stamp.json`

**Decision.** Committed, tool-neutral directory, version 2.

```json
{
  "version": 2,
  "tool": "contextify",
  "toolVersion": "<semver>",
  "generatedAt": "<RFC 3339 UTC>",
  "generatedBy": "<writer identity or unknown>",
  "commit": "<full sha or null>",
  "scope": "<repository-relative scope>",
  "normalizerVersion": 1,
  "fastKey": "sha256:<hex>",
  "discovery": ["<evidence path>"],
  "evidenceFileDigest": "sha256:<hex>",
  "evidence": {"package.json#scripts": "sha256:<hex>"},
  "claims": {
    "commands": [
      {"id": "<id>", "text": "npm run test", "location": {"file": "AGENTS.md", "line": 9},
       "cwd": ".", "resolver": "npm-run", "target": "scripts.test",
       "evidenceRefs": ["package.json#scripts"], "status": "verified"}
    ],
    "paths": [
      {"id": "<id>", "text": "src/server/index.ts", "location": {"file": "AGENTS.md", "line": 18},
       "cwd": ".", "resolver": "tracked-file", "target": "src/server/index.ts",
       "evidenceRefs": ["tree#depth2"], "status": "verified"}
    ]
  },
  "contextFiles": {
    "AGENTS.md": {"kind": "file", "digest": "sha256:<hex>", "managedBlockDigest": "sha256:<hex>"}
  }
}
```

A `symlink` entry carries `linkTarget`; a regular file forbids it. Resolved paths stay inside scope; every evidence reference exists in `.contextify/evidence.json`; every verified claim has at least one evidence reference; a missing command or path cannot be stored as verified; unknown normalizer versions are rejected. Digests are SHA-256 over canonical UTF-8 JSON with sorted keys, compact separators and no trailing newline. After `accept`, `generatedBy` names deterministic acceptance, never a model that did not run.

Fast path, in `sh`: derive the worktree from the hook input `cwd`, discover relevant paths including newly added manifests and workflows, digest NUL-delimited `git ls-files -s -z -- <evidence paths>`, and return silently only if the key matches, relevant tracked files have no unstaged changes, discovery gained nothing, and the context and evidence digests match. Any failed guard forces the Python normalizer over working-tree contents. The stamp is never part of its own digest. The shell reads only a canonical `fastKey` field; non-canonical JSON falls through to Python and is never evaluated as shell.

**Why / Source.** B, primary, improving the prototype in `04-auto-update-mechanics.md`. `git ls-files --stage` reports index information, so index equality alone cannot establish working-tree freshness; hence the extra guards and the recorded `cwd` per claim.

## D15. Normalizers: what is hashed, what is ignored

**Decision.**

| Normalizer | Hash exactly | Deliberately ignore |
|---|---|---|
| `package.json` | sorted script name and body map; dependency names grouped by category; package-manager name; workspace declarations; engine names | dependency versions, package version, description, formatting, manager and engine versions unless a line claims one |
| Lockfiles | sorted `(relative filename, present)` pairs | all contents |
| CI | workflow path, job ids and names, ordered `run` strings, shell, working directory, conditions, referenced matrix and env definitions | `uses:` pins, `with:` values, comments, display formatting |
| Dockerfile | ordered image identities with tags and digests removed, stage aliases, platform, `EXPOSE` port and protocol tuples | image versions, unrelated instructions, comments |
| Compose | sorted service names | images, tags, unrelated service config unless a claim uses it |
| tsconfig | `paths`, `strict`, `target`, `module`, and the resolved local `extends` chain for those fields | every other compiler option, formatting |
| `.env.example` | sorted variable names | values (never read past `=`, never stored), comments, ordering |
| Tree, depth two | sorted typed path names through two components | file contents, deeper names, excluded output trees, generated context artifacts |
| Makefile, justfile | literal target and recipe names, parameters, prerequisites, recipe bodies, statically resolvable local includes | comments, unrelated formatting |
| pyproject | `[project.scripts]`, `[project.gui-scripts]`, supported Poetry script mappings and their targets | package metadata, dependency versions |
| Cargo | declared bin names and paths, `autobins`, conventional bin paths when enabled, workspace members | dependency versions, package version, source bodies |
| `go.mod` | module path and the exact `go` directive | `require` versions, checksums, unrelated directives |
| Gemfile | presence | contents |
| Maven, Gradle | presence and filenames of `pom.xml`, build and settings files, wrappers | contents, dependency versions |

Where a generated line states a version, port, branch or deploy detail, a claim-specific selector additionally hashes that exact value, so a generic normalizer can never hide a change to an explicit claim. The guarantee is therefore narrow and honest: **dependency-version-only and lockfile-content-only changes produce no notice when they do not alter a represented claim.** "Every Renovate change is ignored" would be false. Normalizing runs on Python 3.11 or newer so TOML uses stdlib `tomllib`. YAML, JSONC and dynamic build syntax get a documented bounded grammar; an unsupported alias, a computed target or unresolved inheritance yields `unverified`, never a fabricated empty result. Configuration is never executed to parse it.

**Why / Source.** B, primary. The noise tier is what stops the check being switched off after the first dependency-bot run: `04-auto-update-mechanics.md`, slow path and prototype validation.

## D16. Claim liveness

**Decision.** Extract executable examples from inline code spans and shell fences in every context file, inside or outside the managed block. Record `cwd` explicitly, defaulting to the selected scope; a literal `cd DIR && command` updates it. Split on `&&`, `||`, `;` and `|`, drop leading `VAR=value` assignments, ignore metadata comments, and leave unsupported shell syntax unverified.

| Quoted form | Resolution |
|---|---|
| `npm run X` | `scripts.X` in the manifest applicable to the recorded `cwd` |
| `pnpm X`, `yarn X`, `bun X` | explicit `run X`, or an unambiguous script shorthand. A built-in name collision requires explicit `run`; other forms stay unverified |
| `make X` | literal target `X` in the selected Makefile and statically resolved includes |
| `just X` | literal recipe `X` in the selected justfile and supported imports |
| `python -m X` | a local module file or package `__main__.py`, or metadata explicitly proving the module mapping. A dependency name alone is not enough |
| `cargo X` | the versioned built-in verb table plus Cargo workspace evidence, or a supported literal alias in Cargo configuration |
| `go test ./...` | the recorded directory is inside the evidenced module or workspace and the package tree contains Go source |
| backticked relative path | resolved from the recorded scope and `cwd`; existence and file or directory kind checked; escape outside scope rejected |

A single-test example additionally validates the literal test path, and a name-filter flag needs its own repository evidence. "Verified command" means its declaration or target resolves; it does not mean the command was executed successfully.

**Why / Source.** B, primary. A context file confidently naming a deleted script is the failure that actually costs an agent a turn: `04-auto-update-mechanics.md`, slow path section.

## D17. `accept`

**Decision.** Re-read prose and evidence, re-extract claims, validate liveness and budgets, show the metadata difference, then replace only `.contextify/evidence.json` and `.contextify/stamp.json`. Every context file stays byte-identical. `accept` refuses on a known-dead claim, a changed managed block, an invalid pointer or a budget violation; outside `--strict` it preserves explicitly `unverified` claims; with no stamp it exits 3.

**Why / Source.** B, primary. The common case after a refactor is that the docs are still right and only the evidence moved, and no comparable in `03-comparables-and-skills-cli.md` Part A has the verb.

## D18. The bounded mistakes log

**Decision.** `.contextify/mistakes.md` is optional and never created automatically. If it exists it is bounded: at most 60 lines, newest first, oldest pruned on write. `update` reads it and offers to promote an entry into a rule only when the same pattern appears in more than one entry, never on first occurrence, and a promoted rule keeps a reference to the incidents in evidence. The log is never imported into any context file: it is an evidence store, not context.

**Why / Source.** B for "do not create it automatically", plus `06b-reddit-browser.md` tips 20, 21 and 22, where the documented failure mode is exactly the bloat contextify exists to prevent: one reported log reached 250 entries and 16,000 lines with no pruning.

## D19. What the plugin ships, and what is opt-in

**Decision.** The plugin ships exactly one hook: a Claude Code `SessionStart` entry in `hooks/hooks.json`, matcher `startup|resume|clear`, `timeout: 5`, a single command string rather than an `args` array, reading `cwd` from the hook's stdin before falling back to `CLAUDE_PROJECT_DIR`. Codex, Gemini, Cursor, git `pre-commit` and a GitHub Action are documented opt-in snippets the user installs. One detection code path serves all of them, and `--hook AGENT` only selects the output envelope. Whether `04`'s example `args` field is accepted is `uncertain`, hence the single command string.

**Why / Source.** B plus A's `args` caution. Cursor uses `sessionStart` with snake_case `additional_context` while Claude Code and Gemini use `SessionStart` with camelCase `additionalContext` (`07-skeptic.md` correction 8), and Codex plugins cannot ship hooks at all (`04-auto-update-mechanics.md`, does-not-exist section), so shipping four hooks means owning four contracts that do not agree.

## D20. The story sentence

**Decision.**

```text
Tell every coding agent how your repo works. Then prove it is still true.
```

73 characters, counted with `python3 -c "print(len(s))"`. Pure ASCII, no comma, no apostrophe, no em dash, so it survives byte-identically through JSON, YAML and Markdown and smart-quote conversion cannot break it. Two beats, action then proof, matching `Find what a stranger can take from your app. Then close it and prove it closed.` (79) and `Hand Claude a huge task. Come back to proof it's done.` (54), and short enough to sit in a `SKILL.md` frontmatter description verbatim. Stored once in the plugin manifest and asserted from there across `.claude-plugin/marketplace.json` (`plugins[0].description` and `metadata.description`), the Cursor and Copilot manifests, `README.md` and `SKILL.md`.

**Why / Source.** A and C converged on it; chairman's pick. B's own `Give your agent the repo facts. Keep them current.` names maintenance but not proof, breaking the sibling pattern the brief locks. Equality chain and the two-suite gap: `07-skeptic.md` claim 10 detail.

## D21. The accent pair

**Decision.**

| Variant | Accent | HSL hue | Ground | Contrast |
|---|---|---:|---|---:|
| Dark | `#E879DF` | 304.86 | `#0A0F1C` | **7.4969:1** |
| Light | `#A32698` | 305.28 | `#FFFFFF` | **6.3870:1** |

Recomputed here with python3 and the WCAG 2.x formula, not taken on trust:

```text
s = channel / 255
linear(s) = s / 12.92                    when s <= 0.04045
linear(s) = ((s + 0.055) / 1.055) ** 2.4 otherwise
L = 0.2126 R + 0.7152 G + 0.0722 B
contrast = (L_lighter + 0.05) / (L_darker + 0.05)

L(#E879DF) = 0.361582625   L(#0A0F1C) = 0.004900180 -> 7.4969
L(#A32698) = 0.114397551   L(#FFFFFF) = 1.000000000 -> 6.3870
```

The same script reproduces the design system's published 7.11 for humanizer `#C77DFF` and 6.10 for sniff `#FF4D8D`, which is the check that the implementation is right. Both hues sit inside the 290 to 315 band, 30.71 degrees clear of humanizer (274.15) and 33.57 degrees clear of sniff (338.43), wider than the ladder's tightest existing pair of 20 degrees. Reserved green `#3DFFAB` is untouched. Gradient pair on dark: `#E879DF` to `#FF4D8D`.

**Why / Source.** B's pair was the only one of the four both inside the hue band and above 4.5 on the correct ground for each variant, and it clears the floor with the most margin. Ground tokens, accent ladder and the 20-degree rule: `/Users/adamboudj/projects/10x/.goal/research/svg-design-system.md`.

## D22. The mark

**Decision.** Two facing square brackets joined by an upper and a lower stepped rail. At `viewBox="0 0 40 40"` the whole mark is one closed path, stroke width 3, no fill, no text, no gradient and no glow at 40 px:

```text
M14 8 H7 V32 H14 V26 H26 V32 H33 V8 H26 V14 H14 V8 Z
```

The full geometry stays visible as a muted track. A second copy of the same path carries `pathLength="100"` and `stroke-dasharray="8 92"`, and its dash offset animates through one circuit in eight seconds. The travel is CSS, never SMIL and never a transform animation, so the reduced-motion guard stops it and the skew-clobber class of bug cannot occur. **What the travelling light traces:** the bright segment runs the left bracket, the lower rail, the right bracket and the upper rail back to the start, which is one instruction source travelling out to every agent file and back. Under reduced motion the segment freezes and the whole track stays drawn. Recognizability at native 40 px is `uncertain` until rendered: acceptance needs inspection at 40 px in both themes, visibly distinct frames in motion, identical frames under reduced motion.

**Why / Source.** B, primary. Brackets are not a blob, ring, loupe, page or nib, so the mark does not collide with a sibling. Animation primitives and the one-SMIL-exception rule: `svg-design-system.md`.

## D23. Target agents

**Decision.** Capped at about ten agents as one data table rather than one adapter class per agent, so adding a target is a row, not a file.

| Agent | File it reads | Pointer by default | `-a` code for `npx skills add` |
|---|---|---|---|
| Claude Code | `CLAUDE.md`, not `AGENTS.md` | yes | `claude-code` |
| Codex CLI | `AGENTS.md`, with `AGENTS.override.md` first at every level | no, it reads AGENTS directly | `codex` |
| Cursor | root and nested `AGENTS.md` natively; `.cursor/rules/*.mdc` optional | no, opt in with `--targets cursor-rule` | `cursor` |
| GitHub Copilot | `AGENTS.md` nearest-wins, plus root `CLAUDE.md` or `GEMINI.md` | yes when `.github/` exists | `uncertain` |
| Gemini CLI | `GEMINI.md`, or a `context.fileName` array | yes | `uncertain` |
| OpenCode | context file `uncertain` | no | `opencode` |
| Cline | `.clinerules` per airul's `src/generator.ts` | no | `cline` |
| Windsurf | `.windsurfrules` per airul's `src/generator.ts` | no | `uncertain` |
| Amp | listed among rulesync's `src/constants/*-paths.ts` targets | no | `uncertain` |
| Kiro | listed among rulesync's `src/constants/*-paths.ts` targets | no | `uncertain` |

Only `claude-code`, `codex`, `cursor`, `opencode` and `cline` are confirmed `-a` codes; the README states roughly 80 more exist but the rest were not individually confirmed, so they are `uncertain` rather than guessed.

**Why / Source.** B for the capped table. Thirty near-identical adapter classes is surface area for drift, and 47 targets is a promise of 47 untested pairs: `08-steal-list.md` sections 1 and 2. Confirmed `-a` codes: `07-skeptic.md` claim 8c. Per-agent file facts: claims 3b, 4, 4c, 6, 7, 7b and correction 1.

## Beat-them-here claims (each becomes a test)

Every row runs offline on fixture git repos against the deterministic scripts only: no model, no network. Comparisons are scoped to the implementation paths inspected in `08-steal-list.md`, not to claims about every current release.

| # | Claim | Comparable it beats (name plus path from 08) | Test: input, action, expected assertion |
|---|---|---|---|
| 1 | Human edits outside the managed block survive, and a no-op re-run is byte-identical | ruler: `AbstractAgent.applyRulerConfig` to `writeGeneratedFile` overwrites the body, while only `src/core/GitignoreUtils.ts` keeps a block | **Input:** generated files plus a `Human sentinel` line after the end marker. **Action:** `update` twice with unchanged evidence. **Assert:** sentinel bytes identical; run 2 changes no file, no header timestamp and no stamp field |
| 2 | The 150-line ceiling is enforceable without a local hook | ClaudeForge: `agent/claude-md-guardian.md` plus `hooks/validate-claude-md.py`, advisory when a developer disables the validator locally | **Input:** a 151-line AGENTS.md, local hooks disabled. **Action:** run the opt-in CI gate. **Assert:** the gate fails naming the actual count 151; generation refuses the same proposal; no file changes |
| 3 | The freshness check calls no model and no network | agentrules-architect: `core/pipeline/orchestrator.py` with `phase_1.py` through `final_analysis.py` | **Input:** stamped repo, model and network executables replaced by failing sentinels. **Action:** check fresh, then delete a referenced script without staging and check again. **Assert:** zero sentinel calls; first stdout empty at exit 0; second names the stale claim with file and line, still exit 0 |
| 4 | An unreferenced dependency bump is silent, a command-body change is caught | airul: `src/generator.ts` regenerates wholesale on every run | **Input:** `scripts.test` set to `runner-a`, no version claims. **Action:** stage a dependency-version and a lockfile-content change, check; then change the script body to `runner-b`, check. **Assert:** first check exits 0 with zero stdout bytes; second reports `package.json#scripts`; neither rewrites prose |
| 5 | Every generated claim names its supporting selector and source line | ruler: `src/core/RuleProcessor.ts` attributes a whole source file, not a claim | **Input:** a manifest with `scripts.test`, candidate prose with that command plus an unsupported port. **Action:** validate the proposal. **Assert:** the command resolves to an exact selector and source line; the port is omitted or visibly `unverified`; `--strict` rejects it |
| 6 | The drift notice is bounded at 12 lines however much moved | ClaudeForge: `agent/claude-md-guardian.md` emits unbounded LLM prose | **Input:** a stamped fixture, then one commit moving 20 evidence keys and killing 6 claims. **Action:** `ctx-check`. **Assert:** stdout is at most 12 lines and 2,048 bytes, exit 0, and the last line names the next command |
| 7 | Adding an agent never duplicates repository instructions | airul: `src/generator.ts` writes one content blob to `.windsurfrules`, `AGENTS.md`, `.clinerules` and `CLAUDE.md` | **Input:** AGENTS.md containing the unique sentence `Fixture ownership rule 17`. **Action:** generate every pointer target. **Assert:** the sentence occurs exactly once across all generated instruction files; each pointer resolves to AGENTS.md; CLAUDE.md line 1 is `@AGENTS.md`; GEMINI.md is 3 lines; the `.mdc` parses with `alwaysApply: true` and a non-empty `description` |
| 8 | Output budget scales with repository size | agents-md-generator: `AGENTS.md.template` plus `agents-md-seed.sh`, one fixed template always | **Input:** a 3-file single-unit fixture and a 200-file two-workspace fixture with fixed evidence-backed candidates. **Action:** classify and render. **Assert:** tiny classified tiny and at most 20 lines with no Architecture heading; monorepo targets 60 and includes evidenced cross-package architecture; neither exceeds 150 |
| 9 | Byte overflow is caught even when the line count passes | ClaudeForge: `hooks/validate-claude-md.py` caps lines only | **Input:** a valid AGENTS.md under 150 lines but 40,000 UTF-8 bytes, Codex selected. **Action:** `init --dry-run`, then an attempted write. **Assert:** the report names 40,000 and 32,768; the write is refused; `git status --porcelain` stays empty. Separate fixtures cover inherited instructions and a shadowing `AGENTS.override.md` |
| 10 | An existing hand-written context file has a preservation path | Gemini CLI: `packages/cli/src/ui/commands/initCommand.ts` `performInit()` refuses outright when GEMINI.md exists | **Input:** a hand-written GEMINI.md, no AGENTS.md. **Action:** `init --dry-run`, then approve explicit migration. **Assert:** pre-approval files byte-identical; approved text retained exactly in AGENTS.md; resulting GEMINI.md is 3 lines; the dry-run diff has no removal line for the human file |
| 11 | An interrupted multi-file update can never be reported fresh | agentrules-architect: `tempfile.mkstemp` plus `os.replace` per artifact, which is not a multi-file transaction | **Input:** an existing generation plus proposed changes to several outputs. **Action:** inject termination after each replacement boundary in turn. **Assert:** the journal survives until completion; `ctx-check` returns 1 with stderr only and empty stdout while incomplete; recovery restores the old generation or completes the validated new one before freshness can pass |
| 12 | One refusal class guards every target path | ruler has the guards only in `src/core/FileSystemUtils.ts`; rulesync spreads them across `src/constants/*-paths.ts` | **Input:** `--targets` entries whose resolved output escapes the scope, one per supported target id. **Action:** `init --dry-run` and `init --yes`. **Assert:** every target refuses with the identical error class and exit code; no file is created outside the repository root |

## Open risks

1. **Bounded parsers may leave too much evidence `unverified`.** Coverage is `uncertain`, especially for YAML inheritance, computed build targets, and runners outside the extraction table such as `uv run`, `poetry run`, `mise` and `task`. *What would change the decision:* counting how often real target repositories use forms outside the table. If they clear roughly ten percent, those forms go into the extractor before launch; if bounded parsing still leaves most claims unverified on real repositories, the liveness promise gets narrowed in the README rather than quietly overstated.

2. **Thin pointers may load differently across agent surfaces.** Copilot feature coverage and Gemini duplicate-loading behaviour are `uncertain`, and only Claude Code is documented as stripping block-level HTML comments, so the provenance header may be costing tokens in every other reader. *What would change the decision:* versioned integration tests inspecting what each agent actually loaded, plus a Codex or Gemini session dumping its merged instructions. If the header reaches the model, it shrinks to a bare `<!-- contextify:begin v1 -->` and the metadata lives only in the stamp.

3. **The fast path's extra guards may cost more than the fast path saves, and the index is the wrong baseline under heavy worktree use.** Latency is `uncertain` beyond the roughly 10 ms measured for the bare `git ls-files -s` digest, and a committed stamp in a repository with several worktrees could report another worktree's staged state as drift. *What would change the decision:* warm and cold benchmarks on a large monorepo plus a failing two-worktree reproduction. Either result moves the fast key off the index onto HEAD tree hashes, keeping unstaged-change coverage in the slow path.
