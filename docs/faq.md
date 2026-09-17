# FAQ

Tell every coding agent how your repo works. Then prove it is still true. Contextify writes a short `AGENTS.md`, optional supporting documents and editor pointers. Installed Git hooks check for drift at commit and push.

## Why AGENTS.md and not CLAUDE.md as the source

Because AGENTS.md is the file Codex, Cursor and, nearest-wins, GitHub Copilot read natively, while
Claude Code reads `CLAUDE.md`. The entry point carries common instructions; editor pointers refer to it. Longer architecture or workflow explanations can live in linked supporting documents without being copied into every editor file. See
[the design decisions](design/DECISIONS.md), D6.

## Does Claude Code read AGENTS.md

No. Claude Code reads `CLAUDE.md`. contextify's `CLAUDE.md` is four lines, and its first line is
`@AGENTS.md`, which imports the real content. If that import line is removed, `check` reports
`CLAUDE.md:1 no longer imports AGENTS.md`. See [D6](design/DECISIONS.md).

## Why 60 lines

The targets are 20 lines for a tiny repository, 40 for a medium one and 60 for a
monorepo, with a hard ceiling of 150. The budget exists because of a specific finding: the ETH Zurich
paper (arXiv 2602.11988) reports that context files "do not generally improve task success rates,
while increasing inference cost by over 20% on average." Claude Code's own `/init` guidance is to keep
a context file "target under 200 lines". contextify's ceiling sits well under that. See
[D1 and D2](design/DECISIONS.md).

## Can it write architecture or workflow documents

Yes, when they fill an evidenced gap. Contextify first reuses accurate existing docs. It can generate `docs/context/architecture.md` and `docs/context/workflows.md`, each capped at 120 lines, and link them from `AGENTS.md`. It does not automatically create an ADR collection, API reference or security policy. See [supporting documents](supporting-docs.md).

## Why no code blocks

Because a pasted snippet rots silently the moment the code it describes changes, and an agent greps a
one-line fact faster than it reads a fenced block. The writer rejects fenced code blocks in `AGENTS.md` drafts. Supporting documents should keep commands short and reference source files instead of copying large examples. See
[D3](design/DECISIONS.md).

## Does the hook rewrite my files

Never. `ctx-check` only reads and prints. Git and host-session checks do not modify files. The optional CI mode may write the GitHub job summary, but never repository context. Only `/contextify init`, `update`, and `accept` write, and each
shows a diff first.

## What does the hook cost

The checker makes no model calls. A fresh Git check is silent; a drift notice costs context only if an agent later reads it. Notices are bounded to 12 lines and 2,048 bytes. Runtime depends on the repository and machine; see [limits](limits.md).

## Why commit .contextify/stamp.json

So the freshness check is shared, not personal. When `stamp.json` is committed, one person's
`/contextify update` after a refactor quiets the notice for every clone that pulls the new commit,
instead of every teammate separately hitting and re-fixing the same drift. See
[D14](design/DECISIONS.md).

## What if I hand-edit AGENTS.md

Outside the managed block, marked by `<!-- contextify:begin v1 -->` and `<!-- contextify:end -->`,
your bytes are preserved exactly. Inside the block, a hand edit is reported as `edited`, not silently
overwritten. `accept` refuses a changed managed block: review the edit and use the writer's explicit conflict-resolution path with a matching draft. See
[D5 and D7](design/DECISIONS.md).

## What is accept for

The common case after a refactor: the prose in `AGENTS.md` is still correct and only the evidence
moved underneath it. `accept` re-validates liveness and budgets, updates `.contextify/evidence.json`
and `.contextify/stamp.json`, and leaves every context file byte-identical. It refuses on a known-dead
claim. See [D17](design/DECISIONS.md).

## Does it work with Codex, Gemini, Cursor, Copilot

Yes, for the files: `AGENTS.md` and its pointers are ordinary Markdown any agent can read. No session hook is enabled by default. Git hooks are editor-independent; host-session adapters are optional. See [editors](editors.md) and [hooks](hooks.md).

## What about monorepos

A monorepo is classified by build units, directories with their own manifest and an independently
declared build, test or executable entry point, joined by workspace configuration. It targets 60
lines and can carry nested `<package>/AGENTS.md` bodies. See [D2](design/DECISIONS.md).

## Does a check call a model

No. `ctx-check` runs local shell and Python code. Generation and revision use your coding agent when you invoke `init` or `update`. The `accept` script revalidates and refreshes metadata without a model call; deciding whether prose remains correct still requires a review.

## Does it send anything anywhere

The deterministic discovery, writer and checker scripts do not make network requests. Your coding agent handles generation under its own data policy. Installation and the optional CI setup fetch the released code from GitHub.

## What is .contextify/mistakes.md

An optional, bounded log, at most 60 lines, newest first, that you or the agent can keep of repeated
mistakes. It is never created automatically and it is never imported into any context file: it is
evidence a promoted rule can point back to, not context an agent loads by default. See
[D18](design/DECISIONS.md).

## Why not symlink CLAUDE.md to AGENTS.md

The supported default is a regular `CLAUDE.md` containing `@AGENTS.md`. It can carry a Claude-only addendum without copying repository instructions. The current writer refuses `--symlink` rather than silently ignoring it.

## Can I turn the hook off

Yes. Remove the Contextify calls from your active Git hooks, or restore your previous hooks configuration. Do not delete hooks owned by other tools. Removing the plugin does not remove independently installed Git hooks or project session settings. Manual checks continue to work. See [hooks and migration](hooks.md).

## More

- [Quickstart](quickstart.md) · [Install in your editor](editors.md) · [Hooks and CI](hooks.md)
- [Honest limits](limits.md) · [Comparison](comparison.md)
