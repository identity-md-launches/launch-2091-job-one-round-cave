"""Offline integration checks using the real historical ZTO and pool proofs."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('proof_set_for_tests', HERE / 'proof_set.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class ProofSetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.base, cls.digest = p.load_manifest(HERE / 'examples' / 'zto-and-pool.json')

    def test_real_zto_and_pool_share_one_checked_root(self):
        result = p.verify(self.manifest, self.base, p.a.DEMO_HASH, self.digest)
        self.assertTrue(result['verified'])
        self.assertEqual(len(result['accounts']), 2)
        self.assertEqual(result['accounts'][0]['code']['byteLength'], 1287)
        self.assertEqual(result['accounts'][0]['state']['address'], p.w.ZTO)
        self.assertEqual(result['accounts'][1]['state']['address'], p.w.POOL_MANAGER)
        self.assertEqual(result['accounts'][1]['state']['storage'][0]['value'],
                         '0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41')
        self.assertEqual({row['state']['stateRoot'] for row in result['accounts']},
                         {result['anchor']['stateRoot']})

    def test_wrong_checkpoint_fails_everything(self):
        with self.assertRaisesRegex(p.w.Invalid, 'trusted block hash'):
            p.verify(self.manifest, self.base, '0x' + '00' * 32)

    def test_wrong_pool_slot_fails_even_after_valid_zto(self):
        changed = copy.deepcopy(self.manifest)
        changed['accounts'][1]['slots'] = ['0x0']
        with self.assertRaisesRegex(p.w.Invalid, 'account 1 .*storage'):
            p.verify(changed, self.base, p.a.DEMO_HASH)

    def test_wrong_address_rejected_by_proof(self):
        changed = copy.deepcopy(self.manifest)
        changed['accounts'][1]['address'] = '0x' + '11' * 20
        with self.assertRaisesRegex(p.w.Invalid, 'account 1 .*address'):
            p.verify(changed, self.base, p.a.DEMO_HASH)

    def test_duplicate_account_and_slot_rejected(self):
        changed = copy.deepcopy(self.manifest)
        changed['accounts'][1]['address'] = changed['accounts'][0]['address'].upper().replace('0X', '0x')
        with self.assertRaisesRegex(p.w.Invalid, 'duplicate account'):
            p.verify(changed, self.base, p.a.DEMO_HASH)
        changed = copy.deepcopy(self.manifest)
        changed['accounts'][0]['slots'] = ['0x0', '0x00']
        with self.assertRaisesRegex(p.w.Invalid, 'duplicate requested storage'):
            p.verify(changed, self.base, p.a.DEMO_HASH)

    def test_code_mismatch_rejects_set(self):
        with mock.patch.object(p.c, 'load_code', return_value='0x00'):
            with self.assertRaisesRegex(p.w.Invalid, 'account 0 .*code'):
                p.verify(self.manifest, self.base, p.a.DEMO_HASH)

    def test_manifest_shape_and_path_bounds(self):
        changed = copy.deepcopy(self.manifest)
        changed['accounts'].append({'address': '0x' + '22' * 20,
                                    'slots': [], 'witness': 'fake.json', 'sneaky': True})
        with self.assertRaisesRegex(p.w.Invalid, 'unknown'):
            p.verify(changed, self.base, p.a.DEMO_HASH)
        with self.assertRaisesRegex(p.w.Invalid, 'relative'):
            p.relative_file(self.base, '/outside.json')

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(p.w.Invalid, 'duplicate JSON'):
            p.w.parse_json(b'{"format":"proof-set/1","format":"proof-set/1"}')


if __name__ == '__main__':
    unittest.main()
