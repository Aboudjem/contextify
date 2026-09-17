# Supporting documents and Git checkpoints: 0.2 verification

Measured on 2026-09-17 with Codex and independent Codex reviewers. This report covers the 0.2 extension. [Earlier dogfood](dogfood.md) remains historical 0.1 evidence. [Machine-readable results](supporting-docs-results.json) record commands, exit codes, timestamps and reviewed source hashes.

## Deterministic suites

All seven suites ran sequentially against the extension's final code and exited 0.

| Command | Result |
| --- | --- |
| `python3 tests/test_ctx_check.py` | 119/119 checks |
| `python3 tests/test_verify_claims.py` | 30/30 checks |
| `python3 tests/test_hooks.py` | 20 tests |
| `python3 tests/test_regressions.py` | 23 tests |
| `python3 tests/test_supporting_docs.py` | 16 tests |
| `python3 tests/test_manifests.py` | 130/130 checks |
| `python3 evals/check_skill.py skills/contextify/SKILL.md` | 114/114 checks |

Supporting-document fixtures cover creation and omission, scoped commands and cross-links, strict provenance, preserved human text, merged budgets, unsafe paths, rollback, no-op updates and drift. An independent review caught silent adoption of an edited document omitted from a draft. The fixed writer refuses it, including with `--force-managed`, without changing target bytes or mtimes.

Hook fixtures perform real commits and pushes to a local bare remote. They check advisory and strict behavior, fresh silence, unavailable runners, preview immutability, activation conflicts, global-hook preservation, worktrees, pre-push stdin and unchanged CI summaries. No external repository is used for these mutation tests.

## Generated example in this repository

Codex read implementation and workflow sources, drafted three documents and mapped factual bullets to 48 source locations. A separate reviewer checked each bullet against those sources before the strict writer applied the draft.

| Output | Physical lines |
| --- | --- |
| [AGENTS.md](../AGENTS.md) | 21 |
| [Architecture](../docs/context/architecture.md) | 20 |
| [Workflows](../docs/context/workflows.md) | 21 |
| [CLAUDE.md](../CLAUDE.md), preserved pointer | 4 |

Strict claim and budget validation resolved 29 command/path claims, with zero stale or unverified claims. These resolver results do not replace the separate review of the prose. The checker is fresh and silent; a repeated strict write preserves all output and metadata bytes. See the [example guide](../examples/supporting-docs/README.md).

## Limits of this validation

- Supporting documents are selected when evidence warrants them; these tests do not show that generating both is useful for every repository.
- Git hooks inspect the working tree, not the staged index or exact pushed refs. Default wrappers are advisory; enforcement requires the strict option.
- Existing global/custom hook configurations are preserved. Installing Contextify does not automatically activate or replace them.
- Local Claude CLI manifest validation and component inventory pass: one skill, zero packaged hooks. The root CLAUDE.md contributor file produces the expected distribution warning.
- Claude model generation was not run because the user's weekly quota is exhausted. This is Codex authoring and independent review plus deterministic tests, not a Claude behavioral pass.
