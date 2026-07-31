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

## Current Notes Content
**howto-temperature-control.json** — 3 sections:
- "Truma CP plus" (product page + Aventa/Combi-specific operating instructions)
- "Truma Aventa eco + soft start" (product page, product guide, operating instructions, quick start guide)
- "Truma Combi G comfort" (product page, one sheet, operating instructions, quick start guide)

**howto-power.json** (built 2026-07-11) — notes sections in order: Generator (Cummins, 2 real links), Inverter (2,000 W Victron — placeholder), Solar panels (placeholder), House battery (Group 8D, 330 Ah AGM — placeholder), then the 3 Truma sections **copied verbatim** from howto-temperature-control.json.
- ⚠ Truma docs now DUPLICATED across howto-power.json AND howto-temperature-control.json — if a Truma URL changes, update BOTH.
- 3 "To be researched" placeholders await real doc URLs: inverter, solar, house battery.

## Hosting supplier PDFs (caveat)
Can't just drop a PDF in `media/` and have it sync. `syncFiles` in local/sync/sync.js only uploads `.json`/`.jst`/`.cst` under `media/` to the WP media library — it is NOT a general binary uploader. Repo stores no binaries (images live locally in ~/Pictures/GettingLost; image pipeline planned, not built). Self-hosting a manual PDF would need a sync-code change or a manual WP-admin upload. (Was mid-investigation when session ended.)

**howto-awning.json** — 2 sections:
- "Carefree Eclipse" (product page, owner's manual r10, installation manual)
- "Carefree Connects (not installed)" (product page, owner's manual with BT12 r12, mobile app manual)

(The awning's actual configuration — basic single-switch, no auto-retract — is in `~/Claude/van.md`.)
