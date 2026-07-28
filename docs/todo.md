# TODO

Work parked for later: small issues found while working on something bigger, plus
planned passes. Noted, not fixed. Delete a line when it's done.

Code and data-integrity work only. **Content authoring does not belong here** (2026-07-27).

Numbers are sequential and unique. Renumbered 2026-07-28 (completed entries deleted
per the rule above); old numbers are gone, so refer to items by their text if an
older note cites a number.

## List browser

1. **On-demand keyword validation pass (2026-07-25).** Unlike badges and access, the
   keyword vocabulary is open and derived from the data, so it drifts. Loose authoring
   rules: singular/plural are the same word — pick one; synonyms are the same word —
   pick one. Wanted: a pass, run on demand (not in the build, not in the filter), that
   walks every `tags.keywords` value across the datasets and SURFACES suspects — near-
   duplicates, plural/singular pairs, one-off values used a single time. It reports; a
   human decides. Do NOT normalize in the filter (stemming/synonym maps) — that would
   hide exactly the drift this is meant to expose.

## Data integrity

2. **Cross-reference validation pass.** Walk the cross-referenced pages against each
   other and confirm they agree. Only the rows carrying a `file` link are in scope —
   a catalog-only row has nothing to check against.

## DRA pavement-distance — ABANDONED 2026-07-25

Dropped by Pierre. The DRA can't describe a road the way the site needs it: its
`ROAD_SURFACE` is a two-value guess (`loose`/`rough`) that doesn't separate "potholes,
drive slow and you're fine" (Echo, Beavertail) from "large gravel that flats a tire"
(Morton) — and Morton, the worst of the three to drive, reads the same `loose` as the
other two. Legs get filled manually, as Pierre drives them.
