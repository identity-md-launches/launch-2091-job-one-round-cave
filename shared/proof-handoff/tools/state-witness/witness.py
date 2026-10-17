#!/usr/bin/env python3
"""Verify EIP-1186 account/storage witnesses. Python standard library only.

No signing, transactions, wallets, environment access, or third-party packages.
Capture uses exactly eth_chainId, eth_getBlockByNumber, and eth_getProof.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ZTO = '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e'
PUBLIC_RPC = 'https://ethereum-rpc.publicnode.com'
POOL_MANAGER = '0x000000000004444c5dc75cb358380d2e3de08a90'
ZTO_POOL_ID = '0x888b07bd282f587d3c6b0fcb23e7fc55bbb33abe8910dd7492db815dc8dc5592'
MAX_FILE = 1_000_000
MASK = (1 << 64) - 1
ROTATIONS = (
    0, 1, 62, 28, 27, 36, 44, 6, 55, 20, 3, 10, 43,
    25, 39, 41, 45, 15, 21, 8, 18, 2, 61, 56, 14,
)
ROUND_CONSTANTS = (
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
)


class Invalid(ValueError):
    """Invalid input or a proof that does not establish the claim."""


def require(condition, message):
    if not condition:
        raise Invalid(message)


def rotate(value, count):
    return ((value << count) | (value >> ((64 - count) % 64))) & MASK


def keccak256(data):
    """Ethereum's legacy Keccak-256, NOT hashlib.sha3_256."""
    rate = 136
    padded = bytearray(data)
    padded.append(0x01)
    padded.extend(b'\0' * ((-len(padded)) % rate))
    padded[-1] |= 0x80
    state = [0] * 25
    for offset in range(0, len(padded), rate):
        for lane in range(rate // 8):
            state[lane] ^= int.from_bytes(padded[offset + lane * 8:offset + lane * 8 + 8], 'little')
        for rc in ROUND_CONSTANTS:
            columns = [state[x] ^ state[x+5] ^ state[x+10] ^ state[x+15] ^ state[x+20] for x in range(5)]
            deltas = [columns[(x-1) % 5] ^ rotate(columns[(x+1) % 5], 1) for x in range(5)]
            for i in range(25):
                state[i] ^= deltas[i % 5]
            mixed = [0] * 25
            for x in range(5):
                for y in range(5):
                    mixed[y + 5 * ((2*x + 3*y) % 5)] = rotate(state[x + 5*y], ROTATIONS[x + 5*y])
            for x in range(5):
                for y in range(5):
                    state[x + 5*y] = mixed[x + 5*y] ^ ((~mixed[(x+1) % 5 + 5*y]) & mixed[(x+2) % 5 + 5*y])
            state[0] ^= rc
    return b''.join(x.to_bytes(8, 'little') for x in state)[:32]


def hex_data(value, size=None, label='hex data'):
    require(isinstance(value, str) and re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', value) is not None,
            f'{label}: expected even-length 0x-prefixed hex')
    result = bytes.fromhex(value[2:])
    require(size is None or len(result) == size, f'{label}: expected {size} bytes')
    return result


def quantity(value, label='quantity'):
    require(isinstance(value, str) and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)', value) is not None,
            f'{label}: expected canonical unsigned hex quantity')
    result = int(value, 16)
    require(result < 1 << 256, f'{label}: exceeds uint256')
    return result


def slot_number(value):
    """Storage proof keys may be either QUANTITY or zero-padded 32-byte DATA."""
    require(isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]{1,64}', value) is not None,
            'slot: expected 1..64 hex digits with 0x prefix')
    return int(value, 16)


def hex0(data):
    return '0x' + data.hex()


