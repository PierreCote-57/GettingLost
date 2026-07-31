# Image editing toolkit

Established 2026-07-03 while cropping/retouching the 5 van-overview photos (`~/Pictures/GettingLost/Images/van/van-overview/`).

## Environment (what's actually available)
- **Python3 + Pillow 11.3.0** — the workhorse. `from PIL import Image, ImageOps, ImageFilter, ImageDraw`.
- **numpy is NOT installed** — do not `import numpy`; write pure-PIL.
- **`sips`** (built-in) exists but only rotates in 90° steps and reports `orientation: <nil>` (doesn't surface the EXIF tag) — not useful here.
- **No `magick`/`convert` (ImageMagick)** locally. Node *is* installed (since 2026-07-20, see [docs/conventions/github-workflow.md](../conventions/github-workflow.md)) but image work stays pure-PIL. Write the script into the scratchpad and run it by path — not an inline heredoc, which prompts every time.

## EXIF orientation (critical gotcha)
iPhone photos are stored as a landscape 4032×3024 buffer plus an EXIF **Orientation tag** (tag id 274). Values seen: `1`=upright, `6`=rotate 90° CW on display. The **Read tool shows RAW pixels and ignores the tag**, so tag-6 photos look sideways to me but are upright to Pierre in Preview. Nothing is actually crooked.
- Always `im = ImageOps.exif_transpose(Image.open(f))` FIRST to get the upright frame Pierre sees, then crop in that coordinate space. exif_transpose bakes rotation into pixels and strips the tag, so saved output stays upright.

## Techniques used
- **Crop**: `im.crop((l,t,r,b))` in exif-uprighted coords.
- **Object / reflection removal via donor-clone** (no AI/inpaint model needed): copy a clean donor region, `canvas.paste(donor,(x,y))`, then composite through a feathered mask: `ImageDraw` a white rect on an "L" image, `ImageFilter.GaussianBlur(feather)`, `Image.composite(canvas, im, mask)`.
  - Removed a neighbor truck by sampling a **horizontal-band donor** from the clean right-of-van background (ocean→road→gravel bands align). Left a faint ghost at the van edge (accepted).
  - Removed reflected sign text ("OMNIA" wordmark + "8LA/930") on tinted glass by **cloning clean glass from just above** the letters (`dy` negative), split around the chrome pillar so it stays untouched.

## Workflow
The image folder is `~/Pictures/GettingLost/Images/…`; write each step's result into a
`_preview/` subfolder of it so Pierre reviews and zooms in Preview. Keep originals
untouched. The scratchpad is fine for intermediate inspection crops, but nothing he is meant
to look at stays there.

The general rule — show work as files in the folder he has open, don't iterate silently — is
in `~/Claude/working-with-pierre.md` §9.

Downstream: cropped masters get uploaded to WP keeping their exact names (e.g. `IMG_2769_crop.jpg`, flat under `/wp-content/uploads/`) and referenced bare in photoGalleries JSON — see [docs/rendering/blocks.md](../rendering/blocks.md), [docs/schema/image.md](../schema/image.md).
