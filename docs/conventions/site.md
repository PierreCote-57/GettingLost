## Standing Conventions
- ALL placeholder body text is "Under construction" — never lorem ipsum
- Every new page gets an "Under construction" featured image set AT CREATION TIME (mandatory `featuredImage`)
- **As of 2026-07-04, `featuredImage` is grid/list-ONLY — it is NOT shown at the top of pages/posts** (the `wp:post-featured-image` block was removed from the Pages & Single Post templates). Top/body images are hand-placed `gl-photo`s. `galleryImage` is retired. See [docs/schema/image.md](../schema/image.md) and [docs/rendering/wp-templates.md](../rendering/wp-templates.md).
- Root-relative URLs site-wide
- External links: `target="_blank" rel="noopener noreferrer"`
- WPautop disabled via "Disable WPautop" plugin (Nick Momrik) — no stray `<br/>` in multi-line inline elements
- **JSON house format** — tab-indented, one field per line, written through `local/tools/jsonio.py`. The rule lives in [.claude/rules/json-format.md](../../.claude/rules/json-format.md), which loads every session, because it governs an action rather than describing the site. `local/data/**` is exempt and frozen.
- **After adding or editing `tags.keywords`, run the keyword validation pass.** Keywords are an OPEN vocabulary — unlike badges and access, nothing declares the valid values, so the list drifts: plurals, synonyms and one-off spellings accumulate silently. The `keyword-validation` skill walks every value across the datasets and surfaces the suspects; it reports, and the author decides. Run it on demand, never in the build and never in the filter. The rule lives in [.claude/rules/keywords.md](../../.claude/rules/keywords.md), which loads whenever a `media/data` JSON file is in play.
- **After changing destination content, check the cross-references both ways.** Pages point at each other by `file` — a lake's `destinations` block names nearby rec-sites and parks, and those pages point back. Editing one side without the other leaves them disagreeing, and nothing at build time catches it. Only rows carrying a `file` link are in scope; a catalog-only row has nothing to check against. Turning this into a repeatable skill is `docs/todo.md` #16.
- **A new HTML page always gets its matching JSON at the same time** — pages fetch their JSON at runtime, so a missing file is a console error. Use the proper structure for the page type, never a bare `{}`.
- **List JSON files are sorted BY HAND**, in the file itself — the reverse of the old rule. `gallery.jst` used to sort alphabetically at render time; it is retired, and the list browser treats source order as authoritative. `destinations.json` is kept sorted by name.

## Slug / filename model — github filename is MASTER (finalized 2026-07-08)
- The github **filename is the single source of truth**. A WP slug is always DERIVED, never authored or stored as truth. Any prior "slug is the key/master" rule is DEAD — do not reintroduce it.
- WP slug for every object (page/post/attachment) = `<base>_<ext>` = `fileToSlug(filename)` (replace the last `.`→`_`, then WP-sanitise: lowercase etc.). Inverse: `slugToFilename(slug)` = last `_`→`.`. Both transforms live **byte-identically in sync.js AND gettinglost.jst**.
  - `amor-lake.html` → slug `amor-lake_html`; `beavertail-lake.json` → attachment slug `beavertail-lake_json`. The FILE keeps its plain name (`amor-lake.json`, fetched by URL); only the slug carries `_<ext>`. NEVER hardcode `_html` (that was the `htmlSlug` bug, removed).
- **Every map (sync.js + jst) is keyed by the github FILENAME. Base is NEVER a key** — base exists only transiently to construct a related filename (a page `foo.html` finds its data by swapping to the fixed `.json` → `foo.json`).
- Authors reference other pages/files by FILENAME, never a slug: `data-file="foo.html"` (pageLink), `"file":"foo.html"` (internal reference). Internal link = `file`; external = `url`. The jst derives the slug. See [docs/rendering/blocks.md](../rendering/blocks.md).
- Sync validates what WP actually stored (pages via the permalink, media via `slug`). A DRIFT (WP stored something else, e.g. a `-2` suffix) now emits a GitHub `::error::` annotation AND **fails the run red** (`annotateFailure()`) — was a silent `console.warn` before 2026-07-08. So a green sync means every slug landed exactly as requested.
- One-shot migration action: `local/refactor/slug-refactor.js` + `.github/workflows/slug-refactor.yml` (manual, dry-run by default; `-N` dup slug/filename → FLAGGED, no action). Deliberately placed OUTSIDE `local/sync/**` so committing it does not trigger a sync. See [docs/projects/slug-rebuild.md](../projects/slug-rebuild.md).

