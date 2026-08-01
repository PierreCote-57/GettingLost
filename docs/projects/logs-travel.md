# Logs and travel system

`logs/` holds Pierre's van and travel logs. It is the auto-commit exception (CLAUDE.md rule
3) and is **not synced to WP** — sync only walks `pages/`, `posts/` and `media/`.

**Data-only; there is no renderer.** A browser-side renderer would need to load
`locations.json` to resolve `location_id` references.

## Naming rule (`<referent>_id`)
A field pointing at another object is named `<target>_id`; bare `id` = an object's OWN
identity. "id" = the target's canonical identifier: a `locations.json` record's `id`, or a
page's **github filename**. So `location_id` → locations.json; `destination_id` → destination
page (filename); `post_id` → blog post (filename).

## The `location` block (shared by every log file)
One block, two forms — never two competing top-level fields:
- Reference: `"location": { "location_id": "oyster-bay-rest-area" }` → resolve in locations.json.
- Inline (ad-hoc/roadside, phone-GPS): `"location": { "lat":…, "lng":…, "name"?:…, "pin"?:… }`.
`location_id` present ⇒ resolve; absent ⇒ use inline coords. In `locations.json` records the
block is ALWAYS inline (the definition). Superset of the site's `{lat,lng,pin,zoom}` schema
([docs/schema/map-pins-location.md](../schema/map-pins-location.md)).

## `logs/travel-log.json` — unified "stop" entries
One type, a **stop**: `{ name, arrival, departure, location, note?, post_id?, id }`.
- `name` FIRST — IntelliJ collapses each entry to its name line; Pierre scans that way.
- `arrival`/`departure` = ISO-8601 with offset (Pierre uses `-08:00` year-round by choice).
  Duration is DERIVED (departure − arrival), never stored.
- `departure` three-way: `== arrival` → instant checkpoint (drive-by); later → completed stay;
  **null/absent → still there (van's current location)**.
- `location` = shared block above. `post_id`/`note` optional. No `from`/`to` — a stop is at
  ONE place; the journey is the chronological sequence. Only real destinations are logged
  (home/indoor-storage returns were dropped).
- **Weekend default:** a stay logged as "the weekend" (no exact times) = arrival **Fri 16:00**,
  departure **Mon 08:00**, unless Pierre specifies otherwise. Overridable per entry.
- ids: single `stop-000N` series.

## Insertion & sort (both travel-log and fuel-log)
**Always APPEND the newest entry LAST, by creation time — NOT by arrival/datetime.** This is
deliberate: appending is trivial, with no hunting for a chronological slot. Array order is
creation order. **Sort by `arrival`/`datetime` only on demand**, at render, never eagerly on
write.

## `logs/locations.json` — place registry
Record: `{ name (first), id, address?, url?, destination_id?, location:{lat,lng,pin?} }`.
`id` kebab-case = own identity; `destination_id` = the destination page's github filename;
`location` inline. Pin vocab: tent/campground/picnic/
lake/park/home. Rest-stop `url` uses the DriveBC map link w/ the API id ([docs/reference/bc-rest-stops.md](../reference/bc-rest-stops.md)).

## `logs/fuel-log.json` — fuel entries
`{ name (first), datetime, odometer_km, liters, price_per_liter_cad,
total_cost_cad, location, fullTank, id }`. Time field is `datetime` (NOT `arrival`).
`fuel-0001` = full-tank baseline (odo 641, 2026-07-05, Shell station inline location).
**Tank state is odometer-driven and lives entirely here**, decoupled from travel-log
granularity; the two join only via odometer for per-trip economy (later — needs a 2nd
`fullTank` fill with `liters` to get L/100km). `location` uses the shared block (coords or
ref) so fills are mappable and "near home vs on the road" is computed from coords.

## Commit workflow — device split (see `~/Claude/working-with-pierre.md`)
- **Computer:** Claude makes/edits entries then STOPS; Pierre pushes.
- **Phone:** Claude does full edit → commit → push to `main` (rule 3 auto-commit).

See [docs/conventions/github-workflow.md](../conventions/github-workflow.md) and
[docs/conventions/site.md](../conventions/site.md).
