# Schema unification

One schema and one derivation for destinations. Before it, a destination's data existed in
three shapes — the authored page JSON, a hand-built gallery projection that renamed fields,
and an overview file that re-declared `access`, `location` and `sites` inline with nothing
checking for drift. Badge derivation was triplicated across `sync.js`, the overview jst and
`gettinglost.jst`.

## Principles

These still govern anything that touches the pipeline.

1. **`sync.js` does not mutate content.** Its jobs are select (publish filter, path rules),
   pack, hydrate (`{file}` → the page's JSON), inject `file`, and validate — failing or
   annotating the build on bad data. No renames, no derivation.
2. **One derivation, at render.** The road badge word comes from `access.legs` via a single
   shared `GL.deriveRoadBadge` in `gettinglost.jst`. Never stored.
3. **Filename is the master.** A page JSON never carries its own `file`; sync injects it. A
   link to a local page is a scheme-less `*.html` url, resolved at render by `onLostHref()`
   via `fileToSlug`. Sync does not check those urls — that is `crossref_check.py`'s job,
   run by hand ([../recipes/crossref-check.md](../recipes/crossref-check.md)).
4. **Clean data, not legacy-tolerant code.** Every rename was a coordinated cutover — data,
   sync and renderer in one deploy. No dual-read shims.
5. **Size is a non-issue.** Verbatim copy is fine; page JSONs are 0.9–5.5 KB.

## The unified destination JSON

Comments below are annotations; real JSON has none. `file` is **not** in the file — sync
injects it.

```jsonc
{
  "name": "Elk Falls Park",                    // drives the table, the gallery, and WP post_title
  "featuredImage": "under-construction.png",   // stored; the default is applied at render
  "excerpt": "A thundering waterfall ...",     // teaser text, not renamed anywhere
  "tags": {                                    // `badges` moved in here 2026-07-24 — was top-level
    "badges": ["camping", "fishing", "hiking"],// flat array; road is DERIVED at render
    "types": ["park"],                         // closed facet, added 2026-08-01
    "keywords": ["Visited"]                    // open vocabulary
  },
  "wpSettings": { "published": true, "comments": "open" },

  "location": {                                // RENAMED 2026-08-16 — see docs/schema/map-pins-location.md
    "lat": 50.037009, "lng": -125.295734,
    "icon": "tent", "zoom": 13,                // was `pin`
    "displayName": "Near Campbell River"       // optional; was `notes`
  },

  "access": {                                  // omitted on lakes
    "haversine": [ { "town": "Campbell River", "km": 5 } ],
    "legs": []                                 // [] = paved all the way
  },

  "links": [                                   // TYPED 2026-08-01 — see docs/schema/links.md
    { "label": "Website",    "url": "https://bcparks.ca/elk-falls-park/", "type": "homepage" },
    { "label": "Campground", "url": "https://bcparks.ca/…/map.pdf",       "type": "map" },
    { "label": "Quinsam River Trail", "url": "elk-falls-quinsam-campground.html" }
    //                                  ^ untyped, and a scheme-less *.html → local page
  ],

  "googleMap": {                               // every destination page has at least one NAMED map
    "road": { "file": "elk-falls-quinsam-campground.html" }   // this page's own location
  },

  "footnotes": [ { "field": "siteCount", "text": "2 vehicle pads + 4 walk-in tent pads" } ],

  "notes": [                                   // the single container: Destinations AND Further readings
    {
      "sectionName": "Destinations",
      "list": [
        { "name": "Amor Lake", "url": "https://www.sitesandtrailsbc.ca/resource/REC0174", "description": ["BC Sites & Trails"] }
      ]
    }
  ]
}
```

`links` renders through the `links` block via the shared `linkRow`.

> **What 2026-08-01 changed.** The migration shipped `links[]` keyed by its **label**.
> That was replaced by a closed, optional `type` (`homepage` / `map` / `reservation`), the
> label going back to being display text; `campground.links` was merged up into the same
> array; and the `OnLost` label was dropped — a page on this site is signalled by the
> presence of `file`. The scheme-less `*.html` url convention is unchanged.
> **[docs/schema/links.md](../schema/links.md) is current for everything about links.**

### Type block — campgrounds, parks, rec-sites

```jsonc
"campground": {
  "operator": "Quality Recreation Ltd.",
  "siteCount": 6,                              // a number; composition ("2 + 4") goes to a footnote
  "amenities": ["suspension bridge", "waterfall"]
  // `links` was REMOVED 2026-08-01 — merged up into the row's own links[], typed.
}
```

A day-use site with nothing to say drops the `campground` block entirely.

Two keys above have their own docs and are the authority there, not this file:
`googleMap` ([../schema/map-pins-location.md](../schema/map-pins-location.md)) and `links`
([../schema/links.md](../schema/links.md)). `photoGalleries` is a further page key, omitted
above because it is a rendering concern ([../rendering/blocks.md](../rendering/blocks.md)).
`footnotes` is legal anywhere the shape is, but in practice only the inline dataset rows
carry it.

### Type block — lakes

```jsonc
"fishingReferences": { "bcIdentifier": "00517SALM", "areaKm2": 0.211, "lakeChartList": [], "stockingName": "" }
```

A lake has no `access` and no `campground`. Its nearby places live in a `notes` section named
"Destinations" — there is no `destinations` block or renderer.

## Hydration is sync-time

`sync.js` replaces each `{file}` pointer with that page's own JSON before upload, so the
browser fetches an already-flat array and the page stays the single source. This is what
eliminates access and location drift.

A row in the destinations dataset is therefore one of two things: a unified partial entry
inline, or a hydrated `{file}` pointer. See
[docs/projects/destinations-overview.md](destinations-overview.md).

Table columns: Name, On lost, Location, Distance, Access, Sites (plain `siteCount`), Maps,
Amenities, Reservation. Maps and Reservation select from `links[]` by `type` (2026-08-01);
they used to be split out of `campground.links` by a `/map/i` test on the label.

## Enabled follow-ons

Not part of the migration; recorded because the unification is what made them possible.

1. **Cross-reference validation** — both halves landed. A dangling `{file}` pointer in a
   dataset is a hard build failure: `hydrateList` skips the entry so no partial list can
   publish, and `validateLists` annotates the run red. Everything else — a `file` link
   anywhere in `media/**`, and whether the two sides agree on the target's name — is
   `crossref_check.py`, run by hand
   ([../recipes/crossref-check.md](../recipes/crossref-check.md)). An *unpublished* target
   still resolves at build; `loadPerPageDataMap` reads every page JSON regardless of status.
2. **Unpublished-page display** — done, at render rather than at build. `filterView` keeps
   `wpSettings.published === true` for `grid` and `map`, so the table is the one view that
   shows unpublished rows, and the "On lost" column withholds its View link for them.
   See [../rendering/list-browser.md](../rendering/list-browser.md).
3. **Per-page content pass** — re-enriching prose that the migration dropped. Authoring, not
   code.

Related: [docs/schema/access.md](../schema/access.md),
[docs/schema/badges-road.md](../schema/badges-road.md),
[docs/rendering/blocks.md](../rendering/blocks.md).
