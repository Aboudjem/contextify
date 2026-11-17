# Python service, contextify 0.3.0 run

A real run on 2026-11-17 with contextify 0.3.0. The source is the [Python service fixture](../python-service/source/), copied to a throwaway Git repo. This is the run record for the Claude Code row of the README.

## What was run

1. Claude Code, headless, with the plugin loaded from this repository: `/contextify:contextify init --yes`, targets claude and codex.
2. The skill drafted the instructions. A separate verifier subagent checked 22 claims and ran both test commands. The writer applied the draft.
3. The output was committed. A stray tool folder (`.omc/`, not from contextify) was deleted, so `/contextify:contextify accept` refreshed the stamp. Then `ctx-check` printed nothing and exited 0.
4. The `test-health` target was deleted from the `Makefile` ([the change](makefile-change.diff)).
5. `ctx-check` ran again and printed [this notice](drift-notice-0.3.0.txt), exit 0.

## Replay it

Every input of that run ships here, so one command rebuilds it:

```bash
sh examples/python-service-0.3.0/replay.sh
```

It copies the fixture into a temp repo and restores the written files and the committed stamp. Then it checks the repo is fresh, applies the `Makefile` change and runs the checker from your clone. Nothing is written in this repository.

## Files

| File                                                                            | What it is                                                  |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| [AGENTS.generated.md](AGENTS.generated.md)                                      | The written `AGENTS.md`, 17 lines                           |
| [CLAUDE.generated.md](CLAUDE.generated.md)                                      | The 4-line Claude Code pointer                              |
| [draft-AGENTS.md](draft-AGENTS.md) and [draft-evidence.tsv](draft-evidence.tsv) | The draft the agent wrote and its line-to-source map        |
| [evidence.json](evidence.json) and [stamp.json](stamp.json)                     | The committed `.contextify/` metadata after `accept`        |
| [makefile-change.diff](makefile-change.diff)                                    | The edit that caused the drift                              |
| [drift-notice-0.3.0.txt](drift-notice-0.3.0.txt)                                | The notice 0.3.0 printed in the original run                |
| [drift-notice.txt](drift-notice.txt)                                            | The notice 0.3.1 prints when `replay.sh` runs               |
| [codex-run-0.3.1.md](codex-run-0.3.1.md) | Codex installing the skill and running the same drift check |

The files are renamed so an agent browsing this repo does not apply another repo's instructions.

## The notice

From `replay.sh` with 0.3.1, on 2026-11-17:

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

The first action names the dead line. `Accept` is refused until that line is fixed. The `Unverified` row is the module form of the same test. The resolver does not parse `python3 -m unittest` module paths, so it labels the claim instead of guessing.

What changed from 0.3.0: the command is the one Claude Code accepts, an `Agents` line says what to type elsewhere, and every value starts in the same column. 0.3.0 showed `Changed provenance:Makefile:6` as a fifth detail row. In 0.3.1 the new `Agents` line takes that row, so it moves into the `More` count.

## Limits

The verifier ran the two test commands; contextify itself only checks that they resolve. One run on one small fixture proves the shape of the output, not task success.
