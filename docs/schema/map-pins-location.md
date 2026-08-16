# Map pins and location schema

Unified 2026-08-16: `location`, a named `googleMap` entry and a `pin` are **one shape**, so a
place can be a map, a marker, or the target of a pointer without being restated.

## The shape

```
Point               lat, lng
googleMap : Point   zoom?, pinList?   (or file? / location_id? in place of lat/lng)
pin       : Point   icon?, displayName?, img?
location  : both    zoom?, pinList?, icon?, displayName?, img?
```

| Element | location | googleMap | pin |
| --- | --- | --- | --- |
| `file` | — | one of | — |
| `location_id` | — | one of | — |
| `lat`/`lng` | required | one of | optional |
| `icon` | optional | — | optional |
| `zoom` | optional | optional | — |
| `pinList` | optional | optional | — |
| `displayName` | optional | — | optional |
| `img` | optional | — | optional |

*one of* — exactly one required, precedence `file` → `location_id` → `lat`/`lng`.

`location` is the **union** of the other two, and the only one with no pointer fields — it is
what `file` and `location_id` resolve to. That is the whole model: a `location` is a valid
`googleMap` AND a valid `pin`.

- `zoom` overrides `MAP_CONFIG.mapZoom` (default 13).
- In a `pin`, absent `lat`/`lng` mean the map's centre.
- `displayName` on a `location` is the list browser's Location-column text
  ([list_browser.jst](../../media/data/scripts/list_browser.jst)); on a `pin` it is the
  marker's hover title / InfoWindow header.
- `location` stays top-level and does not move into `googleMap`: a road map's centre is a
  *viewport* (Morton's frames the highway, not the lake), and the Location column needs a
  place record, not a map.

## Resolution

Every block is named. `data-map` picks one entry out of `pageData.googleMap`; a div with no
`data-map` is an error.

1. `file` — a page **filename** (`"morton-lake.html"`, matching `file` everywhere else in the
   repo). That page's `location` becomes the map. A page naming itself is answered from
   `pageData` with no fetch.
2. `location_id` — an id in `logs/locations.json`; that record's `location` becomes the map.
3. `lat` + `lng` — the entry is the map.

**A pointer replaces the entry outright** — `zoom` and `pinList` come from the target too,
never a mix. Extra keys are legal and ignored, so a `file` can be renamed to `fileSAV` to fall
back to an older source while testing. A `location` never points, so resolution is always one
hop and always terminates.

After resolution a top-level `icon` becomes a `pinList` entry at the centre (copied, not
appended — the self-pointer path hands back `pageData.location` by reference).

Typical destination: `"road": { "file": "<own filename>.html" }`. A map spells out
coordinates only when it genuinely differs from the page's location — today that is Morton's
`road` and `campground`, and mohun's `road`.

## icon vocabulary + assignment rules
Values (lowercase, controlled): `lake`, `campground`, `park`, `tent`, `picnic`, `home`. Rules:
- **lake** — lake pages.
- **campground** — COMMERCIAL campground / RV resort (Pacific Playgrounds, Salmon Point).
- **tent** — rec site (or park) you can CAMP at (Elk Falls/Quinsam = `tent`, even though it's under `parks/`).
- **picnic** — DAY-USE rec site (the two `*-dayuse` pages).
- **park** — Tyee Spit in the registry.
- **home** — added 2026-07-08 (garage icon) for home-base / storage locations; introduced for the travel log's `logs/locations.json` (indoor-storage uses it), NOT used by destination pages. See [docs/projects/logs-travel.md](../projects/logs-travel.md).
General rule Pierre stated: rec site with camping = tent; commercial campground = campground.

## Marker rendering (gettinglost.jst googleMap renderer)
- **A pin** is `{ icon?, displayName?, img?, lat?, lng? }`: `img` with `/` = `"galleryKey/itemId"` ref into `photoGalleries` (pulls img + its label); without `/` = direct file. Render: `icon`→custom marker else default; resolved `img`→click InfoWindow; label-only→hover `title`; neither→plain marker. Label chain: `pin.displayName`→gallery item's label→the `img` string→none. There is **no** automatic page-name label (see `docs/todo.md` #35).
- **Live center/zoom caption** under EVERY map (no width gate — Pierre removed it): a centered `<div>` after the map, wired to the map's `idle` event, `Center = (lat, lng) · Zoom = n`, 6-decimal. Deliberate authoring aid to dial in center/zoom; "public for now, hide from real users later."
- Maps inside collapsed `<details>` init zero-size → never fire `idle` (caption frozen, tiles may not draw) — known quirk, not a bug to chase.
- `pinIcon(icon)`: unknown/absent → `null` → default Google pin. `google.maps.Marker` now emits a **deprecation console warning** (AdvancedMarkerElement); parked (needs a Map ID + kills inline `mapStyles`). Migration recipe + prereqs in [docs/rendering/blocks.md](../rendering/blocks.md)/todo.

## Pin delivery — GL.PIN_ICONS as inline SVG data-URI
The 6 marker figures are inline SVG STRINGS in `gl-constants.jst` (`GL.PIN_ICONS`), keyed by a pin's `icon`. `pinIcon()` returns `{ url: "data:image/svg+xml," + encodeURIComponent(svg), scaledSize: 48×48, anchor: (24,24) }`.
- Each SVG is a standalone `48×48` viewBox, figure centered via `transform="translate(24,24)"`; `xmlns` is REQUIRED (data-URI images need it). Anchor is CENTER (Pierre rejected the teardrop shape → not bottom-anchored).
- Chosen over `google.maps.Symbol` (single-path only — can't do our multi-shape/multi-color glyphs) and `AdvancedMarkerElement` (needs `mapId` + marker library — bigger change, not needed now).
- Tweak art = edit the SVG numbers in `gl-constants.jst`. Design is a first pass; expect to nudge on real maps. Figures: lake=blue disc+waves, campground=amber caravan, park=green tree, tent=brown tent w/ door+guy-lines, picnic=red A-frame table, home=slate garage (peaked roof + light roll-up door, added 2026-07-08).

## gl-constants.jst — home for sitewide ALL-CAPS constants
New file `media/data/scripts/gl-constants.jst`. Holds `GL.PIN_ICONS`, and `GL.TAG_COLORS` / `GL.TAG_FALLBACK` / `GL.MAP_CONFIG` MOVED here out of gettinglost.jst. `gettinglost.jst` now aliases them (`var MAP_CONFIG = GL.MAP_CONFIG;` at IIFE top). Renderer-SPECIFIC config stays with its renderer (lakes.jst's `CONFIG` stocking URL, list_browser.jst's `DATASETS_URL`/`UPLOADS` — NOT moved). Put genuinely global ALL-CAPS constants here going forward.

## Load order (WP footer) — load-bearing
`gl-constants.jst` MUST load BEFORE `gettinglost.jst` (which reads those globals). Both are injected in the **Footer template part** — see [docs/rendering/wp-templates.md](../rendering/wp-templates.md) for the exact edit. All `.jst` upload to `wp-content/uploads` via the sync pipeline (`docs/conventions/github-workflow.md` — sync runs in GitHub Actions). Related: [docs/rendering/blocks.md](../rendering/blocks.md), [docs/conventions/site.md](../conventions/site.md).
