# Worked examples

Current0.2 example: [Contextify with optional architecture and workflow docs](supporting-docs/README.md). The earlier examples below retain their original0.1 outputs and measurements.

Read the generated instructions alongside the files that support them. These are saved outputs, not templates to paste into an unrelated repository.

| Example | Origin | What it shows |
| --- | --- | --- |
| [Tiny greeting](tiny/README.md) | Teaching fixture created for this repository | A small command list without empty sections. |
| [Python service](python-service/README.md) | Standard-library HTTP service fixture | Commands, a single-test target and relationships between implementation files. |
| [Next.js app](nextjs/README.md) | Real run on an isolated copy of HazeLab | Evidence from an existing application, including a test configuration without a declared test script. |

The fixtures are not part of the real-repository dogfood count. The [dogfood report](../evals/dogfood.md) records those runs separately, with dates and limits.

Each saved `AGENTS.generated.md` and `CLAUDE.generated.md` contains the full writer output. The filenames are changed for publication so an agent browsing Contextify does not accidentally apply another repository's instructions. Recorded stamps describe the isolated source repository at generation time; they are not stamps for this examples directory.

The writer's checks prove that supported commands and paths resolve. They do not prove that application commands succeed, that a deployed service works, or that the instructions improve an agent's task success.
