# Init prompts

The verbatim `/init` prompts contextify is measured against, what contextify keeps from each, and what it does differently and why.

All four prompts below were extracted by `strings` on installed binaries or from source, recorded in `10x/.goal/research/ctx/08-steal-list.md`, section 2. No success-rate percentage is claimed anywhere in this file; see the closing section for why.

## Claude Code, current stable prompt

Extracted via `strings` on the installed `claude` binary (`claude` 2.1.273), function `Fqs`:

> Please analyze this codebase and create a CLAUDE.md file, which will be given to future instances of Claude Code to operate in this repository.
>
> What to add:
> 1. Commands that will be commonly used, such as how to build, lint, and run tests. Include the necessary commands to develop in this codebase, such as how to run a single test.
> 2. High-level code architecture and structure so that future instances can be productive more quickly. Focus on the "big picture" architecture that requires reading multiple files to understand.
>
> Usage notes:
> - If there's already a CLAUDE.md, suggest improvements to it.
> - When you make the initial CLAUDE.md, do not repeat yourself and do not include obvious instructions like "Provide helpful error messages to users", "Write unit tests for all new utilities", "Never include sensitive information (API keys, tokens) in code or commits".
> - Avoid listing every component or file structure that can be easily discovered.
> - Don't include generic development practices.
> - If there are Cursor rules (in .cursor/rules/ or .cursorrules) or Copilot rules (in .github/copilot-instructions.md), make sure to include the important parts.
> - If there is a README.md, make sure to include the important parts.
> - Do not make up information such as "Common Development Tasks", "Tips for Development", "Support and Documentation" unless this is expressly included in other files that you read.
> - Be sure to prefix the file with: `# CLAUDE.md` / `This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.`

**What contextify keeps.** Commands first, then architecture. The single-test invocation. The "big picture, requires reading multiple files" framing for what counts as architecture, not a directory listing. The exclusion instinct against generic advice and invented sections. All of this is D1's evidence and skeleton design, sourced to this exact prompt.

**What contextify does differently, and why.**
- Evidence per line. This prompt asks the model to avoid making things up but gives it no mechanism; D3 requires every command, path, port, branch and deploy fact to trace to a file the run actually read, or be labelled `unverified`, recorded in `.contextify/evidence.json`.
- Budget. This prompt gives no line count; D1 and D2 give an explicit per-section allowance that sums to 60 lines and scales by repository size, with a hard 150-line ceiling.
- No code blocks. This prompt does not forbid pasted snippets; D3 forbids a code block anywhere in the generated `AGENTS.md`, on the theory that the agent greps faster than it reads and a pasted snippet rots silently.
- No header boilerplate line. This prompt requires a fixed prefix sentence naming Claude Code and claude.ai/code; D5 replaces it with a single HTML-comment provenance line (tool version, writer, timestamp, commit) that every reader can ignore, not a sentence aimed at one agent.
- A drift stamp. This prompt has no freshness mechanism at all; re-running `/init` is the only way to notice staleness. D9 and D14 give contextify a committed stamp and a `ctx-check` that reports drift without a model call.

## Claude Code, experimental interactive prompt

Gated behind `CLAUDE_CODE_NEW_INIT=1` (also `tengu_slate_harbor_experiment`), found in the same binary, function `$qs`, and independently confirmed by https://code.claude.com/docs/en/memory ("Set `CLAUDE_CODE_NEW_INIT=1` to enable an interactive multi-phase flow"). A full 9-phase flow, summarized as `08-steal-list.md` gives it:

- **Phase 0**: check for an existing `CLAUDE.md`, branch the whole flow on found or not found.
- **Phase 1**: `AskUserQuestion`, which files to set up (project `CLAUDE.md` / personal `CLAUDE.local.md` / both / "let Claude decide"), then whether to also set up skills and hooks.
- **Phase 2**: explore via subagent, manifests, README, CI config, existing rule files from six other tools (`.cursor/rules`, `.github/copilot-instructions.md`, `.devin/rules/`, `.windsurf/rules/`, `.clinerules`, `.mcp.json`), plus a presence-only check for `~/.codex/config.toml` and `~/.gemini/settings.json`/`GEMINI.md` behind the `tengu_import` flag.
- **Phase 3**: a gap-fill interview via `AskUserQuestion`, never marking any option "recommended" for a personal-preference question; builds a typed preference queue of `{type: hook|skill|note, description, target file}`.
- **Phase 4**: write `CLAUDE.md`. Every line must pass this test: "Would removing this cause Claude to make mistakes?" If no, cut it. Excludes file-by-file structure, standard conventions, generic advice, long references, using `@path/to/import` instead.
- **Phase 5**: write `CLAUDE.local.md`, auto-added to `.gitignore`, with a branch for external worktrees.
- **Phase 6**: propose and scaffold skills at `.claude/skills/<name>/SKILL.md`.
- **Phase 7**: check for the `gh` CLI, missing lint config, and build hooks through the `update-config` skill's hook-construction flow.
- **Phase 8**: a summary plus a prioritized follow-on checklist.

**What contextify keeps.** The line-by-line test from Phase 4, "would removing this cause a mistake," is the same instinct behind D3's evidence rule and D1's per-section allowances: every line has to earn its place. The include/exclude list (exclude file-by-file structure, generic advice, long references; use `@path/to/import` instead) matches D6's thin pointers exactly.

**What contextify does differently, and why.** This flow is a full interactive product, single-agent, Claude-only, that asks the human questions and scaffolds skills and hooks unattended. Contextify runs the same deterministic evidence extraction across all ten D23 targets at once rather than one interactive session per agent, asks at most three questions total (D13) instead of a multi-phase interview, and ships a committed stamp (D14) so staleness is checked at configured Git checkpoints rather than depending on someone remembering to re-run `/init`.

