# Supporting context documents

Keep AGENTS as the entry point. Add depth only when a task needs it, and keep that depth out of the automatically loaded instructions.

## Choose the smallest useful set

| Repository evidence | Action |
| --- | --- |
| Accurate architecture or contributor docs already exist | Link them from AGENTS. Do not generate duplicates. |
| Several components interact and their relationships require reading multiple files | Consider `docs/context/architecture.md`. |
| Build, test, release or operations work has non-obvious ordering or prerequisites | Consider `docs/context/workflows.md`. |
| Tiny repository, generic advice, or too little evidence | Omit both files. |

These are optional outputs, not a standard documentation pack. Do not manufacture README, API reference, security policy or ADR files. A source file can prove what the system currently does; it cannot prove why somebody chose that design. Link existing decisions instead of inventing them.

## Architecture

Use only the sections the code supports: entry points, component boundaries, important data flows, state ownership, integrations and extension points. Explain relationships across real files. A directory tree or a list of libraries is not an architecture explanation.

Trace each factual line to the implementation or configuration that demonstrates it. Include both ends of a relationship in its evidence mapping when needed. Omit inferred intent, unsupported scaling guarantees and claims about production state.

## Workflows

Use only evidenced procedures: development setup, targeted tests, build prerequisites, migrations, release gates, deployment or incident checks. State the working directory and exact commands. Distinguish a workflow that declares an action from proof that the action currently succeeds.

Do not invent a test command, cloud environment, rollback procedure or operational permission. Environment-variable names may come from a template; secret values never belong in the document.

## Draft and apply

Put the bodies at `.contextify/draft/docs/context/architecture.md` and `.contextify/draft/docs/context/workflows.md`. With an explicit package scope, use these paths relative to that scope. Omit unneeded drafts. Unrecognized names under draft `docs/context/` are refused rather than silently ignored.

Record each factual line in the shared draft `evidence.tsv`: SHA-256 of the complete draft line, a tab, and its repository `file:line` source. Reuse the normal independent verification pass and the writer's diff, preflight, managed-block merge and rollback. Do not write target docs directly.

Each final document is capped at 120 physical lines, including human content outside the managed block. Leave fences out of generated bodies; concise Markdown headings and bullets are enough. Keep existing human text byte-identical. Leaving an existing document out of a later draft does not delete it or stop checking it.

## Navigation and scope

In AGENTS, use a pure navigation line for a generated document:

```markdown
- [Architecture](docs/context/architecture.md)
- [Workflows](docs/context/workflows.md)
```

These exact navigation labels name the matching output. They are not substitutes for evidence for architectural prose. Do not add an unsupported claim to the link label or append it to the line.

Markdown links resolve relative to the containing Markdown file. Backticked commands and repository paths inside a supporting document resolve from its owning repository or package scope, not from `docs/context/`. For example, a package-scoped workflow's `npm test` refers to that package's manifest.

Link the documents for relevant tasks. Do not add `@` imports or paste their content into AGENTS or its editor pointers. Ordinary Markdown links do not force every host to read the destination; the agent must open it when the task needs the detail.

## What checking proves

The committed stamp includes generated supporting documents. Changed managed content, missing docs, dead quoted commands/paths and changed evidence can trigger drift. The checker still cannot prove arbitrary prose logically follows its sources: the separate reviewer must do that.
