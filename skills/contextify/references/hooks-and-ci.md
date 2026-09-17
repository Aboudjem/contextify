# Hooks and CI

Every opt-in snippet the plugin documents, copy-paste ready, with its firing event, output envelope, timeout, and what each exit code does.

## The Claude Code hook the plugin ships

`hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/skills/contextify/scripts/ctx-check --hook claude",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

This is the only hook the plugin ships. Codex, Gemini, Cursor, git `pre-commit` and the GitHub Action below are documented opt-in snippets the user installs separately, all served by the one detection code path in `ctx-check`; `--hook AGENT` only selects the output envelope. Source: `docs/design/DECISIONS.md` D19.

`${CLAUDE_PLUGIN_ROOT}` is the plugin's installation directory, exported for scripts bundled with a plugin. Source: https://code.claude.com/docs/en/hooks.

Why a single command string, not an `args` array: whether Claude Code accepts the `args` field the way the exploratory prototype snippet in `04-auto-update-mechanics.md` used it is `uncertain`, so D19 locks the command as one string rather than owning an unconfirmed field.

`cwd` stdin field versus `CLAUDE_PROJECT_DIR`: in a worktree, `${CLAUDE_PROJECT_DIR}` stays pinned to the original checkout while the `cwd` field in the hook's stdin JSON follows Claude into the worktree. A stamp path built from the environment variable would point at the wrong tree. `ctx-check` reads `cwd` from stdin first, then falls back to `$CLAUDE_PROJECT_DIR`, then `$PWD`. Source: `10x/.goal/research/ctx/04-auto-update-mechanics.md`, Claude Code section, citing https://code.claude.com/docs/en/hooks.

Matchers `startup|resume|clear`: `compact` and `fork` are deliberately excluded, because a compaction resume re-fires `SessionStart` and would re-inject the same notice the model already saw. Source: `04-auto-update-mechanics.md`, same section.

Only four events surface plain hook stdout to the model: `SessionStart`, `UserPromptSubmit`, `UserPromptExpansion`, `PostModelSwitch`. Every other event's stdout goes to the debug log only, which is why `SessionStart` is the injection point rather than, say, `PreToolUse`. Source: `10x/.goal/research/ctx/07-skeptic.md` claim 1 and 1b, quoting https://code.claude.com/docs/en/hooks.

## Opt-in: `.codex/hooks.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "<path-to-plugin>/skills/contextify/scripts/ctx-check --hook codex"
          }
        ]
      }
    ]
  }
}
```

- Fires on: `SessionStart`, sources `startup`, `resume`, `clear`, `compact` (no `fork`; Codex's vocabulary is Claude Code's minus one source).
- Envelope: `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<notice>"}}`, the same shape as Claude Code, kept as a separate code path in `ctx_check.py` so it can diverge later.
- Cap: `additionalContext` is capped around 2,500 tokens by default, tunable with `additionalContextLimit`; the exact truncation behaviour past the cap is `uncertain`.
- Timeout: not documented for `SessionStart` specifically; `uncertain`.
- Exit codes: never blocks. `ctx-check`'s own contract, fresh is 0 with empty stdout, drift is 0 with the notice, no stamp is 3, a broken check is 1, does not change under `--hook codex`; only the output wrapping changes.
- Config locations, in order: `~/.codex/hooks.json` or `[hooks]` in `~/.codex/config.toml`, then `<repo>/.codex/hooks.json` or a repo `[hooks]` block, then a plugin-bundled `hooks/hooks.json` (Codex plugins cannot currently ship hooks: `plugin_hooks` reports `removed` in `codex features list`), then enterprise `requirements.toml`.
- Source: https://learn.chatgpt.com/docs/hooks, via `10x/.goal/research/ctx/04-auto-update-mechanics.md` and `07-skeptic.md` claim 4d.

## Opt-in: `.gemini/settings.json`

Hooks block:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "name": "ctx-check",
            "command": "<path-to-plugin>/skills/contextify/scripts/ctx-check --hook gemini",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

- Fires on: `SessionStart`, sources `startup`, `resume`, `clear`.
- Envelope: `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<notice>"}}`. Gemini documents the field as added as the first turn in interactive mode, or prepended to the user prompt in non-interactive mode, which is why the same hook also works unattended in CI.
- Timeout: default 60,000 ms; the snippet above sets 5,000 ms to bound startup work independently of local check timings.
- Exit codes: same contract as Codex, never blocks; `--hook` only picks the envelope.
- Source: https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/reference.md, via `04-auto-update-mechanics.md` and `07-skeptic.md` claim 5d.

The `context.fileName` switch is a separate, one-time settings change, not a hook:

```json
{
  "context": {
    "fileName": ["AGENTS.md", "GEMINI.md"]
  }
}
```

