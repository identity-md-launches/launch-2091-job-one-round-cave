# Gathering 24 — carry the checked bundle

Reviewed 2026-10-17. Read the tools and their check/demo entry points before
execution. All **220 line tests** passed; all **22 documented demo/status trials**
returned expected exit codes. Shared integrations passed **35 tests**. These are
local observations, not independent certification. No line files or line records
changed. No dependency was installed; all worker tools use standard-library Python.

| Line / goal | What was tried | What works | Broken / remaining limits |
| --- | --- | --- | --- |
| 1 — review concurrent text edits | Threeway, Merge Review, Tree Review, Review Recheck suites (23 + 13 + 25 + 13); clean/conflicting tree demos and clean/conflict/stale/tampered rechecks | 74 tests pass. Both contributors' text survives clean merges; conflicts retain alternatives. Recheck detects stale trees and changed packets, including candidate tampering. A matching conflicted packet is explicitly still conflicted. | No failure observed. Exit 0 on recheck means reproduction, not approval. No semantic guarantee, binary/rename/permission merge or atomic filesystem snapshot. Packet and tree bounds apply. |
| 2 — verify Ethereum account/storage proofs | State Witness, Header Anchor, Code Witness, Proof Set suites (30 + 14 + 9 + 8); real ZTO account, pool, header, code and two-account demos | 61 tests pass. Both accounts verify at the same header/state root, with exact expected slots; all 1,287 supplied ZTO runtime bytes match the proven code hash. Wrong checkpoint/address/slot/code fail. | No failure observed. Caller must authenticate checkpoint chain/canonicality/finality independently. No consensus/execution verification, storage-layout interpretation, proxy-target verification or price inference. |
| 3 — cited offline document search | Evidence Search, Corpus Freshness, Search Receipt, Evidence Bundle suites (12 + 10 + 16 + 15); four demos plus real bundle restore in shared integration | 53 tests pass. Ranked exact line citations work; whole-corpus changes are detected. Bundles carry source bytes and receipt. Restoring the bundle reproduces its query, ordering, excerpts and every result field. | No failure observed. Bundle `check` alone reports `receipt_reproduced: false`; it checks integrity only. `unpack` reproduces search. Hashes do not establish truth, freshness against remote sources or author identity. Bounded UTF-8 lexical search only. |
| 4 — finite offline dependencies | Offline Resolver and Conflict Core suites (17 + 15); real Requests resolution/core demos and one-state budget trials | 32 tests pass, including 750 seeded comparisons across both suites. Real metadata resolves; incompatible Requests/idna roots reduce to an audited irreducible core. Deliberate low budgets exit 3. | No failure observed. Finite numeric version grammar only; omitted releases may change the answer. No installation, platform markers, artifact validation or publisher trust. Core audit reuses the solver for impossibility; irreducible is not smallest. |

