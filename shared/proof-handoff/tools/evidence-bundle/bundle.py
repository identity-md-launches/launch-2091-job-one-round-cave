#!/usr/bin/env python3
"""Carry a bounded UTF-8 corpus and its search receipt in one offline JSON file."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

_path = Path(__file__).absolute().parents[1] / 'search-receipt' / 'receipt.py'
_spec = importlib.util.spec_from_file_location('bundle_receipt', _path)
receipt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(receipt)
engine = receipt.engine
FORMAT = 'evidence-bundle/v1'
MAX_BYTES = 24_000_000
RECEIPT_NAME = '.search-receipt.json'


def validate(value):
    if not isinstance(value, dict) or set(value) != {'format', 'index', 'receipt'}:
        raise engine.SearchError('invalid bundle envelope')
    if value['format'] != FORMAT:
        raise engine.SearchError('unsupported bundle format')
    index = engine.validate_index(value['index'])
    engine.passages(index)
    saved = receipt.validate(value['receipt'])
    names = [doc['path'] for doc in index['documents']]
    if names != sorted(names):
        raise engine.SearchError('bundle documents must be sorted')
    # A valid search index may still contain paths that cannot coexist on disk.
    paths = set(names)
    for name in names:
        if any(parent.as_posix() in paths for parent in Path(name).parents
               if parent.as_posix() != '.'):
            raise engine.SearchError('source file/directory path conflict')
    if receipt.canonical(saved['sources']) != receipt.canonical(receipt.manifest(index)):
        raise engine.SearchError('receipt manifest differs from bundled sources')
    if len(receipt.canonical(value)) + 1 > MAX_BYTES:
        raise engine.SearchError('bundle byte limit exceeded')
    return value


def identity(value):
    return engine.digest(receipt.canonical(value))


def check(value, expected):
    if not receipt.valid_hash(expected):
        raise engine.SearchError('expected SHA-256 must be 64 lowercase hexadecimal characters')
    validate(value)
    actual = identity(value)
    return {'format': 'evidence-bundle-check/v1', 'integrity_matches': actual == expected,
            'bundle_sha256': actual, 'expected_sha256': expected,
            'documents': len(value['index']['documents']),
            'source_bytes': sum(len(d['text'].encode('utf-8')) for d in value['index']['documents']),
            'receipt_sha256': receipt.receipt_hash(value['receipt']),
            'receipt_reproduced': False}


def pack(root, query, limit=5, require_all=False):
    saved = receipt.create(root, query, limit, require_all)
    index = engine.build_index(root)
    value = validate({'format': FORMAT, 'index': index, 'receipt': saved})
    # Reproduce before publishing. This is a captured collection, not an atomic
    # filesystem snapshot or a claim about future changes to the original root.
    report = receipt.verify(saved, root, receipt.receipt_hash(saved))
    if not report['verified']:
        raise engine.SearchError('corpus changed while packing; retry in a static workspace')
    return value


def load(filename):
    raw = engine.read_bytes(engine.workspace_path(filename), MAX_BYTES)
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=engine.reject_duplicates,
                           parse_constant=receipt.reject_constant)
    except engine.SearchError:
        raise
    except (UnicodeError, ValueError, RecursionError):
        raise engine.SearchError('bundle is not valid UTF-8 JSON') from None
    return validate(value)


def write(filename, value):
    validate(value)
    path = engine.workspace_path(filename)
    if path.suffix.lower() != '.json':
        raise engine.SearchError('bundle output must have a .json extension')
    # Exclusive creation: never replace another worker's file or symlink.
    with path.open('xb') as stream:
        stream.write(receipt.canonical(value) + b'\n')


def unpack(value, destination, expected):
    report = check(value, expected)
    if not report['integrity_matches']:
        return report  # No directories or files created on a pin mismatch.
    root = engine.workspace_path(destination)
    if not root.parent.is_dir():
        raise engine.SearchError('destination parent must already exist')
    root.mkdir()  # Refuses even an existing empty directory.
    # All names and prefix collisions were validated before the first write.
    # On I/O failure leave a partial NEW directory for inspection; never delete
    # or merge into user data. Keep parent directories static against races.
    for doc in value['index']['documents']:
        path = engine.workspace_path(root / doc['path'])
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(doc['text'].encode('utf-8'))
    receipt.write(root / RECEIPT_NAME, value['receipt'])
    verified = receipt.verify(value['receipt'], root, report['receipt_sha256'])
    report['receipt_reproduced'] = verified['verified']
    report['receipt_check'] = verified
    report['destination'] = str(destination)
    return report


def demo():
    root = _path.parent.parent / 'evidence-search' / 'examples' / 'docs'
    value = pack(root, 'ZTO token decimals', require_all=True)
    return {'check': check(value, identity(value)),
            'receipt_result': value['receipt']['result'],
            'note': 'In-memory pack/check; no files written. Unpack reproduces the receipt. Historical ZTO evidence, not current chain state or truth authentication.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    make = sub.add_parser('pack')
    make.add_argument('root')
    make.add_argument('query')
    make.add_argument('--limit', type=int, default=5)
    make.add_argument('--all', action='store_true')
    make.add_argument('--output', required=True)
    for name in ('check', 'unpack'):
        command = sub.add_parser(name)
        command.add_argument('bundle')
        command.add_argument('--expected-sha256', required=True)
        if name == 'unpack':
            command.add_argument('--destination', required=True)
    sub.add_parser('demo')
    args = parser.parse_args(argv)
    try:
        status = 0
        if args.command == 'demo':
            result = demo()
        elif args.command == 'pack':
            value = pack(args.root, args.query, args.limit, args.all)
            write(args.output, value)
            result = {'bundle': args.output, 'bundle_sha256': identity(value),
                      'documents': len(value['index']['documents'])}
        else:
            value = load(args.bundle)
            if args.command == 'check':
                result = check(value, args.expected_sha256)
                status = 0 if result['integrity_matches'] else 1
            else:
                result = unpack(value, args.destination, args.expected_sha256)
                status = 0 if result['receipt_reproduced'] else 1
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return status
    except (engine.SearchError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
