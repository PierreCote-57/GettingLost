# Slug rebuild — COMPLETE & DEPLOYED (2026-07-08)

## What it fixed
Per-page JSON uploaded as a WP attachment `<slug>.json` had its `post_name` derived
from the filename minus extension (`beavertail-lake`), colliding with the **page**
slug in the shared post-slug namespace → pages bumped to `-2`, and sync re-created
pages every run. Fixed by a **universal `<base>_<ext>` slug** for everything we push
(page→`_html`, json→`_json`, etc.) so nothing shares a slug, plus a paradigm shift:
**the github filename became the master** (was the slug).

## The finalized model — see [docs/conventions/site.md](../conventions/site.md) "Slug / filename model"
- `fileToSlug(filename)` (last `.`→`_`, sanitised) + inverse `slugToFilename` — byte-identical
  in sync.js and gettinglost.jst. `htmlSlug`'s hardcoded `_html` was deleted.
- Every map keyed by the FILENAME; base is never a key (only a transient to build `<base>.json`).
- Authors link by filename (`data-file`, references `file`); jst derives slugs. See [docs/rendering/blocks.md](../rendering/blocks.md).

## How it rolled out (order that worked)
1. `slug-refactor.js` one-shot action (in `local/refactor/`, NOT `local/sync/`, so it
   doesn't trigger a sync) renamed existing WP slugs in place, dry-run-by-default,
   `-N` dups FLAGGED. Ran clean.
2. `sync.js` rewritten: filename-keyed maps, `loadWpPageMap/PostMap` keyed via
   `slugToFilename(item.slug)`, `perPageDataMap` keyed by data filename, generators
   driven by the page-file map emitting `file`.
3. `gettinglost.jst`: `fetchPageData` reverses URL slug→`<base>.json`; `renderCard`
   uses `entry.file`; `pageLink` reads `data-file`; `window.GL.fileToSlug` exposed.
4. Block/attr cleanup: `pageLink data-file`, `backToGallery data-file`=full `<name>.json`
   (gallery URL derived from `gallery.html`), internal-vs-external `file`/`url` on
   `notes` + lakes.jst `buildReferencesCell`. Content swept (data-slug→data-file, internal
   url→file).
5. Drift now FAILS the build: `annotateFailure()` emits `::error::` + increments failCount
   → red run (was silent `console.warn`).

## Still open / housekeeping
- Sweep the duplicate slugs the refactor action FLAGGED (if any remained) — Pierre cleans manually.
- Brewster Lake stub still to be wired (untracked stub from an earlier session).
