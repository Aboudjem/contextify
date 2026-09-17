# Hooks and CI

Default policy since 0.2.0: use Git checkpoints. The packaged `hooks/hooks.json` registers no session event. Installing the skill alone does not install or activate Git hooks.

## Git commit and push

Preview from the installed skill directory:

```bash
bash scripts/install_hooks.sh /path/to/repository
```

Apply and activate in a compatible repository:

```bash
bash scripts/install_hooks.sh --yes --activate /path/to/repository
```

The default target `git` creates `.githooks/pre-commit` and `.githooks/pre-push`. `--yes` alone writes the files without changing Git configuration. `--activate` configures the repository, never global Git settings, and refuses if activation would mask existing hooks. Existing custom/global `core.hooksPath`, executable default hooks and linked worktrees need explicit integration; do not solve this by silently overriding them.

The installer resolves the checker path from its own installation. Keep that installation available; moving or deleting it requires reinstalling the hook templates. A new clone needs its own installation and activation. Existing differing hook files require a manual merge.

Git mode is `ctx-check --git`: no stdin reads, no files or GitHub summary writes, no model, no stamp changes, and silence when fresh. Default wrappers warn without blocking on drift, missing metadata or checker failure. Add installer `--strict` for hooks that block these states. Invalid installation options and activation conflicts refuse before any target write.

These checks inspect the working tree. They do not reconstruct the staged index at commit time or validate every ref supplied to pre-push. Git documents [pre-commit and pre-push](https://git-scm.com/docs/githooks) and [core.hooksPath](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corehooksPath). Local hooks can be bypassed; use CI for a server-side gate.

## Explicit session adapters

Only choose these when the user requests checks at session start:

```bash
bash scripts/install_hooks.sh --targets claude,codex,gemini,cursor --yes /path/to/repository
```

| Target | File | Event | Checker mode |
| --- | --- | --- | --- |
| claude | `.claude/settings.json` | `SessionStart` | `--hook claude` |
| codex | `.codex/hooks.json` | `SessionStart` | `--hook codex` |
| gemini | `.gemini/settings.json` | `SessionStart` | `--hook gemini` |
| cursor | `.cursor/hooks.json` | `sessionStart` | `--hook cursor` |

The adapters merge supported JSON lists without erasing unrelated settings. Cursor IDE uses version1 and direct command entries; this is not a promise about Cursor cloud-agent events. Host adapters retain their documented envelopes and host-specific behavior. Their checker exit3 means no stamp, exit1 a checker failure; an optional host's handling of errors is not a guarantee that its session cannot block.

For hook modes, input `cwd` takes precedence over the host project-directory fallback. Git mode does not parse host JSON. Gemini's optional `context.fileName` configuration is displayed separately, never silently applied.

## Explicit GitHub CI

```bash
bash scripts/install_hooks.sh --targets github --yes /path/to/repository
```

The generated workflow runs on push and pull requests, checks out the target repo, fetches the released Contextify tag and runs `ctx-check --ci`. It does not contain the author's machine-specific path. CI emits a freshness/drift message and writes to `GITHUB_STEP_SUMMARY` when set; Git mode does neither of these things when fresh.

Add `--strict` to the workflow's checker command to fail on drift or missing metadata. Internal errors remain errors in CI. A hook's read-only notice never updates documentation by itself; use `update`, or `accept` after confirming the prose is still correct.

## Upgrade from 0.1

The bundled Claude SessionStart registration is removed in0.2.0. Independently installed project hooks are separate files and are not removed by upgrading the package. Inspect those settings and remove only the Contextify entry if switching to Git-only checks; preserve other tools' entries. Existing0.1 Git templates may require a manual merge because different hook files are never overwritten silently.
