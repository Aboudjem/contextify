# Hooks and CI

Contextify defaults to checks at **commit and push**, after you install and activate its Git hooks. The plugin registers no session-start events. All checks use the same local evidence and claim checker; none invoke a model or regenerate context.

## Install the Git hooks

From a Contextify checkout, pass the target repository explicitly:

```bash
bash skills/contextify/scripts/install_hooks.sh /path/to/repo
bash skills/contextify/scripts/install_hooks.sh --yes --activate /path/to/repo
```

The first command is a read-only proposal. The second writes `.githooks/pre-commit` and `.githooks/pre-push` and requests repository-local activation through `core.hooksPath`. The installer shows a diff before applying changes. Existing differing hook files are refused rather than overwritten; repeating the same installation changes nothing.

`--yes` without `--activate` only writes files. They are inactive unless Git already uses `.githooks`. `--activate` without `--yes` remains a proposal, including its configuration change.

Activation refuses a custom/global hooks path, existing executable default hooks that it would hide, and linked worktrees whose configuration could affect sibling checkouts. It never edits global Git configuration or global hooks. In these cases, integrate the checker through your existing hook manager instead of replacing its configuration. Git documents hook lookup and working directories in [githooks](https://git-scm.com/docs/githooks) and [`core.hooksPath`](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corehooksPath).

## What an installed Git hook does

- Fresh context: no output, exit 0.
- Drift, no stamp or a checker/setup failure: an actionable notice; advisory mode still exits 0.
- Strict mode: drift, no stamp and failures return nonzero and block the operation.

For enforcing hooks, add `--strict` to the installer before applying the proposal. For example, use `install_hooks.sh --strict --yes --activate /path/to/repo`. This flag requires the `git` target; it does not make the optional GitHub workflow strict. Existing differing wrappers still need a manual merge.

The wrapper calls `ctx-check --git`, adding `--strict` for enforcement. The raw checker returns nonzero on internal errors; the installed advisory wrapper converts those failures to a warning and exit 0. When integrating through another hook manager, preserve that policy deliberately. It reads the current working tree, **not** the staged snapshot or the exact refs being pushed. It does not read pre-push ref data from stdin, modify the index, write a CI summary or update any context file.

Git can bypass hooks, and a local check is not a server-side enforcement policy. A quoted command resolving also does not mean its tests ran successfully.

## Keep session checks only if you want them

Session-start adapters remain explicit installer targets. For example:

```bash
bash skills/contextify/scripts/install_hooks.sh --targets codex,gemini,cursor --yes /path/to/repo
```

These write project settings for the selected hosts, preserving unrelated settings and hook entries. They do not install Git hooks unless `git` is included in `--targets`.

| Target | Configuration | Event and output |
| --- | --- | --- |
| `claude` | `.claude/settings.json` | `SessionStart`, Claude additional context |
| `codex` | `.codex/hooks.json` | `SessionStart`, additional context |
| `gemini` | `.gemini/settings.json` | `SessionStart`, additional context; timeout in milliseconds |
| `cursor` | `.cursor/hooks.json` | `sessionStart`, `additional_context`; version 1 |

Cursor's entry targets the IDE; its standard cloud-agent hook table does not include `sessionStart`. See the [Cursor hook reference](https://cursor.com/docs/hooks). A missing stamp or check error can have a different display in each host; these adapters do not use the advisory Git wrapper.

## Migrate from 0.1

Updating the plugin removes its packaged session hook, but previously installed project settings remain yours. To keep checks only at commit/push, remove only the Contextify `SessionStart` or `sessionStart` entry from the affected host settings. Preserve unrelated entries and settings. Install the Git hooks through the safe activation path above. Existing 0.1 Git hook files may require a manual merge before the installer can apply the new wrapper.

## Optional GitHub checks

```bash
bash skills/contextify/scripts/install_hooks.sh --targets github --yes /path/to/repo
```

The generated workflow runs on pushes and pull requests, fetches a pinned Contextify release into the runner's temporary directory and uses `ctx-check --ci`. It does not embed a machine-specific installation path. Inspect the generated release pin before committing it.

CI prints a summary and appends to `GITHUB_STEP_SUMMARY` when available. It warns on drift by default; `--ci --strict` fails on drift or a missing stamp. Internal checker errors fail the job in either mode. Git mode deliberately has different advisory error handling.

[Quickstart](quickstart.md) · [Supporting documents](supporting-docs.md) · [Limits](limits.md)
