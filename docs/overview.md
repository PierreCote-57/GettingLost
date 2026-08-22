## WordPress Site
- Site: **Getting Lost in Canada** at `gettinglostonvi.wpcomstaging.com` (atomic, blog_id: 255518505)
- WP user: `logicielpierre` (Pierre Cote, id: 29687718)
- Custom domain `GettingLostInCanada.ca` is available and planned for future

## Repo Structure

`ls` it — the tree is not copied here (see [docs/README.md](README.md), "These files are not
a cache of the repo"). What the layout means:

- `pages/` — page HTML, one file per page, foldered by section (`about/`, `destinations/`
  with its four typed subfolders, `shared/`, `templates/`, `van/`).
- `posts/` — blog post HTML, one per post, peer of `pages/`.
- `media/data/` — mirrors `pages/` exactly, one JSON per page, plus `posts/` and `scripts/`.
- `local/` — never synced. `sync/` holds the two GitHub Actions scripts; `tools/` the local
  Python run by hand; `refactor/` one-shot migrations, outside `sync/` so committing one
  does not trigger a sync; `data/` FROZEN reference data; `charting/`; `plugins/`.
- `logs/` — travel, locations and fuel logs. **Synced**: `syncLogs` publishes the tree
  flat to `/wp-content/uploads/`, which is how the browser reaches `locations.json`.

Conventions that govern the tree are in
[docs/conventions/folders.md](conventions/folders.md).

## Current Navigation Structure (WP navigation post id: 5)
- **Destinations** (top-level, no dropdown) → `/list_browser_html/?dataset=destinations&view=grid`
- **Vehicles** (dropdown) → Van `/van-overview/`, "-> Maintenance" `/van-maintenance/`, Bronco
  `/bronco/`, "-> Maintenance" `/bronco-maintenance/`, an "—" separator (href `#`), then
  Checklists `?dataset=van-checklist&view=grid&booklet=checklists`, How to
  `?dataset=van-howto&view=grid&booklet=howto`. Renamed from "The Van" when the Bronco joined.
  The maintenance hrefs are the BARE page names, so they 301 to the real `_html` slugs — the
  same hop the Van and Bronco items take.
- The old per-type items (Lakes/Campgrounds/Parks/Rec Sites) are GONE — that axis is the
  list browser's **types** filter now (`tags.types`, a closed vocabulary — see
  [docs/schema/types.md](schema/types.md)). Those four words were keywords until 2026-08-01.
  See [docs/rendering/list-browser.md](rendering/list-browser.md).
- **Blog** → `/blog/`
- **Info** (dropdown) → About `/about/`, Useful Links `/useful-links/`, Useful Contacts `/useful-contacts/`, FSR/Logging roads `/logging/`
- CRITICAL: Always update navigation using Gutenberg block markup (`<!-- wp:navigation-link ... /-->`), NOT raw HTML `<li>` tags — raw HTML corrupts the nav and makes it disappear

## Sync Pipeline — GitHub Masters Everything (except navigation)
- **GitHub is master** for both pages and posts — push triggers the sync action automatically
- `sync.js` validates first, then pushes in six phases:
  1. **Pages** — dynamic WP lookup (no page-map.json), auto-creates missing pages, pushes title/excerpt/featured_image/status from per-page JSON
  2. **Posts** — same pattern as pages, using `/posts` WP endpoint. Pushes title/excerpt/featured_image/date/status. New posts get `comment_status: "open"`
  3. **Files** — uploads `.json`/`.jst`/`.cst`/`.pdf` to the WP media library (delete-then-recreate), flat under `/wp-content/uploads/`
  4. **List hydration** — manifest-driven (`loadHydratedListSet` reads `datasets.json`);
     each `{file}` pointer is replaced by the page's own JSON before upload. Replaced the
     old GALLERY_RULES auto-generation, which is deleted. The published manifest also carries
     a `counts` map per dataset (`collectCounts`) — how many rows each keyword, type, badge
     and road value would match, so the browser's dropdowns can show a number without walking
     the rows themselves.
  5. **Logs** — `syncLogs` publishes the whole `logs/` tree flat to
     `/wp-content/uploads/`, filed in FileBird under a top-level `logs` folder. This is how
     `locations.json` becomes fetchable, which is what resolves a `googleMap`
     `location_id` — see [docs/projects/logs-travel.md](projects/logs-travel.md)
  6. **PageMap** — `generatePageMap` writes `PageMap.json`, keyed by page filename with
     `{name}`, holding **published pages only**; `pageLink` reads it for its label
