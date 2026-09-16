# Monorepo

Nested AGENTS.md rules per tool, when contextify writes a nested pointer, what goes in it, and the budget.

## Nested AGENTS.md, per tool

| Tool | Nested behaviour | Source |
|---|---|---|
| Codex CLI | Root-to-cwd concatenation: `AGENTS.override.md` then `AGENTS.md` are checked at every directory level from repo root down to cwd, joined with blank lines; closer files win because they land later in the combined text. Capped at 32,768 bytes total (`project_doc_max_bytes`). | `10x/.goal/research/ctx/07-skeptic.md` claims 4, 4b, 4c; https://learn.chatgpt.com/docs/agent-configuration/agents-md |
| Cursor | Nested `AGENTS.md` files are supported natively in any subdirectory; instructions from a nested file combine with parent directories, with more specific instructions taking precedence. | `07-skeptic.md` claim 6; https://cursor.com/docs/context/rules |
| GitHub Copilot | The nearest `AGENTS.md` in the directory tree wins; a repository can carry more than one `AGENTS.md`, stored anywhere in the tree. | `07-skeptic.md` claim 7; https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions |
| Claude Code | Loads a subdirectory `CLAUDE.md` on demand, only when Claude reads a file in that directory; ancestor files above the working directory load at launch and everything found is concatenated, not overridden. `@` imports resolve relative to the file containing the import, not the working directory, to a maximum depth of 4 hops. | `10x/.goal/research/ctx/01-official-docs.md`, sections (a) and (b)1; `07-skeptic.md` claim 3 |

## When contextify writes a nested `<pkg>/AGENTS.md`

Only when a directory is a **build unit**, DECISIONS.md D2's definition: a directory with its own manifest and an independently declared build, test or executable entry point, **and** that unit's commands differ from the root's. A build unit whose commands match the root gets no nested file: the root `AGENTS.md` already covers it, and a second file would only restate the same commands under a different path.

## What goes in a nested file

- Commands that differ from the root: a package-local test runner, a different build target, a non-default working directory.
- Package-specific hazards evidenced inside that package: a migrations directory, a generated-code marker, a deploy script scoped to that package.
- Nothing that repeats the root. Architecture, conventions and repository workflow stay in the root `AGENTS.md` and are never restated per package.

## Budget

DECISIONS.md D2 sets a Tiny-classified repository's target at 20 lines. A nested `<pkg>/AGENTS.md` uses the same 20-line target, by the same logic: it is describing one build unit's differences from the root, which is a Tiny-repo-sized amount of content. D2 does not separately define a nested-file ceiling; this is an application of the Tiny number, not a distinct decision, and should be read as such.

## Pointer files in packages

None by default. Claude Code's subdirectory `CLAUDE.md` is optional, loaded only on demand when Claude reads a file in that directory, and `@../AGENTS.md`-style imports resolve relative to the importing file rather than to the working directory. A package that needs to point at the root file can carry one import line if a human adds a `CLAUDE.md` there; contextify does not scaffold a pointer file for every package by default. Source: `01-official-docs.md`, section (b)1; `07-skeptic.md` claim 3.
