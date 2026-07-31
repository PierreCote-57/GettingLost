## Status: Partially done
Image schema (featuredImage/galleryImage) + the `formatImageUrl` seam were implemented 2026-07-03 — see [docs/schema/image.md](../schema/image.md). The resize script (`glmedia.py`), the sizing suffix, and the upload/FileBird pipeline below are still pending.

## Local Folder Structure
Root: `~/Pictures/GettingLost/Images/` — mirrors the same hierarchy as `pages/`, `media/data/`, and FileBird.

```
~/Pictures/GettingLost/
  _inbox/          ← staging: dump from Photos here, script moves out (planned)
  Images/          ← mirrors FileBird Images/ and pages/ structure
    about/
    destinations/
      campgrounds/
      lakes/
      parks/
    shared/
    templates/
    van/
      checklists/
      howto/
      maintenance/
      van-overview/
```
Full tree with all leaf folders: see [docs/conventions/folders.md](../conventions/folders.md)
Data files (JSON) are NOT here — they live in GitHub `media/data/`.

## Filename Convention
Format: `{person}_{camera}-{original}.jpg`
- Examples: `PC_i14-IMG_1234.jpg`, `JC_i14-IMG_5678.jpg`
- Preserves traceability back to original in Photos app
- Person+camera prefix avoids collision across devices

## Device Config (`~/.gl-devices.json`)
```json
{
  "iPhone 14 Pro": "PC_i14",
  "iPhone 14 Pro Max": "JC_i14"
}
```
Canon cameras (Joy has two) to be added when needed — format: `JC_C70` etc.
Script reads EXIF `Model` field to auto-determine prefix.

## Sizing Convention — SETTLED 2026-07-03: Jetpack Photon, not baked variants
- Data/JSON always stores **original bare filename** (no suffix, unchanged).
- Resizing is done LIVE by Jetpack Photon (`i0.wp.com/...?fit=w,h&quality=80`), implemented in `gettinglost.jst`'s `formatImageUrl(img,w,h)`. See [docs/schema/image.md](../schema/image.md) and [docs/rendering/blocks.md](../rendering/blocks.md).
- **No `-1920`/`-600` variant files, no filename suffix, no multi-upload.** The old bake-and-upload-multiples plan (glmedia.py steps 4–5 below) is abandoned for display sizing — Photon replaces it. glmedia.py's remaining job = rename + upload ONE master.
- Per-caller display sizes chosen: gallery card 600×400, mini-gallery thumb 360×220, lightbox 1920×1920, custom-tag inline 480×480 (all `fit=`, contain semantics). quality=80 global (72/60 available if smaller wanted).

## Script: `glmedia.py`
Planned interface:
```
glmedia.py --dest Images/Lakes/echo-lake
glmedia.py --dest Images/Van/howto-temperature-control --size 1920
glmedia.py --dest Images/Lakes/echo-lake --size 1920 --size 600
```

Script steps:
1. Read EXIF `Model` from each file in `_inbox/` → look up prefix in `~/.gl-devices.json`
2. Rename `IMG_1234.jpg` → `PC_i14-IMG_1234.jpg`
3. Move renamed master to `--dest` folder
4. Generate `-1920` (and other sizes) alongside master
5. Upload master + sized versions to WP via `POST /wp-json/wp/v2/media`
6. Assign to matching FileBird folder via `POST /wp-json/filebird/public/v1/folder/set-attachment`
7. Clear `_inbox/`

Script is idempotent — skips files already ending in `-{digits}` before extension.
Requires WP application password or auth token (supplied per-session).

## Rendering Change Needed (gettinglost.jst)
DONE as `formatImageUrl(filename)` — exists in both `gettinglost.jst` and `sync.js`,
prepends `/wp-content/uploads/`, throws on empty. Resizing = add a `size` arg to
BOTH mirrors to append `-1920`/`-600` before the extension; each renderer passes
`size` for `<img src>` while passing the bare filename for `<a href>` (full res).
See [docs/schema/image.md](../schema/image.md).

**Why:** `~/Claude/working-with-pierre.md`
