# Python service

This standard-library HTTP service is a teaching fixture created for Contextify. It is not a production application and does not count as real-repository dogfood. The source has a server entry point, request handler, health payload and unit tests, so the instructions can explain their relationships with specific paths.

- [Full generated AGENTS.md](AGENTS.generated.md) and [Claude pointer](CLAUDE.generated.md)
- [Draft reviewed before writing](draft.md) and [line-to-source mapping](draft-evidence.tsv)
- Sources: [Makefile](source/Makefile), [project metadata](source/pyproject.toml), [server](source/service/server.py), [handler](source/service/handler.py), [health payload](source/service/health.py) and [fixture README](source/README.md)
- Tests: [health response](source/tests/test_health.py), [bind settings](source/tests/test_config.py)
- [Evidence](evidence.json), [stamp](stamp.json) and [recorded command results](results.json)

The independent review checked the draft against these source files. The writer then checked supported commands and paths. Any test execution recorded in `results.json` is a separate step; resolving a command does not execute it.

The output files use `.generated.md` names so they do not become active instructions for Contextify. The isolated fixture had no commit, which explains `commit=none` in its provenance header.

To reproduce from the Contextify repository root:

```bash
fixture=$(mktemp -d)
cp -R examples/python-service/source "$fixture/repo"
git -C "$fixture/repo" init
git -C "$fixture/repo" add .
mkdir "$fixture/draft"
cp examples/python-service/draft.md "$fixture/draft/AGENTS.md"
cp examples/python-service/draft-evidence.tsv "$fixture/draft/evidence.tsv"
python3 skills/contextify/scripts/ctx_write.py --root "$fixture/repo" --draft "$fixture/draft" --targets claude,codex --dry-run
python3 skills/contextify/scripts/ctx_write.py --root "$fixture/repo" --draft "$fixture/draft" --targets claude,codex --generated-by codex --yes
sh skills/contextify/scripts/ctx-check "$fixture/repo"
make -C "$fixture/repo" test
```

Timestamps may differ. The freshness check should exit 0 with empty stdout. `make test` runs the fixture's tests separately. No listening service is needed to run them.
