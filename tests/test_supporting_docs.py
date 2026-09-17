#!/usr/bin/env python3
"""Supporting docs: writer/checker lifecycle, provenance and preservation contracts."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/contextify/scripts'
sys.path.insert(0, str(SCRIPTS))
import ctxlib
import ctx_write


class SupportingDocs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='contextify-docs-')
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.repo = self.home / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.draft = self.home / 'draft'
        self.draft.mkdir()
        self.put('package.json', '{"scripts":{"test":"runner"}}\n')
        self.put('src/server.py', 'def serve():\n    return 200\n')
        self.draft_put('AGENTS.md', '# Project\n\n- [Architecture](docs/context/architecture.md)\n- [Workflows](docs/context/workflows.md)\n')
        self.arch = '- `src/server.py` defines the request entry point.'
        self.workflow = '- Run `npm run test`.'
        self.draft_put('docs/context/architecture.md', '# Architecture\n\n' + self.arch + '\n- [Workflows](workflows.md)\n')
        self.draft_put('docs/context/workflows.md', '# Workflows\n\n' + self.workflow + '\n')
        self.evidence()

    def put(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, newline='')
        return path

    def draft_put(self, name, text):
        path = self.draft / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def evidence(self, scope=''):
        self.draft_put('evidence.tsv', ctxlib.digest_bytes(self.arch) + '\t' + scope + 'src/server.py:1\n' + ctxlib.digest_bytes(self.workflow) + '\t' + scope + 'package.json:1\n')

    def cli(self, name, *args, env=None):
        return subprocess.run([sys.executable, str(SCRIPTS / name), '--root', str(self.repo), *args], capture_output=True, text=True, env=env)

    def write(self, *args, env=None):
        return self.cli('ctx_write.py', '--draft', str(self.draft), '--yes', '--strict', *args, env=env)

    def snapshot(self):
        return {str(path.relative_to(self.repo)): (path.read_bytes(), path.stat().st_mtime_ns) for path in self.repo.rglob('*') if path.is_file() and '.git' not in path.parts}

    def assert_written(self, *args):
        result = self.write(*args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_supporting_docs_planned_links_strict_fresh_and_noop(self):
        before = self.snapshot()
        preview = self.cli('ctx_write.py', '--draft', str(self.draft), '--strict', '--dry-run')
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(before, self.snapshot())
        self.assert_written('--targets', 'claude,codex')
        stamp = json.loads((self.repo / '.contextify/stamp.json').read_text())
        self.assertTrue(set(ctxlib.SUPPORTING_DOCS).issubset(stamp['contextFiles']))
        self.assertEqual(stamp['unverifiedLines'], [])
        result = self.cli('ctx_check.py', '--strict')
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        original = self.snapshot()
        self.assert_written('--targets', 'claude,codex')
        self.assertEqual(original, self.snapshot())

    def test_strict_rejects_unproven_architecture_and_descriptive_navigation(self):
        self.draft_put('evidence.tsv', ctxlib.digest_bytes(self.workflow) + '\tpackage.json:1\n')
        before = self.snapshot()
        self.assertEqual(self.write().returncode, 4)
        self.assertEqual(before, self.snapshot())
        self.evidence()
        self.draft_put('AGENTS.md', '# Project\n- [Architecture scales to millions](docs/context/architecture.md)\n')
        self.assertEqual(self.write().returncode, 4)
        self.draft_put('AGENTS.md', '# Project\n- [Architecture](docs/context/architecture.md) is distributed.\n')
        self.assertEqual(self.write().returncode, 4)

    def test_supporting_fences_refuse_before_writes(self):
        self.draft_put('docs/context/architecture.md', '# Architecture\n```text\nDiagram\n```\n')
        before = self.snapshot()
        result = self.write()
        self.assertEqual(result.returncode, 4)
        self.assertIn('fenced code block', result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_scoped_paths_and_commands_are_relative_to_scope(self):
        (self.repo / 'package.json').unlink()
        (self.repo / 'src/server.py').unlink()
        self.put('packages/api/package.json', '{"scripts":{"test":"runner"}}\n')
        self.put('packages/api/src/server.py', 'def serve():\n    return 200\n')
        self.assert_written('--scope', 'packages/api')
        result = self.cli('ctx_check.py', '--strict')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        stamp = json.loads((self.repo / '.contextify/stamp.json').read_text())
        command = next(c for c in stamp['claims']['commands'] if c['text'] == 'npm run test')
        self.assertEqual(command['cwd'], 'packages/api')
        self.assertIn('packages/api/docs/context/architecture.md', stamp['contextFiles'])
        check = self.cli('verify_claims.py', '--strict', '--budget', 'packages/api/docs/context/workflows.md')
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_nested_root_infers_scope_and_evidenced_sibling_paths_resolve(self):
        self.put('packages/api/package.json', '{"scripts":{"test":"runner"}}\n')
        self.put('packages/api/src/server.py', 'def serve():\n    return 200\n')
        result = self.cli('ctx_write.py', '--root', str(self.repo / 'packages/api'), '--draft', str(self.draft), '--yes', '--strict')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo / 'packages/api/docs/context/architecture.md').is_file())
        self.arch = '- The server is `../../src/server.py`.'
        self.draft_put('docs/context/architecture.md', '# Architecture\n' + self.arch + '\n')
        self.draft_put('evidence.tsv', ctxlib.digest_bytes(self.arch) + '\t../../src/server.py:1\n' + ctxlib.digest_bytes(self.workflow) + '\tpackage.json:1\n')
        result = self.write('--scope', 'packages/api')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.cli('ctx_check.py', '--strict').returncode, 0)

    def test_accept_refuses_changed_or_deleted_supporting_docs(self):
        self.assert_written()
        path = self.repo / 'docs/context/architecture.md'
        original = path.read_text()
        path.write_text(original.replace('request entry point', 'other entry point'))
        before = self.snapshot()
        self.assertEqual(self.cli('ctx_stamp.py', '--accept').returncode, 4)
        self.assertEqual(before, self.snapshot())
        path.unlink()
        before = self.snapshot()
        self.assertEqual(self.cli('ctx_stamp.py', '--accept').returncode, 4)
        self.assertEqual(before, self.snapshot())

    def test_existing_human_bytes_preserved_and_final_120_line_ceiling(self):
        human = '# Human\r\noriginal text\r\n\r\nNo final newline'
        path = self.put('docs/context/architecture.md', human)
        self.assert_written()
        written = path.read_bytes()
        self.assertIn(b'original text\r\n\r\nNo final newline', written)
        path.write_bytes(written + b'\n' + b'human line\n' * 120)
        before = self.snapshot()
        result = self.write()
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertIn('ceiling is 120', result.stderr)
        self.assertEqual(before, self.snapshot())
        checked = self.cli('ctx_check.py', '--strict', '--ci')
        self.assertEqual(checked.returncode, 1)
        self.assertIn('ceiling is 120', checked.stdout)

    def test_omitting_existing_supporting_docs_retains_files_stamp_and_provenance(self):
        self.assert_written()
        doc = self.repo / 'docs/context/architecture.md'
        original = doc.read_bytes(), doc.stat().st_mtime_ns
        (self.draft / 'docs/context/architecture.md').unlink()
        (self.draft / 'docs/context/workflows.md').unlink()
        (self.draft / 'evidence.tsv').unlink()
        self.assert_written()
        self.assertEqual(original, (doc.read_bytes(), doc.stat().st_mtime_ns))
        stamp = json.loads((self.repo / '.contextify/stamp.json').read_text())
        self.assertIn('docs/context/architecture.md', stamp['contextFiles'])
        self.assertTrue(any(p['file'] == 'docs/context/architecture.md' for p in stamp['provenance']))
        self.assertEqual(self.cli('ctx_check.py', '--strict').returncode, 0)

    def test_omitted_supporting_doc_human_overflow_refuses_before_writes(self):
        self.assert_written()
        path = self.repo / 'docs/context/architecture.md'
        with path.open('a') as handle:
            handle.write('human line\n' * 120)
        (self.draft / 'docs/context/architecture.md').unlink()
        (self.draft / 'docs/context/workflows.md').unlink()
        (self.draft / 'evidence.tsv').unlink()
        before = self.snapshot()
        result = self.write()
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        self.assertIn('ceiling is 120', result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_omission_cannot_adopt_edited_managed_heading_even_with_force(self):
        self.assert_written()
        path = self.repo / 'docs/context/architecture.md'
        path.write_text(path.read_text().replace('# Architecture', '# Hand edited architecture'))
        (self.draft / 'docs/context/architecture.md').unlink()
        (self.draft / 'docs/context/workflows.md').unlink()
        (self.draft / 'evidence.tsv').unlink()
        before = self.snapshot()
        for args in ((), ('--force-managed',)):
            result = self.write(*args)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual(before, self.snapshot())
        self.assertEqual(self.cli('ctx_check.py', '--strict', '--ci').returncode, 1)

    def test_source_change_doc_deletion_and_omission_cannot_erase_drift(self):
        self.assert_written()
        self.put('src/server.py', 'def other():\n    return 200\n')
        result = self.cli('ctx_check.py', '--strict', '--ci')
        self.assertEqual(result.returncode, 1)
        self.assertIn('provenance:src/server.py:1', result.stdout)
        (self.repo / 'docs/context/architecture.md').unlink()
        result = self.cli('ctx_check.py', '--strict', '--ci')
        self.assertEqual(result.returncode, 1)
        self.assertIn('docs/context/architecture.md', result.stdout)
        (self.draft / 'docs/context/architecture.md').unlink()
        before = self.snapshot()
        self.assertEqual(self.write().returncode, 4)
        self.assertEqual(before, self.snapshot())

    def test_unknown_drafts_and_path_escapes_refuse_before_writes(self):
        unknown = self.draft_put('docs/context/security.md', '# Security\n')
        before = self.snapshot()
        self.assertEqual(self.write().returncode, 4)
        self.assertEqual(before, self.snapshot())
        unknown.unlink()
        outside = self.home / 'outside'
        outside.mkdir()
        (self.repo / 'docs').symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.write().returncode, 5)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.repo / 'AGENTS.md').exists())

    def test_draft_symlink_escape_is_not_followed(self):
        path = self.draft / 'docs/context/architecture.md'
        path.unlink()
        outside = self.home / 'outside.md'
        outside.write_text('# Escaped\n')
        path.symlink_to(outside)
        before = self.snapshot()
        self.assertEqual(self.write().returncode, 5)
        self.assertEqual(before, self.snapshot())

    def test_unmanaged_recognized_path_remains_evidence_not_context(self):
        self.draft_put('AGENTS.md', '# Project\n')
        (self.draft / 'docs/context/architecture.md').unlink()
        (self.draft / 'docs/context/workflows.md').unlink()
        (self.draft / 'evidence.tsv').unlink()
        self.put('docs/context/architecture.md', '# Existing hand-written architecture\n')
        self.assertIn('docs/context/architecture.md', ctxlib.eligible_files(str(self.repo)))
        self.assertNotIn('docs/context/architecture.md', ctxlib.present_context_files(str(self.repo)))
        self.assert_written()
        stamp = json.loads((self.repo / '.contextify/stamp.json').read_text())
        self.assertNotIn('docs/context/architecture.md', stamp['contextFiles'])
        self.assertIn('docs/context/', next(r['value'] for r in json.loads((self.repo / '.contextify/evidence.json').read_text())['records'] if r['key'] == 'tree#depth2'))

    def test_interrupted_write_can_recover_supporting_files(self):
        original = self.put('docs/context/architecture.md', '# Human\r\nkeep\r\n').read_bytes()
        env = dict(os.environ, CONTEXTIFY_TEST_CRASH_AFTER='2')
        result = self.write(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.repo / '.contextify/journal.json').exists())
        self.assertNotEqual((self.repo / 'docs/context/architecture.md').read_bytes(), original)
        recovered = self.cli('ctx_write.py', '--recover')
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        self.assertEqual((self.repo / 'docs/context/architecture.md').read_bytes(), original)
        self.assertFalse((self.repo / 'AGENTS.md').exists())
        self.assertFalse((self.repo / '.contextify/journal.json').exists())

    def test_failed_postwrite_check_rolls_back_all_supporting_files(self):
        from unittest.mock import patch
        opts = ctx_write.parse_args(['--root', str(self.repo), '--draft', str(self.draft), '--yes', '--strict'])
        bad = ctxlib.CheckResult()
        bad.status = 'drift'
        bad.changed.append('injected-postwrite-failure')
        before = {key: value[0] for key, value in self.snapshot().items()}
        with patch.object(ctxlib, 'run_check', return_value=bad), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = ctx_write.run(str(self.repo.resolve()), opts)
        self.assertEqual(result, 6)
        self.assertEqual(before, {key: value[0] for key, value in self.snapshot().items()})


if __name__ == '__main__':
    unittest.main()
