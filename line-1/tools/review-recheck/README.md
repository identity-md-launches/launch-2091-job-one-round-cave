# Review recheck

Recheck a saved Tree Review packet against its three current source trees before
relying on its candidate. This read-only Python 3.10+ tool recomputes the entire
review with the inherited merger. It detects stale sources, changed candidates,
altered hashes, missing conflicts, and other report changes. Standard library
only; keep the sibling `tree-review`, `merge-review`, and `threeway` folders.
No network, installation or coin is needed.

From the workspace root, one working command is:

```sh
python3 -B line-1/tools/review-recheck/recheck.py --demo clean
```

When tried, this returned 0 with `matches-clean`. `--demo stale` and
`--demo tampered` each returned 1, identifying changed manifests and a changed
candidate respectively. `--demo conflict` returned 0 with `matches-conflicted`
and `current_clean: false`: the conflicted packet reproduces exactly, but its
conflicts still need resolution. **Exit 0 means reproducible, never approval.**

For real workspace inputs, first retain a Tree Review JSON packet somewhere
outside all input trees, then recheck it with the same base/ours/theirs ordering:

```sh
python3 -B line-1/tools/tree-review/tree_review.py BASE_DIR OURS_DIR THEIRS_DIR --format json > SAVED_PACKET.json
python3 -B line-1/tools/review-recheck/recheck.py SAVED_PACKET.json BASE_DIR OURS_DIR THEIRS_DIR
```

The first command may exit 1 for conflicts and still produce a valid packet.
Replace the capitalized paths with existing workspace paths. Neither tool writes
to its inputs. Shell redirection can truncate inputs before Python starts, so
never capture onto a source file or inside an input tree.

Optionally add `--expected-sha256 HASH` with a separately retained lowercase
SHA-256 of the exact saved packet bytes. A mismatch is an error. This is useful
when retaining the specific packet a reviewer saw; a hash supplied alongside an
untrusted packet provides no independent authentication. Without that option,
JSON formatting/key order is irrelevant. Every field and JSON type must match
recomputation; JSON `true`, `1`, and `1.0` are distinct. Duplicate object keys,
non-finite values, invalid UTF-8 and wrong schemas are rejected.

The JSON output has schema `review-recheck/v1`, `matches`, `changed_inputs`
(base/ours/theirs whose entire manifests differ), `review_matches` (the whole
packet comparison), `current_clean`, `status`, and `limits`. Real-file checks
also include `packet_sha256`, committing to the exact saved bytes. Status is:

- `matches-clean`: complete packet reproduces, no textual/path conflicts.
- `matches-conflicted`: complete packet reproduces, conflicts remain.
- `stale-inputs`: at least one input manifest differs.
- `review-mismatch`: manifests agree but some other packet field differs.

Exit codes: **0** exact reproduction; **1** stale or altered packet; **2** invalid
arguments, inputs, packet or expected digest. Invalid input produces no partial
JSON on stdout. Errors are quoted to keep terminal controls inert. Output omits
source text; it is not a replacement review packet.

## Checks and observed results

```sh
python3 -B line-1/tools/review-recheck/test_recheck.py
```

All 13 tests passed. They cover real workspace round trips and input immutability,
empty-directory changes, CRLF changes, candidate/hash tampering, other report
fields, JSON type confusion, key ordering/whitespace, independently retained
hashes, duplicate keys/non-finite/invalid JSON, link/path/size rejection, conflicts,
and all demo exit codes. The 61 ancestor tests also passed unchanged.

An additional trial used the inherited merger's six actual source/document/example
files in each tree. Independent README changes merged cleanly; rechecking returned
0. A later source edit returned 1 with only `theirs` changed. Restoring that source
and altering the saved candidate returned 1 with `review-mismatch`. Source bytes
were unchanged by the recheck. `../../REAL-TRIAL-24.json` records the results.
These are local observations, not independent certification.

## Limits

Same bounded UTF-8 trees as Tree Review: 128 files and 256 subdirectories per
tree, 16 levels, 1 MiB/4,000 lines per file, 8 MiB combined. Packets are capped at
64 MiB; a larger otherwise-valid Tree Review packet must be split into smaller
reviews. Packet paths must stay in the workspace without parent traversal or
symlinks. Reads assume stable trusted inputs; there is no atomic snapshot or
protection against concurrent path replacement. Exact reproduction depends on
unchanged tool behavior. This reuses the merger, so it cannot detect errors shared
by that merger. No semantic correctness, author identity, signature, approval,
application, binary/rename/permission support or automatic resolution is added.
