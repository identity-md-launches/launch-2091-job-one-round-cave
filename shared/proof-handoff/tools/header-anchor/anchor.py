#!/usr/bin/env python3
"""Bind an Ethereum state witness to an explicitly trusted execution block hash.

Offline, standard library only. Never obtains its trust anchor from input JSON.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
VERIFIER = HERE.parent / 'state-witness' / 'witness.py'
spec = importlib.util.spec_from_file_location('state_witness_for_anchor', VERIFIER)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

# Ordered execution-header fields; None denotes a canonical unsigned quantity.
BASE = (
    ('parentHash', 32), ('sha3Uncles', 32), ('miner', 20),
    ('stateRoot', 32), ('transactionsRoot', 32), ('receiptsRoot', 32),
    ('logsBloom', 256), ('difficulty', None), ('number', None),
    ('gasLimit', None), ('gasUsed', None), ('timestamp', None),
    ('extraData', -1), ('mixHash', 32), ('nonce', 8),
)
TAIL = (
    ('baseFeePerGas', None), ('withdrawalsRoot', 32),
    ('blobGasUsed', None), ('excessBlobGas', None),
    ('parentBeaconBlockRoot', 32), ('requestsHash', 32),
)
SCHEMAS = {0: 'legacy', 1: 'london', 2: 'shanghai', 5: 'cancun', 6: 'prague'}
DEMO_HASH = '0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc'
POOL_SLOT = '0x85763e16f60121d4266264cb693cca4d6bdb9e98ff9cc3d698d892d90342971b'


def encode_header(header):
    """Encode a strict header-only RPC object, rejecting ambiguous fork suffixes.

    Does not validate Ethereum consensus or execute transactions. Unknown fields
    fail closed so a future header extension cannot silently be dropped.
    """
    w.require(isinstance(header, dict), 'header must be an object')
    allowed = {name for name, _ in BASE + TAIL} | {'hash'}
    w.require(not (set(header) - allowed), 'unknown header fields: supply a header-only object using a supported schema')
    present = [name in header for name, _ in TAIL]
    count = sum(present)
    w.require(count in SCHEMAS and present == [True] * count + [False] * (len(TAIL) - count),
              'incomplete or unsupported header suffix')
    encoded = []
    for name, size in BASE + TAIL[:count]:
        w.require(name in header, 'missing header field: ' + name)
        if size is None:
            number = w.quantity(header[name], name)
            raw = number.to_bytes((number.bit_length() + 7) // 8, 'big')
        else:
            raw = w.hex_data(header[name], None if size == -1 else size, name)
            if size == -1:
                w.require(len(raw) <= 32, 'extraData exceeds 32 bytes')
        encoded.append(raw)
    return w.rlp_encode(encoded), SCHEMAS[count]


def verify_header(header, trusted_hash):
    expected = w.hex_data(trusted_hash, 32, 'trusted block hash')
    raw, schema = encode_header(header)
    actual = w.keccak256(raw)
    w.require(actual == expected, 'header does not match trusted block hash')
    # hash is redundant RPC metadata; if supplied, it must also agree.
    if 'hash' in header:
        w.require(w.hex_data(header['hash'], 32, 'header hash') == actual, 'RPC header hash claim mismatch')
    return {
        'blockHash': w.hex0(actual), 'stateRoot': w.hex0(w.hex_data(header['stateRoot'], 32)),
        'blockNumber': hex(w.quantity(header['number'])),
        'timestamp': hex(w.quantity(header['timestamp'])), 'headerSchema': schema,
    }


def verify(header, bundle, trusted_hash, address, slots):
    anchor = verify_header(header, trusted_hash)
    w.require(isinstance(bundle, dict) and bundle.get('format') == 'state-witness/1', 'unsupported witness format')
    # Deliberately ignore bundle block/address/slot labels: only the actual proof
    # and caller expectations participate in verification.
    result = w.verify(bundle.get('proof'), anchor['stateRoot'], address, slots)
    result.pop('trust')
    return {
        'verified': True, 'anchor': anchor, 'state': result,
        'trust': 'Header and state proof match the supplied block hash. The caller must authenticate that hash and its chain, canonicality and finality independently. Consensus and execution validity are not checked.',
    }


def load_header(path):
    with w.workspace_path(path).open('rb') as stream:
        raw = stream.read(65_537)
    w.require(len(raw) <= 65_536, 'header exceeds 64 KiB limit')
    header = w.parse_json(raw)
    w.require(isinstance(header, dict), 'header must be an object')
    return header


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='offline real ZTO/IMD pool proof bound to its historical header')
    check = sub.add_parser('verify', help='verify header and witness against a separately trusted hash')
    check.add_argument('header')
    check.add_argument('witness')
    check.add_argument('--block-hash', required=True)
    check.add_argument('--address', required=True)
    check.add_argument('--slot', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            header = load_header(HERE / 'examples' / 'zto-header-mainnet.json')
            bundle = w.load_bundle(HERE.parent / 'state-witness' / 'examples' / 'zto-pool-mainnet.json')
            result = verify(header, bundle, DEMO_HASH, w.POOL_MANAGER, [POOL_SLOT])
            result['demo'] = 'Historical RPC observation; the bundled block hash is illustrative, not a consensus-authenticated checkpoint.'
        else:
            result = verify(load_header(args.header), w.load_bundle(args.witness),
                            args.block_hash, args.address, args.slot)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except w.Invalid as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        print(json.dumps({'verified': False, 'error': 'Unreadable or malformed header or witness.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
