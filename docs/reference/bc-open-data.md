# BC highway data — `local/data/bc_download/`

Four reference downloads about BC highways: rest stops, offramps, freeway exits, and the
amenities near those exits. Pulled 2026-08-23/24. `local/data/` is reference data and never
syncs to WP.

They come from **two unrelated sources that do not share identifiers**, which is the single
most important thing about this folder:

- **DataBC** — the province's GeoServer at `openmaps.gov.bc.ca`, queried over WFS. Government
  data, authoritative for government assets.
- **OpenStreetMap** — queried through the Overpass API. Community data, and the only source
  here for anything commercial.

Nothing joins by id across that boundary. Every cross-source link is **geometric** — compare
coordinates, there is no key.

## The files

| File | Source | What it is |
| --- | --- | --- |
| `bc_reststop.json` | DataBC WFS, `WHSE_IMAGERY_AND_BASE_MAPS.MOT_REST_AREAS_SP` | Ministry of Transportation rest areas |
| `bc_offramp.json` | DataBC WFS, `WHSE_BASEMAPPING.DRA_DGTL_ROAD_ATLAS_MPAR_SP` | Digital Road Atlas segments that are offramps or carry an exit number |
| `bc-exits.json` | OSM/Overpass | `highway=motorway_junction` nodes inside BC |
| `bc-exit-amenities.json` | OSM/Overpass | fuel/food/lodging/toilets within 1 km of those junctions |

`Index.txt` sits beside the data with the same URLs in it.

## How they relate

**`bc-exits.json` is the anchor for `bc-exit-amenities.json`.** Every amenity in that file was
selected because it lies within 1 km of one of those junction nodes — that is literally the
query that produced it. Discard the exits and the amenities lose their reason for being in
the file.

**`bc-exits.json` is also an exit-number source, and often the only one.** Roughly half its
junctions carry a `ref` tag holding the exit number; most of the rest are explicitly tagged
`noref=yes`. Where DRA left `HIGHWAY_EXIT_NUMBER` blank, OSM's `ref` is the only place the
number exists — Hwy 19 exit 161 (Jubilee Pky, Campbell River) is the worked example: DRA has
the ramp, with no number on it, and no DRA feature anywhere carries 161.

**The two sources disagree about exit numbers where both have one.** Neither is a superset:
DRA knows ramps OSM has no junction for, and OSM numbers exits DRA left blank. Any pipeline
using both needs a rule for which wins.

**`HIGHWAY_EXIT_NUMBER` in DRA is mostly empty** — only about a fifth of ramp segments have
one, and well under half of the roads *named* as offramps. Filtering DRA on the exit number
silently drops most of the province's offramps. That is why `bc_offramp.json` is fetched with
an `OR`, not an `AND`.

**`bc_offramp.json` is not purely offramps.** The `OR` admits anything carrying an exit
number, which brings in onramps, flyovers, turning lanes, and mainline highway segments.
Check `ROAD_NAME_FULL` / `ROAD_CLASS` before assuming a feature is traffic leaving the
highway.

## Reproducing the downloads

DataBC — plain URLs, fine in a browser:

```
bc_reststop.json
https://openmaps.gov.bc.ca/geo/pub/WHSE_IMAGERY_AND_BASE_MAPS.MOT_REST_AREAS_SP/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=pub:WHSE_IMAGERY_AND_BASE_MAPS.MOT_REST_AREAS_SP&outputFormat=application/json&srsName=EPSG:4326

bc_offramp.json
https://openmaps.gov.bc.ca/geo/pub/WHSE_BASEMAPPING.DRA_DGTL_ROAD_ATLAS_MPAR_SP/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=pub:WHSE_BASEMAPPING.DRA_DGTL_ROAD_ATLAS_MPAR_SP&outputFormat=application/json&srsName=EPSG:4326&CQL_FILTER=HIGHWAY_EXIT_NUMBER%20IS%20NOT%20NULL%20OR%20ROAD_NAME_FULL%20LIKE%20%27%25Offramp%25%27
```

OSM — **must be fetched with curl**; see the browser note below.

```
bc-exits.json
https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A600%5D%3B%0Aarea%5B%22ISO3166-2%22%3D%22CA-BC%22%5D-%3E.bc%3B%0Anode%5B%22highway%22%3D%22motorway_junction%22%5D%28area.bc%29%3B%0Aout%20body%3B%0A
```

```
bc-exit-amenities.json
https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A600%5D%3B%0Aarea%5B%22ISO3166-2%22%3D%22CA-BC%22%5D-%3E.bc%3B%0Anode%5B%22highway%22%3D%22motorway_junction%22%5D%28area.bc%29-%3E.j%3B%0A%28%0Anwr%28around.j%3A1000%29%5B%22amenity%22~%22%5E%28fuel%7Crestaurant%7Cfast_food%7Ccafe%7Ctoilets%7Cdrinking_water%29%24%22%5D%3B%0Anwr%28around.j%3A1000%29%5B%22shop%22~%22%5E%28convenience%7Csupermarket%7Cdepartment_store%29%24%22%5D%3B%0Anwr%28around.j%3A1000%29%5B%22tourism%22~%22%5E%28hotel%7Cmotel%7Ccamp_site%29%24%22%5D%3B%0A%29%3B%0Aout%20center%20tags%3B%0A
```

