# Image pipeline

How images are sized on the site. Images are placed and uploaded by hand, **by Pierre** — the
image half of the WP media library is his, with no external master and no tree to reconcile.
Claude's role is on-demand only: confirm a referenced file is present and findable, and handle
ad-hoc requests. See *Images are Pierre's* in
[docs/conventions/folders.md](../conventions/folders.md).

`~/Pictures/GettingLost/Images/` is Pierre's own utility folder, not a master and not a mirror.
It is where [recipes/image-editing.md](../recipes/image-editing.md) works when he asks for an
edit. JSON data files are not there — they live in the repo under `media/data/`.

## Sizing: Jetpack Photon, not baked variants

- The data always stores the **original bare filename**, no suffix.
- Resizing happens live via Jetpack Photon (`i0.wp.com/…?fit=w,h&quality=80`), implemented
  in `gettinglost.jst`'s `formatImageUrl(img,w,h)`. See
  [docs/schema/image.md](../schema/image.md) and
  [docs/rendering/blocks.md](../rendering/blocks.md).
- **No variant files, no filename suffix, no multi-upload.** Photon replaces all of it.
- Per-caller display sizes: gallery card 600×400, mini-gallery thumb 360×220, lightbox
  1920×1920, custom-tag inline 480×480 — all `fit=`, contain semantics. `quality=80`
  globally; 72 and 60 are available if smaller is wanted.
