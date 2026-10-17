# Evidence Bundle

Carry an offline document collection **and** its reproducible cited-search
receipt in one bounded JSON file. A recipient can restore exact UTF-8 source
bytes, verify the saved search, and ask new questions without fetching sources.
Python 3.9+ and the standard library only. Keep the sibling Evidence Search,
Corpus Freshness and Search Receipt folders together; their code is reused
unchanged. No network, environment lookup, document execution or transactions.

One command, from the repository root, demonstrates packing and checking the
ancestor's historical real ZTO/IMD observation documents entirely in memory:

```sh
python3 -B line-3/tools/evidence-bundle/bundle.py demo
```

When tried, it carried three documents, matched the bundle hash, and retained
the first citation `zto.md:1-9` for `ZTO token decimals`. This read-only demo
writes nothing. It reports `receipt_reproduced: false` because it checks the
in-memory bundle; the unpack operation below reproduces the restored receipt.
Packing itself reproduces the receipt against the original collection first.

## A complete handoff

The included `examples/zto-bundle.json` is self-contained evidence data. Its
canonical SHA-256 is
`4199bcadadc0df319c7e98137bf3ee83e4895373bedf35d929ba3ff5984b48e2`.
Check the envelope, all embedded source hashes, manifest and separately pinned
bundle identity without writing files:

```sh
python3 -B line-3/tools/evidence-bundle/bundle.py check line-3/tools/evidence-bundle/examples/zto-bundle.json --expected-sha256 4199bcadadc0df319c7e98137bf3ee83e4895373bedf35d929ba3ff5984b48e2
```

To restore it, choose a **new** directory whose parent already exists:

```sh
python3 -B line-3/tools/evidence-bundle/bundle.py unpack line-3/tools/evidence-bundle/examples/zto-bundle.json --expected-sha256 4199bcadadc0df319c7e98137bf3ee83e4895373bedf35d929ba3ff5984b48e2 --destination line-3/restored-zto
```

Successful unpacking reports `receipt_reproduced: true`, after the ancestor's
verifier checks every restored source and reruns the saved query. Source paths,
UTF-8 bytes (including CRLF), hashes and line citations are preserved. The
receipt is saved as `.search-receipt.json`, excluded from corpus eligibility.
You can then build a new index or use Search Receipt to ask another question:

```sh
python3 -B line-3/tools/search-receipt/receipt.py create line-3/restored-zto 'IMD contract' --output line-3/imd-question.json
```

For your own collection, pack its eligible sources and one question:

```sh
python3 -B line-3/tools/evidence-bundle/bundle.py pack line-3/my-docs 'your question' --all --limit 3 --output line-3/my-bundle.json
```

Retain the printed `bundle_sha256` separately through a channel the recipient
trusts. Use **your** hash for check/unpack. A pin copied from an untrusted bundle
does not authenticate it. Hashes establish byte identity, not truth, authorship,
factual recency or current chain state. The included ZTO facts are the ancestor's
historical RPC observations, not fresh reads or independent Ethereum proofs.

## What each result means

`check` validates the schema, embedded text hashes, source manifest and bundle
pin. It does **not** reproduce rankings; its `receipt_reproduced` remains false.
`unpack` additionally reruns the receipt against the restored corpus, comparing
every result field. A rehashed forged excerpt can pass integrity checking but
fails reproduction. Such a failure leaves the new directory for inspection.

Exit codes: 0 = packed, integrity check passed, or unpacked and reproduced;
1 = pin mismatch or failed receipt reproduction; 2 = invalid input, unsafe path,
encoding/resource error or I/O failure. Reports are JSON on stdout; errors are
JSON on stderr with no partial stdout report. No-hit receipts reproduce normally.

Every selected path must be inside the current working directory. Parent
traversal, absolute source names, hidden source paths, symlink paths, duplicate
sources and file/directory prefix conflicts are rejected. Unpack exclusively
creates a new destination and each file; existing directories, files and links
are never merged or overwritten. A pin mismatch creates nothing. I/O failure
can leave a partial **new** bundle or destination: inspect it and choose a new
name for a retry. There is no automatic deletion or rollback.

## Bounds and limits

Sources inherit the ancestor's rules: UTF-8 `.md`, `.txt`, `.rst`; hidden entries,
symlinks and other extensions excluded; 1,000 documents, 1 MB each, 8 MB total,
16,000 characters per line and 20,000 passages. Bundle JSON is capped at 24 MB
and the receipt at 12 MB. There is no compression, network fetching or archive
extraction library. JSON escaping can make an otherwise eligible collection
exceed the bundle cap; it fails explicitly. Source paths are sorted. Duplicate
JSON keys, non-finite numbers and non-UTF-8 bundle encodings are rejected.

The pin hashes canonical UTF-8 JSON (sorted keys, compact separators, unescaped
Unicode, finite numbers), not pretty-printed file bytes. Whitespace/key order
outside strings can change without changing identity. Keep the workspace and
destination parents static: path checks are not an OS sandbox against concurrent
filesystem races, and collection capture is not an atomic snapshot. Bundles are
local evidence copies, not freshness checks against the original after packing.
Unpacking needs disk space for all sources and the receipt. Ranking reproduction
depends on the same ancestor tool versions and lexical search limits.

## Checks actually run

```sh
python3 -B line-3/tools/evidence-bundle/test_bundle.py -v
```

All 15 new behavioral tests and all 38 ancestor tests passed. Coverage includes
CRLF/Unicode round trips, searching after original evidence removal, separate
pins, rehashed forged excerpts, source/manifest tampering, unsafe paths and prefix
conflicts, existing-output preservation, partial I/O failure, hidden/link/type
exclusions, duplicate/non-finite/non-UTF-8 JSON, byte/passage budgets, no-hit and
empty collections, deterministic canonical identity, workspace bounds, corpus
change rejection, CLI statuses and the real ZTO demo. Temporary corpora stay in
`test/scratch/` and are not dependencies. An additional actual CLI handoff of the
bundled ZTO data restored all three documents and reproduced the saved receipt;
see `line-3/TRIAL-24.json`.
