#!/usr/bin/env bash
# detect_repo.sh - deterministic, read-only fact sheet of a repository.
#
# Surfaces the files the run must READ; it never replaces reading them, and it never
# executes repository configuration. Nothing here writes, and nothing leaves the machine.
# Usage: detect_repo.sh [repo-path]   (defaults to the current directory)
# Portable: bash 3.2+, BSD and GNU coreutils. python3 is used when present, never required.
set -u

REPO="${1:-.}"
case "$REPO" in
  --help|-h)
    sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
    ;;
esac
[ -d "$REPO" ] || { echo "ERROR: not a directory: $REPO" >&2; exit 2; }
cd "$REPO" 2>/dev/null || { echo "ERROR: cannot cd $REPO" >&2; exit 2; }
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" || exit 2

have() { command -v "$1" >/dev/null 2>&1; }
exists() { [ -e "$1" ] && echo "  - $1"; }
section() { printf '\n## %s\n' "$1"; }

echo "# REPO FACT SHEET: $ROOT"

section "Git"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "  default branch:  $(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
  echo "  current branch:  $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  echo "  HEAD:            $(git rev-parse HEAD 2>/dev/null)"
  echo "  tracked files:   $(git ls-files 2>/dev/null | wc -l | tr -d ' ')"
  echo "  remotes:"; git remote -v 2>/dev/null | sed 's/^/    /' | sort -u
  echo "  recent commits:"; git log --oneline -10 2>/dev/null | sed 's/^/    /'
else
  echo "  (not a git repo; contextify refuses to write outside one)"
fi

section "contextify state"
for f in .contextify/stamp.json .contextify/evidence.json .contextify/journal.json \
         .contextify/mistakes.md; do
  exists "$f"
done
[ -d .contextify/draft ] && echo "  - .contextify/draft/ (dir)"

section "Existing context files (UPDATE mode if any are present)"
for f in AGENTS.md AGENT.md CLAUDE.md CLAUDE.local.md GEMINI.md .cursorrules \
         .cursor/rules/contextify.mdc .github/copilot-instructions.md .windsurfrules \
         .clinerules AGENTS.override.md; do
  exists "$f"
done
git ls-files 2>/dev/null | grep -E '(^|/)AGENTS(\.override)?\.md$' | grep -v '^AGENTS.md$' \
  | sed 's/^/  nested: /'

section "Language / package-manager manifests and lockfiles"
for f in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb bun.lock \
         pyproject.toml poetry.lock uv.lock requirements.txt Pipfile setup.py setup.cfg \
         go.mod go.work go.sum Cargo.toml Cargo.lock pom.xml build.gradle build.gradle.kts \
         settings.gradle settings.gradle.kts Gemfile Gemfile.lock composer.json mix.exs \
         pubspec.yaml Package.swift tsconfig.json; do
  exists "$f"
done

section "Runtime version pins"
for f in .nvmrc .node-version .python-version .tool-versions rust-toolchain; do
  [ -f "$f" ] && echo "  $f: $(tr '\n' ' ' < "$f")"
done

section "Declared commands (READ these files for the exact bodies)"
if [ -f package.json ]; then
  echo "  package.json scripts:"
  if have python3; then
    python3 - <<'PY'
import json
try:
    d = json.load(open("package.json"))
except Exception as e:
    print("    (parse error: %s)" % e.__class__.__name__)
else:
    for k, v in (d.get("scripts") or {}).items():
        print("    %-20s = %s" % (k, v))
    if d.get("packageManager"):
        print("    [packageManager] = %s" % d["packageManager"])
    if d.get("workspaces"):
        print("    [workspaces] = %s" % json.dumps(d["workspaces"]))
    if d.get("engines"):
        print("    [engines] = %s" % json.dumps(d["engines"]))
PY
  else
    sed -n '/"scripts"[[:space:]]*:/,/}/p' package.json | sed 's/^/    /'
  fi
