# LakeData source

`local/data/LakeData.json` is keyed by BC waterbody identifier (e.g. `00385SALM` = Mohun Lake) and is the authoritative source to pull from **when creating a new lake page**. For each lake it holds:

- `m_recSiteSet` — the full list of rec-site IDs (REC####) associated with the lake. **All of them belong on the lake page**, not just the one you have photos or a page for (Pierre's rule, 2026-07-17) — today that means one entry each in the lake's `notes` section named "Destinations", since the `recSites` array and the `destinations` table that replaced it are both retired and neither field is left in any file. Resolve each ID's name/type/coords from `local/data/RecSites-Fixed.csv` — how it is used when building a page is in [docs/recipes/lake-page.md](../recipes/lake-page.md).
- `m_lat`/`m_lon` — the real gazetted lake center → use for `location.lat/lng` (don't approximate).
- `m_areaHA` — hectares; ÷100 = `areaKm2` (611.7 ha → 6.117 km²).
- Also: `m_perimeterKM`, `m_elevationM`, `m_depthAvgM`, `m_depthMaxM`, `m_accessPointMap` (boat ramps / water-access points with titles + coords), driving distance/duration from Campbell River.

Lake-page schema and renderers: [docs/rendering/blocks.md](../rendering/blocks.md), [docs/conventions/site.md](../conventions/site.md). A rec site that has its own page is linked from its "Destinations" entry by `file` (the page filename, same-tab); one that does not is plain text with a `description`. The old `references: [{name, file}]` column went with the `destinations` table.
