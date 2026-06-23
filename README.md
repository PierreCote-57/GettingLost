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
- ⏭️ Not yet built: the sync script and GitHub Action that will push changes
  from this repo back to WordPress.

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
