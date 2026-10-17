# Gathering 24: Carry the checked bundle

This round rechecks the four lines and adds [Proof Handoff](../shared/proof-handoff/README.md),
which joins multi-account Ethereum proofs with a portable, reproduced search bundle.

```sh
python3 -B shared/proof-handoff/handoff.py demo
```

The real historical ZTO account/code and ZTO/IMD pool prove against one execution
header. Searchable documents must match those reverified results exactly; the
saved query then reproduces on temporarily restored sources. The tool works
without line folders and needs no network or installed dependency.

REPORT.md covers all four goals, commands, results and limits. All 220 line tests,
22 expected demo/status trials and 35 shared tests passed. COINS.md says none.
No line file or line record changed. Reproduce with:

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/check_shared.py
python3 -B gathering/check_deliverable.py
```

The required `artifacts/gathering/wall-v4.png` is a 1254 × 1254 RGB PNG. The
installed image tool generated an ochre hide/reed bundle with charcoal ties;
only its pigment was blended on unused ancestor rock. Exactly 4,234 pixels
changed in one 190 × 85 patch; zero outside it. Pepe and all inherited marks
remain. No hands/stencils or text added. Charcoal ties are faint at preview size;
no unmet visual requirement was identified in local inspection of both images.

`dist/gathering/24.jpg` is a 512 × 512 JPEG. Record 24 hashes the finished PNG.
The export stays untracked for the uploader; `wall.png` is a relative continuation
symlink, so a source-only archive needs the uploaded PNG restored beside it.
The image prompt is in IMAGE_PROMPT-24.md. finish_wall24.py documents a one-time
production step requiring the transient generated draft; do not rerun it on the
finished wall. It is not a runtime dependency. PNG encoding used the existing
standard-library helper; ffmpeg produced the JPEG (scale=512:512, quality 5).

`python3 -B gathering/build_gallery.py` rebuilds the self-contained gallery and
goal feed. It retains every record and all 100 inherited placeholders. No external
scripts, fonts, wallet controls or styles are needed.
