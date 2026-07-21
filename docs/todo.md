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
2. **`access` is duplicated with nothing checking it.** Each destination JSON and its
   `destinations-overview.json` entry both carry `access`, and they can drift
   silently. Now that linked entries carry a `file`, sync.js could compare the two
   sides and fail the build on mismatch, the way slug drift already does.
3. **98 of 103 overview places have no `file` link.** Only Elk Falls, Morton, Sproat,
   Pacific Playgrounds and Salmon Point are linked. Unlinked entries can't be drift-
   checked or cross-referenced.
4. **Echo Lake Day Use and Beavertail Lake Day Use have no overview entry at all**,
   though both have pages and filled-in `legs`.
5. **`morton-lake-rec3104.json` is titled "Goose Lake Trail"** and filed under
   rec-sites, while its overview entry is "Morton Lake Provincial Park". Same place,
   two identities.

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
