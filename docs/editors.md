# Install contextify in your editor

One Agent Skill: a `SKILL.md` with frontmatter, Markdown underneath, and `references/` and `scripts/`
directories beside it. No server or compiled binary. The scripts use Git, POSIX tools, Bash and Python 3.11 or newer. Claude Code
has a first-party path; every other agent installs the same directory through the skills CLI.

## Claude Code

```bash
claude plugin marketplace add Aboudjem/contextify
claude plugin install contextify@contextify-marketplace
```

Then run `/contextify init`, `/contextify update`, `/contextify check`, or `/contextify accept` in
your project, or describe the same intent in words, telling your agent how the repo works and asking
it to keep that current. The plugin registers no session-start hooks by default. Install the Git checks to report drift at commit and push, or select a session adapter explicitly. See [hooks and CI](hooks.md).

## Any other agent

```bash
npx skills add Aboudjem/contextify -a <agent>
```

Replace `<agent>` with a code below. Codes and default installation paths were checked against the [skills CLI agent registry](https://github.com/vercel-labs/skills/blob/main/src/agents.ts) on 2026-09-17. Environment overrides can change global paths; these are installation destinations, not proof that every host loads context files the same way.

| Agent | `-a` code | Project path | Global path | Context file it reads |
| --- | --- | --- | --- | --- |
| Claude Code | `claude-code` | `.claude/skills/` | `~/.claude/skills/` | `CLAUDE.md` |
| Cursor | `cursor` | `.agents/skills/` | `~/.cursor/skills/` | `AGENTS.md` natively, plus optional `.mdc` |
| Codex | `codex` | `.agents/skills/` | `~/.codex/skills/` | `AGENTS.md` |
| GitHub Copilot | `github-copilot` | `.agents/skills/` | `~/.copilot/skills/` | `AGENTS.md`, nearest-wins |
| Gemini CLI | `gemini-cli` | `.agents/skills/` | `~/.gemini/skills/` | `GEMINI.md`, or the `context.fileName` array |
| OpenCode | `opencode` | `.agents/skills/` | `~/.config/opencode/skills/` | uncertain |
| Windsurf | `windsurf` | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` | uncertain |
| Zed | `zed` | `.agents/skills/` | `~/.agents/skills/` | uncertain |
| Continue.dev | `continue` | `.continue/skills/` | `~/.continue/skills/` | uncertain |
| Kimi Code CLI | `kimi-code-cli` | `.agents/skills/` | `~/.agents/skills/` | uncertain |

So for Cursor, and for Codex:

```bash
npx skills add Aboudjem/contextify -a cursor
npx skills add Aboudjem/contextify -a codex
```

## Copy it in by hand

```bash
git clone https://github.com/Aboudjem/contextify
cp -R contextify/skills/contextify ~/.claude/skills/
```

Swap the destination for your agent's path from the table. Copy the whole directory, not just
`SKILL.md`: everything under `references/` and `scripts/` is loaded by relative path at run time.

## Context and hooks across editors

The default check schedule is the same for every editor: installed Git hooks run at commit and push. Session-start adapters for Claude, Codex, Gemini and Cursor are explicit choices. `install_hooks.sh --yes` writes Git hook files; `--activate` requests safe activation. See [hooks and CI](hooks.md).

No `AskUserQuestion` tool everywhere. `init` asks up to three questions on Claude Code; on an agent
without an interactive question tool, it falls back to its defaults: pointer files for Claude Code
plus whatever the repository's own configuration evidences, and no human-supplied fact beyond what a
file already supports.

The deterministic scripts share the same runtime requirements. `ctx-check`, `ctx_write.py`, `ctx_stamp.py` and `verify_claims.py`
need Git, shell tools and Python on the machine's `PATH`. They use no model, network request or third-party Python package. The installer CLI itself needs Node.js.

Supporting documents such as `docs/context/architecture.md` and `docs/context/workflows.md` are linked from `AGENTS.md` and read when relevant. They are not automatically imported through every editor pointer. See [supporting documents](supporting-docs.md).

## Next

- [Quickstart](quickstart.md), a first run end to end
- [Hooks and CI](hooks.md), the opt-in snippets
- [Honest limits](limits.md), what degrades outside Claude Code and what does not
