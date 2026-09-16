# Budget and style

Purpose: the community rules that govern what earns a line in AGENTS.md, each traced to its source, plus the hard budgets and a worked cut-or-keep table.

Research files referenced below live at `/Users/adamboudj/projects/10x/.goal/research/ctx/`; cited here by filename only.

## Rules, with source

1. **Commands first.** The agent needs the copy-pasteable path before anything else. Source: `02-community-intel.md` tip 6 (builder.io, GitHub's 2,500-repo analysis).
2. **Pointers, not pastes.** Reference `file:line`, never paste a code snippet; a pasted snippet rots silently as the code evolves. Source: `02-community-intel.md` tip 4 (HumanLayer).
3. **Examples over abstractions.** Point at a real file that already shows the pattern instead of describing it in prose. Source: `02-community-intel.md` tip 13 (GitHub's 2,500-repo analysis).
4. **No README duplication.** If a line does not change agent behavior, cut it. Source: `02-community-intel.md` anti-patterns, and DECISIONS.md D3.
5. **Style a linter or formatter already owns is excluded.** Claude is not an expensive linter; enforce style deterministically, not in prose paid for every session. Source: `06b-reddit-browser.md` tip 2 (paraphrase, sittingmongoose).
6. **U-shaped attention: put the highest-priority rule first.** Content buried in the middle of a long file is the most likely to be ignored. Source: `02-community-intel.md` tip 19 (Upsun summary of the ETH Zurich study).
7. **Hard rules read as "if X then Y" conditionals, not vague advisory prose.** This phrasing is reported to pierce through a model's tendency to treat background context as optional. Source: `02-community-intel.md` tip 14 (HN, dhorthy).
8. **Three-tier boundaries: Always / Ask first / Never**, each with its own evidence, never one long "be careful" paragraph. Source: `02-community-intel.md` tip 12 (GitHub's 2,500-repo analysis).
9. **No code blocks in the generated AGENTS.md.** The agent greps faster than it reads, and a pasted block rots invisibly. Source: DECISIONS.md D3, echoing `06b-reddit-browser.md` tip 1.
10. **Only rules the agent has actually gotten wrong.** `init` output is deliberately sparse; a rule earns a line by being promoted from a recurring mistake, never added speculatively. Source: DECISIONS.md D3 and D18, `06b-reddit-browser.md` tip 20 (the MISTAKES.md promotion pattern).
11. **Positive framing over all-caps bans.** State what to do instead of only forbidding. Source: `06b-reddit-browser.md` tip 29 (MirachsGeist).
12. **A hook is a rule; prose is a suggestion.** Say in the README which guarantees are actually hook-enforced (the line ceiling, the secrets check) versus advisory only. Source: `06b-reddit-browser.md` tip 3 and quote (c): a context file is treated as merely a suggestion unless something enforces it.

## The ETH Zurich finding, quoted exactly

Context files "do not generally improve task success rates, while increasing inference cost by over 20% on average" (arXiv 2602.11988). No success-rate percentage from this paper may be quoted in generated content or in this skill's own docs; it reports the direction of the effect, not a number safe to repeat as a headline figure. Source: `docs/design/comparison.md`, "What the comparables do better," and `02-community-intel.md` tip 20.

## Budgets

| Budget | Value | Source |
|---|---|---|
| AGENTS.md target, medium repo | 60 lines | DECISIONS.md D1 |
| AGENTS.md hard ceiling | 150 lines | DECISIONS.md D1, D2 |
| CLAUDE.md | 30 lines | DECISIONS.md D6 |
| Codex combined instruction budget | 32,768 bytes (`project_doc_max_bytes`) | DECISIONS.md D12; `02-community-intel.md` per-tool quirks |
| Claude Code guidance | "target under 200 lines" | `08-steal-list.md` section 3, citing code.claude.com/docs/en/memory |

## Cut or keep: 12 example lines

| # | Line | Cut or keep | Reason |
|---|---|---|---|
| 1 | `Build: \`pnpm run build\`` | Keep | copy-pasteable command, rule 1 |
| 2 | `This project uses React and TypeScript.` | Cut | derivable from `package.json`, rule 4 |
| 3 | `Write clean, readable code.` | Cut | generic, changes no behavior |
| 4 | `Never commit a real value into \`.env\`; \`.env.example\` is the template.` | Keep | evidenced hazard, positive Never framing, rule 11 |
| 5 | a pasted code snippet reproducing a function body | Cut | use a `file:line` pointer instead, rule 2 |
| 6 | `Use 2-space indentation.` | Cut | linter or formatter already owns this, rule 5 |
| 7 | `Server actions in \`src/app/actions/\` return \`{ok, error?}\`, never throw.` | Keep | a convention no linter enforces, changes agent behavior |
| 8 | `Ask first before touching \`prisma/migrations/\`, it runs against shared staging on merge.` | Keep | evidenced Ask-first boundary, rule 8 |
| 9 | `Follow best practices.` | Cut | generic, no evidence, no behavior change |
| 10 | `Single test: \`pnpm run test -- src/lib/pricing.test.ts\`` | Keep | exact runnable example, Claude's own stable init prompt asks for this |
| 11 | `See \`docs/architecture.md\` for the full request lifecycle.` | Keep | pointer, not a paste, rule 2 |
| 12 | `The team plans to migrate to Bun next quarter.` | Cut | a roadmap claim, not a fact evidenced by a tracked file |
