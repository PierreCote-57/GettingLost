# Destination schema unification — spec + migration plan

Consolidates the 2026-07-20 design conversation. **Design is settled; this is the
build reference.** Each phase is its own go.

## Migration status (2026-07-20 — COMPLETE)

All phases done and pushed (verify the newest tweak with `git status`). What remains is
optional: the **review-flags** noted per phase below (design calls worth an eyeball, not
bugs) and the **future follow-ons** in §8. The migration itself is finished.


- **Phase 1 — road badge unified at render.** DONE. One `deriveRoadBadge` in
  gettinglost.jst; gallery cards + overview both call it; sync validates legs only.
- **Phase 2 — gallery = verbatim page JSON + injected `file`.** DONE.
- **Phase 3a — `title` → `name`.** DONE. Sitewide (39 content JSONs); sync
  `body.title` ← `data.name` (pages + posts); PageMap emits `name`;
  renderCard/googleMap/pageLink/gallery-sort read `name`. (jsonio also normalized
  every touched file to the house tab format — review with `git diff -w` to see
  the semantic change past the reindent.)
- **Phase 3b — `badges {tags}` → flat array.** DONE. 22 files (18 destinations +
  4 posts); renderCard reads the flat array; sync's defunct `badges.road` guard
  removed.
- **Phase 3c — campground restructure.** DONE. `campground {website,siteMap,
  reservation}` → `website`→top-level `links[]` HomePage; `siteMap`→`campground.links`
  ("Campground map"; "Park map" on park pages — label choice, review); `reservation`
  → `campground.links` ("Reservation" when a URL; the status prose as the label with
  url:null when informational). Empty-campground day-use sites drop the block entirely.
- **Phase 3d — top-level `links` + OnLost.** DONE. New shared `onLostHref` (scheme-less
  `*.html` → internal `/slug/`) + `linkRow`; new `links` block renderer (HomePage→
  "Website", OnLost→"On Getting Lost"); `campground` renderer now reads
  `campground.links`; `notes` renderer resolves OnLost urls. Page HTML: added a `links`
  block to the 5 pages with a homepage; removed the empty `campground` block from the 3
  day-use pages. **Display choice to review:** homepage now renders as its own `links`
  row above the campground (map/reservation) row, rather than one combined row.
- **Phase 3e — `destinations` → `notes` "Destinations".** DONE. 10 lake pages: each
  `destinations[]` folded into a prepended `notes` "Destinations" section (one entry
  per reference; `file` refs → OnLost; ref-less named sites preserved as bare-name
  rows). Dropped per §5 (in git, re-add in content pass): recId, siteMap, lat/lng,
  prose. Removed the `destinations` renderer + helpers from lakes.jst and the block
  from all 10 lake HTMLs. Templates updated to the new schema.
  - **mohun-lake — RESOLVED.** Its 7 bare rec-site rows were re-linked to
    `sitesandtrailsbc.ca/resource/<recId>` (description "Sites & Trails BC"), matching
    amor's convention; the dropped Sayward Canoe Route brochure PDF was re-added as a
    "Further readings" entry.