def rlp_encode(value):
    if isinstance(value, list):
        payload = b''.join(rlp_encode(item) for item in value)
        short, long = 0xc0, 0xf7
    else:
        require(isinstance(value, bytes), 'RLP encoder accepts bytes or lists only')
        if len(value) == 1 and value[0] < 0x80:
            return value
        payload, short, long = value, 0x80, 0xb7
    if len(payload) <= 55:
        return bytes([short + len(payload)]) + payload
    length = len(payload).to_bytes((len(payload).bit_length() + 7) // 8, 'big')
    return bytes([long + len(length)]) + length + payload


def rlp_decode(data):
    """Strict canonical RLP with bounded nesting and exact consumption."""
    require(isinstance(data, bytes) and len(data) <= 32768, 'RLP input too large or wrong type')

    def read(start, end, depth):
        require(depth <= 80 and start < end, 'RLP truncated or nesting limit exceeded')
        prefix = data[start]
        if prefix < 0x80:
            return data[start:start+1], start+1
        if prefix <= 0xb7:
            size, begin, is_list = prefix - 0x80, start+1, False
        elif prefix <= 0xbf:
            width, is_list = prefix - 0xb7, False
            require(start+1+width <= end, 'RLP truncated string length')
            raw = data[start+1:start+1+width]
            require(raw[0] != 0, 'RLP noncanonical length')
            size, begin = int.from_bytes(raw, 'big'), start+1+width
            require(size > 55, 'RLP long form used for short string')
        elif prefix <= 0xf7:
            size, begin, is_list = prefix - 0xc0, start+1, True
        else:
            width, is_list = prefix - 0xf7, True
            require(start+1+width <= end, 'RLP truncated list length')
            raw = data[start+1:start+1+width]
            require(raw[0] != 0, 'RLP noncanonical length')
            size, begin = int.from_bytes(raw, 'big'), start+1+width
            require(size > 55, 'RLP long form used for short list')
        stop = begin + size
        require(stop <= end, 'RLP payload truncated')
        if not is_list:
            require(not (size == 1 and data[begin] < 0x80), 'RLP noncanonical single byte')
            return data[begin:stop], stop
        items, cursor = [], begin
        while cursor < stop:
            item, cursor = read(cursor, stop, depth+1)
            items.append(item)
        return items, stop

    value, consumed = read(0, len(data), 0)
    require(consumed == len(data), 'RLP trailing bytes')
    return value


EMPTY_TRIE = keccak256(b'\x80')
EMPTY_CODE = keccak256(b'')


def nibbles(data):
    return [digit for byte in data for digit in (byte >> 4, byte & 15)]


def compact_path(encoded):
    require(isinstance(encoded, bytes) and encoded, 'trie path must be nonempty bytes')
    digits = nibbles(encoded)
    flag = digits[0]
    require(flag <= 3, 'invalid compact path flag')
    require(flag & 1 or digits[1] == 0, 'invalid compact path padding')
    return bool(flag & 2), digits[1:] if flag & 1 else digits[2:]


def trie_value(root, key, proof):
    """Return proven bytes, or None for proven absence; reject incomplete proofs.

    Child nodes shorter than 32 encoded bytes are nested RLP lists, not hashes.
    Proof order is irrelevant. Unrelated nodes do not establish a claim.
    """
    require(isinstance(root, bytes) and len(root) == 32, 'trie root must be 32 bytes')
    require(isinstance(key, bytes) and len(key) <= 64, 'trie key exceeds limit')
    require(isinstance(proof, list) and len(proof) <= 128, 'proof must contain at most 128 nodes')
    nodes = {}
    for item in proof:
        raw = hex_data(item, label='proof node')
        require(0 < len(raw) <= 32768, 'proof node size outside bounds')
        decoded = rlp_decode(raw)
        require(isinstance(decoded, list), 'proof node must be an RLP list')
        nodes[keccak256(raw)] = (decoded, len(raw))
    if root == EMPTY_TRIE:
        return None
    remaining = nibbles(key)
    reference, is_root = root, True
    for _ in range(130):
        if isinstance(reference, list):
            require(len(rlp_encode(reference)) < 32, 'oversized inline trie node')
            node = reference
        else:
            require(isinstance(reference, bytes) and len(reference) == 32,
                    'nonempty trie child must be hash or inline list')
            require(reference in nodes, 'missing proof node or root mismatch')
            node, size = nodes[reference]
            require(is_root or size >= 32, 'short child must be inlined')
        is_root = False
        if len(node) == 17:
            require(isinstance(node[16], bytes), 'branch value must be bytes')
            if not remaining:
                return node[16] or None
            reference = node[remaining[0]]
            remaining = remaining[1:]
            if reference == b'':
                return None
        elif len(node) == 2:
            leaf, path = compact_path(node[0])
            require(leaf or path, 'extension path must not be empty')
            if remaining[:len(path)] != path:
                return None
            remaining = remaining[len(path):]
            if leaf:
                require(isinstance(node[1], bytes) and node[1], 'leaf value must be nonempty bytes')
                return node[1] if not remaining else None
            reference = node[1]
            require(reference != b'', 'extension child must not be empty')
        else:
            raise Invalid('trie node must contain 2 or 17 items')
    raise Invalid('trie traversal exceeded bound')


def rlp_integer(raw, label, max_bytes=32):
    require(isinstance(raw, bytes) and len(raw) <= max_bytes, f'{label}: invalid RLP integer size')
    require(not raw or raw[0] != 0, f'{label}: RLP integer has leading zero')
    return int.from_bytes(raw, 'big')


def verify(proof, root_hex, address_hex, requested_slots):
    """Bind all EIP-1186 claims to caller-specified root, address, and slot set."""
    require(isinstance(proof, dict), 'proof must be an object')
    root = hex_data(root_hex, 32, 'state root')
    address = hex_data(address_hex, 20, 'expected address')
    require(hex_data(proof.get('address'), 20, 'proof address') == address, 'proof address differs from requested address')
    require(isinstance(requested_slots, list) and len(requested_slots) <= 64, 'at most 64 slots allowed')
    expected_slots = [slot_number(item) for item in requested_slots]
    require(len(set(expected_slots)) == len(expected_slots), 'duplicate requested storage slot')
    raw_account = trie_value(root, keccak256(address), proof.get('accountProof'))
    if raw_account is None:
        nonce, balance, storage_root, code_hash = 0, 0, EMPTY_TRIE, EMPTY_CODE
    else:
        account = rlp_decode(raw_account)
        require(isinstance(account, list) and len(account) == 4, 'account must have four fields')
        nonce = rlp_integer(account[0], 'nonce', 8)
        balance = rlp_integer(account[1], 'balance')
        storage_root, code_hash = account[2:]
        require(isinstance(storage_root, bytes) and len(storage_root) == 32, 'invalid account storage root')
        require(isinstance(code_hash, bytes) and len(code_hash) == 32, 'invalid account code hash')
    require(quantity(proof.get('nonce'), 'nonce') == nonce, 'nonce claim mismatch')
    require(quantity(proof.get('balance'), 'balance') == balance, 'native ETH balance claim mismatch')
    require(hex_data(proof.get('storageHash'), 32, 'storageHash') == storage_root, 'storage root claim mismatch')
    require(hex_data(proof.get('codeHash'), 32, 'codeHash') == code_hash, 'code hash claim mismatch')
    entries = proof.get('storageProof')
    require(isinstance(entries, list) and len(entries) == len(expected_slots), 'storage proof count differs from requested slots')
    seen, storage = set(), []
    for entry in entries:
        require(isinstance(entry, dict), 'storage entry must be an object')
        slot = slot_number(entry.get('key'))
        require(slot in expected_slots and slot not in seen, 'unexpected or duplicate storage slot')
        seen.add(slot)
        raw = trie_value(storage_root, keccak256(slot.to_bytes(32, 'big')), entry.get('proof'))
        if raw is None:
            value = 0
        else:
            value = rlp_integer(rlp_decode(raw), 'storage value')
            require(value != 0, 'zero storage must be represented by absence')
        require(quantity(entry.get('value'), 'storage value') == value, f'storage value claim mismatch at {hex(slot)}')
        storage.append({'slot': hex(slot), 'value': hex(value), 'exists': raw is not None})
    return {
        'verified': True, 'stateRoot': hex0(root), 'address': hex0(address),
        'accountExists': raw_account is not None, 'nonce': hex(nonce),
        'nativeBalanceWei': str(balance), 'storageRoot': hex0(storage_root),
        'codeHash': hex0(code_hash), 'storage': sorted(storage, key=lambda row: int(row['slot'], 16)),
        'trust': 'Proven relative to the supplied state root; consensus, block identity, and finality are not verified.',
    }


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate JSON object key')
        value[key] = item
    return value


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(Invalid(f'invalid JSON constant: {value}')))


