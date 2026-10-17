"""Real-proof integration and adversarial handoff tests; no network."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('handoff', Path(__file__).with_name('handoff.py'))
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.output = self.root / 'bundle.json'
        self.created = h.pack(h.DEMO_MANIFEST, h.p.a.DEMO_HASH,
                              'storage value', self.output, self.root)

    def check(self, pin=None, **kwargs):
        return h.check(h.DEMO_MANIFEST, h.p.a.DEMO_HASH, self.output,
                       pin or self.created['bundle_sha256'], self.root, **kwargs)

    def replace_bundle(self, mutate):
        value = h.b.load(self.output)
        mutate(value)
        self.output.write_bytes(h.b.receipt.canonical(value))
        return h.b.identity(value)

    def test_real_accounts_receipt_and_new_query(self):
        result = self.check(query=h.p.w.ZTO)
        self.assertTrue(result['verified'])
        self.assertTrue(result['receipt_reproduced'])
        self.assertEqual(result['accounts'], 2)
        self.assertEqual(int(result['anchor']['blockNumber'], 16), 26212390)
        self.assertTrue(result['search']['hits'])
        self.assertTrue(all(x['source_verified'] for x in result['search']['hits']))

    def test_wrong_checkpoint_rejected(self):
        with self.assertRaises(ValueError):
            h.check(h.DEMO_MANIFEST, '0x'+'11'*32, self.output,
                    self.created['bundle_sha256'], self.root)

    def test_wrong_bundle_pin_rejected_before_scratch_writes(self):
        absent = self.root / 'absent'
        with self.assertRaises(ValueError):
            h.check(h.DEMO_MANIFEST, h.p.a.DEMO_HASH, self.output, '1'*64, absent)
        self.assertFalse(absent.exists())

    def test_manifest_pin_mismatch(self):
        with self.assertRaises(ValueError):
            self.check(expected_manifest='1'*64)

    def test_forged_excerpt_rehashed_still_fails_reproduction(self):
        def forge(v):
            v['receipt']['result']['hits'][0]['text'] = 'forged evidence'
        pin = self.replace_bundle(forge)
        with self.assertRaisesRegex(ValueError, 'does not reproduce'):
            self.check(pin)

    def test_rehashed_changed_document_cannot_become_proof(self):
        def forge(v):
            doc = v['index']['documents'][0]
            doc['text'] += 'Unproven assertion.\n'
            doc['sha256'] = h.e.digest(doc['text'].encode())
            v['receipt']['sources'] = h.b.receipt.manifest(v['index'])
        pin = self.replace_bundle(forge)
        with self.assertRaisesRegex(ValueError, 'differs from reverified'):
            self.check(pin)

    def test_missing_account_document_rejected(self):
        def forge(v):
            v['index']['documents'].pop()
            v['receipt']['sources'] = h.b.receipt.manifest(v['index'])
        pin = self.replace_bundle(forge)
        with self.assertRaisesRegex(ValueError, 'differs from reverified'):
            self.check(pin)

    def test_bundle_immutability_exclusive_output_and_cleanup(self):
        before = self.output.read_bytes()
        self.check()
        self.assertEqual(self.output.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['bundle.json'])
        with self.assertRaises(FileExistsError):
            h.pack(h.DEMO_MANIFEST, h.p.a.DEMO_HASH, 'storage', self.output, self.root)
        self.assertEqual(self.output.read_bytes(), before)

    def test_no_hit_receipt_valid(self):
        self.output.unlink()
        self.created = h.pack(h.DEMO_MANIFEST, h.p.a.DEMO_HASH,
                              'unmatchableword', self.output, self.root)
        result = self.check()
        self.assertTrue(result['verified'])
        self.assertEqual(result['search']['hits'], [])

    def test_relocation_without_line_folders(self):
        # Copy only this shared tool; all fixtures and dependencies travel with it.
        isolated = self.root / 'isolated'
        shutil.copytree(h.HERE, isolated)
        proc = subprocess.run([sys.executable, '-B', 'handoff.py', 'demo'],
                              cwd=isolated, capture_output=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(json.loads(proc.stdout)['verified'])

    def test_cli_failure_has_no_partial_success(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = h.main(['check', str(h.DEMO_MANIFEST), '--block-hash', h.p.a.DEMO_HASH,
                             '--bundle', str(self.output), '--expected-sha256', '1'*64])
        self.assertEqual(status, 2)
        self.assertEqual(out.getvalue(), '')
        self.assertFalse(json.loads(err.getvalue())['verified'])


if __name__ == '__main__':
    unittest.main()
