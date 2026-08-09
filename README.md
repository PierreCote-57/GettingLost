# Getting Lost in Canada — GitHub master

This repo is the **source of truth for the site's pages, posts and data** for the
"Getting Lost in Canada" WordPress.com site
([gettinglostonvi.wpcomstaging.com](https://gettinglostonvi.wpcomstaging.com)).

Edit here, push, and a GitHub Action syncs to WordPress. WordPress renders; it does not
master content. Site **navigation** is the one exception — that stays WP-mastered.

## Layout

```
pages/            page body markup, one .html per page
  destinations/     lakes/ · campgrounds/ · parks/ · rec-sites/
  van/              howto/ · checklists/ · maintenance/
  about/  shared/  templates/

posts/            blog posts, one .html each — pulled from WP, then mastered here

media/data/       the JSON each page reads at runtime, mirroring the pages/ tree
                  plus shared/  scripts/  templates/

logs/             travel, locations and fuel logs

local/            never synced — tooling and reference material
  sync/             sync.js · pull-posts.js
  tools/            jsonio.py · build_booklet_pdf.py · keyword_validation.py · check_docs.py
  charting/         gen-chart.py + captured CSVs
  data/             FROZEN reference data (LakeData, rest stops, campground lists)
  refactor/         one-shot migration scripts
  config/  plugins/

docs/             how the site works — see docs/README.md for the index
.claude/          Claude Code settings.json only — no content lives here
```

**Filename is master.** A WordPress slug is always derived, never authored:
`amor-lake.html` → slug `amor-lake_html`. The transform lives byte-identically in
`sync.js` and `gettinglost.jst`. See [docs/conventions/site.md](docs/conventions/site.md).

## Syncing to WordPress

**One-way, full overwrite — GitHub is master.** A sync replaces live WordPress content with
whatever is in the repo. No diff, no confirmation, no merge: anything edited directly in
WordPress since the last sync is lost. Always edit in the repo.

| Workflow | Trigger | Does |
| --- | --- | --- |
| `sync-on-push.yml` | automatic, on push to `main` | incremental sync of what changed; falls back to a full sync when the push includes deletions or touches `local/` |
| `sync.yml` | [manual](https://github.com/PierreCote-57/GettingLost/actions/workflows/sync.yml) | full overwrite, no diffing |
| `pull-posts.yml` | manual | fetches WP posts not yet in the repo, writes the files, commits and pushes |

Pages are created automatically — a new `pages/foo.html` plus `media/data/…/foo.json` is
enough; there is no page-ID map to maintain. JSON, `.jst`/`.cst` and `.pdf` files are pushed
to the media library at the same `/wp-content/uploads/<filename>` path they already use; because
WordPress won't overwrite a same-named file, the sync deletes the existing item first and
re-uploads, so the file 404s for well under a second mid-sync. Files sync before pages, so a
page is never updated ahead of the data it depends on.

### One-time setup

1. In WordPress, create an **Application Password** (admin → Users → your profile).
2. In this repo, **Settings → Secrets and variables → Actions**, add: `WP_SITE_URL`,
   `WP_USER`, `WP_APP_PASSWORD`, `FILEBIRD_TOKEN`.
3. Confirm `<WP_SITE_URL>/wp-json/wp/v2/pages` returns JSON.

Secrets are write-only, so the sync scripts only ever run for real in Actions — locally they
are good for syntax and logic checks. See
[docs/conventions/github-workflow.md](docs/conventions/github-workflow.md).

## Documentation

[docs/README.md](docs/README.md) indexes everything: the data schemas, site conventions,
how a page becomes HTML, recipes for building a page, the external data sources, and the
records of past work.

## Notes

- Images live in the WordPress media library, not in this repo. Pages and data reference
  them by filename.
- A handful of legacy ID-named JSON files (e.g. `00324SALM.json`) still sit in the WP
  uploads folder from before the slug migration. They are stale; the canonical file is
  always the one named after the page's filename.
