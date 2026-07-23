# TODO

Work parked for later: small issues found while working on something bigger, plus
planned passes. Noted, not fixed. Delete a line when it's done.

## Datasets / display×data refactor (2026-07-23)

13. **Cut the live site over to the hydrated `lists/` files, then delete dead gallery
    code.** sync.js no longer generates the old gallery JSONs (`Lakes.json`,
    `Campgrounds.json`, `Parks.json`, `RecSites.json`, `Destinations.json`) — it now
    hydrates `data/shared/lists/{all,known}/*.json` instead. **This FREEZES the live
    galleries** until cutover (stale, not 404): sync never deletes, so the old
    `Lakes.json`/etc. persist on WP from the last gallery-gen run and keep serving the
    menu links (`?file=Lakes.json` …), gallery.jst's `Destinations.json` default, and
    every `backToGallery` `data-file` — they just stop updating when page data changes.
    A full sync.yml run won't refresh or remove them either. Cutover = unified `destinations.html` + dropdowns + menu/back-link
    repoint at the new files (Phase 4/5). Also the new `known-*.json` aren't drop-in
    identical: no publish filter (moved to render time), sorted by `file` not `name`.

14. **Remove now-dead gallery helpers in sync.js.** After gallery-gen removal,
    `GALLERY_RULES` (~L91) and `deriveRoadBadge` + its leg constants
    (`DRIVE_LEG_TYPES`/`NON_DRIVE_LEG_TYPES`/`LEG_TYPES`/`BACK_COUNTRY`, ~L114-155) are
    unused. Left in place to keep the edit focused. **Also lost with them: the build-time
    leg validation** (`deriveRoadBadge` used to run per page during gallery-gen purely to
    warn on unknown leg types / unpaved-no-km). Decide whether to re-home that validation
    (e.g. into hydration or a dedicated pass) or drop it, then delete the dead code.

15. **Dual-master drift: `destinations-overview.json` vs `lists/all/*.json`.** The
    registry data now lives in two places — the old `destinations-overview.json` (still
    the live overview page's render-time source, still copied to WP) and the new
    `lists/all/*.json` (the intended master, hydrated to WP). They started identical (a
    split) but nothing keeps them synced: editing one leaves the other stale. Decision to
    hold until cutover: treat `lists/all/` as the SOLE master and `destinations-overview.json`
    as frozen/legacy — do not author it — until Phase 4/5 deletes the old page.

16. **Create the van list sources.** `datasets.json` now has `van-howto`/`van-checklist`
    entries pointing at `VanHowTo.json`/`VanChecklist.json`, but those are FROZEN on WP
    (gallery generation is gone) and have no `lists/` source. Build hydrated van list
    sources (like `known/`) so the van datasets are live, not stale. Part of the Phase 4
    van migration into `list_browser`.

## Planned

9. ~~**Bring other campground/park pages up to the new campground-block format
   (2026-07-21).**~~ DONE — elk-falls, sproat-park, pacific-playgrounds, salmon-point
   restructured to Morton's layout (campground block → maps → blurb → notes), `links`
   block removed, exact `campground.links` labels in place.

10. ~~**Keep `campground.links` to just the two rendered labels (2026-07-21).**~~ DONE —
    all 5 campground pages carry only `Campground map` + `Reservation`; status prose
    moved to a `notes` "Additional information" → "Availability" row (Salmon Point,
    Elk Falls, Morton). Verified.

11. **Populate the road-map photo pins (2026-07-21).** Every destination now has a
    1-pin `googleMap.road` template (see [[reference-map-pins-location-schema]]).
    Next: hang real "on the way" photo pins on them, like Morton already has
    (`{img:"onTheWay/img_xxxx", lat, lng}` pins pulling from `photoGalleries`).

12. **Verify Morton's Explore BC Parks slug (2026-07-21).** `morton-lake-park.json`
    Further-readings link `https://explorebcparks.ca/morton-lake-provincial-park/` —
    confirm it resolves; the BC Parks HomePage uses `morton-lake-park`, so the slug
    was a guess.

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
