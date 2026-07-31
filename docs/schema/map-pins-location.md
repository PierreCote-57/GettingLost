# Map pins and location schema

Built 2026-07-08. The Google-map block now drops a **single marker for the PRIMARY item only** (the page's own lat/lng — the lake on a lake page, the rec site on a rec-site page; rec-site coords are NOT looped onto the map).

## location object (schema change 2026-07-08)
Top-level `lat`/`lng` on destination page JSON were replaced by one object (all 13 destination files migrated):
```json
"location": { "lat": 49.9812, "lng": -125.5033, "pin": "lake", "zoom": 14 }
```
- `zoom` is OPTIONAL — an absolute override of `MAP_CONFIG.mapZoom` (default 13). Only the two `*-dayuse` sites set it (`14`, one level in).
- Rec-site entries inside `recSites[]` keep their own flat nested `lat`/`lng` (still unused by the map). Rationale for the object over 3 loose top-level keys: groups the whole "where is this" concern and gives `zoom` a home. Pierre's call ("I like clean organization").

## pin vocabulary + assignment rules
Values (lowercase, controlled): `lake`, `campground`, `park`, `tent`, `picnic`, `home`. Rules:
- **lake** — lake pages.
- **campground** — COMMERCIAL campground / RV resort (Pacific Playgrounds, Salmon Point).
- **tent** — rec site (or park) you can CAMP at (Elk Falls/Quinsam = `tent`, even though it's under `parks/`).
- **picnic** — DAY-USE rec site (the two `*-dayuse` pages).
- **park** — defined in the vocab but currently UNUSED (no file uses it).
- **home** — added 2026-07-08 (garage icon) for home-base / storage locations; introduced for the travel log's `logs/locations.json` (indoor-storage uses it), NOT used by destination pages. See [docs/projects/logs-travel.md](../projects/logs-travel.md).
General rule Pierre stated: rec site with camping = tent; commercial campground = campground.

## Marker rendering (gettinglost.jst googleMap renderer) — REBUILT 2026-07-21
`googleRoadMap` was **merged into `googleMap`** — one renderer, selected by the div's `data-map` attribute (like `photoGallery`'s `data-gallery`). Supports MULTIPLE maps per page.
- **No `data-map`** → synthesizes a single plain marker from `pageData.location` (icon from `location.pin`, hover title from `name`). The ~25 single-marker pages are untouched, no JSON change. There is NO reserved "default" map name — Pierre scrapped it as klunky; no-attribute goes straight to `location`.
- **`data-map="road"`** → renders `pageData.googleMap.road = { lat?, lng?, zoom?, pins }`. `lat`/`lng` are **flat peers** (same shape as location/pins — Pierre: "lat/lng/zoom should be peers", NOT a nested `center` object), fall back to `location` when both absent; `zoom` → `MAP_CONFIG.mapZoom`.
- **Unified pin** `{ pin?, label?, img?, lat, lng }` (lat/lng required; `id` was DROPPED — no consumer): `img` with `/` = `"galleryKey/itemId"` ref into `photoGalleries` (pulls img+label); without `/` = direct file. Render: `pin`→custom icon else default; resolved `img`→click InfoWindow; label-only→hover `title`; neither→plain marker. label chain: `pin.label`→gallery item's label→the `img` string→none.
- `location` STAYS top-level (canonical coordinate) — the list browser's table view reads `location.notes` (Location-column text) + lat/lng (Maps link), so it can't move into the map collection. Pierre floated collapsing `location` into `googleMap.road` and REJECTED it: road center is a viewport (≠ the destination point on multi-pin pages like Morton, whose road center frames the highway), and `location.notes` has no home in the map. Only `location` and the list browser's Location column read it — nothing else (grid cards, sync.js don't).
- **Road-map template pass (2026-07-21):** every destination page that used the default single-marker (16 pages: 2 campgrounds, 2 parks, 10 lakes, 2 rec-sites; `mohun-lake-rec0184` excluded — it already had a road map) got a `googleMap.road` seeded as a **1-pin copy of `location`** (`{lat,lng,zoom?,pins:[{pin,lat,lng}]}`, inserted right after `location`) and its HTML `googleMap` div switched to `data-map="road"`. `location` retained (non-breaking — road center falls back to it, overview unaffected). Purpose: a ready template to hang "on the way" photo pins on, like Morton's road map. Applied via a script through [docs/recipes/data-fill.md](../recipes/data-fill.md)'s `jsonio.py`.
- **Live center/zoom caption** under EVERY map (no width gate — Pierre removed it): a centered `<div>` after the map, wired to the map's `idle` event, `Center = (lat, lng) · Zoom = n`, 6-decimal. Deliberate authoring aid to dial in center/zoom; "public for now, hide from real users later."
- Maps inside collapsed `<details>` init zero-size → never fire `idle` (caption frozen, tiles may not draw) — known quirk, not a bug to chase.
- `pinIcon(pin)` unchanged: unknown/absent pin → `null` → default Google pin. `google.maps.Marker` now emits a **deprecation console warning** (AdvancedMarkerElement); parked (needs a Map ID + kills inline `mapStyles`). Migration recipe + prereqs in [docs/rendering/blocks.md](../rendering/blocks.md)/todo.

## Pin delivery — GL.PIN_ICONS as inline SVG data-URI
The 6 marker figures are inline SVG STRINGS in `gl-constants.jst` (`GL.PIN_ICONS`), keyed by pin. `pinIcon()` returns `{ url: "data:image/svg+xml," + encodeURIComponent(svg), scaledSize: 48×48, anchor: (24,24) }`.
- Each SVG is a standalone `48×48` viewBox, figure centered via `transform="translate(24,24)"`; `xmlns` is REQUIRED (data-URI images need it). Anchor is CENTER (Pierre rejected the teardrop shape → not bottom-anchored).
- Chosen over `google.maps.Symbol` (single-path only — can't do our multi-shape/multi-color glyphs) and `AdvancedMarkerElement` (needs `mapId` + marker library — bigger change, not needed now).
- Tweak art = edit the SVG numbers in `gl-constants.jst`. Design is a first pass; expect to nudge on real maps. Figures: lake=blue disc+waves, campground=amber caravan, park=green tree, tent=brown tent w/ door+guy-lines, picnic=red A-frame table, home=slate garage (peaked roof + light roll-up door, added 2026-07-08).

## gl-constants.jst — home for sitewide ALL-CAPS constants
New file `media/data/scripts/gl-constants.jst`. Holds `GL.PIN_ICONS`, and `GL.TAG_COLORS` / `GL.TAG_FALLBACK` / `GL.MAP_CONFIG` MOVED here out of gettinglost.jst. `gettinglost.jst` now aliases them (`var MAP_CONFIG = GL.MAP_CONFIG;` at IIFE top). Renderer-SPECIFIC config stays with its renderer (lakes.jst's `CONFIG` stocking URL, list_browser.jst's `DATASETS_URL`/`UPLOADS` — NOT moved). Put genuinely global ALL-CAPS constants here going forward.

## Load order (WP footer) — load-bearing
`gl-constants.jst` MUST load BEFORE `gettinglost.jst` (which reads those globals). Both are injected in the **Footer template part** — see [docs/rendering/wp-templates.md](../rendering/wp-templates.md) for the exact edit. All `.jst` upload to `wp-content/uploads` via the sync pipeline (`docs/conventions/github-workflow.md` — sync runs in GitHub Actions). Related: [docs/rendering/blocks.md](../rendering/blocks.md), [docs/conventions/site.md](../conventions/site.md).
