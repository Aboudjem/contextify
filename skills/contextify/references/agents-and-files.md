# Agents and files

Per-agent file, discovery-order and ceiling facts for the ten targets in DECISIONS.md D23, the literal pointer contents from D6, and what each pointer costs the reader.

## Per-agent table

| Agent | File(s) it reads | Discovery order | Ceiling | Source |
|---|---|---|---|---|
| Claude Code | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/*.md`. Not `AGENTS.md`. | Root-to-cwd concatenation: ancestor files load at launch, filesystem root down to the working directory; subdirectory files load on demand when Claude reads a file there. | Guidance: target under 200 lines. A file over 4 MiB is skipped entirely. | https://code.claude.com/docs/en/memory |
| Codex CLI | `AGENTS.md`, with `AGENTS.override.md` checked first at every level (home directory, then each directory from repo root down to cwd). | Root-to-cwd concatenation, joined with blank lines; files closer to cwd land later in the combined prompt and so override earlier guidance. | 32,768 bytes (`project_doc_max_bytes`), silent truncation once the combined size reaches the limit. | https://learn.chatgpt.com/docs/agent-configuration/agents-md |
| Cursor | Root and nested `AGENTS.md` natively; `.cursor/rules/*.mdc` optional. | Team Rules, then Project Rules, then User Rules, merged, earlier wins. Nested `AGENTS.md` files combine with parent directories, more specific instructions take precedence. | Guidance: keep rules under 500 lines. | https://cursor.com/docs/context/rules |
| GitHub Copilot | `AGENTS.md` (nearest wins), root `CLAUDE.md` or `GEMINI.md` as an alternative, `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` with `applyTo`. | Nearest `AGENTS.md` in the directory tree wins. Separately, all relevant instruction sets, personal, path-specific, repo-wide, agent, org, are supplied together; precedence resolves conflicts, it does not drop any file. | Agent-generated instructions: no longer than 2 pages. | https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions |
| Gemini CLI | `GEMINI.md` by default, or the file(s) named in `context.fileName`. | Global `~/.gemini/GEMINI.md`, then workspace and parent directories, then a just-in-time scan when a tool accesses a directory. All found files are concatenated. | Not documented. | https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md |
| OpenCode | `AGENTS.md`/`CLAUDE.md` by upward traversal, `~/.config/opencode/AGENTS.md` global, `~/.claude/CLAUDE.md` as a Claude-compat fallback. | Traverse up from cwd; the first matching file wins in each category, then all instruction files are combined. | Not documented. | https://opencode.ai/docs/rules/ |
| Cline | `.clinerules/` directory (`.md` and `.txt` combined), a global rules directory, `~/.agents/AGENTS.md`. | Every file in the workspace `.clinerules/` directory is combined into one rule set. | Not documented. | https://docs.cline.bot/features/cline-rules |
| Windsurf | `.devin/rules/*.md` (preferred), `.windsurf/rules/*.md` (legacy fallback), `.windsurfrules` (legacy single file), `global_rules.md`. | Workspace rules plus an always-on global file; each rule carries a `trigger` frontmatter mode. | 12,000 characters per workspace file, 6,000 for the global file. | https://docs.devin.ai/desktop/cascade/memories |
| Amp | `AGENTS.md`, falling back to `AGENT.md` or `CLAUDE.md`. | cwd and parents up to `$HOME` are always included; subtree `AGENTS.md` files are included when the agent reads a file in that subtree; user-config and system-wide files also apply. | Not documented. | https://ampcode.com/docs/customize/agents-md |
| Kiro | `uncertain`, listed only among rulesync's `src/constants/*-paths.ts` targets, no official page located. | `uncertain` | `uncertain` | `10x/.goal/research/ctx/03-comparables-and-skills-cli.md`, Part A, rulesync row |

Two agents outside D23's ten, included only for contrast in discovery pattern, never as a contextify write target:

| Agent | File(s) it reads | Discovery order | Source |
|---|---|---|---|
| Zed | `.rules`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `.github/copilot-instructions.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`. | First-match-only against a fixed precedence list, genuinely different from every concatenating agent above. | https://github.com/zed-industries/zed/blob/main/docs/src/ai/rules.md |
| Aider | `CONVENTIONS.md`, any filename. | No auto-discovery at all; loaded only with `/read`, `--read`, or a `read:` key in `.aider.conf.yml`. | https://aider.chat/docs/usage/conventions.html |

## Facts the table cells compress

- Codex's `AGENTS.override.md` is checked before `AGENTS.md` at every directory level, the home directory and each level from project root to cwd, not only globally. Source: `10x/.goal/research/ctx/07-skeptic.md` claim 4c and correction 9.
- Gemini's context-file-name switch is a nested settings key, never a flat one: `{"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}}`. A top-level `contextFileName` key does nothing in the installed CLI. Source: `07-skeptic.md` claim 5 and correction 1.
- Cursor's `.cursor/rules/*.mdc` files require frontmatter (`description`, `globs`, `alwaysApply`); a plain `.md` file placed in `.cursor/rules` is ignored because it carries no frontmatter. Source: `07-skeptic.md` claim 6b, https://cursor.com/docs/context/rules.
- Copilot's `.github/instructions/*.instructions.md` files scope by an `applyTo` glob in frontmatter, for example `applyTo: "app/models/**/*.rb"`. Source: `07-skeptic.md` claim 7c.

## Literal pointer file contents (D6)

`CLAUDE.md`, four lines by default, `@AGENTS.md` first:

```markdown
@AGENTS.md
<!-- contextify:begin v1 -->
<!-- Generated by contextify {toolVersion}; writer={generatedBy}; at={generatedAt}; commit={commit}; regenerate: /contextify update -->
<!-- contextify:end -->
```

`GEMINI.md`, exactly three lines:

```markdown
<!-- contextify:begin v1; Generated by contextify {toolVersion}; writer={generatedBy}; at={generatedAt}; commit={commit}; regenerate: /contextify update -->
@AGENTS.md
<!-- contextify:end -->
```

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

Source: `docs/design/DECISIONS.md` D6.

## What each pointer costs the reader

A pointer file is a handful of physical lines: `CLAUDE.md` is 4, `GEMINI.md` is 3, the Cursor `.mdc` is 9, the Copilot pointer is 4. They avoid duplicated maintenance, not the cost of reading the shared instructions. An import loads AGENTS.md too; total context cost depends on the host's loading behavior.

Copilot link-following behavior varies by feature and is not treated here as a guaranteed native import. Measure actual host loading rather than inferring token savings from file length.

Whether Claude Code's `@AGENTS.md` import, once resolved, counts the same way against the importing file's own 200-line guidance is `uncertain`: the memory page documents the import mechanic and the size guidance separately, and neither 01 nor 07 states whether an imported file's lines count against the importing file's own budget.
