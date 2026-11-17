<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/hero-light.svg">
  <img alt="contextify: one repository, one source of instructions, multiple coding agents" src="assets/hero.svg" width="100%">
</picture>

[![Validate](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml/badge.svg)](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml)
[![MIT](https://img.shields.io/badge/license-MIT-E879DF)](LICENSE)

English | [Français](READMEs/fr.md) | [Español](READMEs/es.md) | [日本語](READMEs/ja.md) | [简体中文](READMEs/zh-CN.md)

**Tell every coding agent how your repo works. Then prove it is still true.**

contextify writes one short `AGENTS.md` from files your agent reads. A local script then tells you when it goes stale.

## Install

In Claude Code, from your terminal:

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install contextify@10x
```

Then, inside your repository, ask for a first draft:

```text
/contextify:contextify init
```

For Codex, Cursor, Gemini CLI and other agents, install the skill:

```bash
npx skills add Aboudjem/contextify
```

In those agents there is no `/contextify:` prefix. Ask in words: "contextify init", "contextify update".

Needs Git, Bash and Python 3.11 or newer. No Python packages, no MCP server, no network call from the scripts.

### Run the drift check by hand

It prints nothing when the repo is fresh. Run it from the root of your repository.

Installed as a plugin:

```bash
sh "$(ls -d ~/.claude/plugins/cache/10x/contextify/*/ | sort -V | tail -1)skills/contextify/scripts/ctx-check"
```

Installed with `npx skills add` (Codex, Cursor and most others use `.agents/skills`):

```bash
sh .agents/skills/contextify/scripts/ctx-check
```

For a Claude Code skills install, the folder is `.claude/skills/contextify` instead. Add `--ci --strict` to make drift exit 1.

### Sample report

On 2026-11-17, contextify 0.3.0 wrote `AGENTS.md` for a small Python service. Then the `test-health` target was deleted from its `Makefile`. 0.3.1 prints this for that repo, at no token cost:

```text
contextify: drift
1. Run /contextify:contextify update to fix AGENTS.md:6 (make test-health)
2. Review the diff it shows before it writes
3. Commit the context files with .contextify/
Agents     outside Claude Code, ask for "contextify update"
Scope      .
Stale      AGENTS.md:6 references make test-health
Unverified AGENTS.md:6 python3 -m unittest tests.test_health
Changed    makefile#targets
More       +3 findings
Files      0 written
Accept     unavailable until the stale command is corrected
```

A fresh repo prints nothing. The run's files and stamp ship with the example, so you can replay it:

```bash
sh examples/python-service-0.3.0/replay.sh
```

[Full run, files and the edit that caused it](examples/python-service-0.3.0/README.md).

## How it works

![Evidence, draft, review, write, check](assets/how-it-works.svg)

| Mode     | What happens                                                                               |
| -------- | ------------------------------------------------------------------------------------------ |
| `init`   | Read the repo, draft instructions, review the evidence, show a diff, then write and check. |
| `update` | Re-read the evidence and revise the managed block. Your edits outside the block survive.   |
| `check`  | Compare the evidence with the committed stamp. Nothing is written.                         |
| `accept` | Refresh the stamp when the instructions are still right. Dead claims are refused.          |

What it writes:

| File                                         | Reader                                                   | Lines                            |
| -------------------------------------------- | -------------------------------------------------------- | -------------------------------- |
| `AGENTS.md`                                  | Codex, Cursor and other agents that read this convention | Target 20, 40 or 60; maximum 150 |
| `CLAUDE.md`                                  | Claude Code, through `@AGENTS.md`                        | 4 by default                     |
| `GEMINI.md`                                  | Gemini CLI, through `@AGENTS.md`                         | 3                                |
| `.cursor/rules/contextify.mdc`               | Cursor; optional, since Cursor also reads `AGENTS.md`    | 9                                |
| `.github/copilot-instructions.md`            | GitHub Copilot                                           | 4                                |
| `docs/context/architecture.md`               | Optional map of components and data flow                 | Maximum 120                      |
| `docs/context/workflows.md`                  | Optional build, test and release steps                   | Maximum 120                      |
| `.contextify/evidence.json` and `stamp.json` | The drift check                                          | Depends on the repo              |

Only the targets you pick get a pointer file. Every factual line maps to a source file and line. A separate agent reviews the draft before contextify writes anything.

The drift check exits 0 with no output when the repo is fresh. On drift it prints the notice above and still exits 0. It never rewrites a file.

| Exit         | Meaning                                                           |
| ------------ | ----------------------------------------------------------------- |
| 0, no output | Fresh                                                             |
| 0, a notice  | Drift found; at most 12 lines and 2,048 bytes                     |
| 1            | The check itself broke                                            |
| 1            | Drift or no stamp, under `--ci --strict` or `--git --strict` only |
| 3            | No stamp yet: run `init` first                                    |

`--strict` alone does not change the exit code. It only reports unverified claims as drift. In CI, use `ctx-check --ci --strict` so drift fails the job.

Git checks are opt-in. At the end of `init` the skill offers to install `pre-commit` and `pre-push` checks. From a clone of this repo you can also run:

```bash
bash skills/contextify/scripts/install_hooks.sh --yes --activate /path/to/repo
```

They warn by default and refuse to replace existing hooks. Add `--strict` to block a commit or push on drift.

Activation refuses when a global `core.hooksPath` is set, since it would hide your other hooks. Call `ctx-check --git` from the hook manager you already use instead.

For a CI job that fails on drift, generate the workflow in strict mode. Its step runs `ctx-check --ci --strict`:

```bash
bash skills/contextify/scripts/install_hooks.sh --strict --targets github --yes /path/to/repo
```

[Hooks and CI](docs/hooks.md).

## Proof

One command runs every suite, the skill contract and this repo's own drift check:

```bash
make test
```

It printed this on 2026-11-17 (one summary line per suite, in run order):

```text
tests/test_ctx_check.py        128/128 checks passed
tests/test_verify_claims.py     30/30 checks passed
tests/test_hooks.py             Ran 22 tests, OK
tests/test_regressions.py       Ran 23 tests, OK
tests/test_supporting_docs.py   Ran 16 tests, OK
tests/test_manifests.py        131/131 checks passed
evals/check_skill.py           114/114 checks passed
make dogfood                   PASS: ctx-check is fresh and silent
                               29 claims, 0 stale, 0 unverified
```

CI runs the same `make test` on every push and pull request. This repo's own `AGENTS.md` was written by contextify, so the last step fails if it ever goes stale.

## Works with

| Agent       | Install path                           | Tested                                                                                                    |
| ----------- | -------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Claude Code | `claude plugin install contextify@10x` | 2026-11-17: plugin install, then a full `init` run ([run record](examples/python-service-0.3.0/README.md)) |
| Codex       | `npx skills add Aboudjem/contextify`   | 2026-11-17: skill install, then Codex ran the drift check ([run log](examples/python-service-0.3.0/codex-run-0.3.1.md)) |

Documented, not tested today: Gemini CLI and Cursor (both CLIs refused to sign in on the test machine), GitHub Copilot, OpenCode, Windsurf, Zed, Continue.dev and Kimi Code CLI. Their install codes are in [editor setup](docs/editors.md).

## FAQ

### Why is AGENTS.md the source and not CLAUDE.md?

Codex, Cursor and Copilot read `AGENTS.md` directly. Claude Code and Gemini CLI get a short file that imports it. So the same facts live in one place.

### Does the drift check call a model?

No. It is a shell and Python script. It reads Git and the files the stamp points at, then compares hashes. It spends zero tokens.

### Will it overwrite what I wrote by hand?

No. contextify owns only the block between its markers. Text outside the block survives every update. An edit inside the block raises a conflict instead of being lost.

### Does a verified command actually work?

Not proven. A verified command is one whose script, target or file exists. contextify does not run it. Your tests still decide whether it works.

### What does accept do?

It refreshes the stamp when the evidence moved but the instructions are still right. It refuses while a quoted command is dead, so a broken line cannot be waved through.

More answers in the [full FAQ](docs/faq.md).

## Limits

- A resolved command was found, not executed. Repository evidence can itself be wrong.
- The resolver does not understand every shell expression or build system. Lines it cannot check are labelled `unverified`.
- An [ETH Zurich study](https://arxiv.org/abs/2602.11988) found no general task-success gain from context files, and an inference cost rise above 20%. contextify has no measured task-success advantage. Keep only lines that prevent a concrete mistake.
- Writing a plugin repo? `claude plugin validate --strict` warns on a root `CLAUDE.md`. Point `.claude/CLAUDE.md` at `@../AGENTS.md` by hand, as this repo does. The writer does not target that path yet.
- Privacy: the scripts make no network call. Drafting uses your own coding agent and its usual connection.

All limits, with sources: [docs/limits.md](docs/limits.md).

## Learn more

[Quickstart](docs/quickstart.md) · [Worked examples](examples/README.md) · [Editor setup](docs/editors.md) · [Comparison](docs/comparison.md) · [Design decisions](docs/design/DECISIONS.md)

[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md) · [MIT license](LICENSE) · [10x plugin hub](https://github.com/Aboudjem/10x)
