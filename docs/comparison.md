# Comparing repository-context tools

The competitor observations below come from the source inspection on 2026-09-16. They are historical observations of the named paths, not a guarantee about current releases. Contextify's current behavior is checked by the [tests](../tests/) and [dogfood record](../evals/dogfood.md); a design decision alone is not proof.

| Tool | Observed approach | Source inspected |
| --- | --- | --- |
| [ruler](https://github.com/intellectronica/ruler) | Distributes instructions from `.ruler/` through agent adapters. The inspected write path replaces generated bodies; its gitignore helper uses managed blocks. | `src/core/RuleProcessor.ts`, `src/core/GitignoreUtils.ts`, `src/agents/` |
| [rulesync](https://github.com/dyoshikawa/rulesync) | Imports and exports configurations for different tools, including more than instruction text. | `src/lib/import.ts`, `src/constants/` |
| [ClaudeForge](https://github.com/alirezarezvani/ClaudeForge) | Organizes Claude instructions and supplies examples for different project sizes. | `CLAUDE.md`, `skill/examples/`, `hooks/validate-claude-md.py` |
| [agentrules-architect](https://github.com/trevor-nichols/agentrules-architect) | Uses a multi-stage analysis pipeline and a separate snapshot document. | `core/pipeline/orchestrator.py`, `core/utils/token_estimator.py` |
| [agents-md-generator](https://github.com/nyosegawa/agents-md-generator) | Seeds a small template and links `CLAUDE.md` to `AGENTS.md` with a filesystem symlink. | `AGENTS.md.template`, `agents-md-seed.sh` |
| [airul](https://github.com/mitkury/airul) | Distributes content across multiple instruction filenames. | `src/generator.ts` |
| Built-in `/init` | Generates a host agent's context file. The local Claude and Codex runs in the recorded baseline resolved their quoted commands; the Gemini run failed before generation. | [Historical baseline and its limits](../evals/RED-baseline.md) |

## What Contextify adds

| Behavior | Implementation and evidence |
| --- | --- |
| One instruction source and selected thin pointers | `ctx_write.py` renders `AGENTS.md` and agent-specific pointers. Existing human instructions require preservation and may require an explicit migration. |
| Line ceilings | The writer checks the final merged files, including human content. See writer regression tests. |
| Deterministic freshness check | `ctx-check` resolves declarations and compares recorded evidence without a model call. It does not prove that a command succeeds. |
| Managed updates | The writer previews changes and preserves bytes outside its managed block. In-block edits produce conflicts. |
| Traceable drafting | The skill requires evidence for factual lines and an independent verifier; the writer records supplied provenance. This is not a proof that the primary source is correct. |
| Measured examples | The [dogfood report](../evals/dogfood.md) records outputs, drift probes, preservation and idempotence results with the method used. |

## Trade-offs

Contextify does not import a foreign tool's complete configuration. A distribution tool such as rulesync addresses a broader job. Its bounded command resolvers also leave unsupported expressions unverified; they do not execute a shell to guess what it would do.

Use a built-in initializer when a single agent-specific file is enough. Use Contextify when you want a shared file and an explicit check for later drift. No task-success advantage has been demonstrated for Contextify.

The [ETH Zurich paper](https://arxiv.org/abs/2602.11988) reports no general task-success improvement from repository context files and an average inference-cost increase above 20%. That finding argues for evaluating usefulness, rather than treating longer instructions as better instructions.