## Destination types (2026-07-18)
Under `pages/destinations/` + `media/data/destinations/` there are typed subfolders: `lakes/`, `campgrounds/`, `parks/`, `rec-sites/`. They no longer generate per-type galleries (`GALLERY_RULES` is deleted) — the folder is just filing, and the type a visitor filters on is `tags.keywords` on the page's JSON. A **provincial park is its own type** — it lives in `parks/`, NOT `rec-sites/` (Pierre's call: "a park is a park, not a rec site"; he moved Sproat Lake Provincial Park there by hand). A park page uses the same skeleton as a rec-site page (campground block, googleMap + description, notes, photoGallery, backToGallery). The `backToGallery` block takes **no attributes** — see [docs/rendering/blocks.md](../rendering/blocks.md). On a LAKE page, the list of nearby places is the `destinations` block (renamed from `recSites` 2026-07-18; see [docs/rendering/blocks.md](../rendering/blocks.md)), whose **Type** column labels each entry (Rec site default / Park / Private / …). See also [docs/recipes/lake-page.md](../recipes/lake-page.md).

## Image Path Warning
WordPress's default year/month folder behavior means a bare-filename block reference (photoGallery/photoRef/.gl-photo) can silently 404 unless re-uploaded flat or Settings→Media folder option is disabled. Check this whenever adding new images. As of 2026-07-03 ALL page/post image data is bare filenames resolved via `formatImageUrl` (flat `/wp-content/uploads/`), so flat storage is now a hard dependency — see [docs/schema/image.md](../schema/image.md).

## FileBird Folder Structure
FileBird keeps **two independent folder trees**: media folders (Images/Data, for library attachments) and **post-type folders** (for pages/posts). Sync mirrors a repo path into BOTH: `[filebird:media]` files uploaded media into media folders, `[filebird:pages]` files the WP page/post into a page folder. So a repo folder rename (e.g. `van/instructions`→`van/howto`) creates the new folder in whichever tree the next full sync touches and **leaves the old one orphaned — sync never deletes**; rename it manually in both trees to avoid orphans (case-insensitive match lets sync reuse it).

Two root media folders: **Images** (id:52) and **Data** (id:56) — peers.

Full folder trees with IDs are in [docs/conventions/folders.md](folders.md) — always check there for current state.

**Data/** tree was reorganized 2026-06-30 and matches GitHub `media/data/` exactly.

FileBird REST API: Bearer token auth at `/wp-json/filebird/public/v1/`
- The token is **not in this repo** — it is in Claude's `feedback-session-start` memory. See
  [docs/reference/filebird-api.md](../reference/filebird-api.md).
- Media API docs: https://ninjateam.gitbook.io/filebird/integrations/developer-zone/apis
- Post Type Folders API docs: https://ninjateam.gitbook.io/filebird/integrations/developer-zone/post-type-folders-api

**Media (Images/Data) API — all confirmed working (2026-06-30):**
- `GET /folders` — list folder tree
- `GET /folder/?folder_id=ID` — get folder details
- `GET /attachment-id/?folder_id=ID` — list attachment IDs in a folder. To turn those into filenames (e.g. building a `photoGalleries` block from a folder): `GET /wp/v2/media?include=<ids>&orderby=include&per_page=100&_fields=id,source_url` → `basename(source_url)`. Note `data-count` in `/folders` is RECURSIVE (parent counts children). Find a folder id by walking `/folders` → `data.folders[].children[]` (`text`/`id`).
- `GET /attachment-count/?folder_id=ID` — count attachments in a folder
- `POST /folders` — create folder. Params: `name` (string), `parent_id` (int)
- `POST /folder/set-attachment` — assign media to folder. Params: `folder` (int), `ids` (array of int). Set folder=0 for Uncategorized.
- IMPORTANT: param names differ between endpoints (e.g. `parent_id` for create, `folder` for set-attachment) — always check docs.

**Post Type Folders API (installed and working):**
- `GET /post-type-folders/?post_type=page` — list page folder tree
- `POST /post-type-folders` — create folder (`post_type`, `title`, `parent`)
- `POST /post-type-folder/update` — rename/move folder (`post_type`, `id`, `title`, `parent`)
- `POST /post-type-folder/delete` — delete folder (`post_type`, `ids[]`)
- `POST /post-type-folder/set-posts` — assign pages to folder (`post_type`, `folderId`, `ids[]`)

## Known Bugs
- **Sproat Lake**: fully built 2026-07-18 (lake page + Sproat Lake Provincial Park park page). It uses `fishingReferences.lakeChartList` = array of `{name,url}` (3 bathymetric sheets), the current schema every lake uses (mohun is live) — the old `lakeChartUrl`-single-string bug note is obsolete; the array renders fine.

## Site Icon
RVIcon.png is live.

## Google Maps API Key
Loaded in `gettinglost.jst` as `MAP_CONFIG.mapApiKey`. Whether it carries an HTTP-referrer restriction is not recorded anywhere in the repo and has not been checked — `docs/todo.md` #15. What to do at the domain move is in [docs/site-move.md](../site-move.md).
