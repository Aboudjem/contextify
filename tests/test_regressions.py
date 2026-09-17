#!/usr/bin/env python3
"""Adversarial regressions from the independent 2026-09-17 review, offline only."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/contextify/scripts'
sys.path.insert(0, str(SCRIPTS))
import ctxlib


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='ctx-regressions-')
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.repo = self.home / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.draft = self.home / 'draft'
        self.draft.mkdir()
        self.put('package.json', '{"scripts":{"test":"runner"}}\n')
        (self.draft / 'AGENTS.md').write_text('# Fixture\n\nRun `npm run test`.\n')

    def put(self, name, text):
        p = self.repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, newline='')
        return p

    def cli(self, name, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / name), '--root', str(self.repo), *args], capture_output=True, text=True)

    def write(self, *args):
        return self.cli('ctx_write.py', '--draft', str(self.draft), '--yes', *args)

    def snapshot(self):
        return {str(p.relative_to(self.repo)): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.repo.rglob('*') if p.is_file() and '.git' not in p.parts}

    def test_recovery_traversal_and_malformed_digest_never_touch_victim(self):
        victim = self.home / 'victim'
        victim.write_text('original')
        journal = {'version': 1, 'root': str(self.repo), 'targets': [{'path': '../victim', 'previous': 'attack', 'previousDigest': ctxlib.digest_bytes('attack'), 'newDigest': ctxlib.digest_bytes('original')}]}
        self.put('.contextify/journal.json', json.dumps(journal))
        r = self.cli('ctx_write.py', '--recover')
        self.assertEqual(r.returncode, 5, r.stderr)
        self.assertEqual(victim.read_text(), 'original')
        self.assertTrue((self.repo / '.contextify/journal.json').exists())

    def test_state_and_gitignore_symlink_escapes_refuse_without_writes(self):
        outside = self.home / 'outside'
        outside.mkdir()
        (self.repo / '.contextify').symlink_to(outside, target_is_directory=True)
        r = self.write()
        self.assertEqual(r.returncode, 5, r.stderr)
        self.assertEqual(list(outside.iterdir()), [])
        (self.repo / '.contextify').unlink()
        target = outside / 'ignore'
        target.write_text('human')
        (self.repo / '.gitignore').symlink_to(target)
        self.assertEqual(self.write().returncode, 5)
        self.assertEqual(target.read_text(), 'human')
        self.assertFalse((self.repo / 'AGENTS.md').exists())

    def test_final_human_budget_refused_and_ci_checks_actual_bytes(self):
        self.put('AGENTS.md', '# Human\n' + 'human\n' * 149)
        before = self.snapshot()
        self.assertEqual(self.write().returncode, 4)
        self.assertEqual(before, self.snapshot())
        self.put('AGENTS.md', '# Human\n' + 'x' * 40000)
        self.assertEqual(self.write('--targets', 'codex').returncode, 4)
        (self.repo / 'AGENTS.md').unlink()
        self.assertEqual(self.write('--targets', 'codex').returncode, 0)
        with (self.repo / 'AGENTS.md').open('a') as f:
            f.write('x' * 40000)
        r = self.cli('ctx_check.py', '--ci', '--strict')
        self.assertEqual(r.returncode, 1)
        self.assertIn('32,768', r.stdout)

    def test_human_newlines_migration_and_noop_mtime(self):
        human = '# Human\r\nalpha\r\n\r\n'
        self.put('AGENTS.md', human)
        self.put('CLAUDE.md', '# Instructions\r\nMixed\nNo final newline')
        r = self.write()
        self.assertEqual(r.returncode, 0, r.stderr)
        agents_bytes = (self.repo / 'AGENTS.md').read_bytes()
        self.assertTrue(agents_bytes.startswith(b'# Human\r\n'))
        self.assertTrue(agents_bytes.endswith(b'alpha\r\n\r\n'))
        self.assertTrue((self.repo / 'CLAUDE.md').read_bytes().startswith(b'@AGENTS.md\n'))
        self.assertTrue((self.repo / 'CLAUDE.md').read_bytes().startswith(b'@AGENTS.md\n# Instructions\r\n'))
        self.assertTrue((self.repo / 'CLAUDE.md').read_bytes().endswith(b'Mixed\nNo final newline'))
        before = self.snapshot()
        r = self.write('--json')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)['result'], 'unchanged')
        self.assertEqual(before, self.snapshot())

    def test_dryrun_proposal_and_json_do_not_mutate(self):
        before = self.snapshot()
        r = self.cli('ctx_write.py', '--draft', str(self.draft), '--json')
        self.assertEqual(json.loads(r.stdout)['result'], 'proposed')
        self.assertEqual(before, self.snapshot())
        r = self.write('--dry-run', '--json')
        self.assertEqual(json.loads(r.stdout)['result'], 'proposed')
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.write().returncode, 0)
        before = self.snapshot()
        r = self.cli('ctx_stamp.py', '--accept', '--dry-run', '--json')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)['result'], 'proposed')
        self.assertEqual(before, self.snapshot())

    def test_unsupported_flags_scope_and_symlink_refuse(self):
        before = self.snapshot()
        for args in [('--scope', 'pkg'), ('--symlink',), ('--nonsense',)]:
            self.assertEqual(self.write(*args).returncode, 4)
        self.assertEqual(self.cli('ctx_stamp.py', '--unknown').returncode, 4)
        self.assertEqual(before, self.snapshot())

    def test_scoped_writer_and_nested_root_preserve_root_files(self):
        root_text = '# Human root\r\nunchanged\r\n'
        self.put('AGENTS.md', root_text)
        self.put('pkg/package.json', '{"scripts":{"local":"runner"}}')
        line = 'Run `npm run local`.'
        (self.draft / 'AGENTS.md').write_text('# Package\n' + line + '\n')
        (self.draft / 'evidence.tsv').write_text(hashlib.sha256(line.encode()).hexdigest() + '\tpackage.json:1\n')
        r = self.write('--scope', 'pkg', '--strict')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.repo / 'AGENTS.md').read_bytes(), root_text.encode())
        self.assertTrue((self.repo / 'pkg/CLAUDE.md').read_bytes().startswith(b'@AGENTS.md\n'))
        r = subprocess.run([sys.executable, str(SCRIPTS / 'ctx_write.py'), '--root', str(self.repo / 'pkg'), '--draft', str(self.draft), '--yes', '--json'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)['result'], 'unchanged')
        self.assertEqual(self.cli('ctx_check.py').stdout, '')
        self.assertEqual(self.write('--scope', '../escape').returncode, 5)

    def test_accept_refuses_removed_managed_markers(self):
        self.assertEqual(self.write().returncode, 0)
        path = self.repo / 'AGENTS.md'
        path.write_text(path.read_text().replace(ctxlib.BEGIN_MARK, '').replace(ctxlib.END_MARK, ''))
        before = self.snapshot()
        self.assertEqual(self.cli('ctx_stamp.py', '--accept').returncode, 4)
        self.assertEqual(before, self.snapshot())

    def test_scope_symlink_to_sibling_refuses(self):
        self.put('pkg/package.json', '{"scripts":{"test":"runner"}}')
        (self.repo / 'sibling').mkdir()
        (self.repo / 'pkg/sub').symlink_to(self.repo / 'sibling', target_is_directory=True)
        (self.draft / 'sub').mkdir()
        (self.draft / 'sub/AGENTS.md').write_text('# Nested\n')
        self.assertEqual(self.write('--scope', 'pkg').returncode, 5)
        self.assertEqual(list((self.repo / 'sibling').iterdir()), [])

    def test_shell_command_unknown_go_and_negation_coverage(self):
        self.put('go.mod', 'module example.test/demo\n\ngo 1.22\n')
        claims = ctxlib.extract_claims('Run `sh scripts/dead.sh`. Run `go nonsense ./missing`. Run `npm run absent`, not `npm run test`. Use `exotic --build`.','AGENTS.md')
        for c in claims:
            ctxlib.resolve_claim(c, str(self.repo))
        statuses = {c.text: c.status for c in claims}
        self.assertEqual(statuses['sh scripts/dead.sh'], 'stale')
        self.assertEqual(statuses['go nonsense ./missing'], 'unverified')
        self.assertEqual(statuses['npm run absent'], 'stale')
        self.assertEqual(statuses['exotic --build'], 'unverified')

    def test_strict_requires_evidence_for_whole_prose_line(self):
        line = 'Production deploys on port 99999 from `package.json`.'
        (self.draft / 'AGENTS.md').write_text('# Fixture\n' + line + '\n')
        before = self.snapshot()
        self.assertEqual(self.write('--strict').returncode, 4)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.write().returncode, 0)
        evidence_path = self.repo / '.contextify/evidence.json'
        stamp_path = self.repo / '.contextify/stamp.json'
        evidence, stamp = json.loads(evidence_path.read_text()), json.loads(stamp_path.read_text())
        evidence['unverifiedLines'] = []
        stamp['unverifiedLines'] = []
        stamp['evidenceFileDigest'] = ctxlib.digest(evidence)
        evidence_path.write_text(json.dumps(evidence))
        stamp_path.write_text(json.dumps(stamp))
        r = self.cli('ctx_check.py', '--ci', '--strict')
        self.assertEqual(r.returncode, 1)
        self.assertIn('no supplied per-line provenance', r.stdout)

    def test_strict_all_owned_pointers_pass_and_edited_prose_does_not(self):
        line = 'Run `npm run test`.'
        (self.draft / 'evidence.tsv').write_text(hashlib.sha256(line.encode()).hexdigest() + '\tpackage.json:1\n')
        r = self.write('--strict', '--targets', 'claude,codex,gemini,cursor-rule,copilot')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.cli('ctx_check.py', '--ci', '--strict').returncode, 0)
        copilot = self.repo / '.github/copilot-instructions.md'
        copilot.write_text(copilot.read_text().replace('Read [AGENTS.md]', 'Port 99999. Read [AGENTS.md]'))
        self.assertEqual(self.cli('ctx_check.py', '--ci', '--strict').returncode, 1)
        self.assertEqual(self.cli('ctx_stamp.py', '--accept', '--strict').returncode, 4)

    def test_shell_m_flag_is_not_python_module_evidence(self):
        self.put('foo.py', 'pass\n')
        claim = ctxlib.extract_claims('Run `bash -m foo`.','AGENTS.md')[0]
        ctxlib.resolve_claim(claim, str(self.repo))
        self.assertEqual(claim.status, 'unverified')

    def test_unsupported_make_forms_are_unverified_not_dead(self):
        self.put('Makefile', 'include targets.mk\n')
        self.put('targets.mk', 'test:\n\ttrue\n')
        for snippet in ('make test', 'make -C pkg test', 'pnpm --filter web test', 'pnpm -C pkg test', 'yarn --cwd pkg test', 'bun --cwd pkg test'):
            claim = ctxlib.extract_claims('Run `' + snippet + '`.','AGENTS.md')[0]
            ctxlib.resolve_claim(claim, str(self.repo))
            self.assertEqual(claim.status, 'unverified')

    def test_nested_claims_resolve_from_nested_manifest(self):
        self.put('pkg/package.json', '{"scripts":{"local":"runner"}}')
        claim = ctxlib.extract_claims('Run `npm run local`.','pkg/AGENTS.md')[0]
        ctxlib.resolve_claim(claim, str(self.repo))
        self.assertEqual(claim.cwd, 'pkg')
        self.assertEqual(claim.status, 'verified')

    def test_provenance_rejects_bad_mapping_detects_source_change_and_accept_retains(self):
        source = self.put('src/architecture.py', 'router calls service\n')
        line = 'The router calls the service.'
        (self.draft / 'AGENTS.md').write_text('# Fixture\n' + line + '\n')
        mapping = self.draft / 'evidence.tsv'
        mapping.write_text('not a hash\tno-such-source:987\n')
        self.assertEqual(self.write().returncode, 4)
        mapping.write_text(hashlib.sha256(line.encode()).hexdigest() + '\tsrc/architecture.py:1\n')
        self.assertEqual(self.write('--strict').returncode, 0)
        evidence = json.loads((self.repo / '.contextify/evidence.json').read_text())
        self.assertEqual(evidence['provenance'][0]['source'], 'src/architecture.py:1')
        source.write_text('router calls another service\n')
        r = self.cli('ctx_check.py')
        self.assertIn('provenance:src/architecture.py:1', r.stdout)
        r = self.cli('ctx_stamp.py', '--accept')
        self.assertEqual(r.returncode, 0, r.stderr)
        evidence2 = json.loads((self.repo / '.contextify/evidence.json').read_text())
        self.assertEqual(evidence2['provenance'][0]['source'], evidence['provenance'][0]['source'])
        self.assertNotEqual(evidence2['provenance'][0]['sourceDigest'], evidence['provenance'][0]['sourceDigest'])
        self.assertEqual(self.cli('ctx_check.py').stdout, '')

    def test_scoped_update_retains_root_provenance(self):
        self.put('root-source.py', 'root architecture\n')
        root_line = 'Root architecture uses a router.'
        (self.draft / 'AGENTS.md').write_text('# Root\n' + root_line + '\n')
        (self.draft / 'evidence.tsv').write_text(hashlib.sha256(root_line.encode()).hexdigest() + '\troot-source.py:1\n')
        self.assertEqual(self.write('--strict').returncode, 0)
        self.put('pkg/source.py', 'package architecture\n')
        package_line = 'Package architecture uses a service.'
        (self.draft / 'AGENTS.md').write_text('# Package\n' + package_line + '\n')
        (self.draft / 'evidence.tsv').write_text(hashlib.sha256(package_line.encode()).hexdigest() + '\tsource.py:1\n')
        r = self.write('--scope', 'pkg', '--strict')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.put('root-source.py', 'changed root architecture\n')
        self.assertIn('provenance:root-source.py:1', self.cli('ctx_check.py').stdout)

    def test_equal_text_in_two_scopes_keeps_distinct_provenance(self):
        line = 'Run `npm run test`.'
        identity = hashlib.sha256(line.encode()).hexdigest()
        (self.draft / 'evidence.tsv').write_text(identity + '\tpackage.json:1\n')
        self.assertEqual(self.write('--strict').returncode, 0)
        self.put('pkg/package.json', '{"scripts":{"test":"different runner"}}')
        self.assertEqual(self.write('--scope', 'pkg', '--strict').returncode, 0)
        for invocation in (None, '--accept'):
            if invocation:
                self.assertEqual(self.cli('ctx_stamp.py', invocation).returncode, 0)
            entries = json.loads((self.repo / '.contextify/evidence.json').read_text())['provenance']
            by_file = {entry['file']: entry['source'] for entry in entries}
            self.assertEqual(by_file['AGENTS.md'], 'package.json:1')
            self.assertEqual(by_file['pkg/AGENTS.md'], 'pkg/package.json:1')

    def test_root_update_retains_nested_pointers_and_codex_target(self):
        self.put('pkg/package.json', '{"scripts":{"test":"runner"}}')
        self.assertEqual(self.write('--scope', 'pkg', '--targets', 'codex,claude').returncode, 0)
        self.assertEqual(self.write().returncode, 0)
        stamp = json.loads((self.repo / '.contextify/stamp.json').read_text())
        self.assertIn('pkg/CLAUDE.md', stamp['contextFiles'])
        self.assertIn('codex', stamp['targets'])
        self.put('pkg/CLAUDE.md', '# Missing import\n')
        self.assertIn('pkg/CLAUDE.md:1', self.cli('ctx_check.py').stdout)

    def test_shell_and_python_equivalent_after_deleted_source_and_new_manifest(self):
        self.put('src/a.py', 'pass\n')
        (self.draft / 'AGENTS.md').write_text('# Fixture\nRun `python3 src/a.py`.\n')
        self.assertEqual(self.write().returncode, 0)
        (self.repo / 'src/a.py').unlink()
        self.put('new/package.json', '{"scripts":{"new":"new"}}')
        py = self.cli('ctx_check.py')
        sh = subprocess.run(['sh', str(SCRIPTS / 'ctx-check'), str(self.repo)], capture_output=True, text=True)
        self.assertEqual((py.returncode, py.stdout, py.stderr), (sh.returncode, sh.stdout, sh.stderr))
        self.assertIn('Stale', sh.stdout)

    def test_hook_open_pipe_bounded_and_relative_invocation(self):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.repo))
        child = subprocess.Popen(['sh', str(SCRIPTS / 'ctx-check'), '--hook', 'claude'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        try:
            child.wait(timeout=2)
            self.assertEqual(child.returncode, 3)
        finally:
            if child.poll() is None:
                child.kill()
            child.communicate()
        root = SCRIPTS.parents[2]
        r = subprocess.run(['sh', 'skills/contextify/scripts/ctx-check', str(self.repo)], cwd=root, capture_output=True, text=True)
        self.assertEqual(r.returncode, 3, r.stderr)

    def test_codex_sibling_chains_not_summed_and_override_checked(self):
        one = '# A\n' + 'x' * 16000
        outputs = [('AGENTS.md', '# Root\n'), ('a/AGENTS.md', one), ('b/AGENTS.md', one), ('c/AGENTS.md', one)]
        self.assertEqual(ctxlib.codex_chain_problems(str(self.repo), outputs), [])
        self.put('AGENTS.override.md', 'x' * 40000)
        self.assertTrue(ctxlib.codex_chain_problems(str(self.repo), outputs))

    def test_internal_drafts_excluded_and_integrity_checked(self):
        self.put('.contextify/draft/AGENTS.md', 'draft')
        self.put('.goal/snapshot/AGENTS.md', 'snapshot')
        self.assertEqual(ctxlib.nested_agents_files(str(self.repo)), [])
        self.assertEqual(self.write().returncode, 0)
        evidence = self.repo / '.contextify/evidence.json'
        evidence.write_text('{}\n')
        r = self.cli('ctx_check.py')
        self.assertEqual(r.returncode, 1)
        self.assertIn('integrity', r.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
