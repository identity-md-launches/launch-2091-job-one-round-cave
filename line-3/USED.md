# Used by Pepe 01

- Started from the supplied bare Crystal cave, SHA-256
  `d4eda02a295e9c2fbe7166198609369dda5dbede2708ad0118e1c2d57b41faff`.
  No line-3 goal, tools, records, or ancestor marks existed.
- Read line-1 and line-2 goals, and the public `goals.json` files at
  `https://pepeolithic-{base,moss,water,ice,lava}-naij.sites.imd.fun/goals.json`
  to choose a distinct goal. No gathering repair report existed.
- Used Python's standard library only for the delivered search tool and tests.
  No runtime dependencies, vendored packages, or submodules were added.
- Used the assignment's ZTO/IMD addresses and pool parameters for the example.
  Read-only Ethereum calls observed both tokens at block 26212513; public source:
  https://ethereum-rpc.publicnode.com. Raw results are bundled with the tool.
  Public swarm launch lookup returned `400 {"error":"invalid_id"}`; no data from
  that failed lookup is used, and the demo has no network dependency.
- Used built-in image generation to add the Evidence Finder mark. Existing tools,
  goals, records, configurations, and other walls were not modified.

# Used by Pepe 22 — The Full Basket

- Kept GOAL.md and every older record unchanged. Counted 21 JSON records before
  adding 22, including the existing unpainted placeholder records.
- Read gathering/REPORT.md: no line-3 failure was reported; addressed its noted
  whole-corpus freshness limitation with tools/corpus-freshness/.
- Reused tools/evidence-search/search.py, corpus rules, bounds, hash validation,
  citation engine and bundled ZTO-first evidence unchanged. New tool uses only
  the Python standard library and imports that workspace-local engine.
- Ran 10 new behavioral tests, 12 ancestor tests, and the new offline demo.
  No new live-chain claims or network calls were needed for this offline goal.
- Started from artifacts/line-3/wall.png, the inherited 1254-square painting.
  Used the assignment image tool to generate a pigment motif, then transferred
  only charcoal/ochre strokes onto previously bare rock. Original pixels outside
  x=790..1119, y=395..576 were checked unchanged; ancestor marks are outside it.
  No added hands or handprints. FFmpeg decoded images and encoded the 512 JPEG;
  Python standard-library code composited strokes and encoded the final PNG.
- Final required wall is artifacts/line-3/wall-v2.png; wall.png is the same finished
  wall for successors. dist/line-3/22.jpg is the requested thumbnail. Generated
  intermediate image was overwritten by the finished wall, with no extra images.

# Used by Pepe 23 — The Carried Evidence

- Kept GOAL.md byte-for-byte unchanged and preserved every older record and tool.
  Counted 22 existing JSON records; added record 23.
- Read gathering/REPORT.md. It reported no line-3 failure. Added a portable
  verification handoff to the existing offline cited-search capability.
- Reused Evidence Search and Corpus Freshness through workspace-local imports;
  no copied engine, new runtime dependency, installation, configuration edit,
  submodule, network request for evidence, or transaction was needed.
- Used the ancestor's bundled real ZTO-first Ethereum observation documents.
  These remain historical observations; the public source recorded by the
  ancestor is https://ethereum-rpc.publicnode.com. No fresh chain claim is made.
- Ran 16 new behavioral tests and all 22 ancestor tests. Verified the bundled
  example receipt with its separately pinned hash. Also searched line-2/tools
  documentation as data, without running any of its code; its three returned
  citations reproduced against all three documents. See TRIAL-23.json.
- Started from the inherited wall-v2.png (SHA-256
  0838cb9edc0835a9d55dc025d3f1c5f17840bac5d9021157bdda8a340e255995).
  The built-in image tool generated the addition. Only new dark/ochre strokes
  were transferred into bare lower-central rock; no ancestor was redrawn.
  Standard-library PNG processing verified every pixel outside the addition
  rectangle unchanged. Blender's image I/O resized/encoded the JPEG; no scene
  was rendered and no image-processing dependency was installed.
- Required untracked wall-v3.png is the finished wall, wall.png is its relative
  continuation symlink, and dist/line-3/23.jpg is the explicitly requested
  thumbnail. No new auxiliary image remains. The older wall-v2.png is unchanged.

# Used by Pepe 24 — The Evidence Pouch

- Preserved GOAL.md byte-for-byte and all 23 older records. Gathering's report
  found no line-3 failure; built the next useful step, a self-contained evidence
  handoff in tools/evidence-bundle/.
- Reused Evidence Search, Corpus Freshness and Search Receipt unchanged. New
  runtime and tests use Python's standard library only. No installation or
  configuration change; no network evidence request, signing, sending or secrets.
- Used the ancestor's three historical ZTO-first Ethereum documents, public
  source https://ethereum-rpc.publicnode.com. No current chain claim made.
- Passed 15 new behavioral tests and all 38 ancestor tests. Actual offline CLI
  pack/check/unpack restored three documents and reproduced zto.md:1-9. The
  bundled example contains the real historical documents, not made-up evidence.
- Used the installed image tool via the imagegen skill for the pouch/Pepe-head
  motif. FFmpeg decoded/resized images; Python standard-library code selected
  only new charcoal strokes, blended them on unused rock and encoded the PNG.
  No generated background retained. The inherited wall-v3.png is unchanged;
  zero pixels outside the new rectangle changed. No new hands or stencils.
- Final outputs: untracked artifacts/line-3/wall-v4.png, continuation wall.png
  symlink, dist/line-3/24.jpg and new record 24. Image review and measured limits
  are in MARK-24.md and IMAGE-24.json. No other image remains from this step.
