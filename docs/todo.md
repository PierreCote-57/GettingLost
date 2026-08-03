# TODO — GettingLost

**next id: 22**

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

- **#18 — The non-type keywords in the data are TEST VALUES** *(2026-08-01)*
  `hike`, `hiking`, `picnic`, `trout`, `whale`, `whales`, `whaling` were put in to exercise
  the filter, not to describe the destinations. Pierre authors the real vocabulary later.
  **Until he does, the keyword data proves nothing** — do not read the thin vocabulary, the
  singletons or the near-duplicates as evidence in a design argument (it was read that way in
  #5 on 2026-08-01), and do not "fix" the drift. The `keyword-validation` pass is worth
  running only after the real values land.

## Housekeeping

- **#12 — Delete the two charting SVGs** *(2026-07-31)*
  `local/charting/cabin-indoor-storage.svg` and `local/charting/cabin-outdoors.svg` are
  working files from a charting session — per the charting lifecycle only the CSV persists.
  Now committed, so it's a `git rm`. Pierre's cleanup.

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
