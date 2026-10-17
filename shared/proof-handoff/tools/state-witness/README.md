# State Witness

Check Ethereum account and raw storage claims against a state root you trust. This is a Python 3.9+ standard-library tool: no installation, wallet, keys, signing, transactions, or payment. It includes real ZTO and ZTO/IMD pool witnesses, so the demonstration works with networking disabled.

From the repository root, run:

```sh
python3 -B line-2/tools/state-witness/witness.py demo --pool
```

It prints `"verified": true`, the PoolManager account's proven fields, and a nonzero storage inclusion proof for the ZTO/IMD pool. `demo` without `--pool` instead checks ZTO's contract account and proves that its raw slots 0 and 1 are absent. Those zero values are observed on chain, not token balances, defaults, or example stand-ins. No storage-layout meaning is assigned to those two ZTO slots.

The first round builds the verification layer of the line's goal. It implements Ethereum Keccak-256, canonical RLP decoding, hashed and inline Merkle Patricia trie traversal, account inclusion/absence, storage inclusion/absence, and binding to the exact expected address and storage slot set. Missing nodes, altered hashes, mismatched claims, duplicate slots, and malformed encodings fail closed.

## What happened when tried

On 2026-10-17, the read-only mainnet capture succeeded. Both checked-in witnesses refer to block **26,212,390** (`0x18ff826`), hash `0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc`, with state root:

```text
0x70c13580735123b57c0a9a24692875f4ef366b04c69d92af9f539561e626d512
```

ZTO (`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`) had nonce 1 and code hash `0x24e03ed7d7d3d6dc010b9a9836e419a3eb4215383b463f4e6685b4816435f16d`. Its two requested slots proved absent.

The pool witness is for Uniswap v4 PoolManager `0x000000000004444c5dc75cb358380d2e3de08a90` and the assignment's ZTO/IMD pool ID `0x888b07bd282f587d3c6b0fcb23e7fc55bbb33abe8910dd7492db815dc8dc5592`. [Uniswap's StateLibrary](https://github.com/Uniswap/v4-core/blob/main/src/libraries/StateLibrary.sol) locates pool slot0 at `keccak256(poolId || uint256(6))` (both operands 32 bytes). This derives storage key `0x85763e16f60121d4266264cb693cca4d6bdb9e98ff9cc3d698d892d90342971b`; its proven raw value was `0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41`. The tool deliberately returns the raw word; it does not turn this into a price, guess token ordering, or infer executable swap bounds.

The original block was requested with `finalized`; that label and the block hash are RPC claims. The proof verifies state relative to the root, not Ethereum consensus or the label. Public RPC source: [Ethereum PublicNode](https://ethereum-rpc.publicnode.com). The fixture is a historical observation, not a current quote.

All **30 offline tests passed**, covering real witnesses, nonzero storage, empty tries, leaf divergence, missing children, compact paths, inline nodes, malformed RLP, duplicate JSON keys, altered account/storage claims, wrong roots/addresses, exact requested-slot binding, and read-only capture behavior. Known hash vectors and published RLP examples also passed.

```sh
python3 -B -m unittest discover -s line-2/tools/state-witness -p 'test_*.py' -v
```

## Verify your own witness offline

You must supply the expected root, address, and complete requested slot set explicitly. The tool does not accept a root supplied only by the witness itself. For the historical example:

```sh
python3 -B line-2/tools/state-witness/witness.py verify \
  line-2/tools/state-witness/examples/zto-mainnet.json \
  --state-root 0x70c13580735123b57c0a9a24692875f4ef366b04c69d92af9f539561e626d512 \
  --address 0xd782bdea4ef02a0bd391eb9089470c8080f0a68e \
  --slot 0x0 --slot 0x1
```

Success is exit 0 with a JSON report. Failure is exit 1 with a JSON error on stderr. Argument errors use argparse's exit 2. The report binds to the explicitly supplied state root; unverified bundle metadata such as block number, source, and capture label is not carried into the verified report. An empty slot set verifies the account only and rejects a bundle containing unsolicited storage entries.

For another witness, obtain a trusted block state root independently, for example from a consensus-verified node. Repeating a root from the same untrusted RPC only demonstrates internal consistency. Changing both a proof and its unauthenticated root can create another internally consistent witness.

## Optional fresh capture

```sh
python3 -B line-2/tools/state-witness/witness.py capture \
  --address 0xd782bdea4ef02a0bd391eb9089470c8080f0a68e \
  --slot 0x0 --slot 0x1 > line-2/tools/state-witness/examples/zto-fresh.json
```

Capture needs network access and a mainnet provider supporting `eth_getProof`. It defaults to `https://ethereum-rpc.publicnode.com`; `--rpc https://eth.drpc.org` selects the other named public endpoint. A provided `--rpc` is used literally. No proxy or credential discovery occurs. Environments requiring a proxy need a reachable read-only relay supplied explicitly as `--rpc`. Endpoints with embedded credentials, query parameters, or redirects are refused.

Capture calls only `eth_chainId`, `eth_getBlockByNumber`, and `eth_getProof`, using the custom `Pepeolithic-StateWitness/1.0` User-Agent. It pins the returned numeric block number before requesting the proof and checks all claims against that block's root before printing the bundle. This detects inconsistent reads during a reorganization but does not establish canonicality. `--block` accepts `finalized` (default), `safe`, `latest`, or a hex block number. Historical capture can fail if the provider has pruned the needed state.

Capture prints to stdout; it never writes files itself. Read the output's error status before treating a redirected file as a witness. Verification reads only a path within the current workspace directory, resolving symlinks before opening it. Inputs and RPC responses are capped at 1 MB, with at most 64 slots, 128 nodes per proof, 32 KB per node, and bounded RLP nesting/traversal. Each RPC request has a 25-second socket timeout; three requests are used. There are no retries or polling loops.

## Limits and next pieces

The bundled root is an illustrative fixed anchor, not an independently authenticated checkpoint. This implementation is not an audited light client. It proves raw account/storage data, not that a particular Solidity layout or contract behavior is correct. `nativeBalanceWei` means ETH held by the proven account, not ZTO or IMD holdings. It checks a code hash but does not retrieve or audit bytecode. Trie proofs apply to Ethereum's current Merkle Patricia state format; other commitment schemes require another verifier.

Useful future pieces include authenticated header anchoring and mapping human requests such as a ZTO holder balance to verified, contract-specific storage locations. No new coin or requester-only value is required for this piece.

Protocol references: [EIP-1186](https://eips.ethereum.org/EIPS/eip-1186), [Ethereum's trie description](https://ethereum.org/developers/docs/data-structures-and-encoding/patricia-merkle-trie/), and [RLP](https://ethereum.org/developers/docs/data-structures-and-encoding/rlp/). All code here is local and standard-library-only; these links are background, not runtime dependencies.
