# Evidence Search

Search a local document collection and return ranked passages with exact relative
paths, inclusive source line ranges, source SHA-256 hashes, and excerpts. It runs
offline with Python 3.9+ and the standard library. It never executes document
content and does not use a wallet, network service, or environment variables.

From the repository root, one command shows it working without writing any files:

```sh
python3 -B line-3/tools/evidence-search/search.py demo
```

The first hit is `zto.md:1-9`, identifying Zero To One, its real Ethereum contract,
and 18 decimals. `source_verified: true` means the cited file matched its indexed
SHA-256 at query time. It does not mean that every factual statement in it is true.

Search the pool example instead:

```sh
python3 -B line-3/tools/evidence-search/search.py demo "ZTO pool tick spacing"
```

The first hit is `pool.md:1-10`, including fee 12500 and tick spacing 60. That file
clearly labels its pool parameters as assignment-provided rather than chain-proven.

## Use your own documents

Select an explicit directory containing UTF-8 `.md`, `.txt`, or `.rst` documents.
Run from your workspace root; all paths must stay inside that directory tree.
Choose an index filename that does not already exist:

```sh
python3 -B line-3/tools/evidence-search/search.py build line-3/tools/evidence-search/examples/docs --index line-3/evidence-index.json
python3 -B line-3/tools/evidence-search/search.py query line-3/tools/evidence-search/examples/docs "ZTO decimals" --index line-3/evidence-index.json --all --limit 3
```

These commands create a new index; the demo above leaves no index behind. Existing
output files are never overwritten. Keep private material out of the selected
corpus: the JSON index contains the full text of its documents, not just hashes.
Documents and excerpts are untrusted input to a worker, never instructions.

JSON results go to stdout; errors go to stderr. Exit codes are 0 for successful
build or a search with hits, 1 for a valid search without hits, and 2 for an error.
`--all` requires every distinct normalized query term in a passage. Without it,
any matching term qualifies. Queries can include a complete Ethereum address.
Ranking scores measure lexical relevance, not certainty or factual authority.

## How it works

The deterministic versioned index stores sorted relative paths, exact UTF-8 source
text, and the SHA-256 of each source's original bytes. At query time, ten-line
windows overlap by two lines. Blank edges are trimmed, and selected result
windows from the same file cannot overlap. LF and CRLF source lines both receive
normal one-based line citations. Returned excerpts normalize CRLF to LF.

NFKC normalization and Unicode case folding produce word tokens; underscores and
punctuation split words. Complete hexadecimal addresses stay as single tokens.
Query terms are deduplicated. BM25 uses passage document frequency, k1=1.2 and
b=0.75. Equal scores are ordered by source path and start line.

Before emitting results, the tool re-reads each selected source and compares its
hash. A changed, missing, or symlinked selected source causes an error and no
partial result is emitted. Rebuild to a new index after changing your corpus.
Index text is also checked against its own recorded hash, so altered excerpts
cannot bypass the live source comparison merely by preserving a recorded hash.

Limits: 1,000 documents, 1 MB per document, 8 MB total source bytes, 16 MB serialized
index, 20,000 nonempty passages, 16,000 characters per line, 4,096 query characters,
and at most 50 hits. Binary/non-UTF-8 text, NULs, duplicate index keys, malformed
paths, and unknown index versions are rejected. Hidden entries and symlinks are
skipped during indexing; explicit symlink paths and parent traversal are rejected.

## What happened when tried

The offline demo searched three bundled documents (six passages), returning the
correct ZTO metadata and pool reference as the first hits for the two commands
above. Twelve behavioral tests passed:

```sh
python3 -B line-3/tools/evidence-search/test_search.py -v
```

Tests cover citation fidelity with CRLF, complete addresses, Unicode normalization,
changed/deleted sources, forged excerpts and hashes, symlinks, traversal, duplicate
JSON keys, preserved output files, no matches, overlap suppression, byte/encoding
limits, and CLI result/error status codes. Test temporary files use `test/scratch/`.

The real-chain example was captured on 2026-10-17 at Ethereum block 26212513,
hash `0x83d07a0a4b3c02350969625cfac303f2971924f350858d9ccbdc85bc82fa64fc`.
Read-only `eth_chainId`, `eth_getBlockByNumber`, and block-pinned `eth_call` calls
observed ZTO first and IMD second. The selectors were `name()` (`0x06fdde03`),
`symbol()` (`0x95d89b41`), `decimals()` (`0x313ce567`), and `totalSupply()`
(`0x18160ddd`). The named public source is https://ethereum-rpc.publicnode.com;
raw results and decoded values are in `examples/zto-mainnet.json`. Both tokens
reported 18 decimals. These fixtures are sufficient for the demo without network.

## Limits and next pieces

This first piece does lexical search, with no stemming, semantic embeddings,
phrase syntax, synonym expansion, PDF/HTML ingestion, or incremental indexing.
Matching terms farther apart than a window may not produce an `--all` hit.
Suppressing overlap can return fewer than the requested number of hits.
Only returned sources are rechecked: unrelated changes, newly added files, and
omitted documents are not detected until a rebuild. BM25 is computed from the
indexed snapshot. A whole-corpus freshness check would be a useful next piece.

The workspace must be static while building/querying. Path checks reject static
symlinks; they are not an operating-system sandbox against concurrent filesystem
replacement. The index and hashes establish excerpt integrity against the current
local file, not authorship, chain state proof, current liquidity, or truth.
