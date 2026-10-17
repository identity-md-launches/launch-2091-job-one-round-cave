#!/usr/bin/env python3
"""Recompute a saved tree review against current workspace inputs; read only."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

SOURCE = Path(__file__).resolve().parents[1] / 'tree-review' / 'tree_review.py'
SPEC = importlib.util.spec_from_file_location('recheck_tree', SOURCE)
tree = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tree)
MAX_PACKET_BYTES = 64 * 1024 * 1024


def canonical(value):
    # Serialized comparison distinguishes JSON true from 1 and 1 from 1.0.
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(',', ':'), allow_nan=False)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON object key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('non-finite JSON number is not supported')


def load_packet(path, expected_sha256=None):
    candidate = Path(path)
    if '..' in candidate.parts:
        raise ValueError('packet paths must not contain parent traversal')
    # Reuse the tree reader\'s no-symlink, workspace-contained path checks.
    parent = tree.workspace_directory(candidate.parent)
    source = parent / candidate.name
    if source.is_symlink() or not source.is_file():
        raise ValueError('packet must be a regular non-symlink file')
    with source.open('rb') as handle:
        data = handle.read(MAX_PACKET_BYTES + 1)
    if len(data) > MAX_PACKET_BYTES:
        raise ValueError('packet exceeds 64 MiB')
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None:
        if not re.fullmatch('[0-9a-f]{64}', expected_sha256):
            raise ValueError('expected SHA-256 must be 64 lowercase hexadecimal digits')
        if digest != expected_sha256:
            raise ValueError('packet does not match independently retained SHA-256')
    packet = json.loads(data.decode('utf-8'), object_pairs_hook=unique_object,
                        parse_constant=reject_constant)
    validate_packet(packet)
    return packet, digest


def validate_packet(packet):
    if not isinstance(packet, dict) or packet.get('schema') != 'tree-review/v1':
        raise ValueError('expected a tree-review/v1 JSON object')
    if not isinstance(packet.get('inputs'), dict) or set(packet['inputs']) != set(tree.SIDES):
        raise ValueError('packet must contain all three input manifests')
    canonical(packet)


def compare(saved, current):
    validate_packet(saved)
    changed = [side for side in tree.SIDES
               if canonical(saved['inputs'][side]) != canonical(current['inputs'][side])]
    matches = canonical(saved) == canonical(current)
    return {'schema': 'review-recheck/v1', 'matches': matches,
            'changed_inputs': changed,
            'review_matches': matches,
            'current_clean': current['clean'],
            'status': ('matches-clean' if current['clean'] else 'matches-conflicted')
                      if matches else 'stale-inputs' if changed else 'review-mismatch',
            'limits': [
                'Matching verifies reproducibility, not author identity or approval.',
                'A matching conflicted review still requires conflict resolution.',
                'A clean textual merge can be semantically wrong.',
                'Reads require stable trusted workspace trees; no atomic snapshot.',
                'Requires the same tree-review implementation and limits.']}


def demo(mode):
    current = tree.demo(mode == 'conflict')
    saved = json.loads(json.dumps(current))
    if mode == 'stale':
        current = tree.combine([{'files': {'guide.md': text}, 'directories': set()}
                                for text in ('old\n', 'new\n', 'old\n')])
    elif mode == 'tampered':
        saved['files'][0]['candidate'] = 'silently replaced text\n'
    return compare(saved, current)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='SAVED_PACKET BASE_DIR OURS_DIR THEIRS_DIR')
    parser.add_argument('--expected-sha256', help='separately retained exact packet byte hash')
    parser.add_argument('--demo', choices=('clean', 'conflict', 'stale', 'tampered'))
    args = parser.parse_args(argv)
    if args.demo and (args.paths or args.expected_sha256) or not args.demo and len(args.paths) != 4:
        parser.error('provide packet and three directories, or --demo MODE')
    try:
        if args.demo:
            result = demo(args.demo)
        else:
            saved, digest = load_packet(args.paths[0], args.expected_sha256)
            current = tree.from_directories(args.paths[1:])
            result = compare(saved, current)
            result['packet_sha256'] = digest
    except (OSError, ValueError, UnicodeError, RecursionError) as error:
        print('review-recheck: ' + ascii(str(error)), file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=True, indent=2) + '\n')
    return 0 if result['matches'] else 1


if __name__ == '__main__':
    sys.exit(main())
