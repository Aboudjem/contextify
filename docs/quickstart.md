# Quickstart

Contextify writes a short `AGENTS.md`, pointers for selected editors, and evidence records. It can also add focused architecture or workflow documents when the repository needs them.

## 1. Install

For Claude Code:

```bash
claude plugin marketplace add Aboudjem/contextify
claude plugin install contextify@contextify-marketplace
```

For Codex:

```bash
npx skills add Aboudjem/contextify -a codex
```

## 2. Run it

Run `/contextify init` in Claude Code. In another agent, ask the installed Contextify skill to initialize the current repository.

The agent reads repository evidence, reviews existing documentation and drafts concise instructions. It reuses accurate architecture/workflow docs first. When useful information needs its own page, it proposes `docs/context/architecture.md` or `docs/context/workflows.md`, each capped at 120 lines. `AGENTS.md` links to them for tasks that need more detail.

## 3. Review the proposed diff

Use `init --dry-run` to see proposed files and their line/byte costs without applying them. Check that commands, component relationships and workflow steps are supported by files actually read. A resolved command has not necessarily been executed. Another agent reviews the draft before the writer applies it.

Updates preserve human text outside managed blocks. A conflicting edit inside a managed block requires deliberate resolution. `--yes` skips routine questions; it cannot bypass hard ceilings or silently overwrite conflicts.

## 4. Commit the context

Commit `AGENTS.md`, selected editor pointers, any supporting documents, `.contextify/stamp.json` and `.contextify/evidence.json`. The committed records let each clone check the same reviewed instructions. Temporary drafts are ignored.

## 5. Install Git checks

No session-start hook is registered by default. From a Contextify checkout, preview the Git hook files for your project, then apply and activate them:

```bash
bash skills/contextify/scripts/install_hooks.sh /path/to/repo
bash skills/contextify/scripts/install_hooks.sh --yes --activate /path/to/repo
```

The default creates `.githooks/pre-commit` and `.githooks/pre-push`. `--yes` writes the files; `--activate` also requests safe repository-local activation. Activation refuses to replace an existing custom/global hooks path, hide executable default hooks, or change shared configuration from a linked worktree. Use the existing hook manager's integration mechanism in those cases. See [hooks and CI](hooks.md).

## 6. Check at commit or push

When the context is fresh, the Git checks print nothing. If evidence changes, they report the drift. They are advisory by default, so they do not block your commit or push. Strict checking is optional.

The checks inspect the **current working tree**, not the staged index or the exact commits being pushed. They never rewrite context, refresh metadata or stage files.

You can also ask the agent to run `/contextify check` at any time.

## 7. Update or accept

Run `/contextify update` when instructions need revising. Run `/contextify accept` only after confirming that the instructions remain correct and the evidence alone changed. It refreshes metadata while leaving context files byte-identical. A missing or renamed source needs its provenance mapping corrected; accepting cannot invent a replacement source or adopt edited managed prose.

## Next

[Supporting documents](supporting-docs.md) · [Editor setup](editors.md) · [Hooks and CI](hooks.md) · [Limits](limits.md)
