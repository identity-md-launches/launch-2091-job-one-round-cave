# Code Witness

Check that supplied Ethereum account code bytes match the code hash committed
by a verified account proof and an explicitly trusted execution block hash.
Useful before disassembling or comparing code returned by an untrusted RPC.
Python 3.9+ standard library only; no installation or network at runtime.

From the repository root, run this offline demonstration:

```sh
python3 -B line-2/tools/code-witness/code_witness.py demo
```

It prints `"verified": true`, the checked header/account/storage fields, and
`code.byteLength: 1287` for the real ZTO contract
`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`. Keep the sibling
`header-anchor/` and `state-witness/` folders when copying this tool.

## What happened when tried

On 2026-10-17 the demonstration verified all 1,287 supplied runtime bytes against
the historical ZTO witness at mainnet block 26,212,390. Their Ethereum Keccak-256
is `0x24e03ed7d7d3d6dc010b9a9836e419a3eb4215383b463f4e6685b4816435f16d`.
The header matched the caller's checkpoint
`0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc`.
The demo checkpoint remains an inherited RPC observation, not a consensus
authenticated checkpoint.

The new `examples/zto-runtime.hex` contains actual public-chain account code.
Capture used read-only `eth_getCode` at <https://ethereum-rpc.publicnode.com>,
with User-Agent `Pepeolithic-CodeWitness/1.0`, no proxy/configuration discovery,
and no credentials. The initial block-hash-pinned request returned RPC error
`-32000`: historical state was not available. A second request used `latest`.
Those returned bytes were accepted **only after** their hash matched the older
cryptographically proven account commitment. This establishes byte identity
at that historical checkpoint regardless of when or where the bytes were
retrieved; it does not establish current state or the latest block's identity.

All nine new tests and all 44 unchanged ancestor tests passed. Altered, empty,
truncated, appended and init-code-prefixed replacements fail. Wrong checkpoint,
address, slots, header root and forged code-hash claims fail without printing
partial success. Empty/delegated-code report tests isolate the reporting layer;
the ZTO tests exercise the complete real proof path.

```sh
python3 -B -m unittest discover -s line-2/tools/code-witness -p 'test_*.py' -v
```

## Verify your own inputs

The explicit version of the demonstration is:

```sh
python3 -B line-2/tools/code-witness/code_witness.py verify \
  line-2/tools/header-anchor/examples/zto-header-mainnet.json \
  line-2/tools/state-witness/examples/zto-mainnet.json \
  line-2/tools/code-witness/examples/zto-runtime.hex \
  --block-hash 0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc \
  --address 0xd782bdea4ef02a0bd391eb9089470c8080f0a68e \
  --slot 0x0 --slot 0x1
```

Replace the hash with an independently authenticated checkpoint for your own
use. Header and proof formats are documented by the sibling tools. The code
file must be one ASCII `0x`-prefixed even-length hex string, optionally ending
with one LF newline. It contains account runtime/stored code, not deployment
transaction init code or an RPC response object. Empty code is `0x`.
Hex digits may be upper or lowercase. Whitespace, extra newlines, and oversized
inputs fail. The 49,000-byte code limit is a local resource bound, not a
consensus rule. Every file must resolve inside the current workspace, including
symlinks. Header/proof parsing retains the ancestors' input bounds.

Repeat `--slot` for the exact complete slot set in the proof; omit it for an
account-only proof. The inherited ZTO fixture includes two slots and therefore
requires both arguments even when the immediate question concerns code.
Exit 0 emits the completed verified report; verification/file errors exit 1
with JSON on stderr, and argument errors exit 2. Code bytes are never executed.

## Meaning and limits

Code identity is a commitment check, not a source-code audit, verified ABI,
token-layout assertion or proof of behavior. The tool retains `accountExists`
to distinguish an absent account from an existing account with empty code.
Empty bytes alone do not establish an absence of protocol-defined behavior,
including precompiles. A 23-byte `ef0100` delegation indicator is identified and
its target reported, but the target's code is not fetched or verified. Proxies,
libraries and other execution dependencies are also outside the check.
See [EIP-1052](https://eips.ethereum.org/EIPS/eip-1052) for account code hashes
and [EIP-7702](https://eips.ethereum.org/EIPS/eip-7702) for delegation semantics.

No code hash, root or address is trusted merely because it appears in bundle
metadata. The caller's checkpoint must authenticate chain, canonicality and
finality externally. This tool does not execute blocks or verify consensus.
It inherits Header Anchor's supported encodings and State Witness's MPT scope.
It reads workspace inputs and prints results only: no runtime networking,
environment discovery, keys, wallets, signatures, sends, payments or posts.
ZTO is used directly; this tool needs no new coin.
