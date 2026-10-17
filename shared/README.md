# Shared worker tools

[Proof Handoff](proof-handoff/README.md) joins the latest multi-account Proof Set
and portable Evidence Bundle. It re-verifies ZTO and its IMD pool, binds every
searchable document to the results, and reproduces the carried search receipt.
Run `python3 -B shared/proof-handoff/handoff.py demo` offline. The whole folder
works without any line folders; all copied sources have recorded fingerprints.

[Merge Dependencies](merge-dependencies/README.md) joins line 1's text merge review
with line 4's dependency conflict reduction. It catches a clean text merge that
makes real Requests/idna requirements incompatible, without applying edits or
installing anything. Run `python3 -B shared/merge-dependencies/check_merge.py demo`.

[Proof Search](proof-search/README.md) joins Ethereum state-proof verification
from line 2 with cited offline passage search from line 3. It is self-contained,
standard-library Python and includes a real historical ZTO/IMD pool witness.
See gathering/REPORT.md for all four lines' local checks and trust boundaries.

The new [Anchored Proof Search](proof-search/README.md) incorporates line 2's
Header Anchor and line 3's Corpus Freshness. Every query re-verifies the saved
proof against caller expectations and checks the whole receipt corpus.

```sh
python3 -B shared/proof-search/anchored_search.py demo
```

This demo is read-only and offline. The original state-root workflow is intact.
