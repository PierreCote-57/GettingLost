# Destinations overview

> **The PAGE is retired — this memory survives for its SCHEMA only.** Read
> [docs/rendering/list-browser.md](../rendering/list-browser.md) and [docs/projects/schema-unification.md](schema-unification.md) first.
> Entries are unified-partial `{name, tags, links, location, access,
> campground{operator,siteCount,amenities,links}, footnotes}`, OR a bare `{file}`
> pointer hydrated from its page — at SYNC time now, not render time. Columns are
> Name / On-lost / Location / Distance / Access / Sites=plain siteCount / Maps /
> Amenities / Reservation. The flat-shape details below are pre-migration.

Master table of Vancouver Island campgrounds ("one line per place"), built 2026-07-14.

**NO STATUS IN THIS FILE — BY RULE.** Counts, coverage, "pending", and "N remain" are
deliberately absent: Pierre's standing rule is that memory holds recipes and schema, and
status ALWAYS comes from querying the data. Query the JSON; never quote a count from here.

**Files (2026-07-25)**
- Data (source of truth): `media/data/shared/list_browser/destinations.json` — ONE flat
  array, sorted by name, source order authoritative. The old grouped
  `destinations-overview.json` and its page/renderer are DELETED.
- Rendered by the table view of `list_browser.jst` (the `placesTable` block renderer and
  `destinations-overview.jst` are gone; the column machinery was ported over).
- Built from `local/data/vi-campgrounds.json` + `local/data/vi-non-government-campgrounds.json` (both FROZEN — see [docs/conventions/site.md](../conventions/site.md)).

**Groups are GONE** — BC Parks / RSTBC / Private RV / Government were the old grouping;
the flat file dropped them, and the type axis is `tags.keywords` now.

**Two kinds of row, and the difference matters.** A bare `{file}` pointer is hydrated
from the destination page's own JSON at SYNC time, so there is no second copy to drift.
An inline row has no page and carries its own `access` — mostly `haversine` only, no
`legs`, so it derives no road badge. Match inline rows to pages by `name` when filling
(coords are unreliable — often a town centroid). Beware identity splits: the old
"Morton Lake Provincial Park" row is the page now named `morton-lake-park.html`.

**Editing this file: do NOT json.load/dump it** — a round-trip reformats all 103
places. Use raw-text insertion anchored on the `"name"` or `"file"` line, then
re-parse to validate. Its `access` blocks are fully expanded while the destination
pages use compact one-line entries; that cosmetic mismatch is known and Pierre does
not care about it.

**Place schema:** `name`, `url` (external home page — Name column links to it), `file` (internal GL page → "On lost" column, "View" link), `operator` (carried but NO LONGER DISPLAYED as of 2026-07-19 — the JSON deliberately holds more than the table shows), `location:{lat,lng,pin,zoom,notes}` (Location column shows `notes`, linked to Google Maps when lat/lng exist), `access:{haversine:[{town,km}]}` (see [docs/schema/access.md](../schema/access.md) — replaced both the old top-level `distanceKM:[{from,km}]` and the old flat `access` road-word string on 2026-07-20), `sites:[{label,url}]`, `amenities:[]`, `reservation:[{label,url}]`, `footnotes:[{field,text}]` (a LIST, so one row can carry several, incl. multiple on one field; numbered superscripts on the matching cell, deduped per group). Page publish/comment settings live in top-level `wpSettings` — see [docs/schema/wpsettings-comments.md](../schema/wpsettings-comments.md).

**Columns → fields (2026-07-20 rework):** the Distance column's field is `haversine` and reads `access.haversine` for the **Campbell River** entry only (Nanaimo and Victoria are carried in the data but not yet displayed — widening the column is deferred). The Access column's field is `roadBadge`, a **derived** value computed by the renderer's local `roadBadge(place)` from `access.legs` — blank until legs are filled. Renaming a column's `field` is the seam to watch: `COLUMNS`, `fillDataCell()` and the header-footnote check in the thead builder all switch on the same string, so all three must move together.

**`reservation` (renamed from `reservation_status` 2026-07-19):** was a plain string, now the same `{label,url}` list shape as `sites`, rendered one entry per line (`<br>`). So a row shows its status text plus a link to the booking site. Migration rule used: existing text → one entry with `url: null`; null/empty → `[]`.

**Link + tooltip conventions (2026-07-19):** every link carries a `title` naming where it goes — Name "Open the destination's web site", On lost "Open the page on this web site", Sites "Open the site map", Reservation "Open the reservation web site", Location "Open in Google Maps". Tooltips sit on the `<a>`, NEVER the cell, so an unlinked cell has no tooltip. Shared `fillLinkList()` renders both Sites and Reservation.

**DATA-BUG RULE (Pierre's, general):** never render a link with no display element. `sites` satisfies this via its "Map" fallback for a url with an empty label — that's legitimate and in use. `reservation` has NO fallback: a url with no label renders nothing and is a DATA BUG to report to Pierre and fix in the JSON, not to paper over in code.

**Renderer behaviors:** each group = collapsible `<details>`, collapsed by default, count in summary; fixed-px columns via `table-layout:fixed` + identical colgroup so columns align across the separate per-group tables; `MAX_CONTENT_WIDTH=1180` (overrides the theme's 900 cap); client-side sort by name (on a copy — never mutates source order); footnotes deduped within a group.

**Standing data caveats:** distances are straight-line, approximate, and now say so — the field is named `haversine` and the header footnote reads "not road distance". Coordinate precision VARIES by group — parks/rec-sites are geocoded to campground/lake level, while many private and First Nations/regional entries are only town-level. Since the Location cell is a live Google Maps link, imprecise coords are visible to visitors. The old flat `access` road words were **deleted** 2026-07-20 (Pierre: "virtually all were guesses anyway"); the Access column now shows nothing until real `legs` are authored per place.

See [docs/recipes/data-fill.md](../recipes/data-fill.md) for how to fill this dataset, [docs/projects/logs-travel.md](logs-travel.md), [docs/schema/map-pins-location.md](../schema/map-pins-location.md), [docs/rendering/blocks.md](../rendering/blocks.md).
