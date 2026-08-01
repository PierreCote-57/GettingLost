# Image pipeline

Where photo masters live locally, and how they are sized on the site. Images are placed and
uploaded by hand.

## Local folder structure

Root: `~/Pictures/GettingLost/Images/` — mirrors the hierarchy of `pages/`, `media/data/`
and FileBird.

```
~/Pictures/GettingLost/
  Images/          mirrors FileBird Images/ and the pages/ structure
    about/
    destinations/  campgrounds/ · lakes/ · parks/
    shared/
    templates/
    van/           checklists/ · howto/ · maintenance/ · van-overview/
```

The full tree with every leaf folder is in
[docs/conventions/folders.md](../conventions/folders.md). JSON data files are **not** here —
they live in the repo under `media/data/`.

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
