#!/usr/bin/env bash
# install_hooks.sh - write the opt-in Codex / Gemini / Cursor / git / GitHub snippets.
#
# The plugin itself ships exactly one hook, the Claude Code SessionStart entry in
# hooks/hooks.json (D19). Everything else is opt-in and lives in the target repository,
# because four agents means four contracts that do not agree with each other.
#
# Every snippet calls this installation's ctx-check by absolute path, printed below.
# Idempotent: a second run with the same arguments changes nothing.
#
# Usage: install_hooks.sh [--yes] [--targets codex,gemini,cursor,git,github] [PATH]
# Exit: 0 written or already current, 2 bad arguments, 3 declined.
set -u

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
CTX="$SELF_DIR/ctx-check"

YES=0
TARGETS="codex,gemini,cursor,git,github"
REPO="."
while [ $# -gt 0 ]; do
  case "$1" in
    --yes|-y) YES=1 ;;
    --targets) shift; TARGETS="${1:-}" ;;
    --targets=*) TARGETS="${1#--targets=}" ;;
    --help|-h)
      sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    -*) echo "install_hooks.sh: unknown flag $1" >&2; exit 2 ;;
    *) REPO="$1" ;;
  esac
  shift
done

[ -d "$REPO" ] || { echo "install_hooks.sh: not a directory: $REPO" >&2; exit 2; }
cd "$REPO" || exit 2
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" || exit 2

echo "contextify install-hooks"
echo ""
echo "Scope    $ROOT"
echo "Runner   $CTX"
echo "Targets  $TARGETS"
echo ""

wants() {
  case ",$TARGETS," in
    *",$1,"*) return 0 ;;
    *) return 1 ;;
  esac
}

# write_file <path> <tmpfile>: show the diff, ask unless --yes, then replace atomically.
# A file that already holds exactly these bytes is left alone, mtime included.
write_file() {
  target="$1"
  staged="$2"
  if [ -f "$target" ] && cmp -s "$target" "$staged"; then
    echo "  unchanged  $target"
    rm -f "$staged"
    return 0
  fi
  if [ -f "$target" ] && grep -q "$CTX" "$target" 2>/dev/null; then
    echo "  unchanged  $target (already calls this ctx-check)"
    rm -f "$staged"
    return 0
  fi
  if [ -f "$target" ]; then
    echo "  CONFLICT   $target already exists and does not call this ctx-check."
    echo "             Merge this by hand; contextify will not rewrite it:"
    sed 's/^/             /' "$staged"
    rm -f "$staged"
    return 0
  fi
  if [ "$YES" -ne 1 ]; then
    echo "  would write $target:"
    sed 's/^/    /' "$staged"
    rm -f "$staged"
    return 0
  fi
  mkdir -p "$(dirname "$target")"
  mv "$staged" "$target"
  echo "  written    $target"
}

if wants codex; then
  TMP="$(mktemp)"
  cat > "$TMP" <<JSON
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "sh \"$CTX\" --hook codex"
          }
        ]
      }
    ]
  }
}
JSON
  write_file ".codex/hooks.json" "$TMP"
fi

if wants gemini; then
  TMP="$(mktemp)"
  cat > "$TMP" <<JSON
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "name": "contextify-check",
            "command": "sh \"$CTX\" --hook gemini",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
JSON
  write_file ".gemini/settings.json" "$TMP"
  echo "             Gemini reads GEMINI.md by default. To have it read AGENTS.md too,"
  echo "             add this yourself; contextify never edits it silently:"
  echo '             {"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}}'
fi

if wants cursor; then
  TMP="$(mktemp)"
  cat > "$TMP" <<JSON
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      {
        "command": "sh \"$CTX\" --hook cursor"
      }
    ]
  }
}
JSON
  write_file ".cursor/hooks.json" "$TMP"
fi

if wants git; then
  TMP="$(mktemp)"
  cat > "$TMP" <<HOOK
#!/bin/sh
# contextify pre-commit check. Advisory by default: it prints and lets the commit through.
# Change --ci to "--ci --strict" to make drift block the commit.
sh "$CTX" --ci
exit 0
HOOK
  write_file ".githooks/pre-commit" "$TMP"
  [ -f .githooks/pre-commit ] && chmod +x .githooks/pre-commit
  echo "             Enable it with: git config core.hooksPath .githooks"
fi

if wants github; then
  TMP="$(mktemp)"
  cat > "$TMP" <<YML
name: contextify check

on:
  pull_request:
  push:
    branches: [main]

jobs:
  contextify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check that AGENTS.md still matches the repository
        run: sh "$CTX" --ci --strict
YML
  write_file ".github/workflows/contextify-check.yml" "$TMP"
  echo "             The workflow calls this machine's plugin path. On a runner, install"
  echo "             the plugin first, or vendor ctx-check into the repository."
fi

echo ""
echo "Next     sh \"$CTX\" --ci"
exit 0
