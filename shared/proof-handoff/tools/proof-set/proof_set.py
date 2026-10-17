#!/usr/bin/env python3
"""Verify a bounded set of Ethereum state proofs against one trusted block hash.

Offline Python standard library only. This composes the sibling Header Anchor,
State Witness, and optional Code Witness without signing or sending anything.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'code_witness_for_proof_set', HERE.parent / 'code-witness' / 'code_witness.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
a, w = c.a, c.w

MAX_MANIFEST = 65_536
MAX_ACCOUNTS = 32


def load_manifest(path):
    """Read a bounded, duplicate-key-free manifest from this workspace."""
    resolved = w.workspace_path(path)
    with resolved.open('rb') as stream:
        raw = stream.read(MAX_MANIFEST + 1)
    w.require(len(raw) <= MAX_MANIFEST, 'manifest exceeds 64 KiB limit')
    return w.parse_json(raw), resolved.parent, hashlib.sha256(raw).hexdigest()


def exact_keys(value, required, optional=()):
    w.require(isinstance(value, dict), 'manifest and account entries must be objects')
    w.require(set(required) <= set(value) and set(value) <= set(required) | set(optional),
              'missing or unknown manifest/account field')


def relative_file(base, value):
    w.require(isinstance(value, str) and value and '\0' not in value,
              'file reference must be a nonempty relative path')
    path = Path(value)
    w.require(not path.is_absolute(), 'file reference must be relative to manifest')
    return w.workspace_path(base / path)


def check_manifest(manifest):
    exact_keys(manifest, ('format', 'header', 'accounts'))
    w.require(manifest['format'] == 'proof-set/1', 'unsupported manifest format')
    w.require(isinstance(manifest['accounts'], list) and
              1 <= len(manifest['accounts']) <= MAX_ACCOUNTS,
              'manifest must contain 1..32 accounts')
    seen = set()
    for i, entry in enumerate(manifest['accounts']):
        exact_keys(entry, ('address', 'slots', 'witness'), ('code',))
        address = w.hex_data(entry['address'], 20, f'account {i} address')
        w.require(address not in seen, 'duplicate account address')
        seen.add(address)
        slots = entry['slots']
        w.require(isinstance(slots, list) and len(slots) <= 64,
                  f'account {i}: at most 64 slots allowed')
        numbers = [w.slot_number(slot) for slot in slots]
        w.require(len(set(numbers)) == len(numbers), f'account {i}: duplicate requested storage slot')
    return manifest


def verify(manifest, base, trusted_hash, manifest_sha256=None):
    """Fail atomically if any requested account, slot, header or code is wrong."""
    check_manifest(manifest)
    header = a.load_header(relative_file(base, manifest['header']))
    anchor = a.verify_header(header, trusted_hash)
    results = []
    for i, entry in enumerate(manifest['accounts']):
        try:
            witness = w.load_bundle(relative_file(base, entry['witness']))
            # Bundle metadata is deliberately ignored. The manifest states the
            # caller's expected addresses and slots; the verified header supplies
            # the root for every proof in this set.
            state = w.verify(witness.get('proof'), anchor['stateRoot'],
                             entry['address'], entry['slots'])
            state.pop('trust')
            result = {'state': state}
            if 'code' in entry:
                code = c.decode_code(c.load_code(relative_file(base, entry['code'])))
                actual = w.hex0(w.keccak256(code))
                w.require(actual == state['codeHash'],
                          'supplied code does not match proven account code hash')
                delegated = len(code) == 23 and code[:3] == bytes.fromhex('ef0100')
                kind = 'delegation-indicator' if delegated else ('empty' if not code else 'nonempty')
                result['code'] = {'verified': True, 'byteLength': len(code),
                                  'keccak256': actual, 'storedCodeKind': kind}
                if delegated:
                    result['code']['delegationTarget'] = w.hex0(code[3:])
            results.append(result)
        except w.Invalid as error:
            raise w.Invalid(f'account {i} ({entry["address"]}): {error}') from error
    return {
        'verified': True, 'anchor': anchor, 'accounts': results,
        'manifestSha256': manifest_sha256,
        'trust': ('Every listed account and slot is proven against one header matching the supplied hash. '
                  'The caller must authenticate that hash, chain, canonicality and finality independently. '
                  'Code checks establish stored byte identity only, not source, ABI, layout, proxy targets or behavior.'),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='check historical real ZTO and ZTO/IMD pool together, offline')
    check = sub.add_parser('verify', help='check a caller-authored manifest at an explicit trusted hash')
    check.add_argument('manifest')
    check.add_argument('--block-hash', required=True)
    check.add_argument('--manifest-sha256', help='optional separately obtained manifest fingerprint')
    args = parser.parse_args(argv)
    try:
        path = HERE / 'examples' / 'zto-and-pool.json' if args.command == 'demo' else args.manifest
        manifest, base, digest = load_manifest(path)
        if args.command == 'verify' and args.manifest_sha256 is not None:
            supplied = w.hex_data(args.manifest_sha256, 32, 'manifest SHA-256')
            w.require(supplied == bytes.fromhex(digest), 'manifest SHA-256 differs from expected')
        trusted = a.DEMO_HASH if args.command == 'demo' else args.block_hash
        result = verify(manifest, base, trusted, digest)
        if args.command == 'demo':
            result['demo'] = ('Historical RPC observation; the fixed demonstration hash '
                              'is not a consensus-authenticated checkpoint.')
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except w.Invalid as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({'verified': False,
                          'error': 'Unreadable or malformed manifest, header, witness or code.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