- **Validation runs first.** `main()` is load → validate → push: legs, destination types,
  link types and list hydration are all checked before anything uploads, and a failure means
  nothing is pushed.
- Sync is incremental on push, full on manual trigger. Incremental mode triggers on both HTML and JSON changes (fixed 2026-07-02)
- FileBird integration: media and pages filed into matching folder paths (best-effort)
- `FALLBACK_FEATURED_IMAGE_ID` in `sync.js` stands in when a page names a featured image WP does not have yet — it points at under-construction.png. The id itself lives in the code, not here; a WP id copied into a doc cannot announce that it went stale.
- Sync script does NOT delete orphaned WP content (pages, posts, or media) — must delete manually

## Pull Posts — WP → GitHub
- `pull-posts.js` fetches WP posts not yet in the repo, writes HTML + JSON files
- Runs via GitHub Actions (`pull-posts.yml`, manual trigger from Actions tab)
- Auto-commits and pushes new files (workflow has `permissions: contents: write`)
- The subsequent push triggers sync-on-push (idempotent — content matches)
- Posts can originate in either WP (e.g. phone dictation) or GitHub
- Once a post is in the repo, GitHub is master — WP edits are overwritten on next sync
- Pull never overwrites existing local files

## Per-Page JSON — Single Source of Truth
- Every HTML page has a matching JSON under `media/data/<path>/<name>/<name>.json`
- **The display-name field is `name`**, not `title` — renamed in schema-unification Phase 3a
  (2026-07-20); `sync.js` sets `body.title = pageData.name`. See
  [docs/schema/wp-title-date.md](schema/wp-title-date.md)
- Standard fields for pages that appear in a list: `name`, `featuredImage`, `excerpt`, `tags`, `wpSettings`
- Pages that don't (about, templates, home): `name`, `wpSettings` (plus any page-specific data)
- Post JSON fields: `name`, `excerpt`, `featuredImage`, `date`, `tags`, `wpSettings`, `categories` — `badges` sits under `tags` exactly as on a page (moved 2026-08-22; it was top-level on posts only)
- `wpSettings.published: true` → WP status "publish"; `false` → "draft" (see [docs/schema/wpsettings-comments.md](schema/wpsettings-comments.md))
- Only published pages show in the GRID view — that rule is `filterView`, not the data
- Howto/checklist pages also have `photoGalleries` and optionally `notes`
- Lake pages have `fishingReferences.bcIdentifier` (e.g. "00324SALM")

## List Browser (replaced the Gallery system, 2026-07-25)
- ONE page, `/list_browser_html/`, driven by URL params — `dataset`, `view`, `types`, `keywords`, `badges`, `access`, `search`, `booklet`
- `datasets.json` is the manifest — read it for the dataset list; each entry names its data
  file, title, and the ordered `options` recipe for its controls
- Sources live on disk in `media/data/shared/list_browser/`; sync hydrates the `{file}` pointers
- The old `gallery.*` and `destinations-overview.*` files are retired, and the frozen
  Lakes/Parks/Campgrounds/RecSites/Destinations/VanHowTo/VanChecklist JSONs are deleted from WP
- Details, and the pattern for adding a control or filter: [docs/rendering/list-browser.md](rendering/list-browser.md)

## Back-to-Gallery Links
- One bare `<div data-block-type="backToGallery">` per page — **no attributes at all**.
  The href and label are derived from `document.referrer`; see
  [docs/rendering/blocks.md](rendering/blocks.md).

## Templates
- `destination-template.html` — shared by campgrounds, parks, and rec sites (campground links + map + notes + backToGallery)
- `lake-template.html` — lake-specific (fishing references, rec sites, lake charts)
- `howto-template.html` — van howto/checklists
- `van-template.html` — van overview pages
- Old `campground-template.html` and `park-template.html` removed (2026-07-02)

Outstanding work is in [todo.md](todo.md) — never here. This file describes what the project
is, not what is left to do.