def workspace_path(path):
    resolved = Path(path).resolve()
    require(resolved.is_relative_to(Path.cwd().resolve()), 'input must be inside the current workspace directory')
    return resolved


def load_bundle(path):
    with workspace_path(path).open('rb') as stream:
        raw = stream.read(MAX_FILE + 1)
    require(len(raw) <= MAX_FILE, 'input exceeds 1 MB limit')
    value = parse_json(raw)
    require(isinstance(value, dict) and value.get('format') == 'state-witness/1', 'unsupported witness format')
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Invalid('RPC redirects are not followed')


def rpc(endpoint, method, params):
    require(method in {'eth_chainId', 'eth_getBlockByNumber', 'eth_getProof'}, 'RPC method not allowed')
    url = urllib.parse.urlsplit(endpoint)
    require(url.scheme in {'http', 'https'} and url.hostname and not url.username and not url.password,
            'RPC must be HTTP(S) without embedded credentials')
    require(not url.query and not url.fragment, 'RPC must not have query credentials or fragment')
    # Explicitly disable proxy discovery: no environment or system configuration reads.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    payload = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode()
    request = urllib.request.Request(endpoint, payload, headers={
        'Content-Type': 'application/json', 'User-Agent': 'Pepeolithic-StateWitness/1.0',
    })
    with opener.open(request, timeout=25) as response:
        raw = response.read(MAX_FILE + 1)
    require(len(raw) <= MAX_FILE, 'RPC response exceeds 1 MB limit')
    result = parse_json(raw)
    require(isinstance(result, dict) and result.get('jsonrpc') == '2.0' and type(result.get('id')) is int and result['id'] == 1,
            'invalid JSON-RPC response envelope')
    if 'error' in result:
        error = result['error']
        # Do not echo remote text that could include endpoint credentials or instructions.
        code = error.get('code') if isinstance(error, dict) else None
        code = code if type(code) is int else None
        raise Invalid(f'RPC {method} failed (code {code})')
    require('result' in result, 'RPC response missing result')
    return result['result']


