#!/bin/sh
# Replays the README sample from the files this example ships.
# Builds a throwaway Git repo from the Python service fixture, restores the files and the
# stamp that the 2026-11-17 run wrote, checks it is fresh, deletes the test-health target,
# then prints the drift notice. Writes nothing inside this repository.
# Usage: sh examples/python-service-0.3.0/replay.sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CHECK="$HERE/../../skills/contextify/scripts/ctx-check"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/contextify-replay.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

cp -R "$HERE/../python-service/source/." "$WORK/"
find "$WORK" -name __pycache__ -type d -prune -exec rm -rf {} +
cp "$HERE/AGENTS.generated.md" "$WORK/AGENTS.md"
cp "$HERE/CLAUDE.generated.md" "$WORK/CLAUDE.md"
printf '# START contextify\n.contextify/draft/\n.contextify/journal.json\n# END contextify\n' > "$WORK/.gitignore"
mkdir "$WORK/.contextify"
cp "$HERE/evidence.json" "$HERE/stamp.json" "$WORK/.contextify/"

cd "$WORK"
git init -q
git add -A
git -c commit.gpgsign=false commit -qm "replay" >/dev/null

fresh=$(sh "$CHECK")
if [ -n "$fresh" ]; then
  echo "replay: expected a fresh, silent check before the edit, got:" >&2
  echo "$fresh" >&2
  exit 1
fi
echo "Before the edit: ctx-check printed nothing (fresh)."

git apply "$HERE/makefile-change.diff"
echo "After deleting the test-health target:"
echo
sh "$CHECK"
