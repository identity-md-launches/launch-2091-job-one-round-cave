"""Behavioral checks; temporary corpora stay under the authorized scratch tree."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bundle', Path(__file__).with_name('bundle.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BundleTests(unittest.TestCase):
    def setUp(self):
        scratch = Path.cwd() / 'test' / 'scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'docs'
        self.root.mkdir()
        (self.root / 'nested').mkdir()
        self.raw = 'ZTO evidence\r\nUnicode frog: 蛙\r\nExact third line.\r\n'.encode()
        (self.root / 'nested' / 'zto.md').write_bytes(self.raw)
        (self.root / 'other.txt').write_text('IMD historical observation\n', encoding='utf-8')

    def value(self):
        return b.pack(self.root, 'ZTO evidence', require_all=True)

    def test_roundtrip_preserves_bytes_and_reproduces_receipt(self):
        value = self.value()
        destination = self.base / 'restored'
        result = b.unpack(value, destination, b.identity(value))
        self.assertTrue(result['integrity_matches'])
        self.assertTrue(result['receipt_reproduced'])
        self.assertEqual((destination / 'nested/zto.md').read_bytes(), self.raw)
        self.assertEqual(result['receipt_check']['sources']['fresh'], True)
        # New searches work with the restored corpus, without the original.
        (self.root / 'nested/zto.md').unlink()
        result = b.engine.search(b.engine.build_index(destination), 'third', destination)
        self.assertEqual(result['hits'][0]['citation'], 'nested/zto.md:1-3')

    def test_mismatch_does_not_write(self):
        value = self.value()
        value['receipt']['request']['query'] = 'different'
        destination = self.base / 'absent'
        result = b.unpack(value, destination, '0' * 64)
        self.assertFalse(result['integrity_matches'])
        self.assertFalse(destination.exists())

    def test_rehashed_forgery_is_not_reproduced(self):
        value = self.value()
        value['receipt']['result']['hits'][0]['text'] = 'forged excerpt'
        # An attacker who supplies their own new pin can pass byte integrity,
        # but cannot reproduce forged ranking/citation data on extraction.
        self.assertTrue(b.check(value, b.identity(value))['integrity_matches'])
        result = b.unpack(value, self.base / 'forged', b.identity(value))
        self.assertFalse(result['receipt_reproduced'])
        self.assertEqual(result['receipt_check']['reason'], 'result_not_reproducible')

    def test_existing_directory_and_output_never_overwritten(self):
        value = self.value()
        with self.assertRaises(FileExistsError):
            b.unpack(value, self.root, b.identity(value))
        path = self.base / 'bundle.json'
        b.write(path, value)
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            b.write(path, value)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual((self.root / 'nested/zto.md').read_bytes(), self.raw)

    def test_paths_and_prefix_conflicts_rejected_before_writes(self):
        value = self.value()
        for name in ('../escape.md', '/escape.md', '.hidden.md', 'a/../../b.md', 'a\\b.md'):
            forged = copy.deepcopy(value)
            forged['index']['documents'][0]['path'] = name
            with self.subTest(name=name), self.assertRaises(b.engine.SearchError):
                b.unpack(forged, self.base / 'bad', b.identity(forged))
            self.assertFalse((self.base / 'bad').exists())
        forged = copy.deepcopy(value)
        forged['index']['documents'] = [
            {'path': name, 'text': 'x', 'sha256': b.engine.digest(b'x')}
            for name in ('a.md', 'a.md/b.md')]
        forged['receipt']['sources'] = b.receipt.manifest(forged['index'])
        with self.assertRaisesRegex(b.engine.SearchError, 'path conflict'):
            b.validate(forged)

    def test_source_tampering_and_manifest_mismatch(self):
        for field in ('text', 'sha256', 'path'):
            value = self.value()
            value['index']['documents'][0][field] = 'changed.md'
            with self.subTest(field=field), self.assertRaises(b.engine.SearchError):
                b.validate(value)
        value = self.value()
        value['receipt']['sources'].pop()
        with self.assertRaisesRegex(b.engine.SearchError, 'manifest'):
            b.validate(value)

    def test_json_duplicates_nonfinite_invalid_and_bounds(self):
        path = self.base / 'bad.json'
        for raw in (b'{"format":1,"format":2}', b'{"x":NaN}', b'\xff', b'[]',
                    '{"format":1}'.encode('utf-16')):
            path.write_bytes(raw)
            with self.assertRaises(b.engine.SearchError):
                b.load(path)
        value = self.value()
        with patch.object(b, 'MAX_BYTES', 30), self.assertRaises(b.engine.SearchError):
            b.validate(value)
        with patch.object(b.engine, 'MAX_FILE_BYTES', 2), self.assertRaises(b.engine.SearchError):
            b.validate(value)
        with patch.object(b.engine, 'MAX_PASSAGES', 0), self.assertRaises(b.engine.SearchError):
            b.validate(value)

    def test_canonical_identity_and_determinism(self):
        value = self.value()
        self.assertEqual(b.identity(value), b.identity(self.value()))
        path = self.base / 'pretty.json'
        path.write_text(json.dumps(value, ensure_ascii=True, indent=4), encoding='utf-8')
        self.assertEqual(b.identity(value), b.identity(b.load(path)))
        value['index']['documents'].reverse()
        with self.assertRaisesRegex(b.engine.SearchError, 'sorted'):
            b.validate(value)

    def test_no_hits_and_empty_corpus(self):
        value = b.pack(self.root, 'unmatchable')
        self.assertEqual(value['receipt']['result']['hits'], [])
        self.assertTrue(b.unpack(value, self.base / 'no-hits', b.identity(value))['receipt_reproduced'])
        empty = self.base / 'empty'
        empty.mkdir()
        value = b.pack(empty, 'ZTO')
        self.assertEqual(value['index']['documents'], [])
        self.assertTrue(b.unpack(value, self.base / 'empty-out', b.identity(value))['receipt_reproduced'])

    def test_hidden_unsupported_and_symlinks_not_carried(self):
        (self.root / '.hidden.md').write_text('hidden')
        (self.root / 'script.py').write_text('raise RuntimeError("never execute")')
        (self.root / 'link.md').symlink_to('other.txt')
        value = self.value()
        self.assertEqual(len(value['index']['documents']), 2)
        destination = self.base / 'link-out'
        destination.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(b.engine.SearchError):
            b.unpack(value, destination, b.identity(value))

    def test_failed_io_leaves_new_partial_output_for_inspection(self):
        value = self.value()
        destination = self.base / 'partial'
        with patch.object(b.receipt, 'write', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                b.unpack(value, destination, b.identity(value))
        self.assertEqual((destination / 'nested/zto.md').read_bytes(), self.raw)
        with self.assertRaises(FileExistsError):
            b.unpack(value, destination, b.identity(value))

    def test_changing_corpus_during_pack_fails(self):
        with patch.object(b.receipt, 'verify', return_value={'verified': False}):
            with self.assertRaisesRegex(b.engine.SearchError, 'changed'):
                self.value()

    def test_workspace_boundary_and_wrong_pin_type(self):
        value = self.value()
        with self.assertRaises(b.engine.SearchError):
            b.unpack(value, '/tmp/outside-workspace', b.identity(value))
        for pin in (None, '', 'A' * 64):
            with self.assertRaises(b.engine.SearchError):
                b.check(value, pin)

    def cli(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = b.main(args)
        return status, out.getvalue(), err.getvalue()

    def test_cli_pack_check_unpack_and_error_statuses(self):
        path = self.base / 'bundle.json'
        code, out, err = self.cli(['pack', str(self.root), 'ZTO', '--output', str(path)])
        self.assertEqual((code, err), (0, ''))
        pin = json.loads(out)['bundle_sha256']
        self.assertEqual(self.cli(['check', str(path), '--expected-sha256', pin])[0], 0)
        self.assertEqual(self.cli(['check', str(path), '--expected-sha256', '0' * 64])[0], 1)
        code, out, err = self.cli(['unpack', str(path), '--expected-sha256', pin,
                                   '--destination', str(self.base / 'cli-out')])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)['receipt_reproduced'])
        code, out, err = self.cli(['pack', str(self.root), 'ZTO', '--output', str(path)])
        self.assertEqual((code, out), (2, ''))
        self.assertIn('error', json.loads(err))

    def test_real_zto_demo(self):
        code, out, err = self.cli(['demo'])
        self.assertEqual((code, err), (0, ''))
        result = json.loads(out)
        self.assertEqual(result['check']['documents'], 3)
        self.assertTrue(result['check']['integrity_matches'])
        self.assertFalse(result['check']['receipt_reproduced'])
        self.assertEqual(result['receipt_result']['hits'][0]['citation'], 'zto.md:1-9')


if __name__ == '__main__':
    unittest.main()
