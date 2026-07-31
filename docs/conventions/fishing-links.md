# Fishing links convention

Conventions confirmed with Pierre 2026-07-08 for lake/rec-site fishing links.

## Stocking report = fishingReferences.stockingName (NOT Further readings)
`fishingReferences.stockingName` is a bare Go Fish BC **waterbody name** (e.g. `"ECHO"`, `"BEAVERTAIL"`), not a URL. lakes.jst builds the stocking-report link from it:
`https://www.gofishbc.com/stocked-fish/?reportType=lake&region=VANCOUVER%20ISLAND&waterbody=<NAME>`. Empty `stockingName` → the row shows **"NA"**.
- Only set it if the lake is ACTUALLY FFSBC-stocked. Wild salmon lakes (e.g. Amor Lake, BC id `00324SALM`) are NOT stocked → leave empty. Stocked trout lakes are the `…CAMB`-class ids (Echo `00126CAMB`, Beavertail `00121CAMB`).
- The stocking report ALWAYS goes here, never in Further readings.

## gofishbc has NO static per-lake page
Go Fish BC's per-lake "page" IS the stocking report (dynamic waterbody report keyed by wbid). There is no separate editorial lake-profile URL. So a lake's gofishbc "page" = the stocking report = `fishingReferences`, not Further readings.

## What DOES go in Further readings
- **gofishbc ARTICLES** (editorial, not the stocking tool) — e.g. "new docks make fishing access easier", "new kokanee fisheries on Vancouver Island". These are real standalone pages → Further readings.
- **gohiking.ca per-lake pages** — gohiking HAS static per-lake write-ups (e.g. `https://gohiking.ca/beavertail-lake/`, `/amor-lake/`) → Further readings.
- Rule of thumb Pierre gave: if there's a separate page for THAT lake (on gofishbc or gohiking), it goes in Further readings; the stocking report stays in fishingReferences.

## Useful Links "Fishing" section (added 2026-07-08)
`media/data/about/useful-links/useful-links.json` gained a `Fishing` section: Freshwater Fisheries Society of BC (gofishbc.com) + Go Hiking (gohiking.ca) — general/home links (site-wide, not lake-specific).

## Handy datum
The gofishbc "new docks" article ends with a lake+year dock-install table; **Beavertail Lake dock built 2023** (worked into that link's description). Related: [docs/rendering/blocks.md](../rendering/blocks.md) (notes/Further-readings renderer), [docs/conventions/site.md](site.md).
