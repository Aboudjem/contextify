#!/usr/bin/env python3
"""Hook installer safety, portability and idempotence regressions."""
import json
import os
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

    def install(self, *args):
        return subprocess.run(['bash', str(INSTALLER), *args, str(self.root)], capture_output=True, text=True)

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

    def test_strict_git_status_propagates_and_ci_is_portable(self):
        result = self.install('--yes', '--targets', 'git,github')
        self.assertEqual(result.returncode, 0, result.stderr)
        hook = self.root / '.githooks/pre-commit'
        self.assertTrue(os.access(hook, os.X_OK))
        # Replace only runner command with a failing fixture; exec must preserve status.
        text = hook.read_text()
        self.assertIn('exec sh ', text)
        fake = self.root / 'fails.sh'
        fake.write_text('#!/bin/sh\nexit 1\n')
        import shlex
        text = text[:text.index('exec sh ')] + 'exec sh ' + shlex.quote(str(fake)) + ' --ci --strict\n'
        hook.write_text(text)
        check = subprocess.run(['sh', str(hook)], capture_output=True)
        self.assertEqual(check.returncode, 1)
        workflow = (self.root / '.github/workflows/contextify-check.yml').read_text()
        self.assertIn('--branch v0.1.0', workflow)
        self.assertIn('$RUNNER_TEMP/contextify/skills/contextify/scripts/ctx-check', workflow)
        self.assertNotIn(str(INSTALLER.parent), workflow)
        self.assertTrue(workflow.rstrip().endswith('--ci'))

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

if __name__ == '__main__':
    unittest.main()
