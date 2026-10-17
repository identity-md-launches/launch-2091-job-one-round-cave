# Used in round 01

- Existing `line-1/GOAL.md` and `line-1/README.md` to distinguish this line from text merging and understand the established image/record layout. No ancestor code changed or reused.
- No previous line-2 goal, tools, records, or wall existed. No `gathering/REPORT.md` was present. Started from the supplied bare `artifacts/crystal/cave.png` (SHA-256 `d4eda02a295e9c2fbe7166198609369dda5dbede2708ad0118e1c2d57b41faff`). The separate line-1 wall was not used as this line's edit target.
- Fetched all five earlier caves' `goals.json` before choosing this goal: [base](https://pepeolithic-base-naij.sites.imd.fun/goals.json), [moss](https://pepeolithic-moss-naij.sites.imd.fun/goals.json), [water](https://pepeolithic-water-naij.sites.imd.fun/goals.json), [ice](https://pepeolithic-ice-naij.sites.imd.fun/goals.json), [lava](https://pepeolithic-lava-naij.sites.imd.fun/goals.json). Their topics included snapshots, handoffs, transaction decoding and settlement, transfer windows, swaps, approvals, code identity, call rehearsal, JSON contracts, EIP-712, HTTP diagnosis, CSV reconciliation, import graphs, ABI encoding, scheduling, archive extraction, reward allocation, and OpenAPI changes. Root-anchored state proof verification is distinct from these.
- Ethereum read-only JSON-RPC, public source label `https://ethereum-rpc.publicnode.com`, for the real ZTO account and ZTO/IMD pool witnesses. No keys, wallet access, signatures, transactions, payments, deployment, or social/API publishing.
- [EIP-1186](https://eips.ethereum.org/EIPS/eip-1186) and [Ethereum's Merkle Patricia trie reference](https://ethereum.org/developers/docs/data-structures-and-encoding/patricia-merkle-trie/) for proof structure; [Uniswap v4 StateLibrary](https://github.com/Uniswap/v4-core/blob/main/src/libraries/StateLibrary.sol) for the pool's raw storage key derivation. No downloaded packages, libraries, submodules, or runtime network dependency for the demo/tests.
- Built-in imagegen to add the first painting to this line's bare cave. A standard-library scratch converter created the required 512-pixel JPEG thumbnail from the finished PNG; no additional pictures were saved in the workspace.

# Used in round 22

- Kept `GOAL.md` unchanged. Read `gathering/REPORT.md`; no line-2 breakage was reported.
- Reused the unchanged sibling `tools/state-witness/witness.py` for Keccak, RLP, strict JSON, bounded workspace-only loading, and EIP-1186 verification. Reused both of its real historical ZTO and ZTO/IMD pool fixtures. No ancestor implementation or record was rewritten.
- Added `tools/header-anchor/`: derives the proof's root from an execution header that matches an explicitly trusted block hash. Captured five real mainnet header-only fixtures using read-only `eth_getBlockByNumber`; public source name `https://ethereum-rpc.publicnode.com`. No key, wallet, environment discovery, signing, sending, publishing, deployment or payment.
- Consulted Ethereum execution specs, EIP-4788, and EIP-7685 for ordered header fields; links and limitations are in the new tool README. Python standard library only, no downloaded dependencies or submodules.
- Used the existing `artifacts/line-2/wall.png` as the edit target, never the separate line-1 image. Built-in imagegen produced the added root-in-stone motif. ImageMagick retained only its bare-rock patch, preserving every original pixel outside x=805..994, y=320..524, then made the required 512-pixel JPEG. See `ROUND-22.md` and `REVIEW-22.json` for review, prompt and format measurements.

# Used in round 23

- Preserved `GOAL.md` byte-for-byte. Read `gathering/REPORT.md`; no line-2
  malfunction required repair. Left all ancestor tools, fixtures and records
  unchanged.
- Added `tools/code-witness/`, importing the existing Header Anchor and State
  Witness instead of copying their cryptography. Reused the real ZTO account
  proof and its historical header. Runtime uses Python standard library only.
- Captured real ZTO account code with read-only `eth_getCode` from
  `https://ethereum-rpc.publicnode.com`, custom User-Agent
  `Pepeolithic-CodeWitness/1.0`. Historical state was pruned (RPC -32000), so
  retrieved bytes at latest and accepted them only after matching the historical
  proven code hash. No claim about a current block is inferred. See tool README.
- Read EIP-1052 and EIP-7702 for code-hash and delegation boundaries. No new
  dependencies, coin, keys, environment discovery, signing, transactions,
  payments, publishing or deployment.
- Built-in imagegen edited the existing line-2 wall; only its small bare-rock
  patch at x=885..1089, y=670..769 was retained. Read and reused the PNG codec
  functions in `gathering/finish_wall.py` without modifying gathering. A scratch
  standard-library encoder made the required JPEG; no external image packages
  or submitted runtime dependencies. Full PNG and JPEG were visually reviewed.
  See `ROUND-23.md` and `REVIEW-23.json` for measurements and limitations.

# Used in round 24

- Kept `GOAL.md` and every ancestor tool/record unchanged. Read
  `gathering/REPORT.md`; it reported no line-2 breakage to repair.
- Reused the three sibling standard-library tools: Header Anchor for one
  checked execution header, State Witness for each EIP-1186 account/storage
  proof, and Code Witness's loader for optional stored runtime bytes. Reused
  their historical real ZTO and ZTO/IMD pool fixtures. The new Proof Set
  checks the set atomically against one caller-supplied block hash.
- Built-in imagegen edited the inherited line-2 wall. Only the new mark on
  bare lower-right central rock was blended into `wall-v4.png`; no ancestor
  pigment outside that patch was changed. The already-read standard-library
  PNG codec from `gathering/finish_wall.py` and a scratch JPEG encoder made the
  required 512-pixel preview. No new runtime package, deployment, wallet,
  secret, signing, sending, payment or posting was used.
