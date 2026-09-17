# Tiny greeting

This is a teaching fixture created for Contextify, not a real-repository dogfood run. Its three source files declare one command and no test target. The generated instructions keep those facts and omit empty architecture or workflow sections.

- [Full generated AGENTS.md](AGENTS.generated.md) and [Claude pointer](CLAUDE.generated.md)
- [Draft reviewed before writing](draft.md) and [line-to-source mapping](draft-evidence.tsv)
- Sources: [Makefile](source/Makefile), [hello.py](source/hello.py), [fixture README](source/README.md)
- [Evidence](evidence.json), [stamp](stamp.json) and [recorded command results](results.json)

The output files are saved under `.generated.md` names so they do not become active instructions for this repository. The isolated fixture had no commit, which explains `commit=none` in its provenance header.

To reproduce from the Contextify repository root:

```bash
fixture=$(mktemp -d)
cp -R examples/tiny/source "$fixture/repo"
git -C "$fixture/repo" init
git -C "$fixture/repo" add .
mkdir "$fixture/draft"
cp examples/tiny/draft.md "$fixture/draft/AGENTS.md"
cp examples/tiny/draft-evidence.tsv "$fixture/draft/evidence.tsv"
python3 skills/contextify/scripts/ctx_write.py --root "$fixture/repo" --draft "$fixture/draft" --targets claude,codex --dry-run
python3 skills/contextify/scripts/ctx_write.py --root "$fixture/repo" --draft "$fixture/draft" --targets claude,codex --generated-by codex --yes
sh skills/contextify/scripts/ctx-check "$fixture/repo"
```

Timestamps may differ. The final check should exit 0 with empty stdout. See `results.json` for the recorded run, including whether rerunning the writer changed any generated file.