def capture(endpoint, address, slots, block_tag):
    hex_data(address, 20, 'address')
    normalized_slots = [hex(slot_number(slot)) for slot in slots]
    require(len(normalized_slots) <= 64 and len(set(normalized_slots)) == len(normalized_slots), 'too many or duplicate slots')
    require(block_tag in {'finalized', 'safe', 'latest'} or re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)', block_tag),
            'block must be finalized, safe, latest, or a canonical hex number')
    require(quantity(rpc(endpoint, 'eth_chainId', []), 'chain ID') == 1, 'capture expects Ethereum mainnet (chain 1)')
    block = rpc(endpoint, 'eth_getBlockByNumber', [block_tag, False])
    require(isinstance(block, dict), 'block not found')
    number = hex(quantity(block.get('number'), 'block number'))
    block_hash = hex0(hex_data(block.get('hash'), 32, 'block hash'))
    root = hex0(hex_data(block.get('stateRoot'), 32, 'state root'))
    # Numeric pin avoids a moving latest/finalized tag between calls.
    proof = rpc(endpoint, 'eth_getProof', [address, ['0x' + slot_number(slot).to_bytes(32, 'big').hex() for slot in normalized_slots], number])
    verify(proof, root, address, normalized_slots)
    return {
        'format': 'state-witness/1', 'chainId': 1,
        'block': {'number': number, 'hash': block_hash, 'stateRoot': root, 'requestedTag': block_tag},
        'address': address.lower(), 'slots': normalized_slots, 'proof': proof,
        'anchorNote': 'Block metadata is an RPC claim, not a consensus proof. Verify against an independently trusted state root.',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo', help='verify the bundled real ZTO witness offline')
    demo.set_defaults(command='demo')
    demo.add_argument('--pool', action='store_true', help='check the real ZTO/IMD pool slot0 inclusion proof')
    check = sub.add_parser('verify', help='verify against explicit trusted root, address, and requested slot set')
    check.add_argument('bundle')
    check.add_argument('--state-root', required=True)
    check.add_argument('--address', required=True)
    check.add_argument('--slot', action='append', default=[])
    fetch = sub.add_parser('capture', help='read a mainnet proof, check its internal consistency, print a portable bundle')
    fetch.add_argument('--rpc', default=PUBLIC_RPC)
    fetch.add_argument('--address', default=ZTO)
    fetch.add_argument('--slot', action='append', default=[])
    fetch.add_argument('--block', default='finalized')
    args = parser.parse_args(argv)
    try:
        if args.command == 'capture':
            output = capture(args.rpc, args.address, args.slot, args.block)
        elif args.command == 'demo':
            filename = 'zto-pool-mainnet.json' if args.pool else 'zto-mainnet.json'
            bundle = load_bundle(Path(__file__).parent / 'examples' / filename)
            # Demo root is fixed separately from the untrusted fixture, so a fixture
            # editor cannot silently replace both a proof and its apparent anchor.
            address = POOL_MANAGER if args.pool else ZTO
            slots = [hex0(keccak256(hex_data(ZTO_POOL_ID, 32) + (6).to_bytes(32, 'big')))] if args.pool else ['0x0', '0x1']
            output = verify(bundle['proof'], DEMO_ROOT, address, slots)
            output['demo'] = 'Real captured ZTO state; bundled anchor is illustrative, not independently authenticated.'
        else:
            bundle = load_bundle(args.bundle)
            output = verify(bundle['proof'], args.state_root, args.address, args.slot)
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except Invalid as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, RecursionError, urllib.error.URLError):
        # Do not echo file contents, URLs, or remote error messages.
        print(json.dumps({'verified': False, 'error': 'Unreadable or malformed input, missing proof fields, or unavailable RPC.'}), file=sys.stderr)
        return 1


# Fixed anchor for the bundled real-chain demonstration, not a consensus checkpoint.
DEMO_ROOT = '0x70c13580735123b57c0a9a24692875f4ef366b04c69d92af9f539561e626d512'

if __name__ == '__main__':
    sys.exit(main())
