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
   link to a local page is a scheme-less `*.html` url, resolved via `fileToSlug` and
   drift-checked at build — the "OnLost" convention.
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
  "badges": ["camping", "fishing", "hiking"],  // flat array; road is DERIVED at render
  "wpSettings": { "published": true, "comments": "open" },

  "location": {
    "lat": 50.037009, "lng": -125.295734,
    "pin": "tent", "zoom": 13,
    "notes": "Near Campbell River"             // optional
  },

  "access": {                                  // omitted on lakes
    "haversine": [ { "town": "Campbell River", "km": 5 } ],
    "legs": []                                 // [] = paved all the way
  },

  "links": [                                   // SUPERSEDED 2026-08-01 — see docs/schema/links.md
    { "label": "HomePage", "url": "https://bcparks.ca/elk-falls-park/" },
    { "label": "OnLost",   "url": "morton-lake-park.html" }   // scheme-less *.html → local page
  ],

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

> **Superseded 2026-08-01.** `links[]` gained a closed, optional `type`
> (`homepage` / `map` / `reservation`) which is now the key every renderer selects by, the
> label having gone back to being display text. `campground.links` was merged up into this
> same array, and the `OnLost` label was dropped — a page on this site is signalled by the
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

Table columns: Name, On-lost, Location, Distance, Access, Sites (plain `siteCount`), Maps,
Amenities, Reservation. Maps and Reservation select from `links[]` by `type` (2026-08-01);
they used to be split out of `campground.links` by a `/map/i` test on the label.

## Enabled follow-ons

Not part of the migration; recorded because the unification is what made them possible.

1. **Cross-reference validation** — hydration removed the duplication, so the remaining check
   is a *dangling* `{file}` pointing at a missing or unpublished page. Sync could fail the
   build on it, the way it does for slug drift. `docs/todo.md` #2.
2. **Unpublished-page display** in the hydrated table — skip or grey out. The renderer
   currently ignores `wpSettings`.
3. **Per-page content pass** — re-enriching prose that the migration dropped. Authoring, not
   code.

Related: [docs/schema/access.md](../schema/access.md),
[docs/schema/badges-road.md](../schema/badges-road.md),
[docs/rendering/blocks.md](../rendering/blocks.md).
