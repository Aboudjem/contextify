# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.3] - 2026-11-17

### Changed

- The one-line description is now true to what the check does. It said "prove it is still true". The check resolves the commands, targets and files a line names. It does not read prose and does not run commands. The new line is: "Know when your agent instructions point at something gone. One AGENTS.md for all your agents and a local check that costs no tokens." It ships in `plugin.json`, the Cursor, Copilot and marketplace manifests, `SKILL.md`, `llms.txt` and the FAQ.
- The README first screen is shorter. It shows the install, the drift sample, the problem it solves and a `Why use it` block, with the limit next to the promise. The hand-run command and the `.gitignore` note moved under How it works. The four translations match.
- The hero images and the social preview show the current drift notice wording instead of the old "8 lines" card.
- The generated CI workflow clones tag `v0.3.3`.

No behaviour change in the scripts.

## [0.3.2] - 2026-11-17

### Fixed

- Installing the skill with `npx skills add` no longer reads as drift. The check skips contextify's own copy under any agent folder (`.agents/skills/contextify`, `.claude/skills/contextify`, ...) and `skills-lock.json`. Other skills still count.
- `ctx-check --json` now returns the same command as the text notice in `next`: `/contextify:contextify update` on drift, `/contextify:contextify init` with no stamp.
- The README exit table now covers every mode, measured in bash. With no stamp, `--ci` and `--git` exit 0, not 3. DECISIONS D9 says the same.
- The CI paragraph now says strict CI also fails on a missing stamp and on an unverified claim.
- The four translated READMEs are full translations of the current English README. A test fails when their code blocks or heading levels differ from English.

### Changed

- The generated CI workflow clones tag `v0.3.2`.
- A stamp written by 0.3.1 or older with the skill already installed shows one `Changed tree#depth2` after the upgrade. Run `accept` once.

## [0.3.1] - 2026-11-17

### Fixed

- The README exit table was wrong. `--strict` alone keeps exit 0 on drift. Only `--ci --strict` and `--git --strict` exit 1, and the docs now say so.
- The drift notice now gives `/contextify:contextify update`, the command Claude Code accepts. A new `Agents` line says what to type in other agents.
- Every notice label pads to 11 columns, so `Unverified` no longer breaks the alignment.
- Writer and accept summaries name `/contextify:contextify check` for the same reason. The no-stamp line names both forms.

### Added

- `install_hooks.sh --strict --targets github` writes a CI workflow whose step runs `ctx-check --ci --strict`, so drift fails the job.
- The hooks installer refusal for an existing `core.hooksPath` now prints the exact line to add to your own hooks.
- The README shows how to run the drift check by hand for the plugin and the skills CLI installs.
- The 0.3.0 example ships its stamp, evidence and draft, plus `replay.sh`, which replays the README sample.
- A test fails if any doc shows `--strict` without `--ci` or `--git`.
- The generated CI workflow clones tag `v0.3.1`.

## [0.3.0] - 2026-11-17

### Changed

- The drift notice now opens with the verdict and three numbered actions, then the detail. A reader who stops after four lines knows what to run. The first line is still `contextify: drift`, so existing hooks and greps keep working.
- With a dead claim, the first action names the file, the line and the dead command (cut to 60 characters).
- The closing `Next` line is gone; the actions replace it. The notice stays within 12 lines and 2,048 bytes.
- The generated CI workflow clones tag `v0.3.0`.

### Added

- `make test` runs every suite plus the self-dogfood check. CI runs the same target, and a pinned `skills@1.9.0` discovery check.
- A plugin icon at `.claude-plugin/icon.png`. `claude plugin validate . --strict` now exits 0.
- A current example: a real 0.3.0 run on the Python service fixture, with init and a caught drift.

### Fixed

- This repository's contributor pointer moved from a root `CLAUDE.md` to `.claude/CLAUDE.md`, which the strict plugin validator accepts.

## [0.2.0] - 2026-09-17

### Added

- Optional `docs/context/architecture.md` and `docs/context/workflows.md`, generated only when useful, with per-line evidence, managed updates and drift detection.
- A 120-line ceiling per supporting document, including preserved human content. AGENTS remains the short entry point, with links for on-demand reading.
- Git pre-commit and pre-push templates, an explicit activation option with existing-hook protection, and a read-only Git checker mode.

### Changed

- Git checkpoints are the default hook setup. The package no longer registers an automatic SessionStart hook; host session hooks remain explicitly opt-in.
- Git checks warn by default and can block on drift with `--strict`. Checks inspect the working tree, not a staged or pushed snapshot.

## [0.1.0] - 2026-09-16

First release. Tell every coding agent how your repo works. Then prove it is still true.

### Added

- **The skill** (`skills/contextify/SKILL.md`): `/contextify init`, `update`, `check` and `accept`,
  reading a repository and writing its context files.
- **AGENTS.md as the single source**, with four pointer files generated from it: `CLAUDE.md`,
  `GEMINI.md`, the optional `.cursor/rules/contextify.mdc`, and `.github/copilot-instructions.md`.
- **Size-scaled line budgets**: 20 lines for a tiny repository, 40 for medium, 60 for a monorepo, with
  a hard ceiling of 150, enforced at generation and again by the opt-in CI gate.
- **`.contextify/evidence.json` and `.contextify/stamp.json`**, so every generated claim traces to a
  file and a line, and a second run can diff against the first instead of starting over.
- **`ctx-check`**, a zero-token drift check: a POSIX `sh` entry point runs the complete Python
  evidence and claim checker on every invocation, with a locked exit contract (`0` and
  empty stdout for fresh, `0` with a bounded notice for drift, `3` for no stamp, `1` for a broken
  check, never `2`, never a model call, never a write).
- **A `SessionStart` hook in the plugin** (`hooks/hooks.json`), matcher `startup|resume|clear`,
  timeout 5 seconds, so a fresh repository costs zero tokens at every session start.
- **Opt-in snippets for Codex, Gemini, Cursor, git and a GitHub Action**, each calling the same
  `ctx-check` with a different output envelope, none shipped by the plugin itself.
- **`verify_claims.py`**, a lint over a context file's quoted commands and paths, with `--budget`
  enforcing the line ceilings.
- **`install_hooks.sh`**, the one-command writer for all five opt-in snippets, idempotent, diff first,
  `--yes` to apply the displayed proposal.
- **Ten reference files** under `skills/contextify/references/`, loaded only when the run reaches the
  area they cover, so the skill body stays short.
- **Tests and evals** covering the deterministic scripts and the skill's behavioral scenarios.

[0.1.0]: https://github.com/Aboudjem/contextify/releases/tag/v0.1.0

[0.3.3]: https://github.com/Aboudjem/contextify/releases/tag/v0.3.3
[0.3.2]: https://github.com/Aboudjem/contextify/releases/tag/v0.3.2
[0.3.1]: https://github.com/Aboudjem/contextify/releases/tag/v0.3.1
[0.3.0]: https://github.com/Aboudjem/contextify/releases/tag/v0.3.0
[0.2.0]: https://github.com/Aboudjem/contextify/releases/tag/v0.2.0