fi
for mk in Makefile makefile GNUmakefile; do
  [ -f "$mk" ] || continue
  echo "  $mk targets:"
  grep -E '^[a-zA-Z0-9_][a-zA-Z0-9_.-]*:' "$mk" 2>/dev/null | sed 's/:.*//' \
    | sort -u | sed 's/^/    /' | head -40
  break
done
for jf in justfile Justfile .justfile; do
  [ -f "$jf" ] || continue
  echo "  $jf recipes:"
  grep -E '^[a-zA-Z0-9_][a-zA-Z0-9_-]*( [^:]*)?:' "$jf" 2>/dev/null | sed 's/:.*//' \
    | sed 's/^/    /' | head -40
  break
done
[ -f pyproject.toml ] && { echo "  pyproject [project.scripts]:";
  sed -n '/^\[project.scripts\]/,/^\[/p' pyproject.toml | grep '=' | sed 's/^/    /'; }
[ -f Cargo.toml ] && { echo "  Cargo bins:"; ls src/bin/*.rs 2>/dev/null | sed 's/^/    /';
  [ -f src/main.rs ] && echo "    src/main.rs"; }

section "Workspace / monorepo configuration"
for f in pnpm-workspace.yaml lerna.json nx.json turbo.json go.work; do exists "$f"; done
ls -d packages/*/ apps/*/ 2>/dev/null | head -20 | sed 's/^/  - /'

section "CI / CD"
ls .github/workflows/*.y*ml 2>/dev/null | sed 's/^/  - /'
for f in .gitlab-ci.yml .circleci/config.yml azure-pipelines.yml Jenkinsfile .drone.yml; do
  exists "$f"
done

section "Containers and deploy configuration"
for f in Dockerfile docker-compose.yml docker-compose.yaml compose.yml compose.yaml \
         vercel.json netlify.toml fly.toml render.yaml Procfile app.yaml serverless.yml \
         amplify.yml apprunner.yaml cdk.json Chart.yaml skaffold.yaml; do
  exists "$f"
done
git ls-files 2>/dev/null | grep -E '(^|/)Dockerfile$' | grep -v '^Dockerfile$' \
  | sed 's/^/  nested: /'

section "Environment contract and leak risk"
for f in .env.example .env.sample .env.template .env.dist; do exists "$f"; done
echo "  variable names in .env.example (names only, values are never read):"
[ -f .env.example ] && grep -E '^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*=' \
  .env.example 2>/dev/null | sed 's/=.*//' | sed 's/^[[:space:]]*//' | sed 's/^/    /'
echo "  tracked .env files that are not examples (inspect before writing anything):"
git ls-files 2>/dev/null | grep -E '(^|/)\.env($|\.)' \
  | grep -vE '\.(example|sample|template|dist)$' | sed 's/^/    /'

section "Test signals"
for f in jest.config.js jest.config.ts vitest.config.ts pytest.ini tox.ini noxfile.py \
         playwright.config.ts cypress.config.js phpunit.xml; do exists "$f"; done
git ls-files 2>/dev/null \
  | grep -cE '(\.test\.|\.spec\.|_test\.go$|(^|/)test_[^/]*\.py$)' \
  | sed 's/^/  test-like tracked files: /'

section "Documentation an agent may be told to read"
for f in README.md CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md CHANGELOG.md; do
  exists "$f"
done
[ -d docs ] && echo "  - docs/ (dir)"
ls -d adr ADR docs/adr docs/decisions 2>/dev/null | sed 's/^/  - /'

section "Size class inputs (D2)"
ELIGIBLE=$(git ls-files 2>/dev/null | grep -vE '^(\.contextify/|node_modules/|vendor/|dist/|build/)' | wc -l | tr -d ' ')
UNITS=$(git ls-files 2>/dev/null \
  | grep -E '(^|/)(package\.json|pyproject\.toml|Cargo\.toml|go\.mod|pom\.xml|build\.gradle(\.kts)?)$' \
  | wc -l | tr -d ' ')
echo "  eligible tracked files: $ELIGIBLE"
echo "  manifest-bearing directories: $UNITS"

echo ""
echo "# END FACT SHEET - now READ the surfaced files. Nothing above is a quotable claim"
echo "# until the file it came from has been opened."
