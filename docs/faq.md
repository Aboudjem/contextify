# FAQ

Tell every coding agent how your repo works. Then prove it is still true. contextify reads your
repository, writes `AGENTS.md` as the one source of facts, points every other agent file at it, and
checks at every session start whether anything it wrote still resolves.

## Why AGENTS.md and not CLAUDE.md as the source

Because AGENTS.md is the file Codex, Cursor and, nearest-wins, GitHub Copilot read natively, while
Claude Code reads `CLAUDE.md`. Writing the facts once into `AGENTS.md` and pointing every other file
at it, rather than writing the same facts several times, is the whole single-source design. See
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

## Why no code blocks

Because a pasted snippet rots silently the moment the code it describes changes, and an agent greps a
one-line fact faster than it reads a fenced block. The writer rejects fenced code blocks in generated drafts. See
[D3](design/DECISIONS.md).

## Does the hook rewrite my files

Never. `ctx-check` only reads and prints. Nothing is written by any hook, in Claude Code or in any of
the opt-in snippets for other agents. Only `/contextify init`, `update`, and `accept` write, and each
shows a diff first.

## What does the hook cost

Zero tokens when the repository is fresh: `ctx-check` prints nothing and nothing is injected. When
something has moved, it costs the length of the drift notice, at most 12 lines and 2,048 bytes. See
[D9 and D11](design/DECISIONS.md).

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

Yes, for the files: `AGENTS.md` and its pointers are ordinary Markdown any agent can read. The
`SessionStart` hook is Claude-Code-only out of the box; the equivalent for the others is an opt-in
snippet you install yourself. See [editors](editors.md) and [hooks](hooks.md).

## What about monorepos

A monorepo is classified by build units, directories with their own manifest and an independently
declared build, test or executable entry point, joined by workspace configuration. It targets 60
lines and can carry nested `<package>/AGENTS.md` bodies. See [D2](design/DECISIONS.md).

## Does it run a model at session start

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

Yes: uninstall the plugin, or remove the `SessionStart` entry from `hooks/hooks.json` if you copied
the skill in by hand. Nothing else in contextify depends on the hook running.

## More

- [Quickstart](quickstart.md) · [Install in your editor](editors.md) · [Hooks and CI](hooks.md)
- [Honest limits](limits.md) · [Comparison](comparison.md)
