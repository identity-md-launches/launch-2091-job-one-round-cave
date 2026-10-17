# Search Receipt

Save an offline search result that another worker can verify without the original
index. A receipt binds the query, options, ranked excerpts, exact line citations,
and the path/hash of **every eligible source** to a separately retained SHA-256.
Verification rebuilds the corpus, checks all sources, and repeats the search.
It detects changed or missing evidence, newly added documents, and forged result
fields, including an excerpt with a plausible-looking `source_verified: true`.

Python 3.9+ and the standard library only. No installation, network, environment
lookup, credentials, signing, transaction submission, or document execution.
The two ancestor tools remain dependencies at their existing sibling paths.

From the repository root, one command demonstrates creation and verification
entirely in memory, without writing files:

```sh
python3 -B line-3/tools/search-receipt/receipt.py demo
```

When tried, it checked all three bundled real ZTO/IMD observation documents,
returned `zto.md:1-9` for `ZTO token decimals`, and reported `verified: true`.
The observations are historical Ethereum evidence bundled by the ancestor, not
a new chain read, current price, or independently authenticated chain proof.

## Create and hand off a receipt

This working example uses the bundled ZTO collection and creates a new file:

```sh
python3 -B line-3/tools/search-receipt/receipt.py create line-3/tools/evidence-search/examples/docs 'ZTO token decimals' --all --output line-3/zto-receipt.json
```

The command prints the canonical `receipt_sha256`. Retain that value separately
from the receipt, or convey it through a channel the recipient already trusts.
For this exact bundled query, the value is
`eb68004d99b400202f289750fd24909060cd440a5d69996585ce3c298683f3fb`.
Then verify either your new file or the included example:

```sh
python3 -B line-3/tools/search-receipt/receipt.py verify line-3/tools/evidence-search/examples/docs --receipt line-3/tools/search-receipt/examples/zto-receipt.json --expected-sha256 eb68004d99b400202f289750fd24909060cd440a5d69996585ce3c298683f3fb
```

For your own documents, replace the corpus directory and query, choose a fresh
`.json` output filename, and use the hash printed by **your** creation command.
`--limit` accepts 1–50 (default 5); `--all` requires every query term in a passage.
The output is created exclusively: existing files and symlinks are refused.
Receipt JSON is excluded from source eligibility, so saving it inside the corpus
does not itself invalidate the receipt. No existing index is needed or changed.

To relocate a handoff, copy the receipt and preserve relative paths within the
source collection. Supply the new collection root explicitly to `verify`.
Receipts store no absolute paths or timestamps. Unicode text and CRLF source
bytes retain the ancestor's exact hash and line-number behavior.

## Meaning of verification

`verified: true` means the receipt matches the caller's pinned hash, the complete
eligible collection has the same relative paths and byte hashes, and rerunning
the recorded query reproduces every result field and its ordering. It also
supports a correctly reproduced empty result; success does not imply a match.

Verification reports `receipt_hash_mismatch`, `corpus_changed` (with sorted
added/removed/changed lists), or `result_not_reproducible` on a failed check.
It will not rank a changed collection. A changed receipt fails its pinned hash
before the corpus is read. A forged result with a freshly computed hash still
fails reproduction against the actual sources. A fully self-consistent replacement
of both the receipt and sources can only be distinguished using the **original,
separately retained hash**. Never take the expected hash from untrusted receipt
contents and treat it as authentication. There is no signature or identity claim.

The hash covers canonical UTF-8 JSON: keys sorted, no insignificant whitespace,
non-ASCII text unescaped, compact separators, finite JSON numbers only. It is
**not** the ordinary SHA-256 of a pretty-printed receipt file. Formatting and
object-key order can change without changing the receipt's identity; array
order and numeric types cannot. Duplicate JSON keys are rejected.

Exit codes: 0 = created or verified (including an empty search result); 1 = a
well-formed receipt fails verification; 2 = malformed input, invalid path, I/O
failure, budget failure, or corpus change detected during creation. Reports go
to stdout, errors to stderr with no partial stdout report. A mismatch report
contains `verified: false`; input errors never claim a verified result.

## Bounds and limitations

Eligibility and search are inherited unchanged: UTF-8 `.md`, `.txt`, `.rst`;
hidden entries, symlinks and other suffixes excluded; at most 1,000 documents,
1 MB per document, 8 MB of sources, 20,000 passages, and 16,000 characters per
line. Receipts are capped at 12 MB. Oversized or invalid inputs fail explicitly.
Every source is re-read; there is no incremental cache. The new tool reuses
Evidence Search and Corpus Freshness rather than copying their implementations.

Keep the workspace static during creation and verification. Repeated audits
catch some concurrent changes, but this is not an atomic snapshot or an OS
sandbox against filesystem races. Filesystem I/O failure can leave a partial
new output file; it cannot overwrite an existing file. Remove such an incomplete
output only after reviewing it, or choose a new filename and retry.

Lexical ranking still uses the ancestor's overlapping ten-line windows. Terms
far apart may not match `--all`; hashes do not establish truth, factual recency,
authorship, semantic relevance, or completeness beyond the eligibility rules.
Upgrading the ranking engine can make an older receipt fail reproduction even
when source bytes are unchanged. Keep these three tool folders together when
archiving a handoff whose exact historical ranking must remain reproducible.

## Checks actually run

```sh
python3 -B line-3/tools/search-receipt/test_receipt.py -v
python3 -B line-3/tools/evidence-search/test_search.py -v
python3 -B line-3/tools/corpus-freshness/test_freshness.py -v
```

All 16 new tests and all 22 ancestor tests passed. The new suite exercises exact
citations, relocation, deterministic hashes, whitespace-independent JSON,
query/hash binding, modified excerpts/ranks/types/paths, incomplete manifests,
uncited changes, additions/removals, CRLF changes, no-hit and empty collections,
invalid schema and Unicode, duplicate keys/non-finite numbers, resource bounds,
symlink exclusions, preserved outputs, workspace bounds, inert document text,
mid-audit changes, CLI status codes, and the real ZTO demo. Temporary test files
live only under `test/scratch/` and are not runtime dependencies.