- **Phase 4 — overview hydration.** DONE (node-verified: reshape integrity + a DOM-shim
  render). All 103 entries reshaped to the unified schema; the `sites`→`siteCount`
  mapping for the 16 heterogeneous labels was resolved one-at-a-time with Pierre
  (incl. data corrections: Buttle 79, Ralph 75, Speedway 122+JPG, Sooke rename). The 5
  known entries collapse to `{name, file}` (listing keeps the curated name; everything
  else hydrates) and their overview-only fields (operator/siteCount/amenities/
  location.notes, merged reservation) were migrated into the page JSONs — page/PDF wins
  on conflict. Renderer rewritten: Option-B columns (Sites=plain `siteCount`, new Maps
  column, Amenities/Reservation from `campground`), name links to `links` HomePage.
  - **Hydration is RENDER-TIME** (the overview renderer fetches each `{file}` page's
    JSON and merges), not sync-time — keeps sync a pure copier, fully node-verifiable,
    same drift-elimination. Deviation from §6; flagged for review.
  - **Known pages' campground block** now also shows the migrated reservation *status
    prose* as a plain-text item in its link row (non-lossy merge) — a small page-display
    change to eyeball.
  - **morton-lake-rec3104 — RESOLVED (identity fix).** The page was Morton Lake Park all
    along: renamed `name` "Goose Lake Trail" → "Morton Lake Park", moved rec-sites →
    parks as `morton-lake-park`, refs updated (morton-lake Destinations note + overview
    `{file}`), old WP page removed. Goose Lake Trail is a rec site *within* the park (no
    GL page; it stays a linked row in mohun-lake's list).
- **Phase 5 — cleanups/data.** DONE. 5.1 stray `Destinations.json` was already gone.
  5.2: Echo Lake Day Use + Beavertail Lake Day Use added to the overview (RSTBC group,
  bare `{file}` — day-use, so no homepage/campground). 5.3: docs/memory updated inline.
- Site is coherent: pages AND the overview use the unified schema; every renderer reads
  it; the overview hydrates its 5 (now with day-use, `{file}`-linked) known entries from
  their pages, so there's no inline duplication left to drift.

## 1. Goal

Today three things carry a destination's data in three shapes:

1. The **page JSON** (`media/data/destinations/**/<base>.json`) — the authored source.
2. The **gallery JSON** (`data/shared/gallery/*.json`) — a hand-built projection
   sync.js emits (renames `excerpt`→`teaser`, derives `road`, keeps 5 fields).
3. **`destinations-overview.json`** — a curated list that *re-declares* each place's
   `access`, `location`, `sites`, … inline, duplicating the page JSON with nothing
   checking for drift.

The badge-derivation logic is likewise triplicated (`deriveRoadBadge` in sync.js,
`roadBadge` in destinations-overview.jst, and the paint-only `renderRoad` in
gettinglost.jst).

**Target:** one schema, one derivation. sync.js **packs and hydrates**, it does not
transform. The gallery and overview entries become the page JSON *verbatim* plus a
sync-injected `file`. All defaulting/derivation moves to render time. This also sets
up the future `data-gallery-list` / `data-gallery-table` pair reading one dataset.

## 2. Principles

1. **sync.js does not mutate content.** Its jobs are: select (publish filter, path
   rules), pack (gallery), hydrate (overview `{file}`→page JSON), inject `file`, and
   validate (fail/annotate the build on bad data). No renames, no derivation.
2. **One derivation, at render.** The road badge word is derived from `access.legs`
   by a single shared function in gettinglost.jst, used by gallery.jst and
   destinations-overview.jst. Never stored.
3. **Filename is the master.** A page JSON never carries its own `file`; sync injects
   it. A link to a local page is a scheme-less `*.html` url, resolved via `fileToSlug`
   and drift-checked at build — the "OnLost" convention.
4. **Clean data, not legacy-tolerant code.** Each rename is a coordinated cutover
   (data + sync + renderer in one deploy). No dual-read shims.
5. **Size is a non-issue.** Verbatim copy is fine; page JSONs are 0.9–5.5 KB and the
   overview already ships at 79 KB.

## 3. The unified destination JSON

Comments are annotations; real JSON has none. `file` is **not** in the file — sync
injects it.

### Common core (every destination)

```jsonc
{
  "name": "Elk Falls Park",                    // destination name; drives table, gallery, WP post_title
  "featuredImage": "under-construction.png",   // stored; the default is applied at render
  "excerpt": "A thundering waterfall ...",     // teaser text (NOT renamed in the gallery)
  "badges": ["camping", "fishing", "hiking"],  // flat array; `road` is DERIVED at render, never stored
  "wpSettings": { "published": true, "comments": "open" },

  "location": {
    "lat": 50.037009, "lng": -125.295734,
    "pin": "tent", "zoom": 13,
    "notes": "Near Campbell River"             // optional; untouched
  },

  "access": {                                  // omitted on lakes
    "haversine": [ { "town": "Campbell River", "km": 5 } ],
    "legs": []                                 // [] = paved all the way; road derived from this
  },

  "links": [                                   // [{label, url}]
    { "label": "HomePage", "url": "https://bcparks.ca/elk-falls-park/" },
    { "label": "OnLost",   "url": "morton-lake-rec3104.html" }   // scheme-less *.html → local page
  ],

  "footnotes": [ { "field": "siteCount", "text": "2 vehicle pads + 4 walk-in tent pads" } ],

  "notes": [                                   // the single container: Further readings AND Destinations
    {
      "sectionName": "Destinations",
      "list": [
        { "name": "Amor Lake", "url": "https://www.sitesandtrailsbc.ca/resource/REC0174", "description": ["BC Sites & Trails"] },
        { "name": "Amor Lake", "url": "https://en.wikipedia.org/wiki/Amor_Lake",           "description": ["Wikipedia"] },
        { "name": "Goose Lake Trail", "url": "morton-lake-rec3104.html",                    "description": ["On Getting Lost"] }
      ]
    },
    {
      "sectionName": "Further readings",
      "list": [ { "name": "Explore BC Parks", "url": "https://explorebcparks.ca/...", "description": ["Quality Recreation"] } ]
    }
  ]
}
```

### Type block — campgrounds / parks / rec-sites

```jsonc
"campground": {
  "operator": "Quality Recreation Ltd.",
  "siteCount": 6,                              // number; composition (e.g. "2 + 4") goes to a footnote
  "amenities": ["suspension bridge", "waterfall"],
  "links": [                                   // [{label, url}]; url null when informational
    { "label": "Campground map", "url": "https://.../map.pdf" },
    { "label": "Park map",       "url": "https://.../parkmap" },
    { "label": "Reservation",    "url": "https://camping.bcparks.ca/..." }
  ]
}
```

### Type block — lakes

```jsonc
"fishingReferences": { "bcIdentifier": "00517SALM", "areaKm2": 0.211, "lakeChartList": [], "stockingName": "" }
```

A lake drops `access` and `campground`; the old top-level `destinations` block is
gone (now a `notes` section).

## 4. Field changes (old → new)

| Old | New | Notes |
|---|---|---|
| `title` | `name` | sync WP `body.title` now sourced from `data.name` (sync.js:558, 671) |
| gallery `teaser` | `excerpt` | rename dropped; gallery reads `excerpt` |
| `badges: {tags, road}` | `badges: [ ... ]` | flat; `road` never stored, derived at render |
| `url` / `campground.website` | `links[]` `HomePage` | official site |
| `references[].file` (OnLost) | url = scheme-less `*.html` | resolved via `fileToSlug` |
| `campground.siteMap` (scalar) | `campground.links[]` `Campground map` / `Park map` | multiple maps possible |
| `campground.reservation` (scalar) | `campground.links[]` `Reservation` | url null when informational |
| — | `campground.siteCount` / `operator` / `amenities` | promoted from overview |
| `destinations[]` (block) | `notes[]` `"Destinations"` section | see §5 |
| injected by sync | `file` | never authored in the page JSON |

### §5 — `destinations[]` → `notes` "Destinations" section

Each entry reduces to `{name, url, description}` (the Further-readings shape). One
entry **per link** — same `name` repeats, `description` says where ("BC Sites &
Trails", "Wikipedia", "On Getting Lost"). Dropped: `recId`, `siteMap`,
`reservationLabel`, `lat`/`lng`, and the prose `description` (recoverable at the
link; original observations are lost, to be re-added during the per-page content
pass). `url` follows the OnLost rule (local page if one exists, else the reference's
own url).

## 5. Code changes

- **sync.js** — `generateGalleryJsons` emits the page JSON verbatim + injected
  `file` (drop the 5-field projection); keep publish filter + path rules; keep leg
  *validation* (warn/annotate) but stop deriving/emitting `road`; WP `body.title` ←
  `data.name`. New: hydrate `destinations-overview.json` `{file}` entries.
- **gl-constants.jst** — unchanged vocabulary (`ROAD_COLORS`, `ROAD_RANK`,
  `NON_DRIVE_LEG_TYPES`); the shared derivation can live here or in gettinglost.jst.
- **gettinglost.jst** — add the single `deriveRoadBadge(access)` (render-time),
  export it; `renderRoad` stays (paint only); `links` renderer + `notes` renderer
  gain OnLost resolution (scheme-less `*.html` → `fileToSlug`); "On Getting Lost"
  display text.
- **gallery.jst** — read `excerpt`, flat `badges`, derive `road` from `access.legs`.
- **destinations-overview.jst** — delete `roadBadge()`; read hydrated entries; paint
  via the shared function; drop the inline `access` reliance.
- **lakes.jst** — remove `blockRenderers.destinations` and `buildReferencesCell`
  (folded into `notes`); keep `fishingReferences`.
- **Delete** `rec-sites/beavertail-lake-dayuse/Destinations.json` (stray generated
  file, never read).

## 6. `destinations-overview.json` (hydration model)

`places: [ {group, list:[…]} ]` stays. A **known** entry collapses to just its
hydration pointer:

```json
{ "group": "BC Parks", "list": [ { "file": "elk-falls-quinsam-campground.html" } ] }
```

sync loads the page JSON, replaces the entry's content, injects `file`, applies the
publish filter. The inline `access`/`location`/`sites`/… duplication disappears —
drift becomes impossible by construction (resolves the access-duplication and
no-`file`-link todos). An **unknown** entry (no page yet) stays inline but must match
the unified schema as a partial (name/location/access/campground/links/footnotes as
applicable).

## 7. Migration plan

Constraints: **no local node** — sync.js runs only in GitHub Actions; data transforms
run via Python through `local/tools/jsonio.py` (tab-indented house format). Data and
scripts deploy together in one Action run, so a coordinated per-merge cutover is
atomic. Prefer clean data over tolerant code (Principle 4), so renames are cutovers,
not shims. Each phase is independently deployable and verifiable, and its own go.

**Phase 1 — Unify the road badge (render-time, single copy).** The original ask.
Additive, low risk, no page-JSON change.
1. sync.js: add `access` to gallery entries (additive; keep `badges.road` for now).
2. gettinglost.jst: add shared `deriveRoadBadge(access)`, export it.
3. gallery.jst + destinations-overview.jst: derive via the shared fn; overview's
   `roadBadge()` deleted.
4. sync.js: stop emitting `badges.road`.
5. Verify: gallery cards + overview Access column unchanged.

**Phase 2 — Gallery/overview = verbatim page JSON + injected `file`.** Kills the
`teaser` rename; prerequisite for the renames to flow through untouched.
1. sync.js: emit page JSON verbatim + inject `file`; keep filter/path rules + leg
   validation.
2. gallery.jst: read `excerpt` (not `teaser`).
3. Verify: gallery renders from the fuller entries. (Page JSONs still old-schema;
   verbatim copy carries old names; renderers read old names — safe.)

**Phase 3 — Schema formalization.** Independent field-group cutovers; each is a
Python transform + sync touch + renderer touch + verify. Order is flexible.
- **3a** `title`→`name` (data; sync `body.title`←`data.name`; gallery/overview/pageMap; check the folder-page path at sync.js:982).
- **3b** `badges`→flat array (data; badge renderers; road already derived from Phase 1).
- **3c** `campground` restructure — add `operator`/`siteCount`/`amenities`; `siteMap`→`links`; `website`→`HomePage`; `reservation`→`links` (data; campground renderer).
- **3d** top-level `links` + OnLost resolution (scheme-less `*.html`) in gettinglost.jst (data; links renderer).
- **3e** `destinations`→`notes` "Destinations" section (data; remove lakes.jst destinations renderer; notes renderer resolves OnLost; "On Getting Lost").

**Phase 4 — Overview hydration.** After Phase 3 (unknown entries must match the final
schema).
1. Data: collapse known entries to `{file}`; reshape unknown entries to the unified
   partial schema.
2. sync.js: hydrate `{file}` entries; publish filter.
3. destinations-overview.jst: read hydrated entries.
4. Verify: overview table renders; no drift.

**Phase 5 — Cleanups / data fixes.**
1. Delete stray `Destinations.json`.
2. Add Echo/Beavertail overview entries; resolve `morton-lake-rec3104` identity — or
   fold into the cross-reference pass below.
3. Update docs/memory that reference `title` / `teaser` / the old projection.

## 8. Enabled follow-ons (not part of this migration)

1. **Cross-reference validation pass** — hydration removes the duplication outright,
   so the remaining check is a *dangling* `{file}` (points at a missing/unpublished
   page). sync can fail the build on it, like slug drift.
2. **`data-gallery-list` / `data-gallery-table`** — two renderers over the one
   dataset, with a section parameter mirroring today's `group`.
3. **Unpublished-page display** in the hydrated overview (skip / grey out); short
   term the renderer ignores `wpSettings`.
4. **Per-page content pass** — Pierre's one-page-at-a-time sweep to re-enrich the
   prose dropped in §5.

## 9. Risks

1. **Coordinated cutovers** — a rename that lands in data but not the renderer (or
   vice-versa) breaks rendering until the next deploy. Mitigate by keeping each 3x
   field-group small and verifying on the deployed branch before moving on.
2. **No local sync test** — sync.js behavior is only observable in Actions. Read the
   run's warnings/annotations after each phase.
3. **Verbatim bloat** — gallery entries now carry the whole page body (`notes`,
   photo blocks). Accepted (Principle 5); it's what enables the table view.
