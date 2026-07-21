# TODO

Work parked for later: small issues found while working on something bigger, plus
planned passes. Noted, not fixed. Delete a line when it's done.

## Planned

0. **Cross-reference validation pass — after the access/legs reorg lands.** Walk the
   cross-referenced pages against each other and confirm they agree. Items 2–5 below
   are all instances of the same class and should fold into this pass.

## Access / legs (2026-07-20)

1. ~~**`roadBadge()` has no `km` guard.**~~ RESOLVED by Phase 1 — the overview now
   calls the single shared `GL.deriveRoadBadge`, which carries the km guard.
2. ~~**`access` is duplicated with nothing checking it.**~~ RESOLVED by Phase 4 for the
   5 linked entries — they collapse to `{name, file}` and hydrate from the page at
   render time, so the page JSON is the single source (no duplication left to drift).
   The 98 unlinked entries have no page, so nothing to duplicate.
3. **98 of 103 overview places have no `file` link.** Only Elk Falls, Morton, Sproat,
   Pacific Playgrounds and Salmon Point are linked. Unlinked entries can't be drift-
   checked or cross-referenced.
4. ~~**Echo Lake Day Use and Beavertail Lake Day Use have no overview entry.**~~ RESOLVED
   — added as bare `{file}` entries in the RSTBC group (day-use: no homepage/campground,
   so Name/Distance/Access/On-lost populate, the rest blank by design).
5. ~~**`morton-lake-rec3104.json` two identities.**~~ RESOLVED — the page is Morton
   Lake Park: renamed `name` "Goose Lake Trail" → "Morton Lake Park", moved
   rec-sites → parks as `morton-lake-park`, refs updated (morton-lake Destinations
   note + overview `{file}`). Goose Lake Trail is a rec site *within* the park; GL has
   no page for it (it remains a bare-name row in mohun-lake's list).

## Overview hydration (2026-07-20)

9. **Unpublished-page handling in the hydrated overview — display's job, not
   sync.js.** Once overview `{file}` entries hydrate from page JSONs, an entry
   pointing at an unpublished page needs a defined behavior (skip / grey out).
   Short term the renderer ignores `wpSettings` and shows it anyway; revisit when
   the list/table renderers are reworked.

## Stray files (2026-07-20)

8. ~~**`rec-sites/beavertail-lake-dayuse/Destinations.json` stray file.**~~ RESOLVED —
   the file is already gone from the tree (Phase 5.1 no-op).

## DRA pavement-distance prototype (2026-07-20)

6. **The DRA walk can't seed `km` unsupervised** — validated 1 of 3. Echo 0.6 km was
   plausible; Morton returned 6 km on a road Pierre doesn't drive (real: 15 km via
   Menzies Rd); Beavertail returned 0 km, i.e. it would have asserted `legs: []`
   "paved all the way" on a road that is 6 km of potholes. Two fixes needed before
   it's worth more time: the walk must follow the driven route rather than minimise
   unpaved metres, and it needs a reason to distrust a 0.
7. **Echo's `0.6` is the only DRA-derived number in the data** and is unvalidated by
   Pierre. Prototype scripts live in the session scratchpad, not in the repo.
