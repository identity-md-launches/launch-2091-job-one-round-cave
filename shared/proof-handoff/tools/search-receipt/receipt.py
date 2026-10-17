#!/usr/bin/env python3
"""Portable offline search receipts, checked against a caller-retained hash."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

_freshness_path = Path(__file__).absolute().parents[1] / 'corpus-freshness' / 'freshness.py'
_spec = importlib.util.spec_from_file_location('receipt_freshness', _freshness_path)
freshness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(freshness)
engine = freshness.engine

FORMAT = 'evidence-search-receipt/v1'
MAX_RECEIPT_BYTES = 12_000_000


def canonical(value):
    """Canonical UTF-8 JSON; whitespace in a saved JSON file is immaterial."""
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise engine.SearchError('receipt cannot be encoded as canonical JSON') from None


def receipt_hash(receipt):
    return hashlib.sha256(canonical(receipt)).hexdigest()


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def manifest(index):
    return sorted(({'path': doc['path'], 'sha256': doc['sha256']}
                   for doc in index['documents']), key=lambda item: item['path'])


def validate(receipt):
    """Reject malformed metadata before any caller-selected corpus is read.

    Hit contents are compared byte-for-byte with regenerated results in verify;
    no path or instruction from a hit is ever used for a filesystem operation.
    """
    if not isinstance(receipt, dict) or set(receipt) != {'format', 'request', 'sources', 'result'}:
        raise engine.SearchError('invalid receipt envelope')
    if receipt['format'] != FORMAT:
        raise engine.SearchError('unsupported receipt format')
    request = receipt['request']
    if not isinstance(request, dict) or set(request) != {'query', 'limit', 'require_all'}:
        raise engine.SearchError('invalid receipt request')
    query, limit, require_all = request['query'], request['limit'], request['require_all']
    if not isinstance(query, str) or len(query) > 4096 or not engine.tokens(query):
        raise engine.SearchError('query must contain a word or address and be at most 4096 characters')
    if type(limit) is not int or not 1 <= limit <= 50:
        raise engine.SearchError('limit must be an integer between 1 and 50')
    if type(require_all) is not bool:
        raise engine.SearchError('require_all must be boolean')
    sources = receipt['sources']
    if not isinstance(sources, list) or len(sources) > engine.MAX_FILES:
        raise engine.SearchError('invalid receipt source count')
    names = []
    for source in sources:
        if not isinstance(source, dict) or set(source) != {'path', 'sha256'}:
            raise engine.SearchError('invalid receipt source')
        if not engine.valid_relative(source['path']) or not valid_hash(source['sha256']):
            raise engine.SearchError('invalid receipt source path or hash')
        names.append(source['path'])
    if names != sorted(set(names)):
        raise engine.SearchError('receipt sources must be unique and sorted')
    result = receipt['result']
    if not isinstance(result, dict) or not isinstance(result.get('hits'), list):
        raise engine.SearchError('invalid receipt result')
    if len(result['hits']) > limit:
        raise engine.SearchError('receipt hit count exceeds requested limit')
    if len(canonical(receipt)) > MAX_RECEIPT_BYTES:
        raise engine.SearchError('receipt byte limit exceeded')
    return receipt


def assemble(index, query, limit, require_all, result):
    return validate({'format': FORMAT,
                     'request': {'query': query, 'limit': limit, 'require_all': require_all},
                     'sources': manifest(index), 'result': result})


def create(root, query, limit=5, require_all=False):
    # Validate request types even for an empty corpus, before reading sources.
    validate({'format': FORMAT, 'request': {'query': query, 'limit': limit,
              'require_all': require_all}, 'sources': [], 'result': {'hits': []}})
    index = engine.build_index(root)
    checked = freshness.checked_query(index, root, query, limit, require_all)
    if not checked['freshness']['fresh']:
        raise engine.SearchError('corpus changed during receipt creation; retry in a static workspace')
    return assemble(index, query, limit, require_all, checked['search'])


def source_changes(sources, current):
    old = {source['path']: source['sha256'] for source in sources}
    new = {source['path']: source['sha256'] for source in manifest(current)}
    added, removed = sorted(new.keys() - old.keys()), sorted(old.keys() - new.keys())
    changed = sorted(name for name in old.keys() & new.keys() if old[name] != new[name])
    return {'fresh': not (added or removed or changed), 'added': added,
            'removed': removed, 'changed': changed}


def verify(receipt, root, expected_sha256):
    """Reproduce a pinned search using only the receipt and the source corpus.

    expected_sha256 must come from the caller's earlier retained value or trusted
    handoff; reading it from the same untrusted receipt defeats this binding.
    """
    if not valid_hash(expected_sha256):
        raise engine.SearchError('expected SHA-256 must be 64 lowercase hexadecimal characters')
    validate(receipt)
    actual = receipt_hash(receipt)
    report = {'format': 'evidence-search-receipt-check/v1', 'verified': False,
              'receipt_sha256': actual, 'expected_sha256': expected_sha256,
              'hash_matches': actual == expected_sha256,
              'sources': None, 'result_matches': None}
    if not report['hash_matches']:
        report['reason'] = 'receipt_hash_mismatch'
        return report
    # The caller supplies root explicitly; receipt paths cannot select a root.
    current = engine.build_index(root)
    report['sources'] = source_changes(receipt['sources'], current)
    if not report['sources']['fresh']:
        report['reason'] = 'corpus_changed'
        return report
    request = receipt['request']
    checked = freshness.checked_query(current, root, request['query'],
                                      request['limit'], request['require_all'])
    if not checked['freshness']['fresh']:
        report['reason'] = 'corpus_changed_during_verification'
        report['sources'] = checked['freshness']
        return report
    reproduced = assemble(current, request['query'], request['limit'],
                          request['require_all'], checked['search'])
    # Canonical bytes distinguish bool/int, int/float, missing/extra fields,
    # order, excerpts, line numbers, hashes and every ranking/result attribute.
    report['result_matches'] = canonical(receipt) == canonical(reproduced)
    report['verified'] = report['result_matches']
    report['reason'] = 'verified' if report['verified'] else 'result_not_reproducible'
    return report


def reject_constant(value):
    raise engine.SearchError('non-finite JSON numbers are not allowed')


def load(filename):
    raw = engine.read_bytes(engine.workspace_path(filename), MAX_RECEIPT_BYTES)
    try:
        receipt = json.loads(raw, object_pairs_hook=engine.reject_duplicates,
                             parse_constant=reject_constant)
    except engine.SearchError:
        raise
    except (UnicodeError, ValueError, RecursionError):
        raise engine.SearchError('receipt is not valid UTF-8 JSON') from None
    return validate(receipt)


def write(filename, receipt):
    validate(receipt)
    path = engine.workspace_path(filename)
    if path.suffix.lower() != '.json':
        raise engine.SearchError('receipt output must have a .json extension')
    raw = canonical(receipt) + b'\n'
    if len(raw) > MAX_RECEIPT_BYTES:
        raise engine.SearchError('serialized receipt byte limit exceeded')
    if not path.parent.is_dir():
        raise engine.SearchError('receipt parent directory must already exist')
    try:
        with path.open('xb') as stream:
            stream.write(raw)
    except FileExistsError:
        raise engine.SearchError('receipt output already exists; choose a new filename') from None


def demo():
    root = _freshness_path.parent.parent / 'evidence-search' / 'examples' / 'docs'
    receipt = create(root, 'ZTO token decimals', require_all=True)
    expected = receipt_hash(receipt)
    return {'receipt': receipt, 'verification': verify(receipt, root, expected),
            'note': 'Historical bundled ZTO evidence; verification does not establish factual truth or current chain state.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    make = commands.add_parser('create', help='write a new receipt and print its canonical SHA-256')
    make.add_argument('root')
    make.add_argument('query')
    make.add_argument('--output', required=True)
    make.add_argument('--limit', type=int, default=5)
    make.add_argument('--all', action='store_true')
    check = commands.add_parser('verify', help='check a receipt against a separately retained SHA-256')
    check.add_argument('root')
    check.add_argument('--receipt', required=True)
    check.add_argument('--expected-sha256', required=True)
    commands.add_parser('demo', help='create and verify bundled ZTO evidence in memory; writes nothing')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
            status = 0 if result['verification']['verified'] else 1
        elif args.command == 'create':
            # Prevent a .md/.txt/.rst output inside the corpus from invalidating
            # the newly created receipt simply by becoming another source.
            root = engine.workspace_path(args.root)
            output = engine.workspace_path(args.output)
            if output.suffix.lower() != '.json':
                raise engine.SearchError('receipt output must have a .json extension')
            receipt = create(root, args.query, args.limit, args.all)
            write(output, receipt)
            result = {'receipt': args.output, 'receipt_sha256': receipt_hash(receipt),
                      'documents': len(receipt['sources']), 'hits': len(receipt['result']['hits'])}
            status = 0
        else:
            result = verify(load(args.receipt), args.root, args.expected_sha256)
            status = 0 if result['verified'] else 1
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return status
    except (engine.SearchError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
