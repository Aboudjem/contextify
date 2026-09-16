# Verification

Purpose: the two-layer gate a draft must pass before it is trusted, a different agent re-deriving every claim, then the deterministic scripts.

## The gate: a different agent re-derives every claim

After the draft is written, a different agent, a subagent, not the one that wrote the draft, receives the rendered AGENTS.md and the repo path. For every command, path, port, branch, and deploy fact in the draft, it must open the primary source, never trust the writer's own notes, and answer one of three verdicts with the file:line that backs it:

- **CONFIRMED**: the primary source matches the claim.
- **CORRECTED**: the claim was wrong; the corrected value is given with its source.
- **UNVERIFIED**: no primary source could be found for the claim.

The writer fixes every CORRECTED claim and labels every UNVERIFIED one rather than deleting it outright, since an unconfirmable hazard can still be real. Source: this protocol generalizes the seed skill's `agent-context/references/verification.md` "Layer 2" re-derivation gate to contextify's own claim schema, DECISIONS.md D16.

## Then the deterministic scripts

Two scripts run after the agent gate, both zero-model and zero-network (SCRIPTS-SPEC.md):

- `verify_claims.py AGENTS.md`: extracts every quoted command and path, resolves each against the D16 resolver table, prints one line per claim (`OK|STALE|UNVERIFIED  file:line  text  (reason)`) and a summary. Exit must be 0; it exits 1 if any claim is `STALE`. `--budget` additionally fails on a line-count ceiling breach.
- `ctx-check`: the same freshness check the SessionStart hook runs. Exit 0 with empty stdout is required, meaning fresh, no drift. SCRIPTS-SPEC.md documents the full exit contract; this reference only asserts what a verification pass must see: silence.

## The claims list format

Each claim carries: `id`, `text` (the literal quoted command or path), `location` (`file`, `line`), `cwd`, `resolver` (for example `npm-run`, `tracked-file`), `target` (what it resolved to), `evidenceRefs` (keys into `.contextify/evidence.json`), and `status` (`verified` or `unverified`). This is the same shape `.contextify/stamp.json` persists under `claims`. Source: DECISIONS.md D14.

## What "verified" means, precisely

A verified command means its declaration or target resolves, for example a script name exists in `package.json#scripts`, or a Makefile target exists with that literal name. It does not mean the command was executed, and it does not mean it currently succeeds. Do not let "verified" imply "passing" anywhere in generated prose. Source: DECISIONS.md D16.

## Three hallucinations to hunt first

The most common ways a draft goes wrong, worth checking even when the mechanical verifier is clean:

1. **An invented test script**, typed from habit when the actual script has a different name, or does not exist at all. The correct line in that case is an explicit "no test runner configured," never a fabricated one.
2. **A wrong branch model**, stated from the branch's name rather than confirmed from CI or IaC. A branch called `prod` is not proof it deploys anywhere; a branch called `main` is not proof it is the default. Confirm the trigger, not the name.
3. **A deploy step inferred from a branch name or a platform config's mere presence.** A deploy config file proves deployment exists; it does not prove the trigger is automatic, and it does not by itself justify an Ask-first or Never label. That judgment needs the actual trigger or a recorded policy.

Source: DECISIONS.md D4 (the deploy-approval caveat) and the seed skill's `agent-context/references/verification.md` self-check list, which asks whether the prod branch and deploy trigger were confirmed from CI, IaC, or a live read, not from the branch name.
