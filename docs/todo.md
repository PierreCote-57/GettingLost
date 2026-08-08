# TODO — GettingLost

**next id: 25**

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

## Housekeeping

- **#12 — Delete the two charting SVGs** *(2026-07-31)*
  `local/charting/cabin-indoor-storage.svg` and `local/charting/cabin-outdoors.svg` are
  working files from a charting session — per the charting lifecycle only the CSV persists.
  Now committed, so it's a `git rm`. Pierre's cleanup.

## Tooling

- **#16 — Make the cross-reference check repeatable** *(2026-07-31)*
  Walking cross-referenced pages against each other is something to do whenever destination
  content changes, not a one-time pass — so it needs to exist as a skill or a recipe rather
  than as a habit. Model it on `keyword-validation`: it reports disagreements, a human
  decides. Only rows carrying a `file` link are in scope; a catalog-only row has nothing to
  check against. Replaced todo #2, which wrongly parked a recurring pass as a task.
