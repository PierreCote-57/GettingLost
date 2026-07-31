# Fishing folder to lake pages

Proven end-to-end 2026-07-17 (Mohun Lake `00385SALM`). The lake id is the BC waterbody identifier (e.g. `00385SALM`), and it keys everything.

## Inputs (under `~/Working/Fishing/`)
- `Trips/<lakeId>/TripNote*/Note.json` — one per trip note. Fields of interest: `m_text` (HTML fragment, unicode-escaped, e.g. `<p>Note1</p>`) and `m_timeMS` (epoch **milliseconds**). Also m_title/m_name/m_identifier.
- `Images/<lakeId>/*.JPG` — full-size geotagged photos.

## Steps
1. **Trip notes** — read every `Trips/<lakeId>/TripNote*/Note.json`; collect `{m_timeMS, m_text}`, sort ascending by time.
2. **Photo geotags + rec-site match** — Python+Pillow EXIF GPSInfo → decimal lat/lng for each JPG (see [docs/recipes/image-editing.md](image-editing.md)). Haversine each photo to the lake's rec-site coords; photos within ~100 m = **at the site**, the rest = **on the way** (road/approach). Some have NO GPS → place by capture sequence. This identifies WHICH rec site the trip belongs to. **The ~100 m is a starting guess, not a rule** — the RecSites-Fixed.csv coord is often a *trailhead/parking* point offset from where the visit photos actually cluster. Print the sorted distances and split on the **natural gap** instead (Morton `00517SALM`: whole visit cluster 117–470 m from the trailhead coord, then a clean jump to 3,200 m+ = the drive → at-site was the ≤500 m cluster, not ≤100 m).
3. **Lake data** — `local/data/LakeData.json[<lakeId>]`: `m_recSiteSet` (ALL rec sites for the page), `m_lat`/`m_lon` (center), `m_areaHA`÷100 = areaKm2, depth/perimeter/access points. See [docs/reference/lakedata.md](../reference/lakedata.md).
4. **Rec-site details** — `local/data/RecSites-Fixed.csv` (name, type SIT/RTR, coords, description, directions) for each REC#### in the set.
5. **Bathymetric charts** — `local/data/LakeToChart.csv`, match `WATERBODY_IDENTIFIER_WSA_50K` = lakeId → one row per chart PDF → `fishingReferences.lakeChartList` `[{name,url}]` (name them by DRAFT_DATE year).
6. **Rec-site maps** — `local/data/SiteMap.properties` (`REC####=[url,...]` or `[]`) → each rec site's `siteMap` (most are `[]` → null). Rewrite `http://`→`https://`.

## Outputs — 4 files (computer: Claude writes, STOPS; Pierre pushes)
- Lake: `pages/destinations/lakes/<lake-slug>.html` (lakes.jst skeleton: googleMap, destinations, fishingReferences, notes, ONE backToGallery with `data-dataset="destinations"`) + `media/data/destinations/lakes/<lake-slug>/<lake-slug>.json`.
- Rec site: `pages/destinations/rec-sites/<lake-name>-<recid>.html` + matching JSON under `media/data/destinations/rec-sites/`.

## Conventions locked this session
- **Page slug for a rec site = `<lake-name>-<recid>`, all lowercase** (e.g. `mohun-lake-rec0184`) — scales when a lake has many rec sites. Rec-site page **title = the rec-site's name**.
- **Trip notes = STATIC HTML** in the rec-site `.html` body (no renderer): `<p><strong>April 12, 2021 @ 09:17 PM</strong></p>` then the `m_text`. Format via `TZ=America/Vancouver date -r <epoch_seconds> "+%B %d, %Y @ %I:%M %p"` (m_timeMS/1000).
- **Two galleries** in the rec-site JSON `photoGalleries`: `atSite` + `onTheWay`, ALL photos, every `label:"TBD"`, `img:"IMG_XXXX.jpg"`, `id:"img_xxxx"`.
- Don't fabricate: unknown areaKm2/stockingName/etc. left null/""/[] (render "NA"). `featuredImage` = a placeholder photo Pierre swaps.
- Only rec sites that have their own page get `references:[{name,file}]`; others `[]`.
- **Images: Pierre uploads** (resize + WP/FileBird); JSON just references `IMG_XXXX.jpg` — remind him. If his resize renames (e.g. `-rotated`), update JSON to match.

