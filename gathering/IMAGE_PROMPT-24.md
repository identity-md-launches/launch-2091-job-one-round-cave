# Gathering 24 image production

Used the installed built-in image generation tool (`mcp__image__generate_image`),
one image, requested 1024 × 1024; returned 1254 × 1254 RGB PNG at the required
export path. The prompt was:

> A single very small prehistoric cave pictograph, centered with wide empty margins,
> on uniform pale warm sandstone ochre. Depict a small rolled hide bundle containing
> three short uneven ochre reeds, tied securely by two charcoal bands. This symbolizes
> carrying verified evidence together. Hand drawn with burnt stick and thumb, rough
> irregular earth pigment strokes, worn and broken texture, Lascaux cave art. Simple
> flat symbolic drawing, red ochre outlines and charcoal black binding, bare ochre
> stone showing through. No hands, no people, no animals. Absolutely no text, letters,
> numbers, captions, signature, logos, border, frame or watermark. Not photographic,
> no 3D. The small bundle should occupy only the central half of the square.

The inherited wall was visually inspected first. The generated draft was also
inspected, then `finish_wall24.py` selected only the new pigment and blended it
into a 190 × 85 patch of unused rock below the bowl. It overwrote the transient
draft with the final wall, retaining original dimensions and every pixel outside
that patch. No extra image was saved. ffmpeg produced the required 512-pixel JPEG.

Both final image sizes were inspected explicitly. The central Pepe and ancestral
marks remain; no hands, stencils, text, numbers or prohibited symbols were added.
The charcoal ties are subtle on the rock, especially in the thumbnail. No unmet
visual requirement was identified in this local review. The final export and
preview are artifacts/gathering/wall-v4.png and dist/gathering/24.jpg.
