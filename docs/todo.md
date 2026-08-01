# TODO — GettingLost

**next id: 14**

Work parked for later: small issues found while working on something bigger, plus planned
passes. Noted, not fixed. Delete an entry when it's done.

**What this file is FOR: so the thing is not forgotten AND we stop spending time on it
now.** Parking is the whole transaction — write the entry without asking, then drop it. Do
NOT come back to discuss a parked item mid-task: not to refine its wording, not to check
whether it's framed right, not to ask a question about it. Every one of those spends the
time the parking was meant to save. Questions about a parked item get asked WHEN WE WORK ON
IT (2026-07-30).

Code and data-integrity work only. **Content authoring does not belong here** (2026-07-27).

## Numbering (2026-07-31)

**Ids are permanent and never reused. The list is NEVER renumbered.** A deleted entry leaves
a gap, and that is correct — an id has to still resolve when Pierre cites it weeks later in
a commit message or a conversation. Take the next id from the header above and increment it.

Ids are written as plain text (`**#8**`), never as a markdown ordered list, because a
renderer resequences `3. 4. 5.` into `1. 2. 3.` — so the numbers Pierre sees would not be
the numbers in the file. This numbering scheme is independent of `~/Claude/todo.md`, which
counts separately.

Note: the list was renumbered once, on 2026-07-28, before this rule. Ids cited in anything
written before that date may not resolve.

## List browser

- **#3 — Add count to keywords in `datasets.json`, for display in the dropdown** *(2026-07-30)*
  `collectKeywords()` already walks every hydrated row to build the distinct list — counting
  there instead of de-duplicating is the same walk. The dropdown then shows how many rows
  each choice would match before it's clicked. Changes the published manifest's `keywords`
  shape, so `buildCheckboxDropdown` changes with it.

- **#4 — Count in the structured dropdowns too, badges & access** *(2026-07-30)*
  Not the same problem as keywords: those vocabularies are CLOSED, so a count of zero is
  possible and meaningful — an option that guarantees no results. **Decided 2026-07-31: a
  zero renders as `(0)`, the option is not hidden.** An unused value in a closed vocabulary
  is the dropdown advertising room not yet used. Implementation is the same walk as #3.

- **#5 — Should destination type be its own facet rather than a keyword?** *(2026-07-30)*
  `lake`/`park`/`rec-site`/`campground` are carried as keywords because nothing else on a
  row states the type — for per-page rows it is implied by the folder, for inline dataset
  rows by nothing at all. So the keyword is load-bearing: drop it and lakes become
  unselectable. The question is whether type deserves a structured facet of its own.

## Housekeeping

- **#12 — Delete the two charting SVGs** *(2026-07-31)*
  `local/charting/cabin-indoor-storage.svg` and `local/charting/cabin-outdoors.svg` are
  working files from a charting session — per the charting lifecycle only the CSV persists.
  Now committed, so it's a `git rm`. Pierre's cleanup.

## Data integrity

- **#13 — Brewster Lake has data but no page** *(2026-07-31)*
  `media/data/destinations/lakes/brewster-lake/` exists; there is no
  `pages/destinations/lakes/brewster-lake.html`. An orphaned stub from an earlier session,
  carried in the slug-rebuild record until now. Either build the page or delete the data.

- **#2 — Cross-reference validation pass**
  Walk the cross-referenced pages against each other and confirm they agree. Only the rows
  carrying a `file` link are in scope — a catalog-only row has nothing to check against.
