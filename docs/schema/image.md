# Image schema

Established 2026-07-03. How image fields in `media/data/**/<slug>.json` flow to the WP featured image and to gallery cards. **This is the foundation for the future image-resize work** — see [docs/projects/images.md](../projects/images.md).

## MODEL CHANGE 2026-07-04 — featuredImage is now GRID/LIST-ONLY; galleryImage RETIRED
Pierre redesigned the image model so pages/posts have **no image at the top by default**:
- **`featuredImage` = the lists/galleries image, full stop.** It feeds `featured_media` (which the theme's query-loop listings use — Posts page, home "recent posts") AND the generated gallery JSONs. It is **no longer displayed at the top of a page or single post**, because the `wp:post-featured-image` block was removed from the Twenty Twenty-Five **Pages** (`twentytwentyfive//page`) and **Single Posts** (`twentytwentyfive//single`) templates. See [docs/rendering/wp-templates.md](../rendering/wp-templates.md).
- **Any image inside a page/post body is a `gl-photo`** the editor hand-places (with its own size). The top "hero" is now just content, decoupled from `featuredImage`.
- **`galleryImage` is RETIRED** — obsolete once there's no top featured image to differ from. All data migrated to `featuredImage`; sync.js line ~251 is now `image: data.featuredImage ?? "under-construction.png"` (no `galleryImage` fallback). A repo-wide grep for `galleryImage` returns nothing.
- Keep `featuredImage` populated even though it's not shown at top — it's what listings + SEO/Open-Graph previews use.

## Fields
- **featuredImage** — mandatory, the grid/list image (see model change above). Bare filename (e.g. `"IMG_0795.jpg"`) → that image; **`null`/absent → `featured_media: 0`** = no listing thumbnail. Never `""`.
- **`""` is banned everywhere — a data bug.** `null` = honest "no image" (safe under `??`/`in`/schema checks; `""` is not). **Missing key ≡ null** (idiomatic JS — both falsy, both caught by `??` and `== null`).

## Resolution & consumers
- **featured_media** (sync.js syncPages/syncPosts): featuredImage present → media-id lookup (or `FALLBACK_FEATURED_IMAGE_ID=1751` = under-construction, if named-but-not-yet-uploaded); **`null`/absent → `featured_media: 0`** = TRUE MASTER, the repo can clear it without touching WP. Consumed by the **listing query loops only** now (not shown on the single page/post itself).
- **Gallery card** (sync.js generateGalleryJsons): `image: data.featuredImage ?? "under-construction.png"`. under-construction is a **gallery/render fallback ONLY**. The generated gallery JSON's `image` field holds the resolved BARE filename; gettinglost.jst prepends the path.

## formatImageUrl — the two copies now DIVERGE (resize implemented 2026-07-03 via Jetpack Photon)
- Both take a **bare filename** and throw on empty/null (fail-fast, `~/Claude/working-with-pierre.md`). But they no longer mirror:
- **gettinglost.jst copy = the DISPLAY URL seam.** Signature `formatImageUrl(img, w, h)`; returns `https://i0.wp.com/{location.host}/wp-content/uploads/{img}?fit={w},{h}&quality=80` — a Jetpack Photon URL that resizes on the fly. `fit` = contain (never crops), `w`/`h` default 1920 (long-edge cap). `location.host` survives a future custom-domain move. **The bake-`-1920`/`-600`-variants plan is DEAD** — Photon does it live, no variant files, no filename suffix.
- **sync.js copy stays `/wp-content/uploads/<filename>`** — deliberately NOT Photon-ified, because it's a media-map lookup KEY (matches how loadWpMediaMap keys the map), not a display URL. Photon-ifying it would break every featured-image media-id lookup.
- Per-caller sizes + the two dual-window (thumbnail+lightbox) splits: see [docs/rendering/blocks.md](../rendering/blocks.md).
- WP featured image (theme-rendered, `featured_media`) is already Photon'd via Jetpack srcset — separate track, not our code.

## Reuse across pages — same image on many pages is STANDARD (confirmed 2026-07-13)
Galleries and `featuredImage` reference images by **bare filename**, so the same file can appear in any number of page/post galleries with no duplication — Pierre's explicit "standard practice to show the same image on multiple pages." A WP attachment lives in exactly **one** FileBird media folder, but that residence is irrelevant to rendering — `formatImageUrl` resolves purely by filename. So referencing `IMG_2796.jpeg` (filed under the beavertail-lake-dayuse media folder) from the picnic post gallery is correct and needs no re-filing. **Do NOT flag a "gallery image not in this page's FileBird folder" as a problem — it's by design.** (Media `set-attachment` is manual/broken anyway — see [docs/conventions/folders.md](../conventions/folders.md).)

## Data / pipeline state
- All ~19 source JSONs migrated from full `/wp-content/uploads/...` paths to **bare filenames** under `featuredImage` (2026-07-03).
- Hard dependency: WP media must be FLAT under `/wp-content/uploads/` (no year/month folders) — see Image Path Warning in [docs/conventions/site.md](../conventions/site.md).

## Corner-chip fields moved under `badges` (2026-07-13)
Card corner data no longer sits at top level: `tags` migrated to **`badges.tags`**, and a new **`badges.road`** drives the road-condition badge. `renderCard` and `sync.js` read the nested shape. Full spec in [docs/schema/badges-road.md](badges-road.md).
- **pull-posts.js** writes `featuredImage` as a bare filename (`path.basename` of source_url), **`null` not `""`**, and `console.warn`s when `featured_media` isn't found in the media map (the silent-miss that lost post featured images during the wpcomstaging migration). See [[project-posts-featured-backfill]].
