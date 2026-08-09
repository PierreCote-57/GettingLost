# Destinations dataset

The master table of Vancouver Island campgrounds — one line per place. The page that once
rendered it is retired; the **dataset** is live and is what this file documents. It is
rendered by the table view of `list_browser.jst`. See
[docs/rendering/list-browser.md](../rendering/list-browser.md).

**NO STATUS IN THIS FILE — BY RULE.** Counts, coverage, "pending", "N remain" are
deliberately absent. Status always comes from querying the data. Query the JSON; never quote
a count from here.

## Files

- **Source of truth:** `media/data/shared/list_browser/destinations.json` — one flat array,
  sorted by name, source order authoritative.
- **Built from:** `local/data/vi-campgrounds.json` and
  `local/data/vi-non-government-campgrounds.json`, both FROZEN — see
  [docs/conventions/site.md](../conventions/site.md).

There are no groups. The type axis is `tags.types` — its own closed facet since 2026-08-01,
see [docs/schema/types.md](../schema/types.md).

## Two kinds of row, and the difference matters

A bare `{file}` pointer is hydrated from the destination page's own JSON **at sync time**,
so there is no second copy to drift.

An inline row has no page and carries its own `access` — mostly `haversine` only, no `legs`,
so it derives no road badge. Match inline rows to pages by `name` when filling; coordinates
are unreliable, often a town centroid. Beware identity splits: the row once called "Morton
Lake Provincial Park" is the page now named `morton-lake-park.html`.

## Editing

Through `local/tools/jsonio.py` like every other file under `media/data/**`, including
single-field edits — [../conventions/json-format.md](../conventions/json-format.md). The old
"never `json.load`/`dump` this one, it reformats every place" rule died with the house format
on 2026-07-19: the file is now tab-indented one-field-per-line like its neighbours, so a
round-trip is byte-identical and there is no expanded-vs-compact mismatch left to preserve.

## Place schema

`name`, `url` (external home page — the Name column links to it), `file` (internal GL page →
the "On lost" column's View link), `operator` (carried but not displayed — the JSON
deliberately holds more than the table shows), `location:{lat,lng,pin,zoom,notes}` (the
Location column shows `notes`, linked to Google Maps when lat/lng exist),
`access:{haversine:[{town,km}]}` (see [docs/schema/access.md](../schema/access.md)),
`sites:[{label,url}]`, `amenities:[]`, `reservation:[{label,url}]`,
`footnotes:[{field,text}]` — a LIST, so one row can carry several, including multiple on one
field; numbered superscripts on the matching cell, deduped per group. Page publish and
comment settings live in top-level `wpSettings`, see
[docs/schema/wpsettings-comments.md](../schema/wpsettings-comments.md).

`reservation` uses the same `{label,url}` list shape as `sites`, rendered one entry per line,
so a row shows its status text plus a link to the booking site.

## Columns → fields

The Distance column's field is `haversine` and reads `access.haversine` for the **Campbell
River** entry only; Nanaimo and Victoria are carried in the data but not displayed.

The Access column's field is `roadBadge`, a **derived** value the renderer computes from
`access.legs` — blank until legs are filled.

**Renaming a column's `field` is the seam to watch:** `COLUMNS`, `fillDataCell()` and the
header-footnote check in the thead builder all switch on the same string, so all three move
together.

## Links and tooltips

Every link carries a `title` naming where it goes — Name "Open the destination's web site",
On lost "Open the page on this web site", Sites "Open the site map", Reservation "Open the
reservation web site", Location "Open in Google Maps". Tooltips sit on the `<a>`, **never**
the cell, so an unlinked cell has no tooltip. A shared `fillLinkList()` renders both Sites
and Reservation.

**Never render a link with no display element.** `sites` satisfies this with its "Map"
fallback for a url with an empty label — legitimate and in use. `reservation` has no
fallback: a url with no label renders nothing, and that is a DATA BUG to report and fix in
the JSON, never to paper over in code.

## Renderer behaviors

**One flat table** — colgroup, thead, tbody, numbered footnotes. The collapsible per-group
`<details>` sections, and the footnote deduping that went with them, belonged to the retired
overview page; `list_browser.jst` flattened them away and the only `<details>` left on the
page is a filter dropdown. Fixed-px columns via `table-layout:fixed` plus a colgroup. The
table breaks out of the theme's 900 cap on its own wrapper, not through a shared constant —
the mechanism and why `max-width` cannot do it are in
[../rendering/list-browser.md](../rendering/list-browser.md). Client-side sort by name
operates on a copy and never mutates source order.

## Standing data caveats

Distances are straight-line and approximate, and say so — the field is named `haversine` and
the header footnote reads "not road distance".

Coordinate precision **varies**: parks and rec-sites are geocoded to campground or lake
level, while many private and First Nations/regional entries are only town-level. Since the
Location cell is a live Google Maps link, imprecise coordinates are visible to visitors.

The Access column shows nothing until real `legs` are authored per place.

See [docs/recipes/data-fill.md](../recipes/data-fill.md) for how to fill this dataset, plus
[docs/schema/map-pins-location.md](../schema/map-pins-location.md) and
[docs/rendering/blocks.md](../rendering/blocks.md).
