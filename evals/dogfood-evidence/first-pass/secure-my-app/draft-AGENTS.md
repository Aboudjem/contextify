# secure-my-app
## Commands
- Validate the skill from the repository root: `python3 evals/check_skill.py skills/secure-my-app/SKILL.md`.
- Run release checks: `python3 tests/test_manifests.py`.
## Boundaries
- When invoking the skill, remain read-only until the user approves a fix.
## Read when relevant
- `skills/secure-my-app/references/controls.md` contains the DETECT and VERIFY catalogue used by the skill.
