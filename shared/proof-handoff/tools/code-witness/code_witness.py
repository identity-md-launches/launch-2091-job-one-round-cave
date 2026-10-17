#!/usr/bin/env python3
"""Verify supplied account code bytes against a block-hash-anchored state proof.

Offline; Python standard library only. Input paths stay within the workspace.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'header_anchor_for_code', HERE.parent / 'header-anchor' / 'anchor.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
w = a.w
MAX_CODE = 49_000  # Tool resource bound, not a consensus code-size rule.


def decode_code(value):
    w.require(isinstance(value, str), 'code must be a 0x-prefixed hex string')
    w.require(len(value) <= 2 + MAX_CODE * 2, 'code exceeds tool limit of 49000 bytes')
    return w.hex_data(value, label='account code')


def load_code(path):
    """One ASCII hex string, optionally followed by exactly one newline."""
    with w.workspace_path(path).open('rb') as stream:
        raw = stream.read(2 + MAX_CODE * 2 + 2)
    w.require(len(raw) <= 2 + MAX_CODE * 2 + 1, 'code file exceeds tool limit')
    text = raw.decode('ascii')
    if text.endswith('\n'):
        text = text[:-1]
    decode_code(text)
    return text


def verify(header, bundle, code_hex, trusted_hash, address, slots):
    code = decode_code(code_hex)
    result = a.verify(header, bundle, trusted_hash, address, slots)
    state = result['state']
    actual = w.hex0(w.keccak256(code))
    w.require(actual == state['codeHash'], 'supplied code does not match proven account code hash')
    # This reports stored bytes, never claims that a proxy/delegation target's
    # executable code has also been verified.
    delegated = len(code) == 23 and code[:3] == bytes.fromhex('ef0100')
    kind = 'delegation-indicator' if delegated else ('empty' if not code else 'nonempty')
    result['code'] = {'verified': True, 'byteLength': len(code),
                      'keccak256': actual, 'storedCodeKind': kind}
    if delegated:
        result['code']['delegationTarget'] = w.hex0(code[3:])
    result['trust'] += (' Supplied bytes match the account code commitment only. '
                        'Source, ABI, storage layout, proxy/delegation targets and '
                        'execution behavior are not verified. Empty bytes do not '
                        'establish that an address has no protocol-defined behavior.')
    return result


def demo_inputs():
    return (a.load_header(a.HERE / 'examples' / 'zto-header-mainnet.json'),
            w.load_bundle(HERE.parent / 'state-witness' / 'examples' / 'zto-mainnet.json'),
            load_code(HERE / 'examples' / 'zto-runtime.hex'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='verify real historical ZTO account code offline')
    check = sub.add_parser('verify', help='verify code, header and account/storage proof')
    check.add_argument('header')
    check.add_argument('witness')
    check.add_argument('code', help='workspace ASCII 0x-prefixed hex file')
    check.add_argument('--block-hash', required=True)
    check.add_argument('--address', required=True)
    check.add_argument('--slot', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = verify(*demo_inputs(), a.DEMO_HASH, w.ZTO, ['0x0', '0x1'])
            result['demo'] = 'Historical ZTO mainnet observation; bundled hash is not an independently authenticated checkpoint.'
        else:
            result = verify(a.load_header(args.header), w.load_bundle(args.witness),
                            load_code(args.code), args.block_hash, args.address, args.slot)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except w.Invalid as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({'verified': False, 'error': 'Unreadable or malformed code, header or witness.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
