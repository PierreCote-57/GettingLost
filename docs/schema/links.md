# `links[]` — one flat list, `type` is the key

```
links [ { label, url, type? } ]
```

One array per row or page. `campground.links` is gone — it was merged up on
2026-08-01, so there is exactly one place a link can live.

- **`url`** — an entry without one is not a link. Reservation status with no booking page
  ("First-come-first-served, free") is prose and lives in a **`Reservation notes`** notes
  section instead.
- **`type`** — a closed vocabulary, `GL.LINK_TYPES` in `gl-constants.jst`, mirrored as
  `LINK_TYPES` in `sync.js`: **`homepage`**, **`map`**, **`reservation`**. Optional.
- **`label`** — display text, and nothing else.

## The label is NOT a key

It was, in three incompatible ways, and that is the whole reason this shape exists:

| Reader | Old rule |
| --- | --- |
| `list_browser.jst` Maps column | label matches `/map/i` |
| `gettinglost.jst` campground block | label is exactly `"Campground map"` |
| both, for the website link | label is exactly `"HomePage"` |

Two separate bugs came out of that. **Maps nobody looked up were invisible:** a `"Park map"`
or `"Trail map"` appeared in the table but never on the destination's own page, because the
page's lookup was for the exact label `"Campground map"`. **And renaming the classifier
silently reclassified:** changing `"Campground map"` to `"Campground"` moved those links out
of the Maps column into Reservation, because the thing being renamed *was* the test.

With `type` as the key both readers select the same way, the label is free to say whatever
reads best, and `validateLinks` fails the build on a value outside the vocabulary.

## Optional on purpose

A link that is none of the three keeps its label and carries no type — like `tags.types`,
the check is on the VALUE, never the presence. **VI Camping** on Pacific Yew Recreation Site
is the case in the data: a real external site that is not the destination's own homepage,
not a map, not a booking page. It still renders in the `links` block; it is simply not part
of the campground logistics row.

## What each reader does now

- **`list_browser.jst`** — `linksOfType(place, …)`. Name links to the `homepage`; the Maps
  column lists **every** `map`, one per line, distinguished by its label; the Reservation
  column lists every `reservation`.
- **`gettinglost.jst`** campground block — `Website · <every map> · <every reservation>`,
  where `homepage` is the one entry displayed under a different word.
- **`links` block** — every link the page carries, `homepage` shown as "Website".

Unrelated despite the name: a **scheme-less `*.html` url** is resolved to an internal
`/slug/` link by `onLostHref()`. That is a URL convention used by the notes cross-references
and has nothing to do with `type`. The old `OnLost` *label* convention is gone — whether a
destination has a page on this site is said by the presence of `file`, kept through
hydration.

Related: [rendering/blocks.md](../rendering/blocks.md),
[rendering/list-browser.md](../rendering/list-browser.md),
[types.md](types.md).
