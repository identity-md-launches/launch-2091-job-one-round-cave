# Line 4 — parts that fit

Round 22 adds [Conflict Core](tools/conflict-core/README.md): isolate an
irreducible set of conflicting root requirements, with compatible assignments
for removing each member and a catalog-bound audit command.

```sh
python3 -B line-4/tools/conflict-core/core.py demo
```

The real Requests/idna example reduces four roots to two. All 15 new and 17
original tests pass. Round 22's wall adds two incompatible ochre pieces inside a
charcoal loop and one unnecessary pebble outside. [REVIEW-22.json](REVIEW-22.json)
records image dimensions, preservation measurements and limitations. The new
record is `dist/line-4/22.json`; the required export is
`artifacts/line-4/wall-v4.png`. The original goal and earlier tools are preserved.

The goal is finite offline dependency resolution, with an explanation when the
catalog cannot satisfy the requested constraints. The first working piece is
[Offline Resolver](tools/offline-resolver/README.md). From the repository root:

```sh
python3 -B line-4/tools/offline-resolver/resolve.py demo
```

It resolved a bundled snapshot of real Requests dependencies in six search states.
Seventeen behavioral tests passed, including 400 randomly generated catalogs
cross-checked by exhaustive enumeration. Package execution and installation are
outside this tool's scope. Unsupported constraint syntax is rejected; budget
exhaustion returns `inconclusive`, not `unsatisfiable`. Details and limitations
are in the tool README.

## Mark 01 — Parts That Fit

Pepe sorts ochre stones beside converging charcoal paths: finding compatible parts
that can work together. This first painting leaves much of the lit rock open.
The scene uses charcoal, red/yellow ochre, and chalk on the original warm cave.

- Wall: `artifacts/line-4/wall.png`, square RGB PNG, 1254 × 1254.
- Preview: `dist/line-4/01.jpg`, RGB JPEG, 512 × 512.
- Record: `dist/line-4/01.json`, with the finished PNG's SHA-256 URL.
- Review: `REVIEW.json`, with dimensions, formats, checks, and visual limitations.

The built-in image tool edited the supplied bare cave. The prompt is saved in
[IMAGE_PROMPT.md](IMAGE_PROMPT.md). Visual review checks the original framing,
major cracks, crystals and warm light, recognizable heavy-lidded Pepe and wide
mouth, five digits per hand, and absence of writing and forbidden symbols.
AI editing does not guarantee byte-identical background texture. This is a local
visual review; the verifier's byte checks do not certify appearance.
