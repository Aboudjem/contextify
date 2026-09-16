# RED baseline: the built-in /init commands on one fixture

Date: 2026-09-16

## Fixture

Source repo considered first: `/Users/adamboudj/projects/recap-studio`. Rejected per the stated fallback rule: its root `package.json` has no `next` dependency and the project describes itself as "Claude Code plugin + CLI + MCP server" (a monorepo whose only Next.js app lives nested at `apps/recap-web`), so the root is not itself a Next.js app.

Source repo used: `/Users/adamboudj/projects/hazelab`, a genuine Next.js app (root `package.json` depends on `next` 16.1.6, has `next.config.ts` at the root).

Fixture build: `rsync -a` from `/Users/adamboudj/projects/hazelab/` into the scratchpad, excluding `node_modules`, `.git`, `.next`, `.omc`, `.claude`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, then `git init -b main && git add -A && git commit -m "fixture"`.

- `git ls-files | wc -l` on the fixture after that commit: **77**
- For reference, `git ls-files | wc -l` on the source repo's own last commit: 67. The 10 extra fixture files are components that existed in the source repo's working tree but were not yet committed there (`src/components/effects/page-transition.tsx`, `src/components/effects/smoke-background.tsx`, `src/components/flavor/flavor-radar.tsx`, `src/components/hookah/bowl-segment.tsx`, `src/components/hookah/hookah-bowl.tsx`, `src/components/hookah/smoke-wisps.tsx`, `src/components/layout/animated-grid.tsx`, `src/components/mix/flavor-picker.tsx`, `src/components/mix/ingredient-row.tsx`, `src/components/mix/mix-builder.tsx`); the fixture procedure commits the working tree as-is, so they were swept into the single "fixture" commit.
- `package.json` `scripts` keys: `dev`, `build`, `postinstall`, `start`, `lint`. There is no `test` or `typecheck` script.

Three identical copies were made after the fixture commit: `claude/`, `codex/`, `gemini/`.

## Commands run

All three launched in parallel (backgrounded with `&`, then `wait`), each under a 600 s `timeout`.

1. Claude Code:
   `cd $SCR/claude && timeout 600 claude -p "/init" --permission-mode acceptEdits > $SCR/claude.log 2>&1`
   Exit code: 0. Wall time: 224 s. The flag was accepted as-is; no fallback needed. Result file `CLAUDE.md` was written.

2. Codex:
   `codex exec --help` was checked first, as instructed, because `--full-auto` does not exist as a flag in this install (`codex-cli 0.154.0`). The available non-interactive auto-approve equivalent is a sandbox policy flag, so the command run was:
   `cd $SCR/codex && timeout 600 codex exec -s workspace-write --skip-git-repo-check "Run /init: Generate a file named AGENTS.md that serves as a contributor guide for this repository." > $SCR/codex.log 2>&1`
   Exit code: 0. Wall time: 113 s. Result file `AGENTS.md` was written.

3. Gemini CLI:
   `cd $SCR/gemini && timeout 600 gemini -p "/init" --yolo > $SCR/gemini.log 2>&1`
   Exit code: 55. Wall time: 3 s. FAILED. No `GEMINI.md` was written.

## Results table

| tool | file | lines | bytes | approx tokens | code blocks | commands quoted | dead commands | missing paths | generic lines |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude | CLAUDE.md | 72 | 6772 | ~1693 (bytes/4, approximate) | 1 | 14 | 0 | 0 | 1 |
| codex | AGENTS.md | 46 | 3900 | ~975 (bytes/4, approximate) | 0 | 6 | 0 | 0 | 1 |
| gemini | failed | failed | failed | failed | failed | failed | failed | failed | failed |

Notes on the counts:
- "commands quoted" counts backticked tokens matching `npm run X` / `pnpm run X` / `pnpm X` / `yarn X` / `npx X` / `make X` anywhere in the file (`grep -oE`).
- "dead commands" checks the subset of those tokens that are actual script-name invocations (`npm run X`, `pnpm run X` / bare `pnpm X` used as a script name, `yarn X`) against the fixture's five `package.json` scripts. Both files also quote direct binary invocations through the package manager (`pnpm tsc`, `pnpm vitest`, `pnpm prisma`, `pnpm dlx`, `pnpm exec`) which are not script names and were not counted against the scripts list; both files correctly describe these as not being package.json scripts.
- "missing paths" checks every backticked relative path against the actual fixture tree with `test -e`. Every path quoted in both files exists.

## Claude (CLAUDE.md)

First 15 lines, verbatim:

