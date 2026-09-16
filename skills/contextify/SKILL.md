---
name: contextify
description: >-
  Tell every coding agent how your repo works. Then prove it is still true. Use when the user says
  "contextify", "contextify this repo", "write an AGENTS.md", "generate CLAUDE.md", "agent context",
  or "context file is stale", or when a repo has no instruction file at all, or the one it has names
  a command that no longer exists. Writes one AGENTS.md plus thin pointers for Claude Code, Codex,
  Gemini CLI, Cursor and Copilot, so the same instructions are never copied into five files. Every
  line traces to a file the run read, or it is omitted, or it is labelled unverified. The drift check
  is a shell script: it spends zero tokens, calls no model, and never rewrites a file on its own.
  Claude Code's own /init writes one file for one agent, with no evidence behind any line and no way
  to tell later that the line went stale.
argument-hint: "[init|update|check|accept] [path]"
license: MIT
metadata:
  version: "0.1.0"
---

# contextify

## Overview

In one line, for anyone: **Tell every coding agent how your repo works. Then prove it is still true.**

Two halves, and the second one is what nobody ships. Writing a context file is a single afternoon.
Knowing three months later whether it is still describing the same repository is the hard part, and
every tool in this category stops before it. A context file that confidently names a deleted script
is worse than no file at all: it sends an agent somewhere the repo does not go, and it costs a turn
before anyone notices.

So contextify does two things. It generates one `AGENTS.md` from evidence, with thin pointer files
for the agents that read something else. Then it records what each line was derived from, and ships
a deterministic check that tells you when that evidence moved.

**The whole skill rests on one rule. Do not break it:**

> **Evidence, or omit, or label it `unverified`. Never invent.**

A command, a path, a port, a branch, a deploy fact: each one traces to a file this run actually read,
or it does not go in the file. Omission is free. A wrong line is not.

## Invocation

