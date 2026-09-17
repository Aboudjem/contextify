#!/usr/bin/env python3
"""Hook installer safety, portability and idempotence regressions."""
import hashlib
import json
import os
import shlex
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

INSTALLER = Path(__file__).resolve().parents[1] / 'skills/contextify/scripts/install_hooks.sh'

class HookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ctx-hooks-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.env = dict(os.environ)
        for key in list(self.env):
            if key.startswith('GIT_CONFIG_'):
                self.env.pop(key)
        # Isolate hook configuration while retaining the actual user's global identity.
        fixture_global = Path(self.temp.name) / 'identity-config'
        fixture_global.touch()
        for field in ('user.name', 'user.email'):
            actual = subprocess.run(['git', 'config', '--global', '--get', field], capture_output=True, text=True)
            if actual.returncode != 0 or not actual.stdout.strip():
                self.fail('A configured global Git identity is required for real commit fixtures')
            subprocess.run(['git', 'config', '--file', str(fixture_global), field, actual.stdout.strip()], check=True)
        self.env['GIT_CONFIG_GLOBAL'] = str(fixture_global)
        self.env['GIT_CONFIG_NOSYSTEM'] = '1'

    def install(self, *args):
        return subprocess.run(['bash', str(INSTALLER), *args, str(self.root)], capture_output=True, text=True, env=self.env)

    def test_preview_has_no_files(self):
        result = self.install('--targets', 'codex,gemini,cursor,git,github')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertIn('Proposal only', result.stdout)

    def test_conflict_preserves_contents_and_mode(self):
        path = self.root / '.githooks/pre-commit'
        path.parent.mkdir()
        path.write_bytes(b'#!/bin/sh\r\n# human\r\n')
        path.chmod(0o644)
        for args in [(), ('--yes',)]:
            result = self.install('--targets', 'codex,git', *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_bytes(), b'#!/bin/sh\r\n# human\r\n')
            self.assertEqual(path.stat().st_mode & 0o777, 0o644)
            self.assertFalse((self.root / '.codex').exists())

    def test_symlink_escape_refuses_before_any_write(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.root / '.githooks').symlink_to(outside, target_is_directory=True)
        result = self.install('--yes', '--targets', 'codex,git')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.root / '.codex').exists())

    def test_json_merge_and_repeat_preserve_human_settings(self):
        path = self.root / '.gemini/settings.json'
        path.parent.mkdir()
        original = {'theme': 'custom', 'hooks': {'SessionStart': [{'hooks': [{'command': 'echo human'}]}]}}
        path.write_text(json.dumps(original))
        first = self.install('--yes', '--targets', 'gemini')
        self.assertEqual(first.returncode, 0, first.stderr)
        value = json.loads(path.read_text())
        self.assertEqual(value['theme'], 'custom')
        self.assertEqual(value['hooks']['SessionStart'][0], original['hooks']['SessionStart'][0])
        before = path.read_bytes(), path.stat().st_mtime_ns
        second = self.install('--yes', '--targets', 'gemini')
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)

    def test_ci_is_portable(self):
        result = self.install('--yes', '--targets', 'github')
        self.assertEqual(result.returncode, 0, result.stderr)
        workflow = (self.root / '.github/workflows/contextify-check.yml').read_text()
        self.assertIn('--branch v0.2.0', workflow)
        self.assertIn('$RUNNER_TEMP/contextify/skills/contextify/scripts/ctx-check', workflow)
        self.assertNotIn(str(INSTALLER.parent), workflow)

    def test_cursor_existing_config_gets_version_and_unknown_version_refuses(self):
        path = self.root / '.cursor/hooks.json'
        path.parent.mkdir()
        path.write_text('{"human": true}')
        result = self.install('--yes', '--targets', 'cursor')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(path.read_text())['version'], 1)
        self.assertTrue(json.loads(path.read_text())['human'])
        path.write_text('{"version": 2}')
        result = self.install('--yes', '--targets', 'codex,cursor')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_text(), '{"version": 2}')
        self.assertFalse((self.root / '.codex').exists())

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], capture_output=True, text=True, env=self.env)

    def init_git(self):
        self.assertEqual(self.git('init', '-q').returncode, 0)
        # Preserve the user's configured identity. Only disable fixture signing.
        self.git('config', 'commit.gpgsign', 'false')

    def fresh(self):
        (self.root / 'package.json').write_text('{"name":"fixture","scripts":{"test":"echo ok"}}')
        draft = Path(self.temp.name) / 'draft'
        draft.mkdir()
        body = '- Run `npm test`.'
        (draft / 'AGENTS.md').write_text('# Fixture\n' + body + '\n')
        (draft / 'evidence.tsv').write_text(hashlib.sha256(body.encode()).hexdigest() + '\tpackage.json:1\n')
        result = subprocess.run(['python3', str(INSTALLER.parent / 'ctx_write.py'), '--root', str(self.root), '--draft', str(draft), '--targets', 'claude,codex', '--yes'], capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_default_only_git_and_packaged_sessions_empty(self):
        result = self.install('--yes')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('inactive', result.stdout)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['.githooks'])
        self.assertEqual(sorted(p.name for p in (self.root / '.githooks').iterdir()), ['pre-commit', 'pre-push'])
        packaged = json.loads((INSTALLER.parents[3] / 'hooks/hooks.json').read_text())
        self.assertEqual(packaged['hooks'], {})

    def test_activation_preview_and_idempotence(self):
        self.init_git()
        config = self.root / '.git/config'
        before = config.read_bytes(), config.stat().st_mtime_ns
        preview = self.install('--activate')
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual((config.read_bytes(), config.stat().st_mtime_ns), before)
        self.assertFalse((self.root / '.githooks').exists())
        result = self.install('--yes', '--activate')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git('config', '--local', '--get', 'core.hooksPath').stdout.strip(), '.githooks')
        paths = [config, self.root / '.githooks/pre-commit', self.root / '.githooks/pre-push']
        before = [(p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_mode) for p in paths]
        repeat = self.install('--yes', '--activate')
        self.assertEqual(repeat.returncode, 0, repeat.stderr)
        self.assertEqual([(p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_mode) for p in paths], before)

    def test_custom_and_global_hooks_refuse_before_writes(self):
        self.init_git()
        self.git('config', 'core.hooksPath', 'custom-hooks')
        result = self.install('--yes', '--activate', '--targets', 'codex,git')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / '.codex').exists())
        self.assertFalse((self.root / '.githooks').exists())
        self.git('config', '--unset', 'core.hooksPath')
        global_config = Path(self.temp.name) / 'global-config'
        global_config.write_text('[core]\n hooksPath = .githooks\n')
        self.env['GIT_CONFIG_GLOBAL'] = str(global_config)
        before = global_config.read_bytes()
        result = self.install('--yes', '--activate')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / '.githooks').exists())
        self.assertEqual(global_config.read_bytes(), before)

    def test_existing_default_hook_refuses_activation(self):
        self.init_git()
        hook = self.root / '.git/hooks/pre-push'
        hook.write_text('#!/bin/sh\nexit 0\n')
        hook.chmod(0o755)
        result = self.install('--yes', '--activate', '--targets', 'claude,git')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('mask existing', result.stderr)
        self.assertFalse((self.root / '.claude').exists())
        self.assertFalse((self.root / '.githooks').exists())

    def test_linked_worktree_refuses_activation(self):
        self.init_git()
        self.assertEqual(self.git('commit', '--allow-empty', '-qm', 'Fixture').returncode, 0)
        linked = Path(self.temp.name) / 'linked'
        result = self.git('worktree', 'add', '-b', 'linked', str(linked))
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(['bash', str(INSTALLER), '--yes', '--activate', str(linked)], capture_output=True, text=True, env=self.env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('linked worktrees', result.stderr)
        self.assertFalse((linked / '.githooks').exists())

    def test_git_mode_preserves_stdin_summary_and_ignores_host_root(self):
        self.init_git()
        self.fresh()
        summary = Path(self.temp.name) / 'summary'
        summary.write_text('human\n')
        data = Path(self.temp.name) / 'stdin'
        data.write_text('{"cwd":"/missing"}\n')
        env = dict(self.env, GITHUB_STEP_SUMMARY=str(summary), CLAUDE_PROJECT_DIR='/missing')
        with data.open() as stream:
            result = subprocess.run(['sh', str(INSTALLER.parent / 'ctx-check'), '--git', '--strict'], cwd=self.root, stdin=stream, capture_output=True, text=True, env=env)
            self.assertEqual(stream.tell(), 0)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout + result.stderr, '')
        self.assertEqual(summary.read_text(), 'human\n')
        for other in ['--ci', '--json', '--hook=claude']:
            result = subprocess.run(['sh', str(INSTALLER.parent / 'ctx-check'), '--git', other], cwd=self.root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)

    def test_real_commit_push_advisory_and_strict(self):
        self.init_git()
        result = self.install('--yes', '--activate')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.fresh()
        self.git('add', '.')
        commit = self.git('commit', '-qm', 'Fresh context')
        self.assertEqual(commit.returncode, 0, commit.stderr)
        self.assertEqual(commit.stderr, '')
        remote = Path(self.temp.name) / 'remote.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
        self.git('remote', 'add', 'origin', str(remote))
        push = self.git('push', '-q', 'origin', 'HEAD')
        self.assertEqual(push.returncode, 0, push.stderr)
        self.assertNotIn('contextify:', push.stderr)
        (self.root / 'package.json').write_text('{"name":"fixture","scripts":{}}')
        self.git('add', 'package.json')
        commit = self.git('commit', '-qm', 'Advisory drift')
        self.assertEqual(commit.returncode, 0, commit.stderr)
        self.assertIn('contextify: drift', commit.stderr)
        push = self.git('push', '-q', 'origin', 'HEAD')
        self.assertEqual(push.returncode, 0, push.stderr)
        self.assertIn('contextify: drift', push.stderr)
        # Install strict in a separate empty hook directory to preserve conflict semantics.
        for hook in (self.root / '.githooks').iterdir():
            hook.unlink()
        result = self.install('--yes', '--activate', '--strict')
        self.assertEqual(result.returncode, 0, result.stderr)
        commit = self.git('commit', '--allow-empty', '-qm', 'Strict drift')
        self.assertNotEqual(commit.returncode, 0)
        # A new local commit bypasses only our fixture hook so pre-push has work to check.
        self.assertEqual(self.git('-c', 'core.hooksPath=/dev/null', 'commit', '--allow-empty', '-qm', 'Push fixture').returncode, 0)
        push = self.git('push', '-q', 'origin', 'HEAD')
        self.assertNotEqual(push.returncode, 0)
        self.assertIn('contextify: drift', push.stderr)

    def test_no_stamp_and_checker_error_advisory_vs_strict(self):
        self.init_git()
        for strict in (False, True):
            if (self.root / '.githooks').exists():
                for hook in (self.root / '.githooks').iterdir():
                    hook.unlink()
            result = self.install('--yes', *(('--strict',) if strict else ()))
            self.assertEqual(result.returncode, 0, result.stderr)
            hook = self.root / '.githooks/pre-commit'
            check = subprocess.run(['sh', str(hook)], cwd=self.root, capture_output=True, text=True)
            self.assertEqual(check.returncode, 1 if strict else 0)
            self.assertIn('contextify:', check.stderr)
            # Missing runner must be advisory unless explicitly strict.
            text = hook.read_text().replace(str(INSTALLER.parent / 'ctx-check'), '/missing/contextify-check')
            hook.write_text(text)
            check = subprocess.run(['sh', str(hook)], cwd=self.root, capture_output=True, text=True)
            self.assertEqual(check.returncode == 0, not strict)
            self.assertTrue(check.stderr)

    def test_unknown_flags_and_non_git_activation_refuse(self):
        for args in [('--yes', '--wat'), ('--yes', '--activate'), ('--yes', '--activate', '--targets', 'cursor')]:
            result = self.install(*args)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(self.root.iterdir()), [])

    def test_absolute_hooks_path_is_reported_active_without_reconfiguration(self):
        self.init_git()
        self.git('config', 'core.hooksPath', str(self.root / '.githooks'))
        result = self.install('--yes')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Git hooks are active', result.stdout)
        self.assertEqual(self.git('config', '--get', 'core.hooksPath').stdout.strip(), str(self.root / '.githooks'))

    def test_symlinked_config_refuses_activation_before_writes(self):
        self.init_git()
        config = self.root / '.git/config'
        external = Path(self.temp.name) / 'external-config'
        external.write_bytes(config.read_bytes())
        config.unlink()
        config.symlink_to(external)
        before = external.read_bytes()
        result = self.install('--yes', '--activate')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('symlinked repository config', result.stderr)
        self.assertFalse((self.root / '.githooks').exists())
        self.assertEqual(external.read_bytes(), before)

    def test_activation_failure_reports_installed_inactive(self):
        self.init_git()
        fakebin = Path(self.temp.name) / 'bin'
        fakebin.mkdir()
        fake = fakebin / 'git'
        fake.write_text('#!/bin/sh\nif [ "$5" = core.hooksPath ] && [ "$6" = .githooks ]; then\n  echo "fixture config failure" >&2\n  exit 1\nfi\nexec ' + shlex.quote(shutil.which('git')) + ' "$@"\n')
        fake.chmod(0o755)
        self.env['PATH'] = str(fakebin) + os.pathsep + self.env['PATH']
        result = self.install('--yes', '--activate')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('installed but inactive', result.stderr)
        self.assertTrue((self.root / '.githooks/pre-commit').exists())
        self.assertEqual(self.git('config', '--local', '--get', 'core.hooksPath').returncode, 1)

    def test_broken_state_strict_and_advisory(self):
        self.init_git()
        result = self.install('--yes', '--activate')
        self.assertEqual(result.returncode, 0, result.stderr)
        state = self.root / '.contextify'
        state.mkdir()
        (state / 'stamp.json').write_text('{broken')
        commit = self.git('commit', '--allow-empty', '-qm', 'Advisory broken state')
        self.assertEqual(commit.returncode, 0, commit.stderr)
        self.assertIn('contextify:', commit.stderr)
        for hook in (self.root / '.githooks').iterdir():
            hook.unlink()
        result = self.install('--yes', '--strict', '--activate')
        self.assertEqual(result.returncode, 0, result.stderr)
        commit = self.git('commit', '--allow-empty', '-qm', 'Strict broken state')
        self.assertNotEqual(commit.returncode, 0)
        self.assertIn('contextify:', commit.stderr)

    def test_claude_is_explicit_opt_in(self):
        result = self.install('--yes', '--targets', 'claude')
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads((self.root / '.claude/settings.json').read_text())
        self.assertIn('--hook claude', config['hooks']['SessionStart'][0]['hooks'][0]['command'])
        self.assertFalse((self.root / '.githooks').exists())

if __name__ == '__main__':
    unittest.main()
