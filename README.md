<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/hero-light.svg">
  <img alt="contextify: one repository, one source of instructions, multiple coding agents" src="assets/hero.svg" width="100%">
</picture>

[![Validate](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml/badge.svg)](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml)
[![MIT](https://img.shields.io/badge/license-MIT-E879DF)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Aboudjem/contextify?style=flat)](https://github.com/Aboudjem/contextify/stargazers)

English | [Français](READMEs/fr.md) | [Español](READMEs/es.md) | [日本語](READMEs/ja.md) | [简体中文](READMEs/zh-CN.md)

**Tell every coding agent how your repo works. Then prove it is still true.**

contextify is an Agent Skill that writes short repository instructions from files your agent reads. It records the evidence so a local script can report when those instructions need another look.

## What it does

- Writes one `AGENTS.md`, with thin pointers for your other agents. Targets 20, 40 or 60 lines by repository size; refuses files above 150 lines.
- Records commands and paths against repository evidence. Unsupported claims must be labelled `unverified` or omitted; a separate agent reviews the draft.
- Checks for drift without calling a model. Fresh checks are silent; updates show a diff and preserve human content outside the managed blocks.

## Install

In Claude Code:

```bash
claude plugin marketplace add Aboudjem/contextify
claude plugin install contextify@contextify-marketplace
```

For other agents, install the skill:

```bash
npx skills add Aboudjem/contextify
```

Then ask your agent to run contextify on the current repository. In Claude Code, use:

```text
/contextify init
```

Review the proposed diff, then commit the generated context files and `.contextify/` metadata. The scripts need Git, POSIX shell tools, Bash and Python 3; there are no Python package dependencies or MCP server. The installer uses Node.js through `npx`. [Editor-specific setup](docs/editors.md).

## What you get

Excerpt from a real run on an isolated copy of HazeLab, a Next.js app, on 2026-09-17. Codex drafted the instructions and Contextify wrote the files. [Full output and evidence](examples/nextjs/README.md).

```markdown
## Commands
- Development from the repository root: `pnpm run dev`.
- Build: `pnpm run build`; this generates the Prisma client before building Next.js.
- Lint: `pnpm run lint`.
## Testing
- No test script is declared in `package.json`; do not assume a package-manager test command exists.
- `vitest.config.ts` selects jsdom and discovers TypeScript tests under the tests directory.
```

Removing the quoted `lint` script in that copy produced this notice:

```text
contextify: drift
Scope    .
Stale    AGENTS.md:7 references pnpm run lint
Changed  package.json#scripts
Changed  provenance:package.json:10
Removed  script lint
Files    0 written
Next     /contextify update
Accept   unavailable until the stale command is corrected
```

The source repository was not changed. See the [run record and validation limits](evals/dogfood.md).

## What it writes

Defaults below describe newly generated files. Human content already present still counts toward the budget.

| File | Reader | Lines |
| --- | --- | --- |
| `AGENTS.md` | Codex, Cursor and other agents supporting this convention | Target 20/40/60; maximum 150 |
| `CLAUDE.md` | Claude Code, through `@AGENTS.md` | 4 by default |
| `GEMINI.md` | Gemini CLI, through `@AGENTS.md` | 3 |
| `.cursor/rules/contextify.mdc` | Cursor; optional because it also reads `AGENTS.md` | 9 |
| `.github/copilot-instructions.md` | GitHub Copilot | 4 |
| `.contextify/evidence.json` | Contextify's evidence records | Depends on repository |
| `.contextify/stamp.json` | Contextify's freshness check | Depends on repository |

Only selected targets get pointer files. See [loading rules and caveats](docs/editors.md).

## How it works

![Evidence, draft, review, write, check](assets/how-it-works.svg)

| Mode | What happens |
| --- | --- |
| `init` | Read the repository, draft instructions, review evidence, show a diff, then write and check. |
| `update` | Re-read evidence and revise affected managed content. Human edits outside the block survive; edits inside it raise a conflict. |
| `check` | Compare evidence with the committed stamp and resolve quoted commands and paths. Nothing is written. |
| `accept` | Refresh metadata when the instructions are still right. Dead claims are refused; prose stays unchanged. |

`init --dry-run` shows the proposed files and their line/byte costs. `--yes` skips routine questions, never a managed-block conflict or a hard ceiling.

The Claude Code plugin includes a session-start hook. [Codex, Gemini, Cursor, Git and CI hooks](docs/hooks.md) are opt-in. The check itself uses no model tokens; a drift notice occupies context when an agent reads it. CI warns by default; use `--ci --strict` to fail on drift.

## Compared with

This is a narrow comparison of sources inspected on **2026-09-16**, not a claim about every current release. The [full matrix and source paths](docs/comparison.md) document the scope and trade-offs.

| Tool | What to compare |
| --- | --- |
| contextify | Evidence records, one instruction source, enforced line ceiling, deterministic drift checks and managed-block updates. |
| ruler / rulesync | Broader configuration distribution across agents; rulesync also imports existing configurations. |
| ClaudeForge | Claude-focused organization and examples for different project sizes. |
| agents-md-generator | Small seed template with `CLAUDE.md` symlinked to `AGENTS.md`. |

## Good to know

A resolved command is one whose declaration or target exists. Contextify does **not** run it to prove it works. Repository evidence can be stale, and the deterministic resolver does not understand every shell expression or build system. Read the [limits](docs/limits.md).

An [ETH Zurich study](https://arxiv.org/abs/2602.11988) found no general task-success improvement from repository context files and an average inference-cost increase above 20%. Contextify has no measured task-success advantage. Keep only instructions that prevent a concrete mistake.

The hook never rewrites files. Generation and revision use your coding agent; the freshness check runs locally without a model or network request. The [dogfood report](evals/dogfood.md) separates script evidence from host-agent behavior, including any Claude validation left untested.

## Learn more

[Quickstart](docs/quickstart.md) · [Worked examples](examples/README.md) · [Hooks and CI](docs/hooks.md) · [FAQ](docs/faq.md) · [Evaluation](evals/README.md) · [Design decisions](docs/design/DECISIONS.md)

[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md) · [MIT license](LICENSE) · [10x plugin hub](https://github.com/Aboudjem/10x)

Local verification on **2026-09-17**: all six commands below exited 0. These are local results; they do not establish that published CI has passed. The [evaluation guide](evals/README.md) explains their scope.

```bash
python3 tests/test_ctx_check.py
python3 tests/test_verify_claims.py
python3 tests/test_hooks.py
python3 tests/test_regressions.py
python3 tests/test_manifests.py
python3 evals/check_skill.py skills/contextify/SKILL.md
```

| Check | Passed |
| --- | ---: |
| Drift and writer fixtures | 119/119 |
| Claim resolver fixtures | 30/30 |
| Hook fixtures | 6/6 |
| Regression tests | 23/23 |
| Manifest checks | 135/135 |
| Skill contract | 110/110 |
