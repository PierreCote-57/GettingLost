# Badges and the road chip

Road-condition badge feature. Originally merged to `main` 2026-07-13 via PR #4
(commit `64c2e0b`). A single badge showing the **worst** stretch of the drive in, color-coded by
severity. On a **gallery card** it sits in the lower-left corner. Since
2026-08-01 it also renders **on the destination page itself**, right-hand end of
the `tags` block's first line and carrying a distance — the same
`deriveRoadBadge` value, painted by the same `renderRoad`. See
[docs/rendering/blocks.md](../rendering/blocks.md), [docs/schema/image.md](image.md), [docs/conventions/site.md](../conventions/site.md).

**Reworked 2026-07-20: the value is now DERIVED, not authored.** The vocabulary,
the leg model it derives from, and the van-anchored severity rank all live in
[docs/schema/access.md](access.md) — read that first. This file covers rendering.

## Data model — `tags.badges`, a flat array
```json
"tags": { "badges": ["fishing", "picnic"] }
```
- `badges` is a bare array of activity tags. Authored. Two moves got it here: the
  `{ "tags": [...] }` wrapper *inside* badges went in the 2026-07-20 unification, and the
  whole field moved **under a top-level `tags`** on 2026-07-24, where `keywords` already
  sat and `types` joined it on 2026-08-01 — the three facets in one place. See
  [types.md](types.md) for the tree.
- The **road badge is never stored.** It is DERIVED at RENDER time from
  `access.legs` by the single shared `GL.deriveRoadBadge` in gettinglost.jst
  (used by both the grid cards and the list browser's Access column). `sync.js` runs the
  same logic only to VALIDATE the legs (warn on bad data), not to emit anything.

## Colors — `GL.ROAD_COLORS` in gl-constants.jst
**Seven** keys as of 2026-07-20, `{bg,text}` each, **no fallback**: `pavement`
(blue), `unpaved` (grey `rgba(120,118,112,0.9)` on `#F1EFE8`), `dirt` (green),
`potholes` (orange), `sharp_rock` (rust), `rugged` (red), `back_country`
(near-black `rgba(20,20,20,0.94)` on `#EDEDED`).

**Two values sit off the severity ramp, for opposite reasons.** `back_country` is
the absence of a ROAD — a darker red would imply "very rugged, but drive it."
`unpaved` is the absence of a JUDGEMENT — a tail was measured but nobody has
driven it and said what it does to the van. Grey reads as "not characterized yet"
rather than as a position on blue→red.

`pavement` and `back_country` both appear in `ROAD_COLORS` only — never in
`GL.ROAD_RANK`, never authorable. `unpaved` IS authorable and is in the rank.

**No-fallback bites on a stale script:** because an unknown value renders nothing,
a browser running an old `gl-constants.jst` silently drops the new `unpaved` badge
while every older type keeps rendering. That exact symptom appeared 2026-07-20.

The non-drive leg types (`walk`/`hike`/`boat`) have **no colors** — they are leg
types that derive to `back_country`, never badges themselves.

## Rendering
- `renderRoad(road)` in `gettinglost.jst` — paints an already-derived string.
  `renderCard` calls `renderRoad(deriveRoadBadge(entry.access))` — the gallery
  entry carries `access` verbatim (Phase 2), not a stored road value.
- **Underscores render as spaces.** `sharp_rock` → "sharp rock". The underscore
  is an id convention (Pierre dislikes spaces in keywords), not something a
  reader should see.
- `.gl-road` in `gettinglost.cst` — same pill as `.gl-tag`,
  `position:absolute; bottom:8px; left:8px`.
- The list browser's table Access column shows the same derived word as **text**
  (see [docs/rendering/list-browser.md](../rendering/list-browser.md)); whether it becomes a
  real badge there is undecided.

## Behavior on bad value
- Falsy road → no badge, silently (means "legs not filled in yet").
- Unrecognized value: browser `renderRoad` → render nothing + `console.error`;
  `sync.js` → `console.warn` naming the file + `::warning::` CI annotation.

## Rejected: a white "TODO" badge
Considered for marking destinations whose legs aren't filled in, then dropped —
it publishes an internal work queue to readers. Pierre only needed to *know*
which ones are missing, and asking Claude to query the data answers that without
shipping anything. A sync build-warning was also offered and declined.
