# Contributing to contextify

Thanks for wanting to help. `contextify` is a skill-only Claude Code plugin: Markdown plus
zero-dependency scripts, no npm package, no MCP server. Installed from GitHub
`Aboudjem/contextify`, it gives you one command, `/contextify init|update|check|accept`, that
writes lean, evidence-backed context files for any repo. `AGENTS.md` is the single source of
truth: every command, path, port, or branch fact in it traces to a file the run actually read,
or it is omitted, or it is labelled `unverified`. Thin pointer files (`CLAUDE.md`, `GEMINI.md`,
`.cursor/rules/contextify.mdc`, `.github/copilot-instructions.md`) point back at it. This guide
explains how to contribute without breaking that contract.

## What we want

- **New evidence normalizers**, for a language, config format, or convention the drift check
  does not yet understand.
- **New target agents**, added as a data-table row rather than special-cased code.
- **Budget or skeleton improvements**, backed by a source: a real repo where the current
  60-line target or 150-line ceiling for `AGENTS.md`, or the 30-line ceiling for `CLAUDE.md`,
  produced a bad result.
- **Dogfood reports**: run contextify on a real repo and report the measured line counts,
  what was correct, and what was missed or labelled `unverified` incorrectly.

Open an issue first if you want to discuss a larger change before writing it.

## Ground rules

- **Every claim in `SKILL.md` and `references/` cites a primary source.** A command, a path, a
  budget number: if it is stated as fact, it traces to a file, a doc, or a measured run.
- **No fabricated figures.** Do not invent a line count, a timing number, or a version.
- **No em dash anywhere**, in prose or in generated output. Use a comma, a colon, parentheses,
  or a new sentence.
- **No emoji in headings**, in this repo's Markdown or in anything the skill generates.
- **Zero dependencies.** Scripts are POSIX sh safe on bash 3.2, or python3 using stdlib only.
  Nothing contextify ships requires `pip install` or `npm install` to run.
- **The drift check stays fast and safe.** Aim for a warm median below 100 ms and keep the
  regression ceiling below 250 ms. No cache may skip a changed source, context file or evidence
  record. `ctx-check` must never exit 2; hook input reads must be bounded.

## How to test locally

```bash
python3 tests/test_manifests.py
python3 tests/test_ctx_check.py
python3 tests/test_verify_claims.py
python3 tests/test_regressions.py
python3 tests/test_hooks.py
python3 evals/check_skill.py skills/contextify/SKILL.md
claude plugin validate . --strict
```

All seven must exit 0 before you open a PR.

## How to add a normalizer

1. Add the normalizer to `skills/contextify/scripts/ctxlib.py`.
2. Add one fixture case to `tests/test_ctx_check.py` that exercises it.
3. Add one row to `skills/contextify/references/detection-signals.md` describing what it
   detects and why.

## How to add a target agent

1. Add one row to `skills/contextify/references/agents-and-files.md`: the agent, the file it
   reads, and the official doc URL that confirms the filename and format.
2. Add the matching entry to `docs/editors.md`.
3. Cite the agent's official documentation URL in both places. Do not guess a filename.

## Commit style

- Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, and so on.
- No AI attribution trailers of any kind.
- Commits land under the contributor's own identity, never a bot or assistant account.

## PR checklist

- [ ] All seven local checks pass (see above).
- [ ] Every new or changed claim in `SKILL.md` or `references/` cites a primary source.
- [ ] No em dash, no emoji in headings.
- [ ] `AGENTS.md` stays within its 60-line target and 150-line ceiling; `CLAUDE.md` stays under
      30 lines, if your change touches either.
- [ ] New normalizer: fixture case added. New target agent: table row and doc URL added.
- [ ] Commit messages follow conventional commits, with no AI attribution trailer.

## Code of Conduct

Be kind in review. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
