# Hooks and CI

contextify's plugin ships exactly one hook: a Claude Code `SessionStart` entry. Everything below is an
opt-in snippet you install yourself, for the agents and workflows the plugin does not hook
automatically. Every snippet calls the same `ctx-check` script; only the output envelope differs.

## Codex: .codex/hooks.json

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "sh /path/to/contextify/skills/contextify/scripts/ctx-check --hook codex"
          }
        ]
      }
    ]
  }
}
```

Fires on `SessionStart` (source `startup`, `resume`, `clear` or `compact`); the notice is wrapped in
`hookSpecificOutput.additionalContext`; the installer does not configure a Codex timeout. Check exit codes are unchanged: 3 means no stamp and 1 means an internal error. Host handling of a nonzero hook exit is separate from freshness.

## Gemini: .gemini/settings.json

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
            "command": "sh /path/to/contextify/skills/contextify/scripts/ctx-check --hook gemini",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

Same `SessionStart` event and the same envelope shape as Codex; note the timeout is in milliseconds
here, not seconds; a missing stamp is exit 3 and an internal failure is exit 1. The host decides how to display hook errors.

Gemini CLI can also read `AGENTS.md` directly, instead of the `GEMINI.md` pointer, through a settings
switch. contextify only ever displays this as a patch for you to apply, never applies it silently:

```json
{"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}}
```

## Cursor IDE: .cursor/hooks.json

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      {"command": "sh /path/to/contextify/skills/contextify/scripts/ctx-check --hook cursor"}
    ]
  }
}
```

The event name is lowercase `sessionStart` and the envelope key is snake_case `additional_context`,
both different from Claude Code and Gemini. The configuration uses the required version 1 and a direct command entry. The standard cloud-agent hook table does not include `sessionStart`; this snippet targets the IDE. See the [Cursor hooks reference](https://cursor.com/docs/hooks).

## git: .githooks/pre-commit

```sh
#!/bin/sh
exec sh /path/to/contextify/skills/contextify/scripts/ctx-check --ci
```

```bash
git config core.hooksPath .githooks
```

This runs on `pre-commit`, so there is no JSON envelope, just plain text on stdout; there is no
per-hook timeout beyond however long the commit is willing to wait; without `--strict`, `--ci` always
exits 0, so this never blocks a commit on its own.

## GitHub Action: .github/workflows/contextify-check.yml

```yaml
name: contextify check
on: [push, pull_request]
permissions:
  contents: read
jobs:
  contextify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Fetch released contextify
        run: git clone --depth 1 --branch v0.1.0 https://github.com/Aboudjem/contextify "$RUNNER_TEMP/contextify"
      - name: Check repository context (advisory; add --strict to enforce)
        run: sh "$RUNNER_TEMP/contextify/skills/contextify/scripts/ctx-check" --ci
```

Runs on `pull_request` and `push`; output is plain stdout, also appended to
`$GITHUB_STEP_SUMMARY`; there is no hook timeout, only the job's own. Add `--strict` to the last step
to make the job itself fail on drift or a missing stamp; that flag is the opt-in, not the default.

## One command for all of it

```bash
bash skills/contextify/scripts/install_hooks.sh --targets codex,gemini,cursor,git,github --yes
```

Shows a diff before applying. JSON hook lists merge without removing other settings. Existing git hooks and workflows require a manual merge if they differ. A second identical run changes nothing. Drop `--yes` for a read-only proposal. The GitHub workflow fetches the release rather than using your local installation path.

## What is guaranteed, what is not

The check itself is hook-enforced: given a stamp and a repository state, `ctx-check` always reports
the same fresh-or-drift answer, deterministically, with no model call. Whether anything happens after
that notice appears is prose: the model reads the injected text and decides whether to act on it, the
same way it decides whether to follow any other instruction in context.
