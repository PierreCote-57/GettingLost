# Fishing images source

Lake source images live at `~/Working/Fishing/Images/` organized by BC fisheries identifier (e.g. `00040CAMB` for gosling-lake).

- Copy only image files (*.jpg, *.JPG, *.png), skip .text files and other non-image files (e.g. `sips`)
- Destination: `~/Pictures/GettingLost/Images/destinations/lakes/{name}/`
- Lake ID → page mapping is in each lake's JSON at `media/data/destinations/lakes/{name}/{name}.json` → `fishingReferences.bcIdentifier`, where `{name}` is the page's filename base — never a slug, which is derived from it
- See [docs/conventions/folders.md](../conventions/folders.md) for the full mapping table
