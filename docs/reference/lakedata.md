# LakeData source

`local/data/LakeData.json` is keyed by BC waterbody identifier (e.g. `00385SALM` = Mohun Lake) and is the authoritative source to pull from **when creating a new lake page**. For each lake it holds:

- `m_recSiteSet` — the full list of rec-site IDs (REC####) associated with the lake. **All of them belong on the lake page's `recSites` array**, not just the one you have photos/a page for (Pierre's rule, 2026-07-17). Resolve each ID's name/type/coords from [docs/conventions/fishing-links.md](../conventions/fishing-links.md)'s companion CSV `local/data/RecSites-Fixed.csv`.
- `m_lat`/`m_lon` — the real gazetted lake center → use for `location.lat/lng` (don't approximate).
- `m_areaHA` — hectares; ÷100 = `areaKm2` (611.7 ha → 6.117 km²).
- Also: `m_perimeterKM`, `m_elevationM`, `m_depthAvgM`, `m_depthMaxM`, `m_accessPointMap` (boat ramps / water-access points with titles + coords), driving distance/duration from Campbell River.

Lake-page schema and renderers: [docs/rendering/blocks.md](../rendering/blocks.md), [docs/conventions/site.md](../conventions/site.md). Only REC sites that have their own page get a `references` entry `{name, file}`; the rest get `references: []` (renders "NA").