## Gemini CLI, `/init`

Extracted from `packages/cli/src/ui/commands/initCommand.ts` and `performInit()` inside the installed `@google/gemini-cli` bundle (`gemini` 0.51.0, `chunk-DHQ53XVO.js`). Gemini writes an empty `GEMINI.md` first, then submits this prompt:

> You are an AI agent that brings the power of Gemini directly into the terminal. Your task is to analyze the current directory and generate a comprehensive GEMINI.md file to be used as instructional context for future interactions.
>
> Analysis Process: (1) Initial Exploration, list files, read README. (2) Iterative Deep Dive (up to 10 files), let discoveries guide which files to read next. (3) Identify Project Type, code project (package.json/requirements.txt/pom.xml/go.mod/Cargo.toml/build.gradle/src dir) vs. non-code project (docs/notes/research).
>
> For a Code Project: Project Overview, Building and Running (infer commands, TODO placeholder if not found), Development Conventions.
> For a Non-Code Project: Directory Overview, Key Files, Usage.
>
> Final Output: Write the complete content to the GEMINI.md file. The output must be well-formatted Markdown.

If `GEMINI.md` already exists, `/init` refuses outright: "A GEMINI.md file already exists in this directory. No changes were made." There is no improve-existing path.

**What contextify keeps.** The infer-then-flag instinct for a missing command, though contextify replaces the bare `TODO` placeholder with an explicit `unverified` label carrying an evidence reference, per D3. The rough code-project versus non-code-project split is subsumed by D2's Tiny / Medium / Monorepo classification, which scales by evidence quantity rather than branching on project type.

**What contextify does differently, and why.** Gemini's `/init` refuses outright when `GEMINI.md` already exists; D7 never simply refuses, it recognizes managed blocks, proposes a migration diff for unmarked human content, and inserts after the first H1. Gemini's output has no ongoing freshness check once written; D9's `ctx-check` and D14's stamp give contextify a same-session, model-free way to know the file is still right. Gemini's budget is an unscaled two-branch template; D2 scales a numeric line target with repository size.

## Codex CLI, `/init`

Extracted from the native `codex-darwin-arm64` binary (`vendor/aarch64-apple-darwin/bin/codex`, `codex-cli` 0.154.0). The entire generative instruction is one sentence, no phases, no exclusion rules, no format priming:

> Generate a file named AGENTS.md that serves as a contributor guide for this repository.

Everything else about Codex's `AGENTS.md` handling is deterministic discovery, not generative prompting: `AGENTS.override.md` then `AGENTS.md` checked at every level from repo root to cwd, concatenated with the closer file overriding by ordering, stopping once the combined size hits `project_doc_max_bytes` (default 32 KiB). Source: https://learn.chatgpt.com/docs/agent-configuration/agents-md.

**What contextify keeps.** Putting the rigor into deterministic mechanics rather than prompt length. Contextify's whole split of labour, scripts own discovery, evidence, budgets and ceilings; the model only drafts prose, is the same instinct scaled up: Codex trusts model judgment for content and puts its engineering into file discovery and a byte budget, and contextify does the same but adds provenance per line on top.

**What contextify does differently, and why.** A one-sentence prompt gives the model no exclusion guidance and no line budget at all, so output quality depends entirely on the model's own judgment every time. D1 through D4 give explicit section-by-section line allowances and an evidence rule so budget and provenance never depend on the model remembering to be terse, and D12 shows the Codex byte cost against the real 32,768-byte ceiling before anything is written, rather than after Codex has silently truncated it.

## The cost this pays for

Quoted verbatim from the abstract of arXiv 2602.11988, "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" (Thibaud Gloaguen, Niels Mündler, Mark Müller, Veselin Raychev, Martin Vechev, submitted 2026-02-12):

> "does not generally improve task success rates, while increasing inference cost by over 20% on average"

No success-rate percentage may be quoted alongside this finding: the abstract states exactly one number, the cost increase, and gives no success-rate figure in either direction. Source: `10x/.goal/research/ctx/07-skeptic.md` claim 9 and correction 2.

## The three questions contextify's own `init` asks

At most three, each asked only when its trigger fires, each skippable. `update`, `check` and `accept` never ask. Nothing is asked about language, framework, package manager or ports when repository evidence answers it (source: `docs/design/DECISIONS.md` D13).

| # | Trigger | Literal question | Default when skipped |
|---|---|---|---|
| 1 | More than one agent is evidenced by existing configuration, or none is | `Which agents should get pointer files?` | Claude Code plus any agent evidenced by existing repository configuration (`.cursor/`, `.github/`, `.gemini/`, `.codex/`). `AGENTS.md` is unconditional; the Cursor rule file is off |
| 2 | No single-test invocation was evidenced, or a deploy or migration path exists with no recorded approval rule | `What must an agent know that the repository does not show, especially a single-test command or an action that needs approval?` | Skip. A human-supplied technical fact stays `unverified` until a file read during the run supports it |
| 3 | The dry-run diff touches an existing file | `Apply the displayed changes?` | Apply safe additions and managed-block replacements, with conflicts excluded and visibly reported |

`init` asks nothing at all when `--yes` supplies the decisions, when `--dry-run` asks only for a proposal, when every choice is explicit and only new non-conflicting files are created, or when input is not interactive (non-interactive without `--yes` produces a dry-run proposal, not a write). Outside Claude Code, where `AskUserQuestion` may not exist, ask each as plain text, wait once, and apply the default when no answer comes.
