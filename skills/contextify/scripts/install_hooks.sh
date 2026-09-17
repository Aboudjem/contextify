#!/usr/bin/env bash
# Opt-in hook installation. Without --yes, print a proposal and change nothing.
# Usage: install_hooks.sh [--yes] [--activate] [--strict] [--targets git,claude,codex,gemini,cursor,github] [PATH]
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
targets = 'git'
activate = False
strict = False
repo = '.'
i = 0
while i < len(args):
    arg = args[i]
    if arg in ('--help', '-h'):
        print('Usage: install_hooks.sh [--yes] [--activate] [--strict] [--targets git,claude,codex,gemini,cursor,github] [PATH]')
        sys.exit(0)
    if arg in ('--yes', '-y'):
        yes = True
    elif arg == '--activate':
        activate = True
    elif arg == '--strict':
        strict = True
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
if selected - {'claude', 'codex', 'gemini', 'cursor', 'git', 'github'}:
    sys.exit('install_hooks.sh: unknown target')
if (activate or strict) and 'git' not in selected:
    sys.exit('install_hooks.sh: --activate and --strict require the git target')
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
    for ancestor in [path, *path.parents]:
        if ancestor == root:
            break
        if ancestor.is_symlink():
            raise ValueError('destination contains a symlink: ' + rel)
    return path

def git_run(*args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)

def git_value(*args):
    result = git_run(*args)
    if result.returncode not in (0, 1):
        raise ValueError('cannot inspect Git configuration: ' + result.stderr.strip())
    return result.stdout.strip() if result.returncode == 0 else None

def hooks_are_active():
    if git.returncode != 0:
        return False
    value = git_value('config', '--path', '--get', 'core.hooksPath')
    return value is not None and (root / value).resolve() == (root / '.githooks').resolve()

def activation_preflight():
    if git.returncode != 0:
        raise ValueError('--activate requires a Git repository')
    gitdir = Path(git_run('rev-parse', '--absolute-git-dir').stdout.strip()).resolve()
    if (gitdir / 'config').is_symlink():
        raise ValueError('--activate refuses a symlinked repository config; integrate hooks manually')
    common = Path(git_run('rev-parse', '--git-common-dir').stdout.strip())
    common = (root / common).resolve()
    if gitdir != common:
        raise ValueError('--activate is unsupported in linked worktrees; integrate hooks manually')
    effective = git_value('config', '--get', 'core.hooksPath')
    local = git_value('config', '--local', '--get', 'core.hooksPath')
    if effective is not None:
        if effective != '.githooks' or local != '.githooks':
            raise ValueError('existing effective core.hooksPath would be replaced; integrate Contextify into your existing hooks manually')
        # Inherited global/system paths must not be silently masked either.
        origins = git_run('config', '--show-origin', '--get-all', 'core.hooksPath')
        expected = 'file:' + str(gitdir / 'config')
        for line in origins.stdout.splitlines():
            origin = line.split('\t', 1)[0]
            if origin != expected and origin != 'file:.git/config':
                raise ValueError('inherited core.hooksPath exists; integrate Contextify into your existing hooks manually')
    else:
        hooksdir = gitdir / 'hooks'
        active = sorted(p.name for p in hooksdir.iterdir() if p.is_file() and not p.name.endswith('.sample') and os.access(p, os.X_OK)) if hooksdir.exists() else []
        if active:
            raise ValueError('activation would mask existing .git/hooks: ' + ', '.join(active) + '; integrate manually')
    return effective == '.githooks'

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
    active = activation_preflight() if activate else hooks_are_active()
    if 'claude' in selected:
        json_hook('.claude/settings.json', 'SessionStart', {'matcher': 'startup|resume|clear', 'hooks': [{'type': 'command', 'command': command + ' --hook claude', 'timeout': 5}]})
    if 'codex' in selected:
        json_hook('.codex/hooks.json', 'SessionStart', {'hooks': [{'type': 'command', 'command': command + ' --hook codex'}]})
    if 'gemini' in selected:
        json_hook('.gemini/settings.json', 'SessionStart', {'matcher': '*', 'hooks': [{'type': 'command', 'name': 'contextify-check', 'command': command + ' --hook gemini', 'timeout': 5000}]})
    if 'cursor' in selected:
        json_hook('.cursor/hooks.json', 'sessionStart', {'command': command + ' --hook cursor'}, {'version': 1})
    if 'git' in selected:
        # Git pre-push owns stdin; the checker must not read it.
        new = '#!/bin/sh\n# contextify: checks the current working tree, not the index or pushed refs.\n'
        if strict:
            new += 'exec ' + command + ' --git --strict\n'
        else:
            new += command + ' --git\nstatus=$?\nif [ "$status" -ne 0 ]; then\n  echo "contextify: advisory check could not complete (exit $status); run /contextify check" >&2\nfi\nexit 0\n'
        for rel in ('.githooks/pre-commit', '.githooks/pre-push'):
            path = safe(rel)
            old = path.read_text() if path.exists() else None
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
        run: git clone --depth 1 --branch v0.2.0 https://github.com/Aboudjem/contextify "$RUNNER_TEMP/contextify"
      - name: Check repository context (advisory; add --strict to enforce)
        run: sh "$RUNNER_TEMP/contextify/skills/contextify/scripts/ctx-check" --ci
'''
        plans.append((rel, old, new, False))
    # Preflight the complete proposal, including conflicts, before the first write.
    for rel, old, new, executable in plans:
        if old is not None and old != new and not rel.endswith('.json'):
            raise ValueError('existing file needs a manual merge: ' + rel)
        path = safe(rel)
        if old == new and executable and not os.access(path, os.X_OK):
            raise ValueError('existing hook is not executable; enable it manually: ' + rel)
    print('contextify install-hooks\n\nScope    ' + str(root) + '\nRunner   ' + runner)
    for rel, old, new, executable in plans:
        if old == new:
            print('unchanged ' + rel)
            continue
        print(''.join(difflib.unified_diff((old or '').splitlines(True), new.splitlines(True), fromfile='a/' + rel, tofile='b/' + rel)), end='')
    if yes:
        # Recheck activation constraints immediately before any mutation.
        if activate:
            active = activation_preflight()
        for rel, old, new, executable in plans:
            if old == new:
                if executable and not os.access(safe(rel), os.X_OK):
                    raise ValueError('existing hook is not executable; enable it manually: ' + rel)
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
        if activate and yes and not active:
            changed = git_run('config', '--local', 'core.hooksPath', '.githooks')
            if changed.returncode != 0:
                raise ValueError('hook files installed but inactive: activation failed; inspect git config --show-origin --get core.hooksPath and integrate manually: ' + changed.stderr.strip())
            active = True
        if active:
            print('Git hooks are active: effective core.hooksPath resolves to .githooks.')
        elif activate:
            print('Proposal: set repository-local core.hooksPath=.githooks; use --yes --activate to apply.')
        else:
            print('Git hook files are inactive; use --yes --activate to activate safely, or integrate with existing hooks manually.')
    if 'gemini' in selected:
        print('Optional Gemini settings, not applied: {"context":{"fileName":["AGENTS.md","GEMINI.md"]}}')
except (ValueError, OSError, TypeError) as exc:
    sys.exit('install_hooks.sh: refused: ' + str(exc))
PY
