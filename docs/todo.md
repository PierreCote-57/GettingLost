# TODO

Work parked for later: small issues found while working on something bigger, plus
planned passes. Noted, not fixed. Delete a line when it's done.

## Datasets / display×data refactor (2026-07-23)

13. ~~**Cutover to `list_browser`.**~~ DONE 2026-07-25 — back-links repointed
    (`backToGallery` renderer + 29 pages → a single `data-dataset` block); old surface
    files retired (`gallery.jst`/`gallery.html`, `destinations-overview.jst`/`.html`);
    frozen gallery JSONs deleted on WP (all 404); **WP nav menu repointed** (`wp_navigation`
    post 5, rev 26): Destinations collapsed from a 6-child submenu to one top-level link
    `?dataset=destinations&view=grid`, the two Van items → `?dataset=van-checklist|van-howto&view=grid`.
    Verified live: 3 new hrefs render, no `/gallery/` or `/destinations-overview/` survives,
    grids show 18 / 2 / 5 cards.

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

18. ~~**Stale `DEFAULT_DATASET` in `list_browser.jst`.**~~ DONE 2026-07-25 — `known-destinations`
    → `destinations`, so a bare `/list_browser_html/` resolves instead of rendering
    "unknown dataset".

20. **⚠️ DELETE the TESTING `alert()` in `list_browser.jst`.** `navigate()` pops
    `window.alert(next.toString())` before doing the real `location.search = …`. It is
    committed and pushed, so it fires on the LIVE site on every filter commit. Deliberate
    (Pierre asked for it, to see the query string), but it must not survive testing.
    Grep `TESTING`. The assignment below it stays.

21. **Native `<details>` has no light-dismiss (2026-07-25).** Clicking elsewhere doesn't
    close the Keywords/Badges panel — you must click its summary again, which is also what
    commits it. Fix if it annoys in use: a document click listener that closes any open
    panel. Trying it as-is first.

22. **`.gl-lb-search` has no explicit width (2026-07-25).** It takes the browser's default
    input size. One-line fix if it reads too narrow/wide beside the other controls.

23. **On-demand keyword validation pass (2026-07-25).** Unlike badges and access, the
    keyword vocabulary is open and derived from the data, so it drifts. Loose authoring
    rules: singular/plural are the same word — pick one; synonyms are the same word —
    pick one. Wanted: a pass, run on demand (not in the build, not in the filter), that
    walks every `tags.keywords` value across the datasets and SURFACES suspects — near-
    duplicates, plural/singular pairs, one-off values used a single time. It reports; a
    human decides. Do NOT normalize in the filter (stemming/synonym maps) — that would
    hide exactly the drift this is meant to expose.

24. **Revisit: badges any/all match toggle (2026-07-25).** First pass ships ONE rule —
    multiple values on the same control = OR, control to control = AND. The designed-but-
    deferred refinement: a two-button any/all segmented control inside the Badges panel,
    committing a separate `badgesMatch=all` param on the `<details>` close edge (default
    "any", so the param is absent unless changed). Badges only — keywords are types, and
    "all of" there just generates empty results. Naming it `<param>Match` leaves room for
    other controls to adopt it. Deferred to keep the first filter pass simple.

25. **More param validation in `processParams()` (2026-07-25).** The normalization step
    is the single place the raw query string becomes what the page acts on (trim + apply
    defaults, as built). It is also the natural home for validation we deliberately did
    NOT do in the first filter pass: unknown `view`/`access` values, values not in the
    known vocabulary, malformed comma lists, unknown keys. Decide per case whether the
    answer is "drop it", "fall back to the default", or "leave it and let it match
    nothing" — today everything downstream just fails gracefully.

26. **Options row shouldn't need the dataset rows (2026-07-25).** Four of the five
    controls (view/badges/access/search) need only their current value. Keywords needs
    the rows solely because its choice list is derived client-side by scanning every
    record's `tags.keywords` — which is also why `showOptions` fetches the dataset file a
    second time, on top of `showDataset`'s fetch. If the distinct keyword values were
    materialized at build time, the options row would need nothing but the params and
    `datasets.json`, the second fetch would go away, and the control signature would lose
    an argument. Works as-is short term; deferred deliberately.

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

19. **Home template shows "Block contains unexpected or invalid content" (2026-07-25).**
    Seen in the Site Editor preview of the Home template, over the hero image, with an
    "Attempt recovery" button. Not investigated, not clicked. Unrelated to the menu work.

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
