#!/usr/bin/env python3
"""Carry searchable, reproduced proof results between offline workers."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


p = load('handoff_proofs', 'tools/proof-set/proof_set.py')
b = load('handoff_bundle', 'tools/evidence-bundle/bundle.py')
e = b.engine
DEMO_MANIFEST = HERE / 'tools/proof-set/examples/zto-and-pool.json'


def proof_report(manifest_path, block_hash, expected_manifest=None):
    path = e.workspace_path(manifest_path)
    manifest, base, digest = p.load_manifest(path)
    if expected_manifest is not None:
        if not b.receipt.valid_hash(expected_manifest) or digest != expected_manifest:
            raise ValueError('manifest does not match separately retained SHA-256')
    return p.verify(manifest, base, block_hash, digest)


def documents(report):
    """No witness labels or unchecked source prose become proven assertions."""
    texts = {}
    anchor = report['anchor']
    for row in report['accounts']:
        address = row['state']['address']
        data = {'anchor': anchor, 'account': row}
        texts[address[2:] + '.md'] = (
            '# Ethereum account proof result\n'
            'Address: ' + address + '\n'
            'Block number (decimal): ' + str(int(anchor['blockNumber'], 16)) + '\n'
            'Checkpoint, canonicality and finality require independent authentication.\n'
            'Raw storage slots are not interpreted as price, decimals or token balance.\n'
            'Stored code identity does not establish source or execution behavior.\n'
            '```json\n' + json.dumps(data, sort_keys=True, indent=2) + '\n```\n')
    return texts


def scratch_parent(path):
    parent = e.workspace_path(path)
    parent.mkdir(parents=True, exist_ok=True)
    return parent


def pack(manifest, block_hash, query, output, scratch='test/scratch',
         expected_manifest=None, limit=5, require_all=False):
    report = proof_report(manifest, block_hash, expected_manifest)
    # Only this newly created temporary directory is removed on return.
    with tempfile.TemporaryDirectory(dir=scratch_parent(scratch), prefix='proof-handoff-') as tmp:
        root = Path(tmp)
        for name, text in documents(report).items():
            (root / name).write_bytes(text.encode('utf-8'))
        value = b.pack(root, query, limit, require_all)
        b.write(output, value)  # Exclusive: never overwrite a user's bundle.
    return {'format': 'proof-handoff-created/v1', 'bundle_sha256': b.identity(value),
            'manifest_sha256': report['manifestSha256'], 'anchor': report['anchor'],
            'documents': len(value['index']['documents'])}


def check(manifest, block_hash, bundle, expected_bundle, scratch='test/scratch',
          expected_manifest=None, query=None):
    value = b.load(bundle)
    integrity = b.check(value, expected_bundle)
    if not integrity['integrity_matches']:
        raise ValueError('bundle pin mismatch')
    report = proof_report(manifest, block_hash, expected_manifest)
    actual = {d['path']: d['text'] for d in value['index']['documents']}
    if actual != documents(report):
        raise ValueError('bundled corpus differs from reverified proof results')
    with tempfile.TemporaryDirectory(dir=scratch_parent(scratch), prefix='proof-handoff-') as tmp:
        root = Path(tmp) / 'restored'
        restored = b.unpack(value, root, expected_bundle)
        if not restored['receipt_reproduced']:
            raise ValueError('saved search does not reproduce')
        search = value['receipt']['result'] if query is None else e.search(
            e.build_index(root), query, root)
    return {'format': 'proof-handoff-checked/v1', 'verified': True,
            'proofs_verified': True, 'corpus_matches_proofs': True,
            'receipt_reproduced': True, 'bundle_sha256': b.identity(value),
            'manifest_sha256': report['manifestSha256'],
            'anchor': report['anchor'], 'accounts': len(report['accounts']),
            'search': search, 'trust': report['trust']}


def demo(scratch='test/scratch'):
    # Fixed demonstration checkpoint is historical RPC data, not consensus trust.
    with tempfile.TemporaryDirectory(dir=scratch_parent(scratch), prefix='handoff-demo-') as tmp:
        output = Path(tmp) / 'bundle.json'
        created = pack(DEMO_MANIFEST, p.a.DEMO_HASH, 'storage value', output, scratch)
        result = check(DEMO_MANIFEST, p.a.DEMO_HASH, output,
                       created['bundle_sha256'], scratch,
                       expected_manifest=created['manifest_sha256'])
    result['demo'] = 'Historical ZTO and ZTO/IMD pool; checkpoint is an inherited RPC observation.'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch-parent', default='test/scratch')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    make = sub.add_parser('pack')
    make.add_argument('--query', required=True)
    make.add_argument('--output', required=True)
    make.add_argument('--limit', type=int, default=5)
    make.add_argument('--all', action='store_true')
    verify = sub.add_parser('check')
    verify.add_argument('--bundle', required=True)
    verify.add_argument('--expected-sha256', required=True)
    verify.add_argument('--query', help='optional new query after receipt reproduction')
    for command in (make, verify):
        command.add_argument('manifest')
        command.add_argument('--block-hash', required=True)
        command.add_argument('--manifest-sha256')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo(args.scratch_parent)
        elif args.command == 'pack':
            result = pack(args.manifest, args.block_hash, args.query, args.output,
                          args.scratch_parent, args.manifest_sha256, args.limit, args.all)
        else:
            result = check(args.manifest, args.block_hash, args.bundle, args.expected_sha256,
                           args.scratch_parent, args.manifest_sha256, args.query)
        print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RecursionError):
        print(json.dumps({'verified': False, 'error':
              'Invalid proof, checkpoint, pin, corpus, search receipt or workspace path.'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
