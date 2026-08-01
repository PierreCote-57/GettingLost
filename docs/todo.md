# TODO — GettingLost

**next id: 21**

Work parked for later: small issues found while working on something bigger, plus planned
passes. Noted, not fixed. Delete an entry when it's done.

**What this file is FOR: so the thing is not forgotten AND we stop spending time on it
now.** Parking is the whole transaction — write the entry without asking, then drop it. Do
NOT come back to discuss a parked item mid-task: not to refine its wording, not to check
whether it's framed right, not to ask a question about it. Every one of those spends the
time the parking was meant to save. Questions about a parked item get asked WHEN WE WORK ON
IT (2026-07-30).

Code and data-integrity work only. **Content authoring does not belong here** (2026-07-27).

**This file is the complete answer to "where are we?"** — if something is outstanding it is
an entry here, and if it is not an entry here it does not get named in a status list. No
"nothing outstanding except…" (2026-07-31).

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

- **#19 — Should a destination's type be VISIBLE, not just filterable?** *(2026-08-01)*
  Cards render `tags.badges` as chips and nothing else, so type shows nowhere today. Whether
  it earns a chip (a color entry, and chip crowding beside the badges) or a table column is a
  separate question from the facet itself — deferred out of #5 deliberately.

- **#18 — The non-type keywords in the data are TEST VALUES** *(2026-08-01)*
  `hike`, `hiking`, `picnic`, `trout`, `whale`, `whales`, `whaling` were put in to exercise
  the filter, not to describe the destinations. Pierre authors the real vocabulary later.
  **Until he does, the keyword data proves nothing** — do not read the thin vocabulary, the
  singletons or the near-duplicates as evidence in a design argument (it was read that way in
  #5 on 2026-08-01), and do not "fix" the drift. The `keyword-validation` pass is worth
  running only after the real values land.

- **#5 — Give destination type its own facet** *(2026-07-30, designed 2026-08-01)*
  `lake`/`park`/`rec-site`/`campground` are carried as keywords because nothing else on a row
  states the type — for per-page rows it is implied by the folder, for inline dataset rows by
  nothing at all. Type moves to a facet of its own. **Facets are the filter axes; keywords,
  badges and access are all facets** — this adds a fourth, it does not promote type out of
  being a tag.

  Settled 2026-08-01:

  - **`tags.types`, a LIST**, beside `keywords` and `badges` — same kind of thing, same
    shape. The data is single-valued today (116 of 116 rows carry exactly one), but that is
    a fact about the data, not a constraint to encode: a rec site on a lake should be able
    to say so without a schema change.
  - **Closed vocabulary**, declared as a bare ordered array `GL.DESTINATION_TYPES` in
    `gl-constants.jst`. Precedent is `GL.ROAD_RANK`, which is exactly this: a closed
    vocabulary with no colors, held separately from the color map.
  - **Never mandatory. The build check is VOCABULARY ONLY** — a value outside the list fails,
    an absent `types` is fine. This is what protects the meaning of `park`: a city park (The
    Spit in Campbell River) carries no type rather than a wrong one, and someone filtering
    for "park" gets Elk Falls, not The Spit. `filterByWord` already fails a row that lacks
    the tag, so an untyped row surfaces under no type filter — no new code.
  - **No `unknown` bucket in the counts**, unlike access: an untyped row matches nothing, so
    it is simply absent and the type counts sum to less than the row count. (Access is the
    opposite because an unmeasured road passes every threshold.)
  - **Multi-select checkbox dropdown**, like badges — the filter wants OR ("lakes and parks")
    even though a row carries one value. Access is single-choice only because a threshold has
    one answer.
  - Ids stay as authored: `rec-site` keeps its hyphen and renders as it does in the Keywords
    dropdown today.

  Current data is clean: all 15 inline `park` rows are bcparks.ca provincial parks (three are
  named without the word "Provincial" — Lower Nimpkish Lake, Nimpkish Lake, Schoen Lake). A
  `city-park` value can be added when the first one arrives; it renders `(0)` until used.

  Touches: the vocabulary in `gl-constants.jst`; a python migration through `jsonio.py` moving
  the word out of `tags.keywords` into `tags.types` on 98 inline rows of `destinations.json`
  and 18 page JSONs; `collectCounts` and the vocabulary check in `sync.js`; `filterTypes` +
  one switch line + one `CONTROL_BUILDERS` entry in `list_browser.jst`; `"types"` into the
  destinations `options` array. Data and code must land in one push. Then the docs and the
  keyword tooling: [rules/keywords.md](../.claude/rules/keywords.md) loses "type keywords are
  load-bearing", the `keyword-validation` skill loses its exemption for them,
  `local/tools/keyword_validation.py` stops seeing them, and
  [conventions/site.md](conventions/site.md) + [rendering/list-browser.md](rendering/list-browser.md)
  get the new facet.

## Tooling — sync.js

- **#20 — Three phases in `main()`: load, validate, push** *(2026-08-01)*
  `syncHydratedLists` reads its dataset files, hydrates them and uploads them, all in one
  step. That read in the push phase is what leaves a validation with nowhere to stand:
  `validateLegs` sits at [sync.js:1306](../local/sync/sync.js:1306) as the lone outlier
  between the load block and the push block, and it can only see `perPageDataMap` — never the
  98 inline dataset rows, which is where most destination data lives.

  Fix: hoist the read + hydrate into the load block as `loadHydratedListSet(datasets,
  perPageDataMap)` — **a name `overview.md` already uses for a function that does not exist**,
  so this restores the documented shape. `syncHydratedLists` then only uploads what it is
  handed. A validate block goes between the two, seeing both per-page and inline rows.

  **Decided: validation runs before ANY push, and a failure means nothing was pushed** —
  better than failing after half the site is up. Every check runs before the block decides, so
  one run reports everything that is wrong. Validations LEAVE the summary, which becomes
  purely about what was pushed; a failed run prints no summary at all, just the validation
  report and exit 1.

  This is a BUG FIX, not a new policy: today an invalid leg is counted, reported, and the site
  is pushed anyway.

  Output — each failure prints as it is found, before its check's tally line, so nothing has
  to be accumulated (`annotateFailure` already streams). The tally carries the count, not a
  bare "Success", because the number is what says the check actually looked at something:

  ```
  === Validating ===
  Legs:  19 checked, 0 invalid
    QuinsamRiver.json: invalid type "river"
  Types: 116 checked, 1 invalid
  FAILED — nothing pushed.
  ```

  A COPY IS NOT A READ. `copy(X, Y)` reading X internally is an implementation detail the
  caller doesn't know about; the test is whether the content changes *what gets published*.
  By that test the file has exactly one offender: [sync.js:1169](../local/sync/sync.js:1169).
  Page content, post content, media bytes and log bytes are payload — read, handed to WP
  unexamined, never consulted for a decision — and stay where they are. Hoisting those would
  mean holding every image in memory for the whole run.

  Do this FIRST and on its own, verified by a full sync producing byte-identical uploads.
  #5's type check goes in on top of it, so the refactor and the new check stay separate
  diffs.

## Housekeeping

- **#12 — Delete the two charting SVGs** *(2026-07-31)*
  `local/charting/cabin-indoor-storage.svg` and `local/charting/cabin-outdoors.svg` are
  working files from a charting session — per the charting lifecycle only the CSV persists.
  Now committed, so it's a `git rm`. Pierre's cleanup.

## Documentation

- **#17 — `site.md` still describes the retired `destinations` table on lake pages** *(2026-08-01)*
  [conventions/site.md](conventions/site.md) says a lake page's nearby places are the
  `destinations` block with a **Type** column labelling each entry. `lakes.jst`'s header says
  that renderer was retired in the schema-unification pass (2026-07-20) and those places are
  now a "Destinations" section inside the shared `notes` block. Check which is true on a live
  lake page, then fix the doc. Found while checking whether a second machine-readable type
  vocabulary existed for todo #5 — it does not, if lakes.jst is right.

## Site configuration

- **#15 — Find out whether the Google Maps API key is referrer-restricted** *(2026-07-31)*
  Nothing in the repo records it and `site.md` only ever said what to do at the domain move,
  not what is set today. Test it: load the Maps JS API with `MAP_CONFIG.mapApiKey` from a
  page on some other origin — `http://localhost` rather than `file://`, so the request
  carries a real referrer. Map renders → no effective restriction. `RefererNotAllowedMapError`
  → an allow-list exists. `InvalidKeyMapError` / `ApiNotActivatedMapError` mean the test is
  wrong, not the key. What to do at the move is in [site-move.md](site-move.md).

## Data integrity

- **#14 — Reconcile the FileBird `Images/` tree with its local master** *(2026-07-31, rescoped
  2026-08-01)*
  The original premise is done: live FileBird `Images/` already has the `Destinations` parent
  and no `Special`. What is left is drift against the master,
  `~/Pictures/GettingLost/Images/` — checked live 2026-08-01:

  Only in FileBird: `Destinations/RecSites/` and its four site folders; eleven extra lake
  folders under `Lakes/` (blackwater, brewster, campbell, chain, crest, drum, gray,
  mccreight, merrill, mohun, morton, snakehead); `Posts/` subfolders; `Van/van-overview/Listing`.

  Only locally: `about/*`, `templates/*` (FileBird `Images/` has no templates at all),
  `shared/{gallery,home}`, `van/checklists/*`, `van/howto/howto-shower`,
  `van/van-overview/{Original,cropped}` (working folders — probably should not be mirrored).

  Naming: FileBird `RecSites` vs GitHub/local `rec-sites`. Convention allows mixed case in
  FileBird, but this also drops the hyphen — decide which way it goes before renaming.

  The `Images/` snapshot in [conventions/folders.md](conventions/folders.md) is dated
  2026-07-01 and is stale; refresh it as part of this. Sync never deletes, so a rename has to
  be done by hand in both the media and post-type trees or it orphans the old folder.

## Tooling

- **#16 — Make the cross-reference check repeatable** *(2026-07-31)*
  Walking cross-referenced pages against each other is something to do whenever destination
  content changes, not a one-time pass — so it needs to exist as a skill or a recipe rather
  than as a habit. Model it on `keyword-validation`: it reports disagreements, a human
  decides. Only rows carrying a `file` link are in scope; a catalog-only row has nothing to
  check against. Replaced todo #2, which wrongly parked a recurring pass as a task.
