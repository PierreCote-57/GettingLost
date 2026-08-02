# Access schema

The `access` object on destination content JSON — "how do I get there" — designed
2026-07-20, replacing the flat `badges.road` string and the old top-level
`distanceKM`. See [docs/schema/badges-road.md](badges-road.md) for how the badge renders,
[docs/projects/destinations-overview.md](../projects/destinations-overview.md) for the overview table.

## The tree

```
access
├── haversine [ { town, km } ]    great-circle, rounded; origins Campbell River / Nanaimo / Victoria
├── driving   [ { town, km } ]    NOT BUILT YET — real road distance, same shape
└── legs      [ { type, km } ]    the unpaved tail, in travel order
```

- `haversine` is named for the **method**, deliberately: the number must never be
  mistaken for a drive. `driving` will sit beside it, not replace it.
- Rounding rule: under 2.5 km → `1`, otherwise nearest 5. Plain round-to-5 sends
  short distances to `0`, which reads as missing data rather than "it's in town."
- Origin coordinates used: Campbell River 50.0244/−125.2475, Nanaimo
  49.1659/−123.9401, Victoria 48.4284/−123.3656 (town centres).

## The three states of `legs` (settled 2026-07-20)

```
legs absent / null            don't know — nobody has looked. No badge.
legs []                       looked: no non-paved road. -> pavement badge (blue)
legs [{unpaved, km}]          measured non-paved tail, character not yet refined
legs [{potholes,10},{…}]      driven and characterized
```

`{type:"unpaved"}` with **no km is illegal** — without a measurement it claims
nothing that `null` doesn't already say. `deriveRoadBadge()` warns, names the
file, and skips such a leg, which lands the badge back on "don't know".

**km rounding (Pierre's rule):** under 2 km → one decimal (`0.6`); 2 km or more →
no decimal (`6`, `15`). Different from the `haversine` rounding rule above,
deliberately: legs are short by nature.

## legs — the unpaved tail only

Pavement segments are **excluded**. `legs` describes the destination's own
approach, not the route, which is what lets `haversine` carry several towns.
Segments run in travel order, so "the last 2 km are the bad part" is readable
without a extra field.

## Leg-type vocabulary — the axis is FOOTING and what it damages

| type | meaning | what it costs you |
|---|---|---|
| `unpaved` | non-paved tail MEASURED, character unknown | unknown — grey badge |
| `dirt` | unsealed, graded; washboard implied | comfort, slow down |
| `potholes` | surface failing | suspension |
| `sharp_rock` | coarse/sharp aggregate (Pierre: "large gravel") | **tire puncture** — not clearance |
| `rugged` | ruts, washouts, grades | drivetrain / clearance |
| `walk` | improved footing, sidewalk or level path | on foot, gear in hand |
| `hike` | trail footing, roots and grade | on foot, need free hands |
| `boat` | water crossing | needs a vessel |

**`walk` vs `hike` is footing, not distance** — Pierre's rule, and it's correct:
there is no standard minimum distance for a "hike". A 500 m trail is a hike; a
2 km promenade isn't. `walk` may go unused; it costs nothing to keep legal.

**`sharp_rock` names the hazard, not the size.** The earlier name `rocks` was
wrong because it reads as boulders/clearance, colliding with `rugged`.
`gravel` was renamed to `dirt` in the same pass.

## Severity is configuration, not truth

`GL.ROAD_RANK` = `[unpaved, dirt, potholes, sharp_rock, rugged]` since 2026-07-20.
**`pavement` was REMOVED from the rank and from `DRIVE_LEG_TYPES`**, joining
`back_country` as derived-only: the array doubles as the list of types that may be
AUTHORED, and neither is ever authored. Pavement segments are excluded from `legs`
entirely — which is exactly what lets one page's legs hold true for several origin
towns, since the paved part is the only part that depends on which town you left.

`unpaved` ranks **mildest on purpose**: rank only ever breaks a tie against a
*known* type, and the known type is the better information and should win. Its
grey, not its position, is what says "unknown".

The rank is anchored to **THE van**:
street tires, upgraded suspension, dually, AWD. That spec is what orders
`sharp_rock` above `potholes` — twin rears double puncture exposure and catch
stones, while the suspension upgrade is exactly what makes potholes tolerable.
A different van or a tire change can legitimately reorder it. The van's specs
are explained in site content, not in code comments.

Non-drive types carry **no rank** — any one of them means you leave the van,
which is the whole distinction.

## Badge derivation (never authored)

```
any non-drive leg  ->  back_country
all drive          ->  highest GL.ROAD_RANK
legs []            ->  pavement      (deliberate: "paved all the way")
legs absent        ->  no badge      (not filled in yet)
```

The `[]` vs absent distinction matters: without it, an unfilled destination
badges as `pavement`, which asserts something false rather than saying nothing.

Now ONE implementation: `GL.deriveRoadBadge()` in `gettinglost.jst`, used by both the
grid cards and the list browser's Access column (the old duplicate `roadBadge()` in
`destinations-overview.jst` died with that page) — kept
in step by the shared vocabulary in `gl-constants.jst` (`GL.ROAD_RANK`,
`GL.NON_DRIVE_LEG_TYPES`). Authoring `badges.road` now warns and is ignored.

## Lakes carry no access

A destination is somewhere you **arrive**; a lake is a feature you **look at**.
You don't drive to a lake, you drive to a rec site or campground on its shore —
so lake pages have no `access`. (The old `GALLERY_RULES` `exclude` that kept them
out of the Destinations gallery is gone with that system — lakes now sit in the one
`destinations.json` and are distinguished by `tags.keywords: ["lake"]`, i.e. by
filtering rather than by exclusion.) Roberts Lake was the known exception — a lake
page describing a day-use site — and was split 2026-08-02: the lake page keeps the
lake and carries no `access`, and the day-use site became its own destination,
`roberts-lake-rec0191`, which carries it.
