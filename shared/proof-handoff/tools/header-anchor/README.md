# Header Anchor

Verify Ethereum account and storage proofs against an execution **block hash**
that you trust. The tool reconstructs the execution header's canonical RLP,
computes Ethereum Keccak-256, checks the expected hash, extracts its committed
state root, and passes that root to the existing State Witness verifier.

From the repository root, with Python 3.9+ and no network or installation:

```sh
python3 -B line-2/tools/header-anchor/anchor.py demo
```

This checks the real ZTO/IMD Uniswap v4 PoolManager storage witness. Success is
JSON containing `"verified": true`, the checked header, and proven account/raw
storage fields. It does not infer a token balance or price from raw storage.
No wallets, secrets, environment discovery, signing, transactions or RPC calls
are used by this tool. Keep its sibling `state-witness/` folder when copying it.
Both tools use only the Python standard library.

## What happened when tried

On 2026-10-17 the demo verified the existing witness for block **26,212,390**,
hash `0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc`.
Its reconstructed Prague header committed to state root
`0x70c13580735123b57c0a9a24692875f4ef366b04c69d92af9f539561e626d512`.
PoolManager `0x000000000004444c5dc75cb358380d2e3de08a90` had the proven pool word
`0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41` at slot
`0x85763e16f60121d4266264cb693cca4d6bdb9e98ff9cc3d698d892d90342971b`.
This is the assignment's ZTO/IMD pool; the sibling tool documents slot derivation.

All **14 new tests** passed, as did all **30 unchanged State Witness tests**.
The new suite reconstructs five real mainnet header hashes, changes every
committed field, removes every field, tampers with a proof, checks exact caller
address/slot binding, and exercises malformed encoding and CLI failure status.
It also verifies the existing ZTO contract-account witness against the same header.

```sh
python3 -B -m unittest discover -s line-2/tools/header-anchor -p 'test_*.py' -v
```

The bundled header-only objects were captured read-only from Ethereum JSON-RPC;
public source: <https://ethereum-rpc.publicnode.com>. Capture used only
`eth_getBlockByNumber`, with a custom User-Agent, and no runtime dependency was
downloaded. The header hashes in the tests are fixed separately from the files:

| Schema | Mainnet block | Reconstructed hash |
| --- | ---: | --- |
| Legacy | 0 | `0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3` |
| London | 12,965,000 | `0x9b83c12c69edb74f6c8dd5d052765c1adf940e320bd1291696e6fa07829eee71` |
| Shanghai | 17,034,870 | `0xe22c56f211f03baadcc91e4eb9a24344e6848c5df4473988f893b58223f5216c` |
| Cancun | 19,426,589 | `0xa2917e0758c98640d868182838c93bb12f0d07b6b17efe6b62d9df42c7643791` |
| Prague | 26,212,390 | `0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc` |

## Verify a witness against your checkpoint

The following reproduces the historical demo explicitly. For your own data,
replace the checkpoint hash with one authenticated independently of the witness
provider. Copying a hash from that same untrusted provider establishes only
internal consistency.

```sh
python3 -B line-2/tools/header-anchor/anchor.py verify \
  line-2/tools/header-anchor/examples/zto-header-mainnet.json \
  line-2/tools/state-witness/examples/zto-pool-mainnet.json \
  --block-hash 0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc \
  --address 0x000000000004444c5dc75cb358380d2e3de08a90 \
  --slot 0x85763e16f60121d4266264cb693cca4d6bdb9e98ff9cc3d698d892d90342971b
```

`--block-hash` and `--address` are mandatory. Repeat `--slot` for the complete
expected set; omit it for account-only verification. Unrequested or duplicate
storage entries fail. Exit 0 means verification succeeded; exit 1 emits an error
JSON on stderr; argparse errors use exit 2. Verification prints only a completed
result, never a partial success.

## Header input contract and trust boundary

Input is a header-only object, **not** a full `eth_getBlockByNumber` response.
`examples/` gives exact field names. Required base fields, in RLP order, are:
`parentHash`, `sha3Uncles`, `miner`, `stateRoot`, `transactionsRoot`,
`receiptsRoot`, `logsBloom`, `difficulty`, `number`, `gasLimit`, `gasUsed`,
`timestamp`, `extraData`, `mixHash`, `nonce`. Byte strings use even-length
`0x` hex with exact Ethereum field lengths; `extraData` allows 0–32 bytes.
Integers use canonical RPC quantities (`0x0`, not `0x00`); zero becomes an empty
RLP byte string, whereas the nonce remains eight bytes.

Only these complete suffixes are accepted, in this order:

- London: `baseFeePerGas`.
- Shanghai: London plus `withdrawalsRoot`.
- Cancun: Shanghai plus `blobGasUsed`, `excessBlobGas`, `parentBeaconBlockRoot`.
- Prague: Cancun plus `requestsHash`.

The legacy form has no suffix. Optional `hash` metadata must match the computed
hash but is never used as the trust anchor. Unknown fields, missing suffix
members, malformed hex, duplicate JSON keys, and unsupported extensions fail
closed. Field presence identifies the **encoding schema**, not whether a fork
was valid at that height. No timestamp-based fork schedule is inferred.

Header files are limited to 64 KiB. The existing witness loader and verifier
retain their 1 MB file and proof/node bounds. Input paths must resolve within the
current workspace. Unproven witness labels (`block`, `chainId`, `address`, `slots`,
sources) are ignored and excluded from the report; expected values come from
the caller and the cryptographically checked header/proof.

A supplied hash commits to the state root but does not establish its chain,
canonicality, finality, or execution validity. The demo's fixed hash is a
historical RPC observation, **not an authenticated checkpoint**. This tool is
not a consensus light client or code audit. It supports the listed header
encodings and MPT proofs only; future header fields need an explicit update.
No new coin is required.

Protocol references: [execution header specification](https://ethereum.github.io/execution-specs/src/ethereum/forks/bpo2/blocks.py.html),
[EIP-4788 header order](https://eips.ethereum.org/EIPS/eip-4788),
[EIP-7685 requests commitment](https://eips.ethereum.org/EIPS/eip-7685).
These are background references, not runtime dependencies.