`install_hooks.sh` offers this as a displayed patch, never applied silently. Taking it means Gemini reads `AGENTS.md` directly instead of importing it through `GEMINI.md`'s `@AGENTS.md` line; whether a given release deduplicates combined discovery and that import is `uncertain`. Source: `docs/design/DECISIONS.md` D6, `07-skeptic.md` claim 5 and correction 1.

## Opt-in: `.cursor/hooks.json`

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      {
        "command": "<path-to-plugin>/skills/contextify/scripts/ctx-check --hook cursor"
      }
    ]
  }
}
```

The [Cursor hooks reference](https://cursor.com/docs/hooks), checked 2026-09-17, requires a positive `version` (use 1) and direct command entries in the event list.

- Fires on: `sessionStart`, camelCase with a lowercase first letter, unlike Claude Code and Codex's `SessionStart`. Fires when a new composer conversation is created.
- Envelope: `{"additional_context": "<notice>"}`, snake_case, unlike Claude Code and Gemini's camelCase `additionalContext`.
- Timeout: not documented. `sessionStart` runs fire-and-forget, so it cannot block the session and a failing hook is invisible to the user.
- Exit codes: not meaningful in a blocking sense; a failing or slow hook is simply not waited on.
- Config locations: `.cursor/hooks.json` (project) or `~/.cursor/hooks.json` (user), resolved enterprise, then team, then project, then user.
- Source: https://cursor.com/docs/agent/hooks, via `07-skeptic.md` claim 6c and `04-auto-update-mechanics.md`.

## Opt-in: `.githooks/pre-commit`

```sh
#!/bin/sh
<path-to-plugin>/skills/contextify/scripts/ctx-check --ci
```

Installed with:

```sh
git config core.hooksPath .githooks
```

- Fires on: every `git commit`, before the commit object is created.
- Output: `--ci` prints the drift notice, or `contextify: fresh` when clean, to stdout. Adding `--strict` makes the same command exit 1 on drift or a missing stamp instead of 0, which is what actually blocks a commit; without `--strict` the hook is informational only.
- Timeout: none stated; measure the checker on the target repository; do not assume a fixed runtime.
- Bypass caveats: `--no-verify` skips the hook entirely; `git commit` from some GUI clients does not run `core.hooksPath` hooks; a `rebase` replays commits without re-running `pre-commit` for each one. A fresh clone does not get this hook unless `core.hooksPath` itself is committed and someone runs the `git config` line once.
- Source: `10x/.goal/research/ctx/04-auto-update-mechanics.md`, "Portable, agent-agnostic options" table.

## Opt-in: `.github/workflows/contextify-check.yml`

```yaml
name: contextify-check
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Fetch contextify
        run: git clone --depth 1 --branch v0.1.0 https://github.com/Aboudjem/contextify "$RUNNER_TEMP/contextify"
      - name: ctx-check --ci
        run: sh "$RUNNER_TEMP/contextify/skills/contextify/scripts/ctx-check" --ci
```

The default is advisory. Add `--strict` to fail the job on drift or a missing stamp. Internal checker errors remain errors in both modes.

- Fires on: whatever the workflow's `on:` block triggers, here every push and pull request.
- Output: `--ci` prints the notice, or `contextify: fresh`, to stdout, and also appends the same text to `$GITHUB_STEP_SUMMARY` when that variable is set, which GitHub Actions runners set automatically. No extra step is needed to populate the summary.
- Exit codes: 0 always without `--strict`; with `--strict`, 1 on drift or a missing stamp, which fails the job.
- Note: `Aboudjem/contextify` does not exist as a GitHub repository as of this research pass; `gh repo view Aboudjem/contextify` returns "Could not resolve to a Repository." This snippet names the intended future location, so the clone step will fail until the repository is published. Source: `10x/.goal/research/ctx/07-skeptic.md` claim 11.
- Source for the exit and summary behaviour: `docs/design/SCRIPTS-SPEC.md`, `ctx_check.py` section.

## Where `ctx-check` lives after install

Every snippet above writes the path as `<path-to-plugin>/skills/contextify/scripts/ctx-check`.

- Installed via the Claude Code plugin marketplace: the exact install directory is not confirmed by 01, 04 or 07, so `<path-to-plugin>` for a marketplace install is `uncertain`. `install_hooks.sh` resolves and writes the absolute path itself at install time rather than requiring the user to know it in advance. Source: `docs/design/SCRIPTS-SPEC.md`, `install_hooks.sh` section.
- Installed via `npx skills add`: the skill lands at `.claude/skills/contextify/` (project scope, the default) or `~/.claude/skills/contextify/` (global scope, `-g`), as a symlink to a canonical copy by default, or a full copy with `--copy`. For this install layout the runner is `<installed-skill>/scripts/ctx-check`, without another `skills/contextify` segment. Source: `07-skeptic.md` claim 8b, `10x/.goal/research/ctx/03-comparables-and-skills-cli.md` Part B.