Triggered by natural language ("contextify this repo", "write an AGENTS.md for this", "our CLAUDE.md
is stale", "generate CLAUDE.md") or as `/contextify <mode> [path]`.

`$ARGUMENTS` is `[init|update|check|accept] [path]`. Both parts are optional.

| Argument | Meaning |
| --- | --- |
| no mode | `init` when the repo has no `.contextify/stamp.json`, `check` when it has one |
| `init` | discover evidence, draft, verify, write |
| `update` | re-read the evidence that moved, revise only the lines it touches |
| `check` | run the drift check, relay what it says, write nothing |
| `accept` | the docs are still right and only the evidence moved: restamp, change no prose |
| `[path]` | scope the run to that directory. It must sit inside the repository the run resolved |

Flags reach the scripts unchanged: `--dry-run`, `--yes`, `--json`, `--strict`, `--targets LIST`,
`--symlink`, `--hook AGENT`. The full table is in `references/agents-and-files.md`.

## When to use / when not

**Use when:** a repo has no `AGENTS.md`; an existing `AGENTS.md` or `CLAUDE.md` contradicts how the
project actually builds, tests or deploys; a team runs more than one coding agent and the same
instructions have been pasted into three files; a monorepo package needs its own nested file; the
session-start check just reported drift; someone asks whether the context file is still true.

**Do not use for:** end-user product documentation or a README, which is written for humans and has a
different job; an API reference, which belongs to a doc generator; a single-file script with nothing
an agent could get wrong; a repository the user does not own and does not want written to (run
`check` and hand over the notice instead).

**Against Claude Code's built-in `/init`:** `/init` writes `CLAUDE.md`, for Claude Code, in one pass,
and it is good at that. It records nothing about where a line came from, so no later run can tell
whether the line is still true, and it serves one agent. contextify writes the file every agent
reads, keeps the per-line evidence, and ships the check. Use `/init` when Claude Code is the only
agent and the repo is small. The full matrix is in `references/comparison.md`.

## The run

Two layers, and never confuse them.

**Deterministic, done by scripts:** `detect_repo.sh` surfaces facts, `ctx-check` decides freshness,
`ctx_write.py` is the only thing that ever writes a context file, `ctx_stamp.py` records evidence and
the stamp, `verify_claims.py` lints a file's commands and paths.

**Judgement, done by the model, which is you:** reading the files the detector surfaced, deciding
what an agent actually needs, writing the prose, and labelling what you could not confirm.

You write a draft. You never write a target file yourself.

### init

1. **Resolve the target.** The argument path, else the repository containing the working directory.
   Confirm it with `git -C <path> rev-parse --show-toplevel`. Refuse a path outside that repository,
   and never let an output path escape the scope.
2. **Fingerprint, then read.** Run the detector:
   `bash "${CLAUDE_SKILL_DIR}/scripts/detect_repo.sh" <path>`. It reports languages, package managers
   and lockfiles, manifest scripts, workspace layout, entry points, infrastructure and deploy config,
   CI workflows, env file names, git remotes and branches. Treat its output as a list of files to
   open. It surfaces candidates and never replaces reading. Map each signal to a section with
   `references/detection-signals.md`.
3. **Fan out.** On a medium or monorepo repository, dispatch parallel readers, one per independent
   subsystem (frontend, backend, infrastructure, CI, data, tooling). Each returns what the subsystem
   is, how it builds, runs and is tested, its hazards, and `file:line` for every claim. Synthesize
   one model of the repo before writing a word. Nested package files follow `references/monorepo.md`.
4. **Decide create against update.** Look for `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules`
   and `.github/copilot-instructions.md`, plus any nested `*/AGENTS.md`. Any of them carrying human
   content puts this run on the preservation path in `references/update-in-place.md`. Read human
   lines as evidence. Never silently adopt them as generated content.
5. **Ask at most three questions, each only when its trigger fires.** Which agents get pointer files.
   What an agent must know that the repository does not show, in particular a single-test command or
   an action that needs approval. Whether to apply the displayed changes. Ask nothing the repo
   already answers. Skip all three under `--yes`, under `--dry-run`, or when input is not
   interactive. Exact wording and defaults: `references/init-prompts.md`.
6. **Draft the managed body** into `.contextify/draft/AGENTS.md`, following the section order in
   `references/section-template.md` and the budget for the size class (see Hard rules). Commands
   first. Omit any section with no evidence: no heading, no placeholder, no TODO. Record the support
   for every line in `.contextify/draft/evidence.tsv`, one row per line, as
   `line-hash<TAB>file:line`. Write a single-test line only when a working directory, an exact
   command and a real test path all exist; otherwise write `Single test: unverified` or leave it out,
   and never invent a filter flag. No code blocks in the draft. Style rules in
   `references/budget-and-style.md`.
7. **Draft the Claude addendum only if it has content.** `.contextify/draft/CLAUDE.md` holds
   Claude-specific notes and nothing else, and only when a file proves them: hooks in
   `.claude/settings.json`, servers in `.mcp.json`. With no such evidence, omit the file. The pointer
   alone is the correct output.
8. **Show the cost before writing anything.**
   `python3 "${CLAUDE_SKILL_DIR}/scripts/ctx_write.py" --root <path> --draft <path>/.contextify/draft --dry-run`
   prints the per-target diff and the cost table. Put both in front of the user.
9. **Verify in a separate lane.** Hand the draft to a separate verifier subagent, never to the pass
   that wrote it. It re-derives every claim from primary sources per `references/verification.md`,
   may run `python3 "${CLAUDE_SKILL_DIR}/scripts/verify_claims.py" --root <path> <draft file>`, and
   returns CONFIRMED, CORRECTED or UNVERIFIED per claim. Apply every correction. Label or cut every
   UNVERIFIED claim. Re-run until nothing is CORRECTED.
10. **Apply.** Re-run the same `ctx_write.py` command with `--yes` instead of `--dry-run`. It
    journals the write, replaces each target atomically, writes the stamp last, and then runs the
    check against what it just wrote. A check that is not clean rolls the whole write back.
11. **Report.** Print the summary block from The output, then the next command. Do not paraphrase the
    numbers the script printed.

### update

1. **Run the check first.** `sh "${CLAUDE_SKILL_DIR}/scripts/ctx-check" <path>`. Read the notice
   before touching anything: it names which evidence changed and which lines went stale.
2. **Re-read only the evidence that moved.** Open the files the notice named. Do not re-derive the
   whole repository, and do not regenerate a file that has no reported problem.
3. **Revise only the affected lines** in `.contextify/draft/AGENTS.md`, starting from the current
   managed block. Keep every still-true managed line byte-identical. Keep every human line outside
   the block byte-identical.
4. **Show the diff, verify, apply.** Same three steps as `init`: `--dry-run` for the diff and the
   cost table, the separate verifier lane for the changed lines, then `--yes`.
5. **Stop and use `accept` instead** when the notice reports only moved evidence and no stale claim.
   Rewriting correct prose to satisfy a hash is churn.

### check

1. Run `sh "${CLAUDE_SKILL_DIR}/scripts/ctx-check" --ci <path>`.
2. Relay its output exactly. Empty output means fresh: say so in one line and stop.
3. Write nothing in this mode, not even a fix the notice makes obvious. Offer `/contextify update`
   and let the user decide.

### accept

1. Run `python3 "${CLAUDE_SKILL_DIR}/scripts/ctx_stamp.py" --root <path> --accept`.
2. Relay the metadata difference it prints, and state plainly that no prose changed and every context
   file is byte-identical.
3. Relay the refusal and switch to `update` when it refuses, which it does on a dead claim, a budget
   violation, or a missing stamp.

## Hard rules

**Evidence or omit or `unverified`.** Before any command, path, env var name, branch, port or deploy
fact reaches a draft, it traces to a primary source you read in this run.

| Claim | The primary source that must back it |
| --- | --- |
| Build, test or lint command | the script in `package.json`, `Makefile`, `justfile`, `pyproject.toml`, `Cargo.toml` or a CI `run:` line, quoted by its real name |
| File or directory path | the path exists in the tracked tree |
| Framework or version | the manifest or lockfile entry, never the marketing name |
| Branch, deploy or environment model | CI config, infrastructure as code, deploy config, or a read-only cloud call. Never a branch name |
| A hazard, a "never do this" | a real incident in git history, an issue, a code comment, or a config that proves the hazard |

Find no source, and the line is cut or carries `unverified`. Never soften a guess into a statement.

**Hold the budget.** Classify the repository first, then write to its line target: 20 for tiny, 40
for medium, 60 for a monorepo. Scaling only ever goes down, so a target of 60 lines is the most any
repository gets, and a hard ceiling of 150 lines caps `AGENTS.md` in every class, human content
included. Keep `CLAUDE.md` under 30 lines. `ctx_write.py` warns above a target and refuses above a
ceiling. Every later mention of the budget in this file means these numbers.

**Update in place. Never clobber.** Rewrite only what is between `<!-- contextify:begin v1 -->` and
`<!-- contextify:end -->`. Preserve every byte outside it, line endings included. Show the full diff
before the write, every time, including under `--yes`.

**Never rewrite a file from a hook.** The session-start hook reads and reports. It has five seconds,
no model, and no write permission. A hook that edits files during startup gets blamed for everything
else in the session and switched off inside a week.

**The check reports, and that is all.** `ctx-check` must never exit 2, never call a model, never
touch the git index, never write. Exit 0 with empty output is fresh, exit 0 with a notice is drift,
exit 3 is no stamp yet, exit 1 is the check itself breaking. When the repo is fresh it prints
nothing, which is why the hook costs zero tokens.

**Read-only for any live fact.** Cloud, deploy and CI reads are describe, list and get calls only,
and only when the CLI and credentials already exist. Credentials absent means skip in silence and
fall back to repository evidence. Never run a mutating call, and never block the run on one.

**Never write a secret.** Read env file names freely. Take key names from `.env.example` and nothing
else. No value, ever, reaches a draft, a summary, a log or the evidence record.

**AGENTS.md is free-form Markdown.** There is no frontmatter, no required schema, no mandated section
list. The template is a good default for a repository that needs those sections, not a form to fill
in. Drop what this repo does not need.

**No code blocks in the generated AGENTS.md.** An agent greps a command out of a line faster than it
reads a fence, and a pasted snippet rots silently while the file still looks maintained. Inline code
spans are fine. Blocks are not.

**A Do-not list only when the repo shows a real hazard.** Every entry names the evidence and says
what to do instead. No all-caps bans, no invented danger, and no section at all when nothing fires.

**No README duplication.** The README explains the product to a person. `AGENTS.md` carries what an
agent gets wrong without it. A line that does not change agent behaviour is cut, however true.

**The pointer files are pointers.** `CLAUDE.md` is this, and line 1 is owned by contextify:

```markdown
@AGENTS.md
<!-- contextify:begin v1 -->
<!-- Generated by contextify {toolVersion}; writer={generatedBy}; at={generatedAt}; commit={commit}; regenerate: /contextify update -->
<!-- contextify:end -->
```

An optional `## Claude Code` section goes inside the block when, and only when, evidence supports it.
`GEMINI.md` is three lines, the Cursor rule and the Copilot pointer are in
`references/agents-and-files.md`. The same instruction text never appears in two files.

**Never verify your own draft.** The pass that wrote a claim cannot be the pass that confirms it.
Verification is a separate subagent with the primary sources, or it did not happen.

## The output

**On screen, after `init`**, exactly the block the writer prints. This is an example rendering, and
the numbers come from a fixture:

```text
contextify init

Result   written
Scope    .
Targets  claude, gemini, cursor-rule, copilot

Files written                              Lines
AGENTS.md                                     60
CLAUDE.md                                      4
GEMINI.md                                      3
.cursor/rules/contextify.mdc                   9
.github/copilot-instructions.md                4
.contextify/evidence.json                     84
.contextify/stamp.json                        72

Evidence     18 records
Unverified    0 claims
Next         /contextify check
```

Every file actually written appears in it. Lines are counted after serialization.

**On screen, from the drift check**, at most 12 lines, dead claims first, again a fixture rendering:

```text
contextify: drift
Scope    .
Changed  package.json#scripts
Removed  script lint:css
Stale    AGENTS.md:14 references npm run lint:css
Files    0 written
Next     /contextify update
Accept   unavailable until the stale command is corrected
```

**The files, and who reads which:**

| File | Which agents read it | Lines |
| --- | --- | --- |
| `AGENTS.md` | Codex CLI, Cursor, Copilot, and everything else following the agents.md convention | the budget |
| `CLAUDE.md` | Claude Code, which does not read `AGENTS.md` on its own | 4, plus an evidenced addendum |
| `GEMINI.md` | Gemini CLI | 3 |
| `.cursor/rules/contextify.mdc` | Cursor, only with `--targets cursor-rule` | 9 |
| `.github/copilot-instructions.md` | GitHub Copilot, written when `.github/` exists | 4 |
| `.contextify/evidence.json` | no agent. It is the record of what each line was derived from | n/a |
| `.contextify/stamp.json` | no agent. It is what the check compares the repo against | n/a |

**The stamp** is the deliverable that makes the second half of the story sentence possible. It holds
the tool version, the commit, the normalized digest of every piece of evidence, and one entry per
claim with its resolver and location. Commit it. Without it, `check` exits 3 and the repo is back to
a context file nobody can date.

**The next commands**, printed in this order: `/contextify check` after a write, `/contextify update`
after a drift notice, `/contextify accept` when only evidence moved.

## Reference files

Load one when the run reaches it. Do not paste a reference into the conversation wholesale.

| File | Load it when |
| --- | --- |
| `references/agents-and-files.md` | Choosing targets. Which agent reads which file, the literal pointer contents, the flag table. |
| `references/section-template.md` | Drafting `AGENTS.md`. The section order, the per-section line allowance, and what earns a line. |
| `references/detection-signals.md` | After the detector runs. The file to fact to section map. |
| `references/budget-and-style.md` | Writing the prose. Size classes, the ceiling, sentence rules, what to cut first. |
| `references/update-in-place.md` | An instruction file already exists. Managed blocks, migration, conflicts, what is never touched. |
| `references/verification.md` | The verification pass. What the separate agent re-derives, and how a claim is labelled. |
| `references/hooks-and-ci.md` | Installing the drift check outside Claude Code, or gating CI. The opt-in snippets. |
| `references/monorepo.md` | Two or more build units. Nested files, closest-file-wins, what belongs at the root. |
| `references/comparison.md` | The user asks how this differs from `/init`, ruler, rulesync or airul. |
| `references/init-prompts.md` | The three `init` questions: their triggers, their wording, their defaults. |

## Common mistakes

Each of these has produced a confidently wrong context file. Do not repeat them.

- **Never guess the stack from folder names.** A `src/` directory proves nothing about a framework.
  Read the manifest and the lockfile.
- **Never infer the deploy model from a branch name.** `main`, `prod` and `develop` routinely lie. An
  Amplify stage labelled PRODUCTION was staging. Confirm from CI, infrastructure as code, or a
  read-only cloud read.
- **Never copy README marketing.** The value proposition changes no agent behaviour. Cut it.
- **Never list a test command that does not exist.** "No test runner is configured" is an accurate,
  useful line. An invented `npm test` costs a turn and some trust.
- **Never clobber a human `CLAUDE.md`.** Insert the managed block, preserve every other byte, and
  report `migration pending` until the human content is explicitly moved.
- **Never prescribe a schema.** A repo with no deploy story gets no Deploy heading. An empty section
  is worse than a missing one, because it reads as a fact.
- **Never paste code snippets into the generated file.** They rot silently and the file keeps looking
  maintained.
- **Never pad to reach the target.** The target is a ceiling on ambition, not a quota. Twelve true
  lines beat forty padded ones, and the padding is what pushes the useful lines out of the budget.
- **Never write a rule from one incident.** Promote a pattern to a rule on the second occurrence, and
  keep the incident reference with it.
- **Never write an all-caps ban.** "NEVER TOUCH THE MIGRATIONS" tells an agent nothing actionable.
  Name the hazard, name the evidence, and name what to do instead.
- **Never write advice instead of facts.** A line that reads "you should run the tests before pushing"
  is what the agent already assumed. Name the command, or cut the line.

## Honest limits

Say these before a user infers the opposite.

- **A verified command is a resolved command, not a working one.** "Verified" means the script name,
  target, recipe or module exists where the line says it does. Nothing was executed. A script that
  resolves can still be broken.
- **The evidence in the repo can itself be wrong.** A stale comment, a dead workflow and an
  abandoned config are all primary sources, and a line derived faithfully from one is faithfully
  wrong. Evidence beats a guess. It does not beat reality.
- **The category has a published negative result.** An ETH Zurich study (arXiv 2602.11988) found that
  context files "do not generally improve task success rates, while increasing inference cost by over
  20% on average". It reports no success-rate figure, so none is quoted here. That finding is exactly
  why the output is deliberately sparse, and it is a reason to doubt this skill too.
- **The hook never rewrites anything.** It reports drift. Fixing is a separate, explicit run, and
  nothing gets corrected while you are not looking.
- **Bounded parsers leave real claims unverified.** YAML inheritance, computed build targets, and
  runners outside the resolver table such as `uv run`, `poetry run`, `mise` and `task` come back
  `unverified` rather than wrong. Coverage on a given repo is unknown until it is measured there.
- **Pointer loading is not uniform across agents.** Copilot's handling of a Markdown pointer across
  every feature, and whether Gemini loads `AGENTS.md` twice under a combined discovery setting, are
  both uncertain. Only Claude Code is documented as stripping block-level HTML comments, so the
  provenance header may be costing tokens in other readers.
- **Nothing here is a code review.** The file describes how the repo works. It does not say the repo
  works well.

## Cross-harness

The skill is Markdown, so it travels.

| Where | How |
| --- | --- |
| Claude Code | `claude plugin install contextify@10x`, then `/contextify` |
| Codex, Gemini CLI, Cursor, Copilot | `npx skills add Aboudjem/contextify -a <agent>` |
| Anything else | copy `skills/contextify/` into the directory your agent reads |

Three things change outside Claude Code, and each degrades honestly.

**The scripts still run.** `${CLAUDE_SKILL_DIR}` is a Claude Code variable. Everywhere else it means
the scripts directory next to this file. The scripts are POSIX `sh`, bash 3.2 safe, and python3
standard library only, so they need no install.

**The session-start hook is not shipped.** The plugin's one hook is a Claude Code `SessionStart`
entry, and it is not installed for any other harness. Install the opt-in equivalent for Codex,
Gemini, Cursor, a git `pre-commit` hook or a GitHub Action with
`bash "${CLAUDE_SKILL_DIR}/scripts/install_hooks.sh" [PATH]`, which shows a diff and asks before it
writes. The snippets are in `references/hooks-and-ci.md`.

**Questions become prompts.** `AskUserQuestion` may not exist in the host harness. Ask the three
`init` questions as plain text, wait once, and apply the documented default when the answer does not
come. Never let a missing question tool turn into a guess in the file.
