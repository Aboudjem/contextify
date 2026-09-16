# Quickstart

A first run on a repository at `/Users/you/tidemark`. Yours prints your real paths. contextify reads
your repository and writes `AGENTS.md` as the one file that carries the facts; every other agent file
it writes is a thin pointer back to it.

## 1. Install

```bash
claude plugin marketplace add Aboudjem/contextify
claude plugin install contextify@contextify-marketplace
```

Any other agent, same skill directory:

```bash
npx skills add Aboudjem/contextify -a claude-code
```

## 2. Run it

Run `/contextify init` in your project.

## 3. What you see

`init` discovers evidence, package.json scripts, CI workflow run lines, tsconfig paths, a Makefile,
whatever the repository actually has, classifies the repository as tiny, medium or monorepo, drafts
`AGENTS.md` against the line budget for that class, and writes the pointer files you selected. It ends
with a summary block. This is an example rendering, not a measured result:

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

## 4. Read the diff before you approve it

Every write goes through a diff first. Every command, path, port, branch and deploy fact that lands in
`AGENTS.md` traces back to a file contextify actually read; anything it could not confirm is labelled
`unverified` or left out. Read that diff the way you would read any pull request before merging it.

## 5. Commit AGENTS.md, CLAUDE.md and .contextify/

Commit `AGENTS.md`, `CLAUDE.md`, the other pointer files you generated, and `.contextify/stamp.json`
plus `.contextify/evidence.json`. Committing the stamp is what makes the freshness check useful past
your own machine: one person runs `/contextify update` after a refactor, and every clone that pulls
the new commit quiets down at its next session start, instead of every teammate separately noticing
the same drift.

## 6. Open a new session, see nothing

Start a fresh Claude Code session in the repository. The plugin's `SessionStart` hook runs `ctx-check`
and, when nothing has moved since the stamp, prints nothing at all. A silent hook costs zero tokens.

## 7. Change something, start a session, see the notice

Remove a script from `package.json` that `AGENTS.md` quotes, or add one, and start a new session. The
hook now injects a short notice. This is an example rendering, eight lines here, twelve the hard max:

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

## 8. Update or accept

If the notice names a real change, run `/contextify update` to re-read the evidence and revise the
affected content. If `AGENTS.md` is still right and only the evidence moved, a claim's source line
shifted, a file it depended on was renamed, run `/contextify accept` instead: it re-digests the
evidence and the stamp and leaves every context file byte-identical.

## Next

- [Install in your editor](editors.md), the skill in Cursor, Codex, Gemini CLI and others
- [Hooks and CI](hooks.md), the opt-in snippets for agents the plugin does not hook automatically
- [Honest limits](limits.md), what a clean run does not prove. Read it before you trust a stamp
