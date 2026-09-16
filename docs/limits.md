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
quoted anywhere in contextify's own docs, because none was measured. This finding is why `init` output
is deliberately sparse and why the line budgets exist at all.

## The hook never rewrites

`ctx-check` only reads and prints. A stale `AGENTS.md` stays stale, and the notice keeps appearing at
every session start, until a human or an agent runs `/contextify update`.

## Bounded parsers leave some evidence unverified

YAML is read with a bounded line-based reader, not a full YAML library; Makefile and justfile includes
are resolved only when they are statically local; a computed build target is not evaluated. Anything
the bounded reader cannot follow is labelled `unverified`, never guessed. See
[D15](design/DECISIONS.md).

## Some runner forms are unverified in 0.1.0

`uv run`, `poetry run`, `task`, and `mise` are not in the resolver table yet, so a quoted command using
one of them is reported `unverified` rather than resolved or marked stale. See
[SCRIPTS-SPEC.md](design/SCRIPTS-SPEC.md).

## Pointer loading is partly uncertain outside Claude Code

Whether Copilot loads a Markdown pointer as a native import across every feature, and whether Gemini
CLI deduplicates `AGENTS.md` when both combined discovery and an explicit import point at it, are both
`uncertain`. See [D6](design/DECISIONS.md).

## The fast path reads the git index

`ctx-check`'s fast path digests `git ls-files -s`, which reflects the index, not the working tree of
every worktree. In a repository with more than one worktree, a change staged in another worktree can
read as drift, or mask drift, in this one. See [D14, open risk 3](design/DECISIONS.md).

## Cursor's .mdc rule is optional

Cursor reads root and nested `AGENTS.md` natively, so `.cursor/rules/contextify.mdc` is off by
default. It exists only for a project that wants an explicit, always-applied pointer, and only with
`--targets cursor-rule`.

## The Codex byte cap is the documented default

32,768 bytes is Codex's documented `project_doc_max_bytes` default. A user override is only honoured
when contextify finds it recorded in `.codex/config.toml`; an override set some other way is not
detected, so the preflight check may still assume the default. See [D12](design/DECISIONS.md).

## No Windows testing in 0.1.0

The scripts are POSIX `sh` (bash 3.2 safe) and python3 standard library, tested on macOS and Linux CI
only. Windows behaviour, including under WSL, has not been verified for this release.

## Related

- [The design decisions](design/DECISIONS.md) · [The scripts spec](design/SCRIPTS-SPEC.md)
- [FAQ](faq.md) · [Quickstart](quickstart.md) · [Comparison](comparison.md)