## Optional: photo-pin road map on the rec-site page
A second, left-floated map showing where selected photos were taken along the approach. Uses the **`googleRoadMap`** renderer ([docs/rendering/blocks.md](../rendering/blocks.md)): add `<div data-block-type="googleRoadMap"></div>` to the rec-site HTML (left of the existing `googleMap`) and a `roadMap` block to the JSON: `{ "zoom": <lake zoom − 1, hardcoded>, "pins": [ { "id": "<gallery item id>", "lat": …, "lng": … } ] }`. Each pin's `id` references a `photoGalleries` item; the pin opens that photo (label → InfoWindow `headerContent`). Pull pin lat/lng from the same photo EXIF (step 2). **Drop any photo with no GPS** — it can't be a pin (Pierre's call for img_0442). Pin set is Pierre's choice (a mix of atSite + onTheWay ids is fine). Size/float overridable via inline `style` on the block div. **Default presentation (Pierre 2026-07-17): collapsed** — wrap the block in `<details><summary><h2 style="display:inline;">Road map</h2></summary>…</details>` with the map at `width:100%;height:600px;float:none;`. See the `<details>` caveat in [docs/rendering/blocks.md](../rendering/blocks.md).

## Variations seen (Morton Lake `00517SALM`, 2026-07-18)
- **No `Trips/<lakeId>/` folder is normal** — many lakes have photos but no trip notes. Then: no static trip-note HTML and **no "Visited on …" line** in the rec-site page body (drop those `<p>`s from the Mohun HTML skeleton).
- **A lake's only rec site can be a *trail* (RTR), not a campground.** Morton's `m_recSiteSet` = just `["REC3104"]` = "Goose Lake Trail" (a recreation trail through Morton Lake Provincial Park). Pierre's call: build the one rec-site page anyway and treat it AS the campground — page title = the rec-site name ("Goose Lake Trail"), pin `campground`, slug `morton-lake-rec3104`. Don't silently swap in the provincial-park name.
- **Fill the `campground` block from `media/data/shared/list_browser/destinations.json`** when the place already has an inline row there (Morton → bcparks.ca website + "Reservable Apr 30–Sept 27 + winter" reservation). That's sourced data, not fabrication. Leave `siteMap` "" unless a park-map PDF gets uploaded.
- **`Images/<lakeId>/` can hold non-`IMG_` assets**: a promo/beauty shot (`MortonLakeCampground.jpg`, no GPS) — good `featuredImage` for both pages — and a park-map PDF. These aren't trip photos; keep them out of the galleries.
- **"notes files" in Pierre's vocabulary = the trip `Note.json` `m_text`**, not the lake-JSON `notes` (Further-readings links) block. Most `m_text` is filler ("Note 0"/"Note1"); count real content by stripping tags + unescaping entities.

## Variations seen (Sproat Lake `01128ALBN`, 2026-07-18)
- **A lake can have NO working folder at all** — no `Trips/<id>/` or `Images/<id>/`, only `Lakes/<id>/` (bathymetric TIFs + `LakeData.properties`/`StockingData.json`). Then there are no trip photos: use a single `under-construction.png` gallery item as a placeholder on both pages (Pierre's call), and `featuredImage` = `under-construction.png` too.
- **`m_recSiteSet` can be empty** — Sproat has zero BC rec sites. The lake page's `destinations` list is then Pierre's manually-curated set of nearby places (private campground, provincial park), not auto-filled from LakeData.
- **A provincial park is its own destination TYPE, not a rec site** — build it under `pages/destinations/parks/` + `media/data/destinations/parks/`, NOT `rec-sites/`. The folder is filing only; what surfaces the page is `tags.keywords: ["park"]`, which the list browser's Keywords filter reads. Same page skeleton as a rec-site page (campground / googleMap+desc / notes / photoGallery), and `backToGallery` carries `data-dataset="destinations"` like every other destination page. See [docs/conventions/site.md](../conventions/site.md), [docs/rendering/list-browser.md](../rendering/list-browser.md).
- **Lake `destinations` block** (renamed from `recSites` 2026-07-18, [docs/rendering/blocks.md](../rendering/blocks.md)): Name/Type/References table; per-entry `type` (default "Rec site", else "Park"/"Private"). Site map + Reservation columns were removed. A park entry on the lake page carries reference #1 = BC Parks URL, reference #2 = the internal park page (`file`), and the internal page is *also* listed under the lake's Further readings.
- **campground block fields carry the park's links** ([docs/rendering/blocks.md](../rendering/blocks.md)): `website`=official park page (BC Parks), `siteMap`=the park-map PDF (**external gov URL is OK here — renders under the title, this supersedes the Morton "leave siteMap blank" note**), `reservation`=pre-populated `camping.bcparks.ca/create-booking/results?resourceLocationId=…` URL (must be a URL; renders "Reservations"). Don't duplicate the BC Parks website in Further readings — the campground `website` already surfaces it under the title.
- **Park facts come from the web, not LakeData** — bcparks.ca + campingrvbc via WebFetch/WebSearch for site counts, amenities, reservation season, petroglyphs, park-map PDF, coords (Nominatim as backup). Don't fabricate reservation dates.

Schema/renderer refs: [docs/rendering/blocks.md](../rendering/blocks.md), [docs/conventions/site.md](../conventions/site.md), [docs/schema/map-pins-location.md](../schema/map-pins-location.md), [docs/schema/badges-road.md](../schema/badges-road.md), [docs/schema/image.md](../schema/image.md). Photo source also at [docs/reference/fishing-images.md](../reference/fishing-images.md).
