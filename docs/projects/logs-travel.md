# Logs and travel system

`logs/` holds Pierre's van and travel logs. It is the auto-commit exception (CLAUDE.md rule
3).

**`logs/` IS synced to WP.** `syncLogs` in `sync.js` publishes the whole tree **flat** to
`/wp-content/uploads/<basename>`, and files it in FileBird under a top-level **`logs`**
folder, peer of `Images` and `Data`. It is walked generically, so a new log file syncs
without touching that code.

**That flat publish is load-bearing, not incidental.** `logs/locations.json` is fetchable at
`/wp-content/uploads/locations.json`, and that is how the `googleMap` renderer resolves a
`location_id` ([docs/schema/map-pins-location.md](../schema/map-pins-location.md)). So a log
file is not rendered as a page of its own — there is no travel-log or fuel-log renderer —
but `locations.json` is read by the browser on any page whose map points at the registry.

## Naming rule (`<referent>_id`)
A field pointing at another object is named `<target>_id`; bare `id` = an object's OWN
identity. "id" = the target's canonical identifier: a `locations.json` record's `id`, or a
page's **github filename**. So `location_id` → locations.json; `post_id` → blog post
(filename). A place that HAS a destination page is referenced by that page's filename in a
`file` field — the same key, and the same meaning, as `file` everywhere else in the repo.

## The `location` block (shared by every log file)
A `location` is the place: `{ lat, lng, icon?, zoom?, pinList?, displayName?, img? }`
([docs/schema/map-pins-location.md](../schema/map-pins-location.md)). **In `logs/` — and
only there — a `location` may point instead**: `file` (a destination page filename) or
`location_id` (a `locations.json` id) stands in place of `lat`/`lng`, exactly as a
`googleMap` entry does, same `file` → `location_id` → `lat`/`lng` precedence. On a page a
`location` is always concrete.

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
Record: `{ name (first), id, address?, url?, location:{lat,lng,icon?,zoom?} }`.
`id` kebab-case = own identity; `location` always inline and concrete. Icon vocab is the one
shared list in `GL.PIN_ICONS` — tent/campground/picnic/lake/park/home/outhouse, see
[docs/schema/map-pins-location.md](../schema/map-pins-location.md). Rest-stop `url` uses the DriveBC map link w/ the API
id ([docs/reference/bc-rest-stops.md](../reference/bc-rest-stops.md)).

**The registry holds only places with no destination page.** A place that gets a page leaves
the registry, and references to it become `file` pointers — the page is the authority. Two
kinds of tenant live here: scaffolding (a real destination whose page doesn't exist yet, e.g.
`tyee-spit`) and permanent oddballs that will never be destinations (the storage
unit, the dealers, a rest area). `destination_id` was deleted with the 2026-08-16 migration —
it had no consumer and only existed to mark records that have now left.

## `logs/fuel-log.json` — fuel entries
`{ name (first), datetime, odometer_km, liters, price_per_liter_cad,
total_cost_cad, location, fullTank, id }`. Time field is `datetime` (NOT `arrival`).
`fuel-0001` = full-tank baseline (odo 641, 2026-07-05, Shell station inline location).
**Tank state is odometer-driven and lives entirely here**, decoupled from travel-log
granularity; the two join only via odometer for per-trip economy (later — needs a 2nd
`fullTank` fill with `liters` to get L/100km). `location` uses the shared block (coords or
ref) so fills are mappable and "near home vs on the road" is computed from coords.

## Commit workflow — device split (CLAUDE.md rule 3)
- **Computer:** Claude makes/edits entries then STOPS; Pierre pushes.
- **Phone:** Claude does full edit → commit → push to `main` (rule 3 auto-commit).

See [docs/conventions/github-workflow.md](../conventions/github-workflow.md) and
[docs/conventions/site.md](../conventions/site.md).
