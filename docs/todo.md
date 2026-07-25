# TODO

Work parked for later: small issues found while working on something bigger, plus
planned passes. Noted, not fixed. Delete a line when it's done.

## Datasets / display×data refactor (2026-07-23)

13. **Cutover to `list_browser` — WP menu is all that's left.** Mostly DONE 2026-07-25:
    back-links repointed (`backToGallery` renderer + 29 pages → a single `data-dataset`
    block); old surface files retired (`gallery.jst`/`gallery.html`,
    `destinations-overview.jst`/`.html`); frozen gallery JSONs deleted on WP
    (`Lakes`/`Parks`/`Campgrounds`/`RecSites`/`Destinations`/`VanHowTo`/`VanChecklist` —
    all 404). **REMAINING: repoint the WP nav menu item to the `list_browser` page.**

14. ~~Remove dead gallery helpers + re-home leg validation.~~ DONE 2026-07-24 —
    `GALLERY_RULES`/`deriveRoadBadge`/`BACK_COUNTRY` deleted; `validateLegs` added as a
    build-time pass (fails on unknown leg type / unpaved-no-km, reported in `=== Summary ===`).

15. ~~Dual-master drift `destinations-overview.json` vs `lists/all`.~~ MOOT — `lists/all`
    deleted; `destinations.json` is the sole master. (destinations-overview page retires in #13.)

16. ~~Create the van list sources.~~ DONE 2026-07-24 — `van-howto.json` /
    `van-checklist.json` created in list_browser/, hydrating via the manifest.

17. **Is "Gallery" the right display word for the back-link label?** The `backToGallery`
    block now shows a fixed "← Back to gallery" (grid of cards = a gallery, to a visitor).
    Revisit the wording later; low stakes, deferred deliberately.

18. **Stale `DEFAULT_DATASET` in `list_browser.jst`.** [`list_browser.jst:31`] still defaults
    to `known-destinations`, an id that no longer exists — so a bare `/list_browser_html/`
    resolves to "unknown dataset". Fix to `destinations`; folds into task 2 (apply URL as filter).

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

12. ~~Verify Morton's Explore BC Parks slug (2026-07-21).~~ DONE 2026-07-24 —
    `https://explorebcparks.ca/morton-lake-provincial-park/` resolves; the guess was correct.

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
