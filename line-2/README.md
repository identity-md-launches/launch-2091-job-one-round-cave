# Following the root

Line 2 begins with State Witness, a portable verifier of Ethereum account and storage proofs against a trusted state root. The cave figure studies a tree whose separate branches reach one root, just as the tool follows witness nodes back to their shared commitment.

Run the real ZTO/IMD pool example offline from the repository root:

```sh
python3 -B line-2/tools/state-witness/witness.py demo --pool
```

See [the tool README](tools/state-witness/README.md) for observed chain data, explicit-root verification, optional fresh captures, test results, trust boundaries, and next pieces. There are no dependencies beyond Python 3.9+ standard library. The one-line goal was chosen after checking the earlier caves; it stays fixed for future rounds.

## Wall files and review

- `artifacts/line-2/wall.png`: PNG, RGB, **1254 × 1254**, the same square dimensions as the supplied cave.
- `dist/line-2/01.jpg`: JPEG, three components, **512 × 512**, a thumbnail of the finished PNG, 69,640 bytes.
- `dist/line-2/01.json`: first numbered record; image URL uses the lowercase SHA-256 of the actual finished PNG bytes.

I visually inspected the generated painting and decoded the JPEG thumbnail with the image viewer. Pepe has heavy-lidded eyes, a wide thick-lipped mouth, and two distinct open hands. I counted **five digits per hand** (four fingers and one thumb). There are no other hands or handprints. The figure and tree use ochre, charcoal, and chalk with worn edges and exposed rock. No letters, numbers, captions, logos, signatures, watermarks, frames, real people, or political/hateful symbols were observed. Major cracks, corner crystals, floor, framing, and warm torchlight remain recognisable. This line had no earlier marks to preserve.

Limitations/unmet requirements: the generative edit preserves the composition and major rock features, but is not pixel-identical to unpainted source texture. The brief requires a JPEG beside the JSON in `dist/line-2/` and also forbids all pictures outside `artifacts/`; these conflict. As in the accepted first line, the JPEG follows the explicit beside-record location, so the blanket picture-location restriction is unmet for that required thumbnail only. The image service also uses its own default generated-output location before copying the selected PNG into the declared artifact path. No other visual requirement was observed unmet. This is local visual review, not external approval.

## Image generation

Method: built-in imagegen, precise-object edit of the supplied bare cave, followed by format conversion and area downsampling for the thumbnail. No painting was drawn procedurally. The generation prompt was:

> Use case: precise-object-edit. Edit target: supplied bare square cave wall, first painting for a new wall. Preserve original square 1254x1254 size, all major cracks, rough warm rock, torch lighting, shadows, framing, floor and both corner crystals. Add ONLY a modest ancient pigment painting in the left-middle of the central stone, leaving most space empty for future painters. One recognizable Pepe the frog as a simple prehistoric cave figure: big heavy-lidded eyes, very wide thick-lipped mouth, squatting, hand-made worn charcoal contours with red and yellow ochre and chalk white; bare rock visible through uneven pigment. Pepe inspects a small branching tree of charcoal lines and ochre/chalk pebble-shaped leaves to his right, symbolizing checking branches back to a shared root. The tree is a primitive pictogram, no technical text or labels. Two open visible hands, EACH with exactly FIVE distinct digits: four fingers and one thumb. Count five per hand. Keep hands clear and separated from the tree. Do not add other hands or handprints. This must look like Lascaux or Chauvet cave art, not a modern cartoon sticker, photo, or 3D frog. No letters, numbers, words, captions, signatures, logos, watermarks, borders, frames, political symbols or real people. Preserve the cave texture and composition; do not repaint the environment. If saving is supported, save only the final image to artifacts/line-2/wall.png.

## Round 22 addition

[Header Anchor](tools/header-anchor/README.md) now binds the existing account and
storage proofs to a caller-supplied execution block hash by reconstructing the
header and extracting its committed state root. Run its real ZTO/IMD pool demo:

```sh
python3 -B line-2/tools/header-anchor/anchor.py demo
```

Fourteen new tests and all thirty ancestor tests passed. Independent checkpoint
authentication and finality remain external. [Round 22](ROUND-22.md) records the
new root-in-stone painting, image prompt, preservation method and limitations;
[review measurements](REVIEW-22.json) describe the finished 1254-pixel PNGs and
512-pixel JPEG. The first-round account above remains a historical record.

## Round 23 addition

[Code Witness](tools/code-witness/README.md) now checks supplied account code
bytes against the header-anchored account proof. Its offline real ZTO demo:

```sh
python3 -B line-2/tools/code-witness/code_witness.py demo
```

Nine new tests and all 44 ancestor tests passed. This proves stored-code byte
identity, not source, ABI, storage layout or execution behavior. The checkpoint
still needs independent authentication. [Round 23](ROUND-23.md) and
[review measurements](REVIEW-23.json) record the matching-stones painting,
1254-pixel PNG outputs, 512-pixel JPEG, preservation check and known limits.

## Round 24 addition

[Proof Set](tools/proof-set/README.md) checks multiple real account and storage
witnesses under a single trusted header hash. Its offline demo combines ZTO's
account and stored-code commitment with the ZTO/IMD pool's raw storage proof:

```sh
python3 -B line-2/tools/proof-set/proof_set.py demo
```

Eight new tests passed. [Round 24](ROUND-24.md) and
[review measurements](REVIEW-24.json) describe the added three-pebble mark,
finished square PNG, 512-pixel JPEG and trust limits.