The amenities query decoded:

```
[out:json][timeout:600];
area["ISO3166-2"="CA-BC"]->.bc;
node["highway"="motorway_junction"](area.bc)->.j;
(
  nwr(around.j:1000)["amenity"~"^(fuel|restaurant|fast_food|cafe|toilets|drinking_water)$"];
  nwr(around.j:1000)["shop"~"^(convenience|supermarket|department_store)$"];
  nwr(around.j:1000)["tourism"~"^(hotel|motel|camp_site)$"];
);
out center tags;
```

`around.j:1000` is the radius in **metres** — that is the 1 km.

## Gotchas that cost time

**Overpass refuses browsers.** A browser User-Agent gets `406 Not Acceptable` — "An
appropriate representation of the requested resource could not be found on this server". The
URL is fine; fetch it with curl, or paste the decoded query into `overpass-turbo.eu` and use
its Export button.

**Overpass returns 504 under load.** Retry the identical request; it usually succeeds.

**Never bound BC with a lat/lng rectangle.** A box wide enough to hold BC also holds Calgary
and Seattle — the first pull of these files had both. Use `area["ISO3166-2"="CA-BC"]`.

**OSM amenities hide half their coordinates.** `type: "node"` carries `lat`/`lon` at the top
level; `type: "way"` and `type: "relation"` carry `center: {lat, lon}` instead, because the
query ends `out center`. Reading only `lat`/`lon` drops every way and relation — and since
buildings are ways, that loses supermarkets, hotels and department stores far more often than
fuel pumps.

**CQL `BBOX` uses the layer's native CRS unless told otherwise.** DRA is stored in BC Albers,
so a lat/lng box silently matches nothing. Pass the CRS as the sixth argument:
`BBOX(GEOMETRY,-125.263,49.953,-125.250,49.963,'EPSG:4326')`.

**Exit numbers are strings.** `119AB`, `23B`, `1A`. Never parse them as integers.

**Ask the server for counts** instead of downloading to count: same WFS URL with
`resultType=hits` and no `outputFormat`, then read `numberMatched` off the returned XML.

## DataBC beyond these files

- Layer capabilities: append `?service=WFS&version=2.0.0&request=GetCapabilities` to a layer's
  `ows` endpoint; `request=DescribeFeatureType&typeName=…` gives field names and types.
- DRA field definitions (the legal values, from the documentation rather than from the data):
  [DGTL_ROAD_ATLAS Public Delivery Data Dictionary](https://catalogue.data.gov.bc.ca/dataset/bb060417-b6e6-4548-b837-f9060d94743e/resource/06f4e80a-dc20-4be3-859d-f9e16d0495d5/download/dgtl_road_atlas-public-delivery-data-dictionary.pdf)
- DRA catalogue record, with the full-province geodatabase download:
  <https://catalogue.data.gov.bc.ca/dataset/digital-road-atlas-dra-master-partially-attributed-roads>
- Rest areas catalogue record:
  <https://catalogue.data.gov.bc.ca/dataset/af9f5551-e605-4a6d-a056-444b680ed4ed>
- CQL filters support `= <> > >= < <=`, `BETWEEN`, `IN`, `IS NULL`, `LIKE`/`ILIKE`, `AND`/`OR`/
  `NOT`, the spatial predicates (`BBOX`, `INTERSECTS`, `WITHIN`, `DWITHIN`, `CONTAINS`,
  `CROSSES`) and the temporal ones (`BEFORE`, `AFTER`, `DURING`).

## Two rest-stop files, two lineages

`bc_reststop.json` (here) is the **DataBC WFS** layer. `local/data/bc-rest-stop.json` is the
older **DriveBC API** pull described in [bc-rest-stops.md](bc-rest-stops.md) — a different
source for the same subject, and the two are not interchangeable:

- The WFS pull is current and complete, and adds records the DriveBC file lacks — but they are
  mostly brake checks, chain-up areas, weigh scales and truck parking, not classic rest areas.
- The DriveBC file carries **WiFi and EV-charging columns that do not exist in the WFS layer**,
  and they are populated. Take the WFS file alone and you lose which rest stops can charge a
  car.

They key to each other on `CHRIS_REST_AREA_ID`, which nearly every DriveBC record shares with
its WFS counterpart. Field names differ by an `_IND` suffix on the yes/no columns
(`DIRECT_ACCESS` vs `DIRECT_ACCESS_IND`). Neither file has been made authoritative.
