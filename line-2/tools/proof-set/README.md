# Proof Set

Verify several Ethereum account and storage proofs against **one** execution
header whose hash the caller supplies. A manifest declares the exact account
addresses, raw storage slots and optional stored-code files expected by the
worker. The result is printed only after every entry passes. This is useful
when a decision depends on related contracts observed at the same state root.

From the repository root, run the real ZTO and ZTO/IMD pool demonstration:

```sh
python3 -B line-2/tools/proof-set/proof_set.py demo
```

Python 3.9+ standard library only. Keep the sibling `state-witness/`,
`header-anchor/` and `code-witness/` folders beside this tool. No installation,
network access, wallet, key, signing, transaction or payment is involved.

## What happened when tried

On 2026-10-17, the bundled offline demonstration verified both real mainnet
witnesses at historical block 26,212,390. The reconstructed header hash was
`0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc`
and its shared state root was
`0x70c13580735123b57c0a9a24692875f4ef366b04c69d92af9f539561e626d512`.
ZTO's 1,287 supplied runtime bytes matched its proven code hash. The pool
manager's ZTO/IMD pool slot was proven present with raw value
`0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41`.
These are historical observations, not a current price or token balance. The
demo's fixed hash came from an RPC observation, not independent consensus.

Eight new tests passed, including valid real fixtures, bad hash/address/slot/code,
duplicate expectations, malformed manifest shape and duplicate JSON keys:

```sh
python3 -B -m unittest discover -s line-2/tools/proof-set -p 'test_*.py' -v
```

## Use with your own checkpoint

Write a manifest matching `examples/zto-and-pool.json`. Its `header`, `witness`
and optional `code` paths are relative to the manifest file and must resolve
inside the current workspace. `slots` lists the **complete** expected raw slot
set for each witness; `[]` means account-only proof. No address may appear twice.
The manifest is the caller's request, so review it before relying on the result.

Supply a block hash authenticated independently of the proof provider:

```sh
python3 -B line-2/tools/proof-set/proof_set.py verify \
  line-2/tools/proof-set/examples/zto-and-pool.json \
  --block-hash 0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc
```

The example command reproduces the historical demo; its hash is illustrative.
If your manifest comes from another party, `--manifest-sha256 0x...` optionally
checks a separately received exact-file SHA-256 before any proof work. The
report includes the manifest file digest. A digest copied only from the same
untrusted manifest does not authenticate it.

The header and witnesses use the sibling tools' strict formats. This tool
accepts at most 32 accounts, 64 slots per account, and a 64 KiB manifest. The
sibling header, witness, trie-node and code size limits still apply. Duplicate
JSON object keys, unknown manifest fields, duplicate accounts/slots, paths
outside the workspace, mismatched proof claims, and code-hash mismatches fail.
Exit 0 prints a complete JSON report; exit 1 prints only a JSON error to stderr;
argument errors exit 2. It never prints partial verification success.

The proof establishes state **relative to the supplied block hash**. The caller
must authenticate that checkpoint's Ethereum chain, canonicality and finality.
This tool does not verify consensus, execute blocks, interpret a contract's
storage layout, or infer a price. Stored-code matching does not verify source,
ABI, proxy/delegation targets or behavior. It reads local inputs only and
does not capture proofs or send data anywhere. ZTO is used directly, so no new
coin is required.
