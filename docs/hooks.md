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
            "command": "sh /path/to/contextify/skills/contextify/scripts/ctx-check --hook codex",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Fires on `SessionStart` (source `startup`, `resume`, `clear` or `compact`); the notice is wrapped in
`hookSpecificOutput.additionalContext`; the timeout is 5 seconds; exit 3 (no stamp yet) and exit 1
(the check itself broke) both mean no notice shows, never a blocked session.

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
here, not seconds; a missing stamp or a broken check again means silence, not a block.

Gemini CLI can also read `AGENTS.md` directly, instead of the `GEMINI.md` pointer, through a settings
switch. contextify only ever displays this as a patch for you to apply, never applies it silently:

```json
{"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}}
```

## Cursor: .cursor/hooks.json

```json
{
  "hooks": {
    "sessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "sh /path/to/contextify/skills/contextify/scripts/ctx-check --hook cursor"
          }
        ]
      }
    ]
  }
}
```

The event name is lowercase `sessionStart` and the envelope key is snake_case `additional_context`,
both different from Claude Code and Gemini; Cursor documents this hook as fire-and-forget with no
stated timeout, so a stall here simply shows nothing rather than stalling the composer.

## git: .githooks/pre-commit

```sh
#!/bin/sh
sh /path/to/contextify/skills/contextify/scripts/ctx-check --ci
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
on:
  pull_request:
  push:
    branches: [main]
jobs:
  ctx-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Clone contextify
        run: git clone --depth 1 https://github.com/Aboudjem/contextify /tmp/contextify
      - name: Run ctx-check
        run: sh /tmp/contextify/skills/contextify/scripts/ctx-check --ci
```

Runs on `pull_request` and on push to `main`; output is plain stdout, also appended to
`$GITHUB_STEP_SUMMARY`; there is no hook timeout, only the job's own. Add `--strict` to the last step
to make the job itself fail on drift or a missing stamp; that flag is the opt-in, not the default.

## One command for all of it

```bash
sh skills/contextify/scripts/install_hooks.sh --targets codex,gemini,cursor,git,github --yes
```

Renders every snippet above, shows a diff against anything already there, and merges idempotently: a
second run changes nothing. Drop `--yes` to be asked first.

## What is guaranteed, what is not

The check itself is hook-enforced: given a stamp and a repository state, `ctx-check` always reports
the same fresh-or-drift answer, deterministically, with no model call. Whether anything happens after
that notice appears is prose: the model reads the injected text and decides whether to act on it, the
same way it decides whether to follow any other instruction in context.
