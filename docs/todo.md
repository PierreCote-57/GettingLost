# TODO

Work parked for later: small issues found while working on something bigger, plus
planned passes. Noted, not fixed. Delete a line when it's done.

Numbers are sequential and unique. Renumbered 2026-07-25 (completed entries deleted
per the rule above); old numbers are gone, so refer to items by their text if an
older note cites a number.

## List browser

2. **Native `<details>` has no light-dismiss (2026-07-25).** Clicking elsewhere doesn't
   close the Keywords/Badges panel — you must click its summary again, which is also what
   commits it. Fix if it annoys in use: a document click listener that closes any open
   panel. Trying it as-is first.

3. **`.gl-lb-search` has no explicit width (2026-07-25).** It takes the browser's default
   input size. One-line fix if it reads too narrow/wide beside the other controls.

4. **On-demand keyword validation pass (2026-07-25).** Unlike badges and access, the
   keyword vocabulary is open and derived from the data, so it drifts. Loose authoring
   rules: singular/plural are the same word — pick one; synonyms are the same word —
   pick one. Wanted: a pass, run on demand (not in the build, not in the filter), that
   walks every `tags.keywords` value across the datasets and SURFACES suspects — near-
   duplicates, plural/singular pairs, one-off values used a single time. It reports; a
   human decides. Do NOT normalize in the filter (stemming/synonym maps) — that would
   hide exactly the drift this is meant to expose.

5. **Badges any/all match toggle (2026-07-25).** The shipped rule is one rule: multiple
   values on the same control = OR, control to control = AND. The designed-but-deferred
   refinement: a two-button any/all segmented control inside the Badges panel, committing
   a separate `badgesMatch=all` param on the `<details>` close edge (default "any", so the
   param is absent unless changed). Badges only — keywords are types, and "all of" there
   just generates empty results. Naming it `<param>Match` leaves room for other controls
   to adopt it. Deferred to keep the first filter pass simple.

6. **More param validation in `processParams()` (2026-07-25).** The normalization step is
   the single place the raw query string becomes what the page acts on (it applies the
   defaults today, nothing more). It is also the natural home for validation deliberately
   left out of the first filter pass: unknown `view`/`access` values, values not in the
   known vocabulary, malformed comma lists, unknown keys, stray whitespace. Decide per
   case whether the answer is "drop it", "fall back to the default", or "leave it and let
   it match nothing" — today everything downstream just fails gracefully.

7. **Options row shouldn't need the dataset rows (2026-07-25).** Four of the five controls
   (view/badges/access/search) need only their current value. Keywords needs the rows
   solely because its choice list is derived client-side by scanning every record's
   `tags.keywords` — which is also why `showOptions` fetches the dataset file a second
   time, on top of `showDataset`'s fetch. If the distinct keyword values were materialized
   at build time, the options row would need nothing but the params and `datasets.json`,
   and the second fetch would go away. Works as-is short term; deferred deliberately.

## Content / pages

8. **Populate the road-map photo pins (2026-07-21).** Every destination now has a
   1-pin `googleMap.road` template. Next: hang real "on the way" photo pins on them,
   like Morton already has (`{img:"onTheWay/img_xxxx", lat, lng}` pins pulling from
   `photoGalleries`).

9. **Home template shows "Block contains unexpected or invalid content" (2026-07-25).**
   Seen in the Site Editor preview of the Home template, over the hero image, with an
   "Attempt recovery" button. Not investigated, not clicked.

## Data integrity

10. **Cross-reference validation pass.** Walk the cross-referenced pages against each
    other and confirm they agree. Item 11 is an instance of the same class and should
    fold into this pass.

11. **98 of the 116 destination rows have no `file` link.** Only the 18 rows that point
    at a GL page can be drift-checked or cross-referenced; the rest are catalog-only.

12. **Unpublished-page handling in the destinations TABLE.** The grid excludes unpublished
    pages (`filterView`), but the table still renders a row whose "View" link points at a
    page that isn't live. Needs a defined behavior: skip, grey out, or drop just the link.

## DRA pavement-distance — ABANDONED 2026-07-25

Dropped by Pierre. The DRA can't describe a road the way the site needs it: its
`ROAD_SURFACE` is a two-value guess (`loose`/`rough`) that doesn't separate "potholes,
drive slow and you're fine" (Echo, Beavertail) from "large gravel that flats a tire"
(Morton) — and Morton, the worst of the three to drive, reads the same `loose` as the
other two. Legs get filled manually, as Pierre drives them.
