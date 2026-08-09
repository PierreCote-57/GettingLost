# TODO — GettingLost

**next id: 31**

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

## Site

- **#29 — The booklet builder reads a `title` key the page JSONs no longer have** *(2026-08-09)*
  `build_booklet_pdf.py` line ~320 is `data.get("title") or <filename base>`. Page JSONs were
  renamed `title` → `name` in schema-unification Phase 3a (2026-07-20), so the `or` branch
  wins every time and both booklets print filenames — "howto-water" instead of "How To: Use
  water". One-word fix, but the PDFs have to be rebuilt and re-pushed after it, which is why
  it is parked rather than done inline. Found reading the docs against the code, 2026-08-09.

## Tooling

- **#30 — sync-on-push.yml's header comment describes a page-map gate that does not exist** *(2026-08-09)*
  Its comment block gates new pages on `local/config/page-map.json`, which does not exist —
  they are warned about rather than created, it says, and a change under `local/config/`
  forces a full sync of all pages. `sync.js` discovers pages dynamically and says so in its
  own header; `local/config/` is empty. The `local/config/**` path trigger is harmless but describes a
  mechanism that is gone. Decide whether the trigger and the comment both go.

- **#16 — Make the cross-reference check repeatable** *(2026-07-31)*
  Walking cross-referenced pages against each other is something to do whenever destination
  content changes, not a one-time pass — so it needs to exist as a skill or a recipe rather
  than as a habit. Model it on `keyword-validation`: it reports disagreements, a human
  decides. Only rows carrying a `file` link are in scope; a catalog-only row has nothing to
  check against. Replaced todo #2, which wrongly parked a recurring pass as a task.

- **#27 — Drop humidity from the Fridge/Freezer charts** *(2026-08-09)*
  **Decided by Pierre 2026-08-09: no humidity for Fridge/Freezer.** Not open — only the edit
  is pending, to be made the next time the chart is worked on. `BANDS` in `gen-chart.py`
  currently gives both a 30–70 humidity band; the series, its band and the right axis all go.
  Update the bands table in `recipes/charting.md` in the same pass — it documents today's
  behaviour and stays correct until the change lands.
