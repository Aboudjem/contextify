# Security Policy

Contextify is an Agent Skill and Claude Code plugin: Markdown plus standard-library scripts, with no service or MCP server. It writes repository instructions, optional supporting documents and evidence records.

## Security boundaries

- **Local deterministic scripts.** Discovery, writing and checking make no network requests. Your coding agent handles generation under its own data policy. Installation and optional CI fetch code from GitHub.
- **Narrow output paths.** The writer produces `AGENTS.md`, selected editor pointers, optional `docs/context/architecture.md` and `docs/context/workflows.md`, `.contextify/` state and its draft-ignore entries in `.gitignore`. The hook installer separately writes the selected hook configurations and can activate repository-local Git hooks explicitly.
- **Evidence can contain repository information.** Stamp and evidence files include paths, quoted commands, provenance locations and normalized values as well as digests. Review them before publishing. They are not anonymized telemetry or a secret scanner's output.
- **Secret handling.** The environment-example normalizer records key names rather than values. Drafts and source mappings still require review: do not cite private credentials or copy secret values into context. A model-generated draft is not safe merely because a source file exists.
- **Managed writes.** Contextify preserves human text outside managed blocks, refuses conflicts inside recorded blocks and checks destination containment. Each file is replaced atomically; the recovery journal handles interrupted multi-file updates. This is not a filesystem-wide transaction.
- **Read-only checks.** Git and host-session checks do not update context, metadata or the Git index. The optional CI mode can append a job summary. Checks never execute quoted repository commands to validate them.
- **Explicit hook policy.** Git hooks are advisory by default. Strict mode deliberately blocks drift, missing stamps and failures. No session hooks are registered by default; opt-in host adapters have host-specific timeout and error behavior.
- **Existing hooks survive installation.** Safe activation refuses to mask custom/global hook paths or executable default hooks. It does not alter global configuration and refuses activation from linked worktrees where shared configuration could be affected.

## Report a vulnerability

Please do not open a public issue for a security problem. Use GitHub private vulnerability reporting for `Aboudjem/contextify`, or email **boudjemaa.adam@gmail.com** with the affected revision, impact and reproduction steps.

Relevant reports include writes outside the selected scope, symlink escapes, command execution caused by repository text, check-time exfiltration, unintended overwrites of human content or hooks, and secret values being copied into generated evidence by a normalizer.

There is no bounty programme.

## Supported versions

Security reports are welcome for the latest published release. The current development line is 0.2.x; consult [GitHub releases](https://github.com/Aboudjem/contextify/releases) for published versions rather than assuming a development branch has shipped.

## Expected limitations

A false source can support a false explanation. A fresh check does not establish semantic correctness, successful tests or secure repository code. A repository with no active hook will not be checked automatically. Intentional strict-mode refusal to commit or push is expected behavior.

See [limits](docs/limits.md) and [hook setup](docs/hooks.md).
