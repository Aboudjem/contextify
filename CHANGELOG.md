# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

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
- **`ctx-check`**, a two-tier, zero-token drift check: a POSIX `sh` fast path over `git ls-files -s`,
  falling through to a python3 normalizer only on a mismatch, with a locked exit contract (`0` and
  empty stdout for fresh, `0` with a bounded notice for drift, `3` for no stamp, `1` for a broken
  check, never `2`, never a model call, never a write).
- **A `SessionStart` hook in the plugin** (`hooks/hooks.json`), matcher `startup|resume|clear`,
  timeout 5 seconds, so a fresh repository costs zero tokens at every session start.
- **Opt-in snippets for Codex, Gemini, Cursor, git and a GitHub Action**, each calling the same
  `ctx-check` with a different output envelope, none shipped by the plugin itself.
- **`verify_claims.py`**, a lint over a context file's quoted commands and paths, with `--budget`
  enforcing the line ceilings.
- **`install_hooks.sh`**, the one-command writer for all five opt-in snippets, idempotent, diff first,
  `--yes` to skip the prompts.
- **Ten reference files** under `skills/contextify/references/`, loaded only when the run reaches the
  area they cover, so the skill body stays short.
- **Tests and evals** covering the deterministic scripts and the skill's behavioral scenarios.

[0.1.0]: https://github.com/Aboudjem/contextify/releases/tag/v0.1.0
