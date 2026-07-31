# BC rest stops dataset

Source switched 2026-07-10 to the **live DriveBC rest-stops API**:
`https://www.drivebc.ca/api/reststops/?format=json`, saved locally as
`local/data/bc-rest-stop.json` (**199** records, server-maintained, `modified_at` current).
This REPLACES the old PDF-parsed `bc-rest-areas.json`.

`local/data/` is reference data — NOT synced to WP (like [docs/projects/logs-travel.md](../projects/logs-travel.md)'s
`logs/`; only `pages/`/`posts/`/`media/` sync).

**By design, this is a lookup accessed on an as-needed basis** — e.g. pulling a
single rest stop's `id`/`url` when building a log location (Oyster Bay id=426). It is
NOT meant to be wired into site pages/galleries/maps; the dataset sitting "unconsumed"
is the intended state, not a gap.

## Schema (per record)
GeoJSON-ish: `{ id (int, e.g. 426=Oyster Bay), rest_stop_id (str), created_at, modified_at,
location:{ type:"Point", coordinates:[lng,lat] }, properties:{ REST_AREA_NAME, HIGHWAY_NUMBER,
NUMBER_OF_TOILETS, TOILET_TYPE, NUMBER_OF_TABLES, WHEELCHAIR_ACCESS_TOILET, POWER_TYPE, WI_FI,
EV_STATION_*, OPEN_YEAR_ROUND, OPEN_DATE, CLOSE_DATE, DIRECTION_OF_TRAFFIC, REST_AREA_CLASS,
DISTANCE_FROM_MUNICIPALITY, barrels… }, bbox }`. **Coordinates are [lng, lat] order.**

- `id` matches the DriveBC map URLs (`drivebc.ca/?...&id=426`) — use it as a rest stop's `url`
  (that's how Oyster Bay's `url` in `logs/locations.json` was set).
- **Open/closed IS captured now** — `OPEN_YEAR_ROUND` + seasonal `OPEN_DATE`/`CLOSE_DATE`
  ("MM-DD"). This was the old PDF dataset's known gap; the live API closes it.

## Retired 2026-07-10 (PDF-parse lineage removed)
Dropped in favour of the API: `bc-rest-areas.json` (201 recs), `bc-rest-areas-list.pdf`,
`bc-rest-areas-PARSE-PLAN.md`. Nothing in the repo referenced them. The 199 (API) vs 201 (PDF)
delta was never reconciled — the live API is authoritative. The old pymupdf/`fitz` positional
parse is no longer needed.
