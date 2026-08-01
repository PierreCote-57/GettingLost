# Image pipeline

The local-to-WordPress pipeline for photos. The schema half is built; the ingest script is
designed but not written.

## Local folder structure

Root: `~/Pictures/GettingLost/Images/` — mirrors the hierarchy of `pages/`, `media/data/`
and FileBird.

```
~/Pictures/GettingLost/
  _inbox/          staging: dump from Photos here, the script moves them out
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

## Filename convention

`{person}_{camera}-{original}.jpg` — `PC_i14-IMG_1234.jpg`, `JC_i14-IMG_5678.jpg`.

The person-plus-camera prefix avoids collisions across devices and preserves traceability
back to the original in the Photos app.

Device prefixes live in `~/.gl-devices.json`:

```json
{
  "iPhone 14 Pro": "PC_i14",
  "iPhone 14 Pro Max": "JC_i14"
}
```

The script reads the EXIF `Model` field to pick the prefix. Canon bodies get the same
treatment when needed — `JC_C70` and so on.

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

## `glmedia.py` — designed, not written

Its job is rename and upload **one** master.

```
glmedia.py --dest Images/destinations/lakes/echo-lake
```

1. Read EXIF `Model` for each file in `_inbox/`, look up the prefix in `~/.gl-devices.json`.
2. Rename `IMG_1234.jpg` → `PC_i14-IMG_1234.jpg`.
3. Move the renamed master to `--dest`.
4. Upload it to WP via `POST /wp-json/wp/v2/media`.
5. Assign it to the matching FileBird folder via
   `POST /wp-json/filebird/public/v1/folder/set-attachment`.
6. Clear `_inbox/`.

Idempotent — it skips files that already carry a device prefix. Needs a WP application
password or auth token, supplied per session.
