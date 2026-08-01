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

There are no groups. The type axis is `tags.keywords`.

## Two kinds of row, and the difference matters

A bare `{file}` pointer is hydrated from the destination page's own JSON **at sync time**,
so there is no second copy to drift.

An inline row has no page and carries its own `access` — mostly `haversine` only, no `legs`,
so it derives no road badge. Match inline rows to pages by `name` when filling; coordinates
are unreliable, often a town centroid. Beware identity splits: the row once called "Morton
Lake Provincial Park" is the page now named `morton-lake-park.html`.

## Editing

**Do not `json.load`/`dump` this file** — a round-trip reformats every place. Use raw-text
insertion anchored on the `"name"` or `"file"` line, then re-parse to validate. Its `access`
blocks are fully expanded while the destination pages use compact one-line entries; that
cosmetic mismatch is known and deliberate.

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

Each group is a collapsible `<details>`, collapsed by default, with the count in the summary.
Fixed-px columns via `table-layout:fixed` plus an identical colgroup, so columns align across
the separate per-group tables. `MAX_CONTENT_WIDTH=1180` overrides the theme's 900 cap.
Client-side sort by name operates on a copy and never mutates source order. Footnotes are
deduped within a group.

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
