## WordPress Site
- Site: **Getting Lost in Canada** at `gettinglostonvi.wpcomstaging.com` (atomic, blog_id: 255518505)
- WP user: `logicielpierre` (Pierre Cote, id: 29687718)
- Custom domain `GettingLostInCanada.ca` is available and planned for future

## Repo Structure
```
pages/
  about/          — about.html, useful-contacts.html, useful-links.html
  destinations/
    campgrounds/  — campground pages
    lakes/        — lake destination pages
    parks/        — park pages
    rec-sites/    — rec site pages (BC rec sites, regional rec areas)
  shared/         — list_browser.html, home.html
  templates/      — destination-template, howto-template, lake-template, van-template
  van/
    van-overview.html
    howto/          — howto-*.html
    checklists/     — checklist-*.html
    maintenance/    — (empty, future)
posts/              — blog post HTML files (one per post)
media/
  data/             — mirrors pages/ exactly, one JSON per page (+ posts/)
    about/, destinations/, shared/, templates/, van/
    posts/          — per-post JSON metadata
    scripts/        — gl-constants.jst, gettinglost.jst, list_browser.jst, lakes.jst
local/
  sync/
    sync.js          — GitHub Actions sync script (pages + posts)
    pull-posts.js    — GitHub Actions script to pull new WP posts into repo
  plugins/
    filebird_new/    — FileBird Pro plugin zip
```
See [docs/conventions/folders.md](conventions/folders.md) for the complete tree with all leaf folders.

## Current Navigation Structure (WP navigation post id: 5)
- **Destinations** (top-level, no dropdown) → `/list_browser_html/?dataset=destinations&view=grid`
- **The Van** (dropdown) → Overview `/van-overview/`, Checklists `?dataset=van-checklist&view=grid`, How to `?dataset=van-howto&view=grid`
- The old per-type items (Lakes/Campgrounds/Parks/Rec Sites) are GONE — that axis is the
  list browser's **types** filter now (`tags.types`, a closed vocabulary — see
  [docs/schema/types.md](schema/types.md)). Those four words were keywords until 2026-08-01.
  See [docs/rendering/list-browser.md](rendering/list-browser.md).
- **Blog** → `/blog/`
- **About** (dropdown) → About `/about/`, Useful Links `/useful-links/`, Useful Contacts `/useful-contacts/`
- Maintenance menu item not yet added (planned)
- CRITICAL: Always update navigation using Gutenberg block markup (`<!-- wp:navigation-link ... /-->`), NOT raw HTML `<li>` tags — raw HTML corrupts the nav and makes it disappear

## Sync Pipeline — GitHub Masters Everything (except navigation)
- **GitHub is master** for both pages and posts — push triggers the sync action automatically
- `sync.js` does five things:
  1. **Pages** — dynamic WP lookup (no page-map.json), auto-creates missing pages, pushes title/excerpt/featured_image/status from per-page JSON
  2. **Posts** — same pattern as pages, using `/posts` WP endpoint. Pushes title/excerpt/featured_image/date/status. New posts get `comment_status: "open"`
  3. **Files** — uploads JSON/JST to WP media library (delete-then-recreate)
  4. **List hydration** — manifest-driven (`loadHydratedListSet` reads `datasets.json`);
     each `{file}` pointer is replaced by the page's own JSON before upload. Replaced the
     old GALLERY_RULES auto-generation, which is deleted. The published manifest also carries
     a `counts` map per dataset (`collectCounts`) — how many rows each keyword, type, badge
     and road value would match, so the browser's dropdowns can show a number without walking
     the rows themselves.
  5. **Validation** — `main()` runs load → validate → push. Legs, types and list hydration
     are checked before anything is uploaded, and a failure means nothing is pushed.
- Sync is incremental on push, full on manual trigger. Incremental mode triggers on both HTML and JSON changes (fixed 2026-07-02)
- FileBird integration: media and pages filed into matching folder paths (best-effort)
- `FALLBACK_FEATURED_IMAGE_ID = 1751` (under-construction.png)
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
- Every HTML page has a matching JSON under `media/data/<path>/<slug>/<slug>.json`
- Standard fields for pages that appear in a list: `title`, `featuredImage`, `excerpt`, `tags`, `wpSettings`
- Pages that don't (about, templates, home): `title`, `wpSettings` (plus any page-specific data)
- Post JSON fields: `title`, `excerpt`, `image`, `date`, `published`, `categories`, `tags`
- `wpSettings.published: true` → WP status "publish"; `false` → "draft" (see [docs/schema/wpsettings-comments.md](schema/wpsettings-comments.md))
- Only published pages show in the GRID view — that rule is `filterView`, not the data
- Howto/checklist pages also have `photoGalleries` and optionally `notes`
- Lake pages have `fishingReferences.bcIdentifier` (e.g. "00324SALM")

## List Browser (replaced the Gallery system, 2026-07-25)
- ONE page, `/list_browser_html/`, driven by URL params: `?dataset=&view=&keywords=&badges=&access=&search=`
- `datasets.json` = the 3 datasets (`destinations`, `van-howto`, `van-checklist`); each names
  its data file, title, and the ordered `options` recipe for its controls
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

## Pending / To Do
- keogh-lake and sproat-lake — no source images found
- ~~Tag badges on gallery cards~~ — DONE
- ~~Tag filtering~~ — DONE 2026-07-25 in the list browser, not the gallery: an options bar
  writing URL params, OR within a control and AND across controls
- ~~Blog post editing~~ — DONE (2026-07-02): sync.js pushes posts, pull-posts.js pulls from WP
- Add Maintenance menu item to The Van dropdown once maintenance pages are created
- A van-maintenance dataset is not yet created (add it to `datasets.json` once van/maintenance/ pages exist)
- Delete `Van.json` from WP Admin → Media Library if still there (orphaned)
- Clean up orphaned WP pages: `park-template`, `campground-template` (sync doesn't delete orphans)
