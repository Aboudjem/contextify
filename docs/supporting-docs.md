# Supporting architecture and workflow documents

`AGENTS.md` is the short entry point. It should tell an agent where to start, what commands are supported and which mistakes to avoid. Longer explanations belong in documents the agent reads when a task needs them.

Contextify first looks for accurate existing documentation. If `docs/architecture.md` already explains the relevant boundaries, link it from `AGENTS.md` rather than generating a competing account. Extra files are useful only when they fill an evidenced gap.

## Two optional outputs

| File | Include when useful | Leave out |
| --- | --- | --- |
| `docs/context/architecture.md` | Component responsibilities, entry points, dependencies, data flow and boundaries supported by source files | Guessed design intent, generic architecture advice, a full directory listing |
| `docs/context/workflows.md` | Development setup, test selection, build or release procedures supported by scripts and configuration | Invented commands, unverified deployment steps, copied tutorials |

Each file has a ceiling of **120 physical lines**, including any preserved human content. A repository can need neither, one or both. Contextify does not create a README, API reference, security policy or ADR collection just to fill a template. An architecture decision needs a recorded rationale; code alone does not establish why someone chose it.

## Keep the entry point short

Add a brief “Read when relevant” link in `AGENTS.md` for each useful document. The editor pointers still refer to `AGENTS.md`; they do not import all supporting prose into every session. A link does not guarantee that every host will read its target automatically.

`AGENTS.md` keeps its 20/40/60-line targets and 150-line ceiling. The supporting documents have their own budgets and are not part of the Codex root-to-leaf AGENTS instruction chain.

## Evidence and updates

The drafting agent reads the source files, maps factual lines to those sources and gets a separate review. Commands must resolve and unsupported facts are omitted or marked unverified. Strict writing refuses factual lines without provenance. Recorded provenance proves which source line was used; it does not prove that the explanation is semantically correct.

The writer uses the same managed blocks as `AGENTS.md`. It preserves human text outside those blocks and refuses conflicting edits inside them. `check` reports missing documents, changed managed content, dead quoted commands and changed evidence. `accept` only refreshes metadata when the content remains valid; it does not adopt edited managed prose.

An update that omits a previously generated document leaves it present and tracked by the stamp. It does not silently delete documentation.

## Draft layout and scope

Supporting drafts use `docs/context/architecture.md` and `docs/context/workflows.md` below the draft directory, alongside `AGENTS.md` and the shared `evidence.tsv`. Unknown filenames in the draft's `docs/context/` directory are refused before writes.

Paths and commands quoted in a supporting document are relative to its owning repository scope. In `docs/context/workflows.md`, `npm run test` means the repository root. In `pkg/docs/context/workflows.md`, it means `pkg`. Ordinary Markdown links should still use the relative path required by their reader.

Commit generated supporting documents with the instruction files, `.contextify/evidence.json` and `.contextify/stamp.json`. Keep temporary drafts out of Git.

[Quickstart](quickstart.md) · [Hooks and CI](hooks.md) · [Limits](limits.md)
