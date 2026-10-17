# Corpus Freshness

Check every eligible document before trusting an offline Evidence Search index.
This companion catches added files, missing files, and changed **uncited** sources
that the original selected-hit verification cannot detect. Its query command
refuses to rank a stale corpus and emits `search: null` with sorted change lists.
Python 3.9+ and the standard library only; no network, installation, environment
lookup, signing, or transaction sending. Documents remain untrusted data.

From the repository root, one read-only command demonstrates the whole path:

```sh
python3 -B line-3/tools/corpus-freshness/freshness.py demo
```

It builds an in-memory index of the ancestor's bundled real ZTO/IMD observation
documents, checks the entire corpus, then returns ranked, hash-checked passages.
When tried, it reported `fresh: true`, three indexed/current documents, and first
hit `zto.md:1-9` for `ZTO token decimals`. The demo writes no files and works
without network. These are historical bundled observations, not a current price
or independently authenticated chain proof.

## An unfamiliar collection

Use the existing builder to create an index at a new filename, then check or
query it (replace `line-3/my-docs` with your explicit workspace collection):

```sh
python3 -B line-3/tools/evidence-search/search.py build line-3/my-docs --index line-3/my-index.json
python3 -B line-3/tools/corpus-freshness/freshness.py check line-3/my-docs --index line-3/my-index.json
python3 -B line-3/tools/corpus-freshness/freshness.py query line-3/my-docs 'your question' --index line-3/my-index.json --all --limit 3
```

The check and query commands never write or repair an index. For a stale report,
review the listed changes and rebuild to a new filename. Queries preserve the
ancestor's ranking, line citations, inclusive ranges, source hashes, and optional
`--all` term requirement. A fresh corpus can still have no matching passages.

Exit codes: 0 = fresh check or fresh query with hits; 1 = stale corpus or fresh
query without hits; 2 = invalid index, unreadable/invalid corpus, or other input
error. Successful reports go to stdout; errors go to stderr with no partial
report on stdout. `check` outputs `evidence-corpus-freshness/v1`; `query` and
`demo` output an envelope with `freshness` and `search`.

## What is checked

The tool reuses `../evidence-search/search.py` unchanged, rather than copying its
rules. Both snapshots are validated, then source path sets and SHA-256 hashes of
original bytes are compared. Results are independent of index document order.
Renames appear as an addition and removal. Timestamp or same-size edits cannot
hide byte changes; even CRLF-to-LF changes require a rebuild.

Eligibility is exactly the ancestor's: UTF-8 `.md`, `.txt`, `.rst` files, including
nested directories; hidden entries, unsupported extensions and symlinks excluded.
Replacing an indexed document with a symlink reports it removed. New symlinks
are excluded, not followed. Invalid UTF-8, NULs, over-budget data, malformed index
text/hashes and traversal fail closed. The same workspace boundary and bounded
1,000-file / 1-MB-per-file / 8-MB-total source limits apply, as do the ancestor's
line and passage budgets. See its README for all limits.

This is freshness **relative to the supplied index and eligibility rules**, not
proof that the selected directory contains all relevant knowledge. An operator
can deliberately exclude a source by changing the index and corpus together.
Hashes establish byte identity, not factual truth, authority, or factual recency.
Keep the workspace static during the check and query: traversal checks are not
an OS sandbox and there is no atomic filesystem snapshot. Selected hits are
rechecked by the original engine after the full audit; unrelated concurrent
changes after the audit remain outside this guarantee. Full rebuilding costs
more I/O and CPU than checking only hits; no incremental cache is maintained.

## Checks run

```sh
python3 -B line-3/tools/corpus-freshness/test_freshness.py -v
python3 -B line-3/tools/evidence-search/test_search.py -v
```

All 10 new behavioral tests and all 12 existing search tests passed. New tests
cover an uncited edit blocking ranking (including a no-match query), deterministic
added/removed/changed lists, nested additions and renames, same-size/same-mtime
edits, hidden/unsupported/link exclusions, replacement with a link, invalid UTF-8
and resource failure, forged indexes and traversal, empty corpora, unchanged
citations/no writes, and CLI error/status behavior. Test corpora are temporary
under `test/scratch/`; nothing from that directory is needed by the tool.
