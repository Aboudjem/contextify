# Honest limits

**A clean contextify run is not evidence that AGENTS.md is right, and a fresh `ctx-check` is not
evidence that your repository is healthy.** Both are narrower claims than they sound. Below is what
contextify does not do, cannot see, or cannot promise.

## A verified command resolves. It was not executed

"Verified" means a quoted command's declaration or target resolves: `npm run test` is verified because
`scripts.test` exists in `package.json`. It does not mean the command was ever run, and it does not
mean it would succeed. See [D16](design/DECISIONS.md).

## Evidence in the repository can itself be wrong

A comment can lie, a stale README line can be copied by a human before contextify ever runs, and a
tracked file can simply be wrong about what the code does. contextify traces every claim to a file it
read; it does not audit whether that file was telling the truth.

## The ETH Zurich finding

The ETH Zurich paper (arXiv 2602.11988) reports that context files "do not generally improve task
success rates, while increasing inference cost by over 20% on average." No success-rate percentage is
quoted here: the [paper's abstract](https://arxiv.org/abs/2602.11988) gives no such percentage. This finding is why `init` output
is deliberately sparse and why the line budgets exist at all.

## The hook never rewrites

`ctx-check` only reads and prints. A stale `AGENTS.md` stays stale, and the notice keeps appearing at
every session start, until a human or an agent runs `/contextify update`.

## Bounded parsers leave some evidence unverified

YAML is read with a bounded line-based reader, not a full YAML library. Makefile/justfile includes and computed build targets are outside the current parser. A target supplied only by an include may be reported missing; review that result against the real build tool instead of treating it as proof of a dead command. See
[D15](design/DECISIONS.md).

## Some runner forms are unverified in 0.1.0

`uv run`, `poetry run`, `task`, and `mise` are not in the resolver table yet, so a quoted command using
one of them is reported `unverified` rather than resolved or marked stale. See
[SCRIPTS-SPEC.md](design/SCRIPTS-SPEC.md).

## Pointer loading is partly uncertain outside Claude Code

Whether Copilot loads a Markdown pointer as a native import across every feature, and whether Gemini
CLI deduplicates `AGENTS.md` when both combined discovery and an explicit import point at it, are both
`uncertain`. See [D6](design/DECISIONS.md).

## A check belongs to one working tree

Run `ctx-check` in the checkout you want to inspect. Git worktrees have separate indexes; a passing
check in one worktree says nothing about another. Hook input selects the working directory.

## Cursor's .mdc rule is optional

Cursor reads root and nested `AGENTS.md` natively, so `.cursor/rules/contextify.mdc` is off by
default. It exists only for a project that wants an explicit, always-applied pointer, and only with
`--targets cursor-rule`.

## The Codex byte cap is the documented default

32,768 bytes is Codex's documented `project_doc_max_bytes` default. A user override is only honoured
when contextify finds it recorded in `.codex/config.toml`; an override set some other way is not
detected, so the preflight check may still assume the default. See [D12](design/DECISIONS.md).

## No Windows testing in 0.1.0

The scripts use POSIX shell tools, Bash and Python 3.11 or newer. Local checks run on macOS; the GitHub workflow runs on Linux. Consult the current CI result for that revision. Windows behavior, including WSL, has not been verified for this release.

## Related

- [The design decisions](design/DECISIONS.md) · [The scripts spec](design/SCRIPTS-SPEC.md)
- [FAQ](faq.md) · [Quickstart](quickstart.md) · [Comparison](comparison.md)

## Plugin validation and contributor context

The root `CLAUDE.md` imports this repository's contributor instructions. Claude's plugin validator warns that a plugin-root `CLAUDE.md` is not loaded as distributed project context. The installed skill lives in `skills/contextify/SKILL.md`. Marketplace validation passes with `--strict`; plugin manifest validation passes with this warning, and therefore does not pass `--strict`.
