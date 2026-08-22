# Slug rebuild

## The problem it solved

A per-page JSON uploaded as a WP attachment `<slug>.json` had its `post_name` derived from
the filename minus extension (`beavertail-lake`), which collided with the **page** slug in
WordPress's shared post-slug namespace. Pages got bumped to `-2`, and sync re-created them
every run.

## The model

A **universal `<base>_<ext>` slug** for everything pushed — page → `_html`, json → `_json` —
so nothing shares a slug. With it came the paradigm shift: **the github filename is the
master**, not the slug.

The finalized rules live in [docs/conventions/site.md](../conventions/site.md) under
"Slug / filename model". In short:

- `fileToSlug(filename)` and its inverse `slugToFilename` exist in both `sync.js` and
  `gettinglost.jst` and must agree on every input — same output, not the same source text.
- Every map is keyed by the FILENAME. Base is never a key — only a transient used to build
  `<base>.json`.
- Authors link by filename (`data-file`, `file`); the jst derives slugs. See
  [docs/rendering/blocks.md](../rendering/blocks.md).

## Artifacts still in the repo

- `local/refactor/slug-refactor.js` — the one-shot migration action that renamed existing WP
  slugs in place. Dry-run by default, `-N` duplicates flagged rather than acted on.
  Deliberately outside `local/sync/` so committing it does not trigger a sync.
- Slug drift now **fails the build**: `annotateFailure()` emits a GitHub `::error::` and
  increments the failure count, turning the run red. It was a silent `console.warn` before.
