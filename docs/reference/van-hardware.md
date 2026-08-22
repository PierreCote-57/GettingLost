## Documentation-Sourcing Convention
For how-to "Supplier documentation" notes sections:
- `sectionName` = specific product/model name (e.g. "Truma CP plus", "Carefree Eclipse")
- Each row's `name` = short doc-type label only ("Product page", "Operating instructions", "Owner's manual", "Quick start guide", "One sheet", "Installation manual") — never repeat product name in the row
- For a not-installed reference option: append "(not installed)" to that section's title (e.g. "Carefree Connects (not installed)")

## Sourcing Method
Don't just take the first manufacturer page found — check whether the manufacturer has a dedicated document library/download center:
- Truma: `truma.com/us/service/download-center/` (JS-filtered tool, requires Claude in Chrome)
- Carefree: "Tech Docs" tab on each product page (e.g. `carefreeofcolorado.com/rv-products/.../eclipse/`)
Always verify at least one new link actually resolves before delivering.

## Van Hardware Context
The hardware itself — Truma units, electrical, awning — is documented in `~/Claude/van.md`,
outside this repo, so it is available in any project.

## What the notes sections hold

Read the files — `media/data/van/howto/howto-{climate,power,awning}/*.json`, the `notes`
array. The section names and their links are not copied here.

One rule that is NOT in the data and has to be stated: **the Truma sections are DUPLICATED
across `howto-power.json` and `howto-climate.json`** — if a Truma URL changes, update BOTH.

A section still being researched carries a row named **"To be researched"** with no url, per
the placeholder convention above.

The hardware each section describes — including which awning configuration is actually
fitted — is in `~/Claude/van.md`, not here.

## Hosting supplier PDFs
A PDF under `media/data/**` syncs like any other file: sync.js uploads `.json`/`.jst`/`.cst`/`.pdf` to the WP media library, flat, so it is fetchable at `/wp-content/uploads/<basename>` (the only files not copied verbatim are the list-browser dataset sources, published hydrated instead) — which is how the booklet PDFs and the maintenance invoices are served. **Flat means a PDF filename must be unique sitewide, not just within its folder.**

A supplier PDF may instead be uploaded to WP **by hand** and referenced at the same
`/wp-content/uploads/<basename>` path — `Coachmen-User-Guide.pdf` on howto-power is the
case in the data. Nothing distinguishes the two at render time; the difference is only
whether the file is in the repo.

Images are the exception and stay out of the repo — they are Pierre's, uploaded by hand ([../conventions/folders.md](../conventions/folders.md)).
