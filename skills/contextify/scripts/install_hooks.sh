#!/usr/bin/env bash
# Opt-in hook installation. Without --yes, print a proposal and change nothing.
# Usage: install_hooks.sh [--yes] [--targets codex,gemini,cursor,git,github] [PATH]
set -eu
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 - "$SELF_DIR/ctx-check" "$@" <<'PY'
import difflib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

runner, *args = sys.argv[1:]
yes = False
targets = 'codex,gemini,cursor,git,github'
repo = '.'
i = 0
while i < len(args):
    arg = args[i]
    if arg in ('--help', '-h'):
        print('Usage: install_hooks.sh [--yes] [--targets codex,gemini,cursor,git,github] [PATH]')
        sys.exit(0)
    if arg in ('--yes', '-y'):
        yes = True
    elif arg == '--targets':
        i += 1
        if i == len(args):
            sys.exit('install_hooks.sh: --targets requires a value')
        targets = args[i]
    elif arg.startswith('--targets='):
        targets = arg.split('=', 1)[1]
    elif arg.startswith('-'):
        sys.exit('install_hooks.sh: unknown flag ' + arg)
    else:
        repo = arg
    i += 1
selected = set(targets.split(','))
if selected - {'codex', 'gemini', 'cursor', 'git', 'github'}:
    sys.exit('install_hooks.sh: unknown target')
root = Path(repo).resolve()
if not root.is_dir():
    sys.exit('install_hooks.sh: target is not a directory')
git = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
if git.returncode == 0:
    root = Path(git.stdout.strip()).resolve()

def safe(rel):
    path = root / rel
    if not path.resolve().is_relative_to(root):
        raise ValueError('destination escapes repository: ' + rel)
    if path.is_symlink():
        raise ValueError('destination is a symlink: ' + rel)
    return path

command = 'sh ' + shlex.quote(runner)
plans = []
def json_hook(rel, event, entry, extras=None):
    path = safe(rel)
    old = path.read_text() if path.exists() else None
    value = json.loads(old) if old is not None else dict(extras or {})
    if not isinstance(value, dict):
        raise ValueError(rel + ' must contain a JSON object')
    for key, default in (extras or {}).items():
        if key in value and (type(value[key]) is not type(default) or value[key] != default):
            raise ValueError(rel + ' has an unsupported ' + key)
        value.setdefault(key, default)
    hooks = value.setdefault('hooks', {})
    if not isinstance(hooks, dict):
        raise ValueError(rel + ' hooks must be an object')
    entries = hooks.setdefault(event, [])
    if not isinstance(entries, list):
        raise ValueError(rel + ' event must be a list')
    if entry not in entries:
        entries.append(entry)
    new = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    # Preserve a human file byte-for-byte when the desired entry already exists.
    if old is not None and json.loads(old) == value:
        new = old
    plans.append((rel, old, new, False))

try:
    if 'codex' in selected:
        json_hook('.codex/hooks.json', 'SessionStart', {'hooks': [{'type': 'command', 'command': command + ' --hook codex'}]})
    if 'gemini' in selected:
        json_hook('.gemini/settings.json', 'SessionStart', {'matcher': '*', 'hooks': [{'type': 'command', 'name': 'contextify-check', 'command': command + ' --hook gemini', 'timeout': 5000}]})
    if 'cursor' in selected:
        json_hook('.cursor/hooks.json', 'sessionStart', {'command': command + ' --hook cursor'}, {'version': 1})
    if 'git' in selected:
        rel = '.githooks/pre-commit'
        path = safe(rel)
        old = path.read_text() if path.exists() else None
        new = '#!/bin/sh\n# contextify: advisory by default; add --strict to block on drift.\nexec ' + command + ' --ci\n'
        plans.append((rel, old, new, True))
    if 'github' in selected:
        rel = '.github/workflows/contextify-check.yml'
        path = safe(rel)
        old = path.read_text() if path.exists() else None
        new = '''name: contextify check
on: [push, pull_request]
permissions:
  contents: read
jobs:
  contextify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Fetch released contextify
        run: git clone --depth 1 --branch v0.1.0 https://github.com/Aboudjem/contextify "$RUNNER_TEMP/contextify"
      - name: Check repository context (advisory; add --strict to enforce)
        run: sh "$RUNNER_TEMP/contextify/skills/contextify/scripts/ctx-check" --ci
'''
        plans.append((rel, old, new, False))
    # Preflight the complete proposal, including conflicts, before the first write.
    for rel, old, new, executable in plans:
        if old is not None and old != new and not rel.endswith('.json'):
            raise ValueError('existing file needs a manual merge: ' + rel)
        safe(rel)
    print('contextify install-hooks\n\nScope    ' + str(root) + '\nRunner   ' + runner)
    for rel, old, new, executable in plans:
        if old == new:
            print('unchanged ' + rel)
            continue
        print(''.join(difflib.unified_diff((old or '').splitlines(True), new.splitlines(True), fromfile='a/' + rel, tofile='b/' + rel)), end='')
    if yes:
        for rel, old, new, executable in plans:
            if old == new:
                continue
            path = safe(rel)
            current = path.read_text() if path.exists() else None
            if current != old:
                raise ValueError('file changed during preparation: ' + rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            safe(rel)
            fd, temp = tempfile.mkstemp(prefix='.contextify-', dir=path.parent)
            try:
                with os.fdopen(fd, 'w') as stream:
                    stream.write(new)
                os.chmod(temp, 0o755 if executable else (path.stat().st_mode & 0o777 if path.exists() else 0o644))
                safe(rel)
                os.replace(temp, path)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
            print('written ' + rel)
    else:
        print('Proposal only; use --yes to apply.')
    if 'git' in selected:
        print('Enable git hook: git config core.hooksPath .githooks')
    if 'gemini' in selected:
        print('Optional Gemini settings, not applied: {"context":{"fileName":["AGENTS.md","GEMINI.md"]}}')
except (ValueError, OSError, TypeError) as exc:
    sys.exit('install_hooks.sh: refused: ' + str(exc))
PY
