# TODO — GettingLost

**next id: 41**

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

## Entries

**#40** `logs/travel-log.json` is 2-space indented, not the tab house format
([docs/conventions/json-format.md](conventions/json-format.md)) that `logs/locations.json`
and everything under `media/data/` use. Consequence: the first `jsonio.save()` on it rewrites
the whole file — tabs, one field per line — losing the inline `location` objects and the
aligned `"arrival":   ` columns. Decide whether to reformat it deliberately or keep it out of
jsonio's path.

**#39** The destination template is pre-unification. `media/data/templates/destination-template/destination-template.json` still carries top-level `lat`/`lng` instead of a `location`
block, and `pages/templates/destination-template.html` has a `googleMap` div with no
`data-map` — which the resolver treats as an error. Anyone starting a page from the template
gets both.

**#38** `list_browser.jst`'s Location column still calls its local `notes` —
`fillDataCell`'s `location` branch reads `loc.displayName` into `var notes` and uses it three
times. The field was renamed; the variable kept the old name and reads as a different field.

**#37** No center/zoom caption under the list browser's map. Every `googleMap` block has one
(`Center = (lat, lng) · Zoom = n`, wired to the map's `idle` event) and it is what the
centre/zoom for a map gets dialled in with. Costed 2026-08-17: lift the 12 lines out of
`drawMap` in `gettinglost.jst`, export them as `GL.mapCaption(map, parentEl)` so one format
serves both, and have `renderMap` return a wrapper holding map + caption instead of the map
div — the same wrapper/mapEl split the block renderer already uses.

**#35** Map marker labels — revisit AFTER the `pin` → `pins` migration. The migration writes
no `label`, and the ruling is *missing label = no label*: the old auto-fill that injected the
page's own `name` into the synthesized marker is gone. Open afterwards: which markers should
carry a label at all, and — for a map that points at another page or a registry entry —
whether the label should come from the pointed-at record's `name` rather than the page
holding the block.

