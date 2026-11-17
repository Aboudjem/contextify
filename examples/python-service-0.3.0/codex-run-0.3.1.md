# Codex run, contextify 0.3.1

Run record for the Codex row of the README. Run on 2026-11-17 with Codex CLI 0.169.0.

## Steps

1. Build a temp repo exactly as [replay.sh](replay.sh) does: the fixture, the written files and the committed stamp.
2. Install the skill from GitHub with the skills CLI:

   ```bash
   npx --yes skills@1.9.0 add Aboudjem/contextify -a codex -y
   ```

   It printed `Installed 1 skill`, `contextify (copied)`, `→ ./.agents/skills/contextify`. The installed `SKILL.md` carries `version: "0.3.1"`.

3. Exclude `.agents/` and `skills-lock.json` in `.git/info/exclude`. Otherwise the new folder itself shows up as moved evidence.
4. Apply [the Makefile change](makefile-change.diff).
5. Ask Codex, with no edits allowed:

   ```bash
   codex exec -s workspace-write "Use the contextify skill installed in .agents/skills/contextify to run its drift check on this repository (the check script, not an update). Report the exact notice it prints, its exit code, and the first action it tells you to take. Do not edit any file."
   ```

## What Codex did

It read `.agents/skills/contextify/SKILL.md`, then ran `sh .agents/skills/contextify/scripts/ctx-check .`. It reported exit code 0, left every file unchanged and quoted this notice:

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

It is byte for byte the notice in [drift-notice.txt](drift-notice.txt). `git status` afterwards showed only the `Makefile` edit from step 4.

## Limits

This proves the skills CLI install and the drift check under Codex. It does not cover a Codex-driven `init` or `update`.
