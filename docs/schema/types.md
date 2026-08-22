# `tags.types` — what kind of place a destination is

```
tags
├── types      [ "campground" | "lake" | "park" | "rec-site" ]   CLOSED, optional, multi
├── badges     [ … ]                                             CLOSED  — badges-road.md
└── keywords   [ … ]                                             OPEN    — conventions/keywords.md
```

The vocabulary is declared once, as `GL.DESTINATION_TYPES` in `gl-constants.jst`, and
mirrored as `DESTINATION_TYPES` in `sync.js` (browser code can't be required there — keep
the two in sync). Alphabetical: unlike `ROAD_RANK`, the order carries no meaning beyond the
order the dropdown lists them in, and alphabetical is the order that doesn't shift as data
lands.

Type became a facet of its own on 2026-08-01. Before that these four words were ordinary
`tags.keywords` values, load-bearing ones — nothing else on a row said what kind of place it
was. **Facets are the filter axes, and `keywords`, `types`, `badges` and `access` are all
facets**; this is a fourth axis, not a promotion of type out of being a tag.

## A LIST, not a scalar

Every row that carries a type carries exactly one. That is a fact about the data, not a
constraint: a rec site on a lake should be able to say it is both without a schema change,
so the field is a list like its two neighbours.

## Never mandatory — and that is the point

`sync.js` validates the VALUE, never the presence. A row with no `types` is a correct row.

This is what keeps `park` meaningful. The Spit, in Campbell River, may well be a city park —
a very different thing from a provincial park. It carries no type at all rather than a wrong
one, so someone filtering for **park** gets Elk Falls, not The Spit. `filterByWord` fails a
row that lacks the tag, so an untyped row answers no type filter, which needs no special
case anywhere.

Add a value here when a kind of place earns one — `city-park`, when the first arrives. Until
data uses it, the dropdown shows it with `(0)`, which is the closed vocabulary advertising
room not yet used, not a dead option.

## Consequences elsewhere

- **Counting** — `collectCounts` gives `types` no bucket for untyped rows, unlike `access`.
  An untyped row matches nothing, so it is simply absent and the type counts sum to less
  than the row count. An unmeasured *road* passes every threshold, so those rows are counted
  and seeded into the running total; the two are opposite on purpose.
- **Validation** — `validateTypes` runs over the HYDRATED rows, the only place both kinds
  are visible: per-page rows resolved from `{file}` pointers and the inline rows that exist
  nowhere but the dataset file. Walking `perPageDataMap` instead would miss every inline
  row, which is most of them.
- **The filter** — `filterTypes` is `filterByWord("types", …)`, membership with OR inside
  the control, identical in shape to `filterBadges`. Multi-select checkboxes, because the
  filter wants "lakes and parks" even though a row carries one value.

Related: [rendering/list-browser.md](../rendering/list-browser.md),
[conventions/keywords.md](../conventions/keywords.md),
[badges-road.md](badges-road.md).