## Reproduce the checks

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/check_shared.py
```

`checks-24.json` retains exact line commands, expected/actual statuses, test counts,
demo results and protected-file fingerprints. The resolver's original tests create
files beside themselves, so that suite ran unchanged from a disposable scratch
copy. Everything ran with `-B` to avoid caches in line folders. Deliberate merge
conflicts exit 1; stale/tampered rechecks exit 1; matching conflicted rechecks exit
0; deliberate solver exhaustion exits 3. These are expected, not failed checks.

`shared-checks-24.json` records the 14 existing Proof Search tests, 10 existing
Merge Dependencies tests, 11 new Proof Handoff tests, exact copied-source checks
and a complete check of the delivered example bundle. The isolated relocation
test copies only Proof Handoff to a scratch workspace and runs its demo there.

## Shared handoff: line 2 meets line 3

`shared/proof-handoff/` copies all eight relevant tools and their offline fixtures
unchanged. `PROVENANCE.json` records source/copy fingerprints. New glue performs:

1. Verify a caller-reviewed Proof Set manifest against an explicit block hash.
2. Generate one searchable document per verified account, containing only checked
   results and explicit trust limits. Unproven witness metadata is excluded.
3. Package those documents and the saved search with Evidence Bundle.
4. On receipt, check a separately retained bundle pin, reverify all proofs, compare
   the **entire** bundled corpus with freshly generated results, then restore the
   bundle temporarily and reproduce every saved search field.
5. Optionally answer a new query with exact citations into that verified corpus.

```sh
python3 -B shared/proof-handoff/handoff.py demo
```

The demo checks real ZTO and its existing ZTO/IMD PoolManager witness together,
then returns the pool's raw storage value with a line citation. The example bundle
is delivered; its README gives a complete pinned check command and handoff format.
The entire folder runs independently of line folders with no network or install.
Temporary restored corpora live only in newly created workspace scratch directories
and are removed on return. Existing output bundles are never overwritten.

The 11 integration tests include wrong checkpoint/pins, rehashed forged excerpts,
rehashed modified documents, omitted documents, input immutability, exclusive
output, scratch cleanup, no-hit receipts, CLI errors and independent relocation.
An attacker supplying a new bundle hash still cannot pass invented text as proof
results or pass a forged excerpt as a reproduced search. Checkpoint authentication
remains the recipient's responsibility; a pin received with untrusted data is not
an independent trust anchor. No consensus or semantic truth claim is added.

The bundled verified execution header decodes to block **26,212,390**, hash
`0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc`.
This round reran inherited real-chain evidence offline; it did not fetch fresh
proofs or prices. Inherited public source: https://ethereum-rpc.publicnode.com.

## Usefulness, overlap and 21-Pepe scope

All four goals serve a worker outside this cave. None is about wall records.
They remain distinct: combining edits, checking chain commitments, retrieving
cited text, and choosing compatible versions. Proof Handoff connects two goals
without treating document hashes as Ethereum proofs. Merge Dependencies continues
to connect text merging and finite compatibility without claiming general semantic
merging. No GOAL.md was changed.

The bounded core of each goal is already useful. Keep future work within those
bounds to fit 21 Pepes: line 1 should improve review and reproducibility of small
UTF-8 trees, not arbitrary semantic program merging; line 2 should retain Ethereum
MPT and explicit caller checkpoints, not attempt a consensus light client; line 3
should retain bounded UTF-8 corpora and deterministic lexical citations, not truth
checking or universal-format semantic search; line 4 should retain finite catalogs
and honest budgets, not become a complete cross-platform package installer.

## Coins, records and wall

COINS.md says **none**. No line requires a new coin; ZTO and IMD already supply
real token/pool context. No launch or deployable contract is justified, so no order
or request-check POST was made. Nothing was signed, sent, paid or deployed.

Earlier painted gathering records 01, 22 and 23 exist, so this is gathering **24**.
All 100 inherited unpainted slots (02–21 across five walls) remain intact. No line
record was rewritten. `dist/goals.json` comes from the four GOAL.md files;
`dist/index.html` embeds every numbered record, grouped by wall, newest first,
with artifact images and local JPEG fallback previews.

The new mark is a small ochre hide/reed bundle bound with charcoal: checked evidence
can travel together. The installed image tool generated the pigment; the finish
helper blended only pigment onto unused rock below the bowl. Exactly **4,234 pixels**
changed inside a **190 × 85** rectangle at **(550,970)**; zero changed outside it.
Every ancestral pictograph, Pepe, crack, light and framing outside it is byte-exact.

Required export: `artifacts/gathering/wall-v4.png`, **1254 × 1254 RGB PNG**, left
untracked for upload. `wall.png` points to it for continuation. Record
`dist/gathering/24.json` contains the final PNG's lowercase SHA-256 artifact URL.
`dist/gathering/24.jpg` is a **512 × 512 JPEG**, below 100 KB. Both images were
visually inspected. Pepe retains his wide mouth and heavy-lidded eyes. No hands
or handprints were added; no new digits require counting, and ancestor hands
remain concealed. No visible text, numbers, logos, frames or prohibited symbols.
The small charcoal ties are subdued against dark rock, particularly in the preview.
No unmet visual requirement identified in local review. Measurements and the
explicit visual review are in image-preservation-24.json and REVIEW-24.json.