```
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

HazeLab: a bilingual (French default, English) web app to discover, build, and share hookah flavor mixes. Next.js 16 App Router, React 19 with the React Compiler enabled, TypeScript strict, Tailwind CSS v4, shadcn/ui, next-intl, Prisma 7 on Supabase Postgres, Supabase Auth via `@supabase/ssr`. Package manager is pnpm.

## Commands

```bash
pnpm install                 # also runs `prisma generate` (postinstall)
pnpm dev                     # http://localhost:3000 → redirects to /fr
pnpm build                   # prisma generate && next build
pnpm lint                    # eslint (flat config, eslint-config-next)
```

Dead-command list: none found. All 14 quoted package-manager commands resolve, either to one of the five real `package.json` scripts (`dev`, `build`, `lint` are quoted; `postinstall` and `start` are not quoted) or to a real binary reachable through pnpm (`tsc`, `vitest`, `prisma`, `dlx shadcn@latest`).

Generic line (no repo-specific fact), verbatim: "This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository."

What an agent reading it would get wrong: nothing factual was found wrong in this run (every quoted command and path checks out against the fixture), so the real risk is that the file carries no timestamp, commit hash, or generated-by marker, so an agent has no way to tell whether it has already gone stale the next time `package.json` or `prisma/schema.prisma` changes.

## Codex (AGENTS.md)

First 15 lines, verbatim:

```
# Repository Guidelines

HazeLab is a bilingual hookah flavor and mix application. The current stack is Next.js 16.1.6 (App Router), React 19.2.3, strict TypeScript, Tailwind CSS 4, Prisma 7, and Supabase authentication. Treat `package.json` and executable configuration as authoritative: `docs/architecture.md` contains older Next.js 15 guidance and planned dependencies that are not installed.

## Project Structure

- `src/app/`: layouts, global styles, localized pages, and the authentication callback. Feature pages live under `src/app/[locale]/`.
- `src/components/`: feature components grouped by domain; shared UI primitives are in `src/components/ui/`.
- `src/actions/`: server actions, including authenticated voting.
- `src/lib/`: shared utilities, Prisma singleton, and separate Supabase browser/server/middleware clients.
- `src/i18n/` and `messages/`: locale routing and French/English translations. French is the default locale.
- `prisma/`: database schema and seed data. `tests/unit/` contains Vitest tests.
- `docs/`: architectural background, design research, and implementation plans; check proposals against current code.

## Setup and Commands
```

Dead-command list: none found. All 6 quoted package-manager commands resolve, either to one of the five real `package.json` scripts (`dev`, `build`, `start`, `lint` are quoted) or to `pnpm install` / `pnpm exec` (real pnpm subcommands, not script names).

Generic line (no repo-specific fact), verbatim: "For application changes, run lint, relevant tests, and the build; report any environment blockers explicitly. Check affected UI in both locales. PRs should explain the behavior change, validation performed, and include screenshots for visual changes. Use concise, imperative commit subjects; the available history does not establish a commit-prefix convention. Commit using the user's configured Git identity without per-command overrides."

What an agent reading it would get wrong: the file gives only "run the tests once" (`pnpm exec vitest run`) and never shows how to run a single test file or a single test by name, so an agent asked to fix one failing test has to guess the invocation, unlike CLAUDE.md which spells out the single-file and `-t` forms.

## Gemini (GEMINI.md)

FAILED. Exit code 55. No file was produced. Last 5 lines of `gemini.log`:

```
}
YOLO mode is enabled. All tool calls will be automatically approved.
Approval mode overridden to "default" because the current folder is not trusted.
Gemini CLI is not running in a trusted directory. To proceed, either use `--skip-trust`, set the `GEMINI_CLI_TRUST_WORKSPACE=true` environment variable, or trust this directory in interactive mode. For more details, see https://geminicli.com/docs/cli/trusted-folders/#headless-and-automated-environments
exit=55 wall=3s
```

A separate 60 s retry with `--skip-trust` added was run to check whether the trust flag alone would fix it. It did not: the process hit an account-eligibility error before reaching the trust check at all ("`IneligibleTierError: This client is no longer supported for Gemini Code Assist for individuals. To continue using Gemini, please migrate to the Antigravity suite of products.`"). This is an auth/account-tier failure in this environment, not a fixable flag or prompt issue.

What an agent reading it would get wrong: nothing, because there is nothing to read. An agent depending on `gemini -p "/init" --yolo` in a fresh headless environment gets a stack trace and no context file at all.

## What contextify must beat

- Line budget: beat 72 lines (Claude's `CLAUDE.md`) for the largest generated root file on a repo this size.
- Token cost: beat approximately 1693 approximate tokens (bytes/4) for the largest generated root file.
- Dead commands: hold at 0. Both Claude and Codex already reached 0 dead commands on this fixture, so contextify has no room to regress here.
- Missing paths: hold at 0, same reasoning.
- Generic, non-repo-specific lines: beat 1 (both Claude and Codex had exactly 1). Zero is the target.
- Reliability: beat Gemini's exit 55. A tool that cannot complete a headless run at all in a clean environment produces nothing at all; contextify's own generation and its `ctx-check` must never fail this way.
- Freshness: none of the three files carries a timestamp, commit hash, generated-by line, or any drift-detection mechanism. All three (including the two that succeeded) are silently unverifiable the moment the repo changes. This is the gap none of the built-in `/init` commands cover at all.
- Multi-agent pointer files: none of the three tools write anything for any agent other than themselves. A repo run through all three ends up with three separate, uncoordinated files and no single source of truth.
