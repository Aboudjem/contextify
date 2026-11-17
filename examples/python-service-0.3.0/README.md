# Python service, contextify 0.3.0 run

A real run on 2026-11-17 with contextify 0.3.0. The source is the [Python service fixture](../python-service/source/), copied to a throwaway Git repo.

## What was run

1. Claude Code, headless, with the plugin loaded from this repository: `/contextify:contextify init --yes`, targets claude and codex.
2. The skill drafted the instructions. A separate verifier subagent checked 22 claims and ran both test commands. The writer applied the draft.
3. The output was committed. A stray tool folder (`.omc/`, not from contextify) was deleted, so `/contextify accept` refreshed the stamp. Then `ctx-check` printed nothing and exited 0.
4. The `test-health` target was deleted from the `Makefile` ([the change](makefile-change.diff)).
5. `ctx-check` ran again and printed [this notice](drift-notice.txt), exit 0.

## Files

| File | What it is |
| --- | --- |
| [AGENTS.generated.md](AGENTS.generated.md) | The written `AGENTS.md`, 17 lines |
| [CLAUDE.generated.md](CLAUDE.generated.md) | The 4-line Claude Code pointer |
| [drift-notice.txt](drift-notice.txt) | The drift notice after the target was removed |
| [makefile-change.diff](makefile-change.diff) | The edit that caused the drift |

The files are renamed so an agent browsing this repo does not apply another repo's instructions.

## The notice

```text
contextify: drift
1. Run /contextify update to fix AGENTS.md:6 (make test-health)
2. Review the diff it shows before it writes
3. Commit the context files with .contextify/
Scope    .
Stale    AGENTS.md:6 references make test-health
Unverified AGENTS.md:6 python3 -m unittest tests.test_health
Changed  makefile#targets
Changed  provenance:Makefile:6
More     +2 findings
Files    0 written
Accept   unavailable until the stale command is corrected
```

The first action names the dead line. `Accept` is refused until that line is fixed. The `Unverified` row is the module form of the same test: the resolver does not parse `python3 -m unittest` module paths, so it labels the claim instead of guessing.

## Limits

The verifier ran the two test commands; contextify itself only checks that they resolve. One run on one small fixture proves the shape of the output, not task success.
