# Getting Lost in Canada — GitHub master

This repo is the **source of truth for the site's pages, posts and data** for the
"Getting Lost in Canada" WordPress.com site
([gettinglostonvi.wpcomstaging.com](https://gettinglostonvi.wpcomstaging.com)).

Edit here, push, and a GitHub Action syncs to WordPress. WordPress renders; it does not
master content. Site **navigation** is the one exception — that stays WP-mastered.

## Layout

`ls` it — the tree is not copied here; it rotted twice before it was removed (see
[docs/README.md](docs/README.md), "These files are not a cache of the repo"). What each
top-level folder is:

- `pages/` — page body markup, one `.html` per page, foldered by section.
- `posts/` — blog posts, one `.html` each. Can originate in WP, then mastered here.
- `media/data/` — the JSON each page reads at runtime, mirroring the `pages/` tree, plus
  `shared/`, `scripts/` and `templates/`.
- `logs/` — travel, locations and fuel logs. **Synced**: `syncLogs` publishes the tree
  flat to `/wp-content/uploads/`, which is how the browser reaches `locations.json`.
- `local/` — never synced: `sync/` (the GitHub Actions scripts), `tools/` (local Python run
  by hand), `charting/`, `data/` (FROZEN reference data), `refactor/`, `plugins/`.
- `docs/` — how the site works. [docs/README.md](docs/README.md) is the index.
- `.claude/` — Claude Code settings only. No content lives here.

**Filename is master.** A WordPress slug is always derived, never authored:
`amor-lake.html` → slug `amor-lake_html`. The transform exists twice — in `sync.js` and in
`gettinglost.jst` — and the two must agree on every input; change one, change the other.
See [docs/conventions/site.md](docs/conventions/site.md).

## Syncing to WordPress

**One-way, full overwrite — GitHub is master.** A sync replaces live WordPress content with
whatever is in the repo. No diff, no confirmation, no merge: anything edited directly in
WordPress since the last sync is lost. Always edit in the repo.

| Workflow | Trigger | Does |
| --- | --- | --- |
| `sync-on-push.yml` | automatic, on push to `main` | incremental sync of what changed; falls back to a full sync when the push includes deletions or touches `local/` |
| `sync.yml` | [manual](https://github.com/PierreCote-57/GettingLost/actions/workflows/sync.yml) | full overwrite, no diffing |
| `pull-posts.yml` | manual | fetches WP posts not yet in the repo, writes the files, commits and pushes |

Pages are created automatically — a new `pages/<name>.html` plus `media/data/…/<name>.json`
is enough; there is no page-ID map to maintain. JSON, `.jst`/`.cst` and `.pdf` files are pushed
to the media library at the same `/wp-content/uploads/<filename>` path they already use — with
one exception: the list-browser dataset sources and `datasets.json` are published in
*hydrated* form instead of verbatim, under those same names
([docs/rendering/list-browser.md](docs/rendering/list-browser.md)); because
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
