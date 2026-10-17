"""Tests use only scratch workspace inputs and no external service."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('recheck', HERE / 'recheck.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RecheckTests(unittest.TestCase):
    def setUp(self):
        scratch = Path.cwd() / 'test' / 'scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dirs = [self.root / side for side in r.tree.SIDES]
        for folder in self.dirs:
            folder.mkdir()
            (folder / 'note.txt').write_bytes(b'first\r\nsecond\r\n')
        (self.dirs[1] / 'note.txt').write_bytes(b'ours\r\nsecond\r\n')
        (self.dirs[2] / 'note.txt').write_bytes(b'first\r\ntheirs\r\n')
        self.packet = self.root / 'packet.json'
        self.report = r.tree.from_directories(self.dirs)
        self.packet.write_text(json.dumps(self.report), encoding='utf-8')

    def run_cli(self, *extra):
        return subprocess.run([sys.executable, '-B', str(HERE / 'recheck.py'),
                               str(self.packet), *map(str, self.dirs), *extra],
                              capture_output=True)

    def test_real_tree_roundtrip_and_immutability(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'matches-clean')
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_stale_even_if_candidate_same(self):
        # All sides gain the same empty directory, leaving merged text untouched.
        for folder in self.dirs:
            (folder / 'new-directory').mkdir()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['changed_inputs'], list(r.tree.SIDES))

    def test_every_report_field_checked(self):
        for key, value in [('clean', False), ('files', []), ('counts', {}),
                           ('path_conflicts', ['invented']), ('limits', [])]:
            altered = copy.deepcopy(self.report)
            altered[key] = value
            self.assertEqual(r.compare(altered, self.report)['status'], 'review-mismatch')

    def test_candidate_and_hash_tampering(self):
        for key in ('candidate', 'candidate_sha256'):
            altered = copy.deepcopy(self.report)
            altered['files'][0][key] = 'replacement'
            self.assertFalse(r.compare(altered, self.report)['matches'])

    def test_json_type_confusion(self):
        altered = copy.deepcopy(self.report)
        altered['clean'] = 1
        self.assertFalse(r.compare(altered, self.report)['matches'])
        altered = copy.deepcopy(self.report)
        altered['inputs']['ours']['files'] = True
        self.assertEqual(r.compare(altered, self.report)['changed_inputs'], ['ours'])

    def test_whitespace_and_key_order_irrelevant(self):
        self.packet.write_text(json.dumps(self.report, sort_keys=True, indent=4))
        self.assertEqual(self.run_cli().returncode, 0)

    def test_independent_digest(self):
        digest = hashlib.sha256(self.packet.read_bytes()).hexdigest()
        self.assertEqual(self.run_cli('--expected-sha256', digest).returncode, 0)
        self.packet.write_bytes(self.packet.read_bytes() + b'\n')
        result = self.run_cli('--expected-sha256', digest)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')

    def test_invalid_packets(self):
        for data in (b'[]', b'{}', b'{"schema":1,"schema":2}', b'{"x":NaN}',
                     b'{"x":Infinity}', b'\xff', b'{'):
            self.packet.write_bytes(data)
            result = self.run_cli()
            self.assertEqual(result.returncode, 2, data)
            self.assertEqual(result.stdout, b'')

    def test_link_packet_rejected(self):
        link = self.root / 'link.json'
        link.symlink_to(self.packet.name)
        with self.assertRaises(ValueError):
            r.load_packet(link)

    def test_escape_and_size_rejected(self):
        for path in ('../packet.json', '/etc/passwd'):
            with self.assertRaises(ValueError):
                r.load_packet(path)
        old = r.MAX_PACKET_BYTES
        try:
            r.MAX_PACKET_BYTES = 8
            with self.assertRaises(ValueError):
                r.load_packet(self.packet)
        finally:
            r.MAX_PACKET_BYTES = old

    def test_all_demos(self):
        for mode, code in [('clean', 0), ('conflict', 0), ('stale', 1), ('tampered', 1)]:
            result = subprocess.run([sys.executable, '-B', str(HERE / 'recheck.py'),
                                     '--demo', mode], capture_output=True)
            self.assertEqual(result.returncode, code, result.stderr)
            self.assertEqual(json.loads(result.stdout)['matches'], code == 0)
        self.assertFalse(r.demo('conflict')['current_clean'])

    def test_conflict_and_deletion_reproducible(self):
        (self.dirs[2] / 'note.txt').unlink()
        report = r.tree.from_directories(self.dirs)
        self.assertFalse(report['clean'])
        self.assertTrue(r.compare(report, report)['matches'])

    def test_line_endings_stale(self):
        source = self.dirs[0] / 'note.txt'
        source.write_bytes(source.read_bytes().replace(b'\r\n', b'\n'))
        result = json.loads(self.run_cli().stdout)
        self.assertEqual(result['changed_inputs'], ['base'])


if __name__ == '__main__':
    unittest.main()
