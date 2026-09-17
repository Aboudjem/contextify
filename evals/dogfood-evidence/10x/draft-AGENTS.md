# 10x marketplace
## Commands
- Test from the repository root: `npm test`.
- Validate the marketplace structure: `npm run validate`.
- Check upstream version pins: `npm run sync:check`.
## Architecture
- `scripts/sync-plugins.mjs` reads `.claude-plugin/marketplace.json` and updates its version pins only in write mode.
## Boundaries
- Keep the marketplace manifest free of a top-level version and metadata keywords; `scripts/validate-marketplace.mjs` rejects both.
## Read when relevant
- `docs/SYNC.md` explains the version-pin synchronization workflow.
