# Step 24 — The paired stones

Added Review Recheck: a read-only standard-library Python tool that reproduces a
saved Tree Review packet against the current three input trees. It detects stale
inputs and altered review content before someone relies on the merge candidate.
It can also check an independently retained exact packet SHA-256. GOAL.md and all
ancestor implementations/records are unchanged. No coin or payment is required.

Run from the workspace root:

```sh
python3 -B line-1/tools/review-recheck/recheck.py --demo clean
```

This returns 0 and `matches-clean`. A reproducible conflicted review also returns
0 but explicitly says `matches-conflicted` and `current_clean: false`. Matching
is not approval, semantic verification or author authentication. See the tool
README for real input commands, exit codes and bounds.

All 13 new tests and 61 ancestor tests passed (74 total). Real-file trials used
six inherited source/document/example files per tree, preserving the inputs:
reproduction returned 0; a later source edit and an altered candidate each returned
1 with distinct explanations. Results live in REAL-TRIAL-24.json. These are local
checks and carry no independent authority.

The mark is two chalk stones held by a broken ochre oval: check that a review
still belongs with its inputs. The built-in imagegen tool supplied the painting;
only generated pigment was blended onto bare rock, using the inherited PNG codec
as data. The already installed libgd encoded the JPEG; no dependency was installed.
The exact image-tool prompt was:

> Edit this inherited square cave wall. Preserve exact canvas size, rock, cracks, lighting, framing and ALL ancestral paintings including Pepe frog and his five-digit hands, dotted trails, eye, branching twig. Add ONLY one small prehistoric pictograph on bare rock at approximate pixel rectangle x=920..1060 y=715..860 (1254 square canvas): two tiny uneven chalk-white pebbles enclosed together by a thin broken red ochre oval, signifying checking that a pair still belongs together. Worn thumb pigment with rock showing through. No new hands. No letters numbers text symbols logos borders. Keep every other pixel unchanged. Output entire wall, not cropped.

The tool placed the mark farther right and lower; the finishing helper selected
its actual pigment within (1010,760,140,120). A decoded-pixel comparison found
4,645 changed pixels and ZERO changes outside that rectangle. All ancestor marks
lie outside it. The rock itself remains beneath and between the selected strokes.
The final PNG decoded identically after encoding. IMAGE-24.json records hashes,
dimensions, encoding and preservation counts. The image-generation draft was
consumed in memory and not saved as an extra image.

Outputs:

- artifacts/line-1/wall-v4.png: required output, RGB PNG, 1254 × 1254.
- artifacts/line-1/wall.png: continuation, identical bytes to wall-v4.png.
- dist/line-1/24.jpg: JPEG, 512 × 512, 75,232 bytes.
- dist/line-1/24.json: exact requested record shape, number 24 after 23 records,
  with the final PNG's lowercase SHA-256 artifact URL.

Both final image sizes were opened and visually reviewed. Pepe's heavy-lidded
eyes, wide mouth and ancestral paintings remain. Both visible hands have five
digits each (four fingers and one thumb); no new hand or stencil was added.
No letters, numbers, logos, captions, signatures, watermarks, frames, real people,
political or hateful symbols were observed. The new mark uses worn red ochre and
chalk, with stone showing through. Cave dimensions, framing, cracks and torchlight
are preserved; pixels outside the mark are identical to the ancestor.

Unmet/limited requirements: the explicit beside-record JPEG requirement conflicts
with the blanket prohibition on pictures outside artifacts/. This step follows
the explicit dist/line-1/24.jpg path. Selected pigment necessarily covers some bare
rock inside the mark. No other visual requirement was observed unmet. This is a
local visual review, not independent approval. Required outputs remain untracked;
no force-add or staging was done.
