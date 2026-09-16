# Security Policy

`contextify` is a Claude Code plugin that writes context files for a repo: `AGENTS.md`, plus
thin pointers (`CLAUDE.md`, `GEMINI.md`, `.cursor/rules/contextify.mdc`,
`.github/copilot-instructions.md`). It is skill-only: Markdown plus zero-dependency scripts, no
npm package, no MCP server, no service of its own. This file says how contextify is built to be
safe, and how to report a hole in contextify itself.

## How contextify is built to be safe

- **No network calls.** The skill and its scripts never make an outbound request. Optional
  live cloud or deploy reads are read-only, opt-in, and skipped entirely when credentials are
  absent.
- **No telemetry.** Nothing about your repo, your commands, or your usage is sent anywhere.
- **Reads broadly, writes narrowly.** contextify reads the repo to gather evidence. It writes
  only `AGENTS.md`, the pointer files listed above, and its own state under `.contextify/`
  (`stamp.json`, `evidence.json`, an optional bounded `mistakes.md`).
- **Never writes a secret value.** contextify reads `.env.example` **key names only**. It never
  reads `.env`, never reads a secret's value, and never writes a value into `AGENTS.md`, a
  pointer file, the stamp, or the evidence file.
- **Atomic writes.** Every file contextify writes goes to a tempfile first, then an atomic
  rename onto the target path. A crash mid-write leaves the original file intact, never a
  half-written one.
- **Refuses paths outside the repo root.** Every path contextify reads or writes is resolved
  and checked against the repo root before use. A path that resolves outside it is refused.
- **Refuses to follow symlinks out of the repo.** A symlink that resolves outside the repo root
  is not followed for reads and is never a write target.
- **The hook never runs a model.** `ctx-check`, the SessionStart hook, is a deterministic
  script: a POSIX sh fast path over `git ls-files -s`, falling back to a python3 stdlib
  normalizer on mismatch. It never invokes Claude or any other model.
- **The hook never rewrites a file.** `ctx-check` only compares evidence against the committed
  stamp and prints a notice when they disagree. It never edits `AGENTS.md` or any other file.
- **The hook never blocks a session.** It prints nothing when fresh, a short notice when
  evidence moved, and it never exits 2. A hook that hangs or blocks the session is a bug.
- **The hook has a 5 second timeout.** If it has not finished by then, it is killed and the
  session continues.
- **The stamp holds digests only.** `.contextify/stamp.json` stores content digests of the
  evidence it checked, never file contents.

## What counts as a security issue in contextify

Report any of the following:

- A path by which contextify **writes a secret's value** into `AGENTS.md`, a pointer file, the
  stamp, or the evidence file, rather than a key name.
- A way that **content contextify reads could steer it into running a command** it was not
  asked to run.
- A path by which contextify **writes outside the repo root**, including through a symlink.
- A way the **hook blocks or hangs a session**, including exceeding its timeout without being
  killed.
- A way the **drift check could exfiltrate anything**: evidence, file contents, or repo
  metadata, off the machine.

## How to report a vulnerability

**Please do not open a public issue for a security problem.**

Report privately, either way:

- GitHub private vulnerability reporting on the `Aboudjem/contextify` repo, or
- Email **boudjemaa.adam@gmail.com** with a description of the issue, its impact, and steps to
  reproduce.

You will get an acknowledgement within 72 hours. There is no bounty programme.

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | yes       |

## What is not a contextify vulnerability

- **A wrong fact in a generated file that traces to a wrong fact in the repo.** contextify
  writes what the evidence says. If the evidence itself is wrong or stale, that is a bug report
  against the check that read it, not a security issue.
- **A stale file when the hook was not installed.** `ctx-check` only runs, and only catches
  drift, when the SessionStart hook is actually wired up. A file going stale with no hook
  installed is expected, not a vulnerability.
