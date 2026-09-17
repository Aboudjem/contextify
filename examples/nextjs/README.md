# Next.js app: HazeLab

This output comes from the 2026-09-17 Codex run on an isolated copy of the existing HazeLab repository. It is a real application sample, not a fixture invented for this README. The source repository was not changed.

The source HEAD was `852985b98dd80b0aceecc4b133ed3c9e74145277`. The copy used tracked working-tree files; seven pre-existing untracked files were omitted. The isolated copy had no commit, so the generated header reports `commit=none` rather than pretending to describe a committed clean checkout.

- [Full generated AGENTS.md](AGENTS.generated.md) and [Claude pointer](CLAUDE.generated.md)
- [Evidence](evidence.json) and [stamp](stamp.json)
- [Writer result](../../evals/dogfood-evidence/hazelab/apply.json) and [actual drift notice](../../evals/dogfood-evidence/hazelab/drift.json)
- [Run method, measurements and validation limits](../../evals/dogfood.md)

The package manifest declares Next.js, development/build/lint scripts and a build step that generates the Prisma client. It does not declare a test script. The Vitest configuration still exists, so the generated file records both facts rather than inventing a package-manager test command.

An independent Codex agent checked the draft against the copied sources. Contextify's writer produced the files and their metadata. Removing the cited lint script in the copy made the freshness check identify the stale instruction. This verifies that script path with Codex; it does not demonstrate generation in a live Claude session or successful execution of the application's commands.

The complete outputs are saved byte-for-byte under `.generated.md` names. These names prevent their instructions from being loaded as active instructions for the Contextify repository. The recorded stamp belongs to the isolated application copy, not to this examples directory. The evidence includes normalized selectors and claim records; it is not a copy of the full application source.
