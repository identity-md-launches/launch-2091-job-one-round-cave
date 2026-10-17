#!/usr/bin/env python3
"""Whole-corpus freshness checking and fail-closed offline passage search."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

# Reuse the ancestor's validation, corpus selection, limits and citation engine.
_engine_path = Path(__file__).absolute().parents[1] / 'evidence-search' / 'search.py'
_spec = importlib.util.spec_from_file_location('evidence_search', _engine_path)
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)


def compare(index, current):
    """Compare validated snapshots without trusting timestamps or document order."""
    engine.validate_index(index)
    engine.validate_index(current)
    old = {doc['path']: doc['sha256'] for doc in index['documents']}
    new = {doc['path']: doc['sha256'] for doc in current['documents']}
    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = sorted(name for name in old.keys() & new.keys() if old[name] != new[name])
    return {'format': 'evidence-corpus-freshness/v1',
            'fresh': not (added or removed or changed),
            'indexed_documents': len(old), 'current_documents': len(new),
            'added': added, 'removed': removed, 'changed': changed}


def audit(index, root):
    # A full rebuild applies exactly the same eligibility and resource policies.
    # Malformed/unreadable/over-budget corpora raise, never report "fresh".
    engine.validate_index(index)
    return compare(index, engine.build_index(root))


def checked_query(index, root, query, limit=5, require_all=False):
    freshness = audit(index, root)
    if not freshness['fresh']:
        return {'freshness': freshness, 'search': None}
    result = engine.search(index, query, root, limit, require_all)
    return {'freshness': freshness, 'search': result}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('check', help='compare every eligible source with an existing index')
    query = sub.add_parser('query', help='search only if the whole corpus is unchanged')
    for command in (check, query):
        command.add_argument('root')
        command.add_argument('--index', required=True)
    query.add_argument('query')
    query.add_argument('--limit', type=int, default=5)
    query.add_argument('--all', action='store_true')
    sub.add_parser('demo', help='audit and search bundled ZTO evidence without writing files')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            root = _engine_path.parent / 'examples' / 'docs'
            result = checked_query(engine.build_index(root), root, 'ZTO token decimals')
        else:
            index = engine.load_index(args.index)
            if args.command == 'check':
                result = audit(index, args.root)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0 if result['fresh'] else 1
            result = checked_query(index, args.root, args.query, args.limit, args.all)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['search'] and result['search']['hits'] else 1
    except (engine.SearchError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
