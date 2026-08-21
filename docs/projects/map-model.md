# Map model — one shape for location, googleMap and pin

The schema and how the renderer resolves it are in
[../schema/map-pins-location.md](../schema/map-pins-location.md); the block's place among the
other renderers is in [../rendering/blocks.md](../rendering/blocks.md). **This file holds only
what those two cannot: the problem it solved, and the alternatives that were considered and
rejected** — so none of it gets re-litigated from scratch.

## The problem

The `googleMap` renderer had two entry shapes. A div with no `data-map` read the page's
top-level `location`; a div with `data-map="road"` read `googleMap.<name>`. The two were not
alternatives but a **partial merge**: when a named map had no `lat`/`lng` of its own, the
centre came from `location` while `zoom` and `pinList` still came from the named entry.

Pierre's objection, and the sentence the whole redesign came out of: *"where what comes from
becomes too complicated."* One map drawn from two sources means no one can answer "where did
this zoom come from" by reading the data.

Underneath it sat a naming problem. A `location` described *where a place is*; a `googleMap`
entry described *how to draw a map*. Their fields overlapped almost completely, so the code
kept converting between them — while a top-level `pin` (an icon) and a `pins` array (markers)
made "pin" mean two different things one line apart.

## What it became

A pointer replaces the **whole** entry, never part of it. A `location` never points, so
resolution is one hop and always terminates. And `location` is the **union** of the other two
shapes, which is what lets a place be a map, a marker, or the target of a pointer without
being restated.

The renaming is what made the union legible: `pin` → `icon`, `pins` → `pinList`,
`location.notes` → `location.displayName`, `pin.label` → `pin.displayName`. After it, "pin"
means exactly one thing — an element of a `pinList`.

## Rejected, with the reason

- **A `self` sentinel for a page pointing at itself.** A literal filename (`{"file":
  "morton-lake.html"}`) uses the one pointer mechanism instead of adding a magic value, and a
  stale self-reference is then a broken link `crossref_check.py` already catches. The rename
  cost that argued for a sentinel is not real: the file is being edited during a rename
  anyway. The resolver spots the self case and skips the fetch — an optimization, not a
  second spelling.
- **"Exactly one source, error on two."** Rejected as complication that removes a capability:
  with a precedence chain, `file` can be renamed to `fileSAV` to fall back to the previous
  source while testing. Extra keys are legal and ignored.
- **Memoizing the `file` fetch.** No page points twice at the same file, so there is nothing
  to cache. (Note for anyone tempted: concurrent `fetch()` calls are *not* deduplicated by the
  browser — only sequential ones can hit the HTTP cache.)
- **Keeping a top-level `pin` on a map object.** Dropped in favour of `pinList` everywhere,
  with a `location`'s `icon` normalized into a centre pin after resolution.
- **Automatic marker labels.** The old unnamed branch injected the page's `name` into the
  synthesized marker. Ruled *missing label = no label*; revisiting labels is `../todo.md` #35.
- **De-duplicating registry coordinates by resolving `destination_id` at runtime.** Solved
  instead by deleting the records: a place with a destination page is referenced by page, so
  it leaves `logs/locations.json` entirely and `destination_id` went with it.

## Artifacts left behind

- `resolveLocation`, `googleRoadMap`'s last traces, and the unnamed-div mode are gone. A div
  with no `data-map` is now an error.
- `logs/locations.json` holds only places with **no** destination page.
- The one-shot migration script was deleted after it ran; it was never idempotent.
