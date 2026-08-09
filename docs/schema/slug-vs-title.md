# Slug vs title

Pierre's mental model, set 2026-07-12:

- **Slug = id = internal to the system** (URL bar = "computer talking to computer").
  Its job is uniqueness + sortability, NOT human readability. Free to pick purely for
  system hygiene.
- **Title = display name = user-facing** (browser tab, top of page, blog-list entry).
  Carries all the descriptive/readable weight.

Consequence for naming: don't argue slug readability/SEO — the Title does the talking.
Pick slugs like ids.

## Recurring-series posts → date-id names
For posts that will recur (e.g. **picnics**), the filename base is `<series>-YYYY-MM-DD`,
e.g. `picnic-2026-07-12.html` — the slug follows from it (`picnic-2026-07-12_html`), since
the filename is master. Rationale: descriptive names like `picnic-at-beavertail-lake`
collide on the *second* visit to the same place; a date id is unique + chronologically
sortable. Same-day collision (rare) → append `-2`/`-b`. This mirrors the travel-log
`stop-000N` id style — both are internal handles, neither is prose.

The **place** stays out of the name; it lives in the Title, the post body pageLinks, and
the `locations.json` record (which is place-keyed, e.g. `beavertail-lake-dayuse`, reused
across every picnic there — see [docs/projects/logs-travel.md](../projects/logs-travel.md)).

Renaming a post = 3 files in lockstep: `posts/<name>.html`,
`media/data/posts/<name>/<name>.json` (folder + file), and any `post_id` referencing it
in `logs/travel-log.json`. Filename is master ([docs/conventions/site.md](../conventions/site.md)).
