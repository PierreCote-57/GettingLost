# Getting Lost in Canada — GitHub Master (Pages)

This repo is the **source of truth for site Pages** (lakes, parks, campgrounds,
templates, and core site pages) for the "Getting Lost in Canada" WordPress.com
site (gettinglostonvi.wpcomstaging.com).

**Blog posts stay native to WordPress** and are not represented here.

## Structure

```
pages/
  lakes/<slug>.html         — raw page body markup for each lake page
  parks/<slug>.html
  campgrounds/<slug>.html
  templates/<slug>.html     — Lake/Park/Campground Templates (drafts in WP)
  site/<slug>.html          — Home, Gallery, About, Useful Links

data/
  lakes/<slug>.json         — per-lake data consumed by lakes.jst
  parks/<slug>.json         (in progress)
  campgrounds/<slug>.json   (in progress)

scripts/
  gettinglost.jst           — sitewide block-renderer registry
  lakes.jst                 — lake-page-specific block renderers
  gallery.jst               — /gallery/ page renderer

gallery-data/               — Destinations.json, Lakes.json, Parks.json,
                               Campgrounds.json (in progress)

config/
  page-map.json             — slug → WordPress page ID, used by the future
                               sync script to know which WP page to update
```

## Status (this migration pass)

- ✅ All 20 lake pages + 3 templates + Elk Falls Park + 2 campgrounds + Home/
  Gallery/About/Useful Links pulled from WordPress (read-only) and saved here.
- ✅ Shared scripts (gettinglost.jst, lakes.jst, gallery.jst) pulled.
- 🔄 Lake JSON data files: 11 of 20 done (echo, amor, sproat, keogh, mohun,
  drum, crest, blackwater, chain, muchalat saved; remaining lakes + park JSON
  + campground JSON + the 4 gallery-data files still to pull).
- ✅ Sync script + GitHub Action built (see "Syncing to WordPress" below).

## Syncing to WordPress

**This is a one-way, full-overwrite sync — GitHub is master.** Running it
replaces the live WordPress content with whatever is currently in this repo.
There is no diff, no confirmation step, and no merge: if something was
changed directly in WordPress since the last sync, that change is lost.
Editing WordPress directly is no longer supported once you start using this —
always edit in the repo and sync.

### One-time setup (you do this, not Claude)

1. In WordPress, create an **Application Password** for the account that
   will authenticate (WordPress admin → Users → your profile → Application
   Passwords).
2. In this GitHub repo, go to **Settings → Secrets and variables → Actions**
   and add three repository secrets:
   - `WP_SITE_URL` — e.g. `https://gettinglostonvi.wpcomstaging.com`
   - `WP_USER` — the WordPress username for that Application Password
   - `WP_APP_PASSWORD` — the Application Password itself
3. Confirm the site's REST API is reachable at
   `<WP_SITE_URL>/wp-json/wp/v2/pages` (should return JSON, not a 404/403).

### Running a sync

1. Go to the **Actions** tab on GitHub.
2. Select **"Sync to WordPress"** from the workflow list.
3. Click **Run workflow** → confirm branch `main` → **Run workflow**.
4. Watch the run's logs to confirm success (it logs each page/file as it
   goes, then a pass/fail summary at the end).

### How it works

- **Pages** (`pages/**/*.html`) are pushed via a full `content` overwrite to
  the WordPress page ID listed in `config/page-map.json` for that slug.
- **JSON data files and `.jst` scripts** are pushed to the media library at
  the same `/wp-content/uploads/<filename>` path they already use. Because
  WordPress doesn't overwrite a same-named file by default (it appends
  `-1`, `-2`, etc. instead), the script deletes the existing media item for
  that filename first, then re-uploads — so the file briefly 404s for
  visitors mid-sync (normally under a second).
- Files sync before pages, so by the time a page is updated, any new data
  it depends on is already in place.
- Blog posts are never touched — the sync script only calls the WordPress
  `pages` and `media` REST endpoints, never `posts`.

## Notes / things to revisit

- A handful of legacy, ID-named JSON files (e.g. `00324SALM.json`) still exist
  in the WordPress uploads folder from before the slug-rename migration.
  These are stale and are **not** included here — only the current slug-named
  files are considered live/canonical.
- `sproat-lake.json`'s `fishingReferences.lakeChartUrl` is an array of
  `{name, url}` objects (3 bathymetric maps), whereas the `lakes.jst`
  renderer's `buildLakeChartRow()` expects a single URL string. This looks
  like a pre-existing data/renderer mismatch on the live site, not something
  introduced by this migration — worth flagging to Pierre separately.
- Images remain hosted in the WordPress media library (not migrated here).
  Page/data files reference them by path only.
