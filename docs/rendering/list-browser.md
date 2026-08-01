# List browser

One param-driven page, `pages/shared/list_browser.html`, with two independent axes —
display (table/grid) × data — driven by URL query parameters. It replaced both the gallery
and the destinations-overview pages.

`list_browser.jst` registers `blockRenderers.list_browser` and runs nothing on load; see
[docs/rendering/blocks.md](blocks.md), "THE INVARIANT". Everything below happens inside the
renderer, long after `window.GL` exists — there is no load-order constraint.

## The four phases

The renderer reads top to bottom, in order:

1. **Process request parameters** — the one place the raw query string becomes what the page
   acts on. It fills defaults, and *everything* reads the result, including `navigate()`, so
   a filled default lands in the next URL. That is deliberate and matches the nav menu, which
   already emits an explicit `view=grid`.
2. **Load data** — `datasets.json`, then the selected dataset's file. Sequential because the
   first names the second; if either fails nothing useful can happen, so error handling
   collapses to one place. Nested `fetch/.then`, not async/await — the file keeps its ES5-ish
   idiom. **Two files, two requests.**
3. **Process** — all of it, up front: filtering, and picking up the keyword vocabulary.
   Nothing is gained by sequencing work between display calls.
4. **Display** — `displayOptionsRow` and `displayDataset`, two different views on "all that
   is known".

### The property bag — `known`

One map owned by the top level, starting empty, accumulating per phase:

- phase 1 adds `params`
- phase 2 adds `datasetList`, `dataset`, `rawRows`
- phase 3 adds `filteredRows` and the keyword list

Five properties. A comment above each phase states what that phase adds; that is the complete
map, and it stays complete because of the read-only rule below.

**Why a bag and not explicit arguments:** the display functions are parallel siblings with
drastically different needs (`displayViewOptions` vs `displayKeywordOptions`). Any signature
serving all of them would just be the union of everyone's needs. The bag says "I don't know
what you need, here is what I know, use what you want."

### Conventions that make it work

- **Every display function has the same signature: `displayX(known)`.**
- **Unpack at the top.** Each opens with a `// what I need from what is known` block naming
  the values it uses — that documents dependencies at the point of use, better than an
  argument list.
- **Phases 1–3 WRITE the bag; phase 4 only READS it.** Display functions are meant to be
  independent views. If either could add a key the other might see it, their order would
  start to matter — the same implicit sequencing the phases exist to remove, one layer down
  where it is harder to see.
- **`known` holds KNOWLEDGE, never DOM, and display functions are pure `known -> DOM node`.**
  The block element is a plain local of the renderer; the two `el.appendChild(displayX(known))`
  calls are the only place the page is touched. An earlier version put `el` in the bag and let
  each display function append to it — that keeps the letter of the rule while losing what it
  is for, because the options row then has to run before the dataset or it lands underneath.
  **The test to apply is not "does it write the bag" but "could these two run in either
  order".**
- **Filtering is not a display concern.** Renderers are pure `rows -> DOM node`; the count is
  a plain value at top level.
- **The keyword list is a processing step.** It is read from the dataset definition —
  `extractKeywords` takes the keys of `dataset.counts.keywords`, which sync.js wrote sorted.
  The migration this convention was written to allow (derive from `rawRows` → read from the
  manifest) has happened, and it touched that one processing step and no view, because the
  keyword control reads the finished list and never `rawRows`.
- `navigate(known, patch)` is the one non-display function that also takes the bag: it clones
  `known.params` to build the next URL, and controls call it from their handlers.

## The two switches

**Related, but NOT the same vocabulary.** One option can emit several query params (a
shortcut preset like "lake camping with van") or none (`viewMode` concise/verbose). `view`
does both — it displays *and* filters.

- **Adding a filter is one function plus one line in the switch.** Same for a control.
- **Silence on both sides is correct, never an error.** A token with no builder builds
  nothing; a param with no filter filters nothing. Legitimate states: staged rollout (see the
  control before wiring the filter), under test, retired-but-kept.
- **VALUES LIVE IN THE QUERY STRING, NOWHERE ELSE.** An options token is a plain name; it
  never carries a value, and the dataset entry never holds one. `options` says a control is
  POSSIBLE for this dataset; the URL says what to do about it. So a builder may legitimately
  return nothing — `booklet` renders a download button when `?booklet=howto` is present and
  nothing at all when it isn't, exactly as a filter applies nothing when its parameter is
  absent. Both `"booklet=howto"` as a token and a `pdf` field on the dataset entry were
  rejected for the same reason: a second home for values breaks the pattern. **Check the
  pattern before reaching for a special case.**
- The filter loop is driven by the URL, not by `options`, so a hand-typed or shared URL
  filters even for controls that dataset does not display.

## Filter semantics

**OR within a control, AND across controls.** Each filter is
`filterX(value, longList) -> shortList`, and chaining is what produces the AND.

- `filterView` — `view=grid` keeps `wpSettings.published === true`. It lives outside
  `renderGrid` so the count cannot disagree with what you see.
- `filterAccess` — ordinal threshold over `Object.keys(GL.ROAD_COLORS)`: the worst road you
  will accept. **Unknown PASSES.** Only the GL pages have authored legs, so a strict rule
  would drop every catalog row; an unmeasured road is not evidence of a bad one.
- `filterKeywords` / `filterBadges` — tag membership; **absence FAILS**. Consequence: no
  catalog row carries badges, so any badge filter narrows to the GL pages.
- `filterSearch` — `JSON.stringify(row)` substring. Broad on purpose: it sees keys and URLs
  too, so "map" matches every row with a map link.

**The keyword vocabulary is derived from the UNFILTERED rows** — sync.js walks the whole
hydrated dataset. A vocabulary derived from the filtered list would delete the choices you
need in order to widen the search next.

## Counts in the controls

Every filter value shows how many rows it would match. The numbers come from the manifest:
`collectCounts` in sync.js walks each hydrated dataset once and writes
`counts: { keywords, badges, access }` onto the dataset entry. The browser never counts.

- **`keywords` is the OPEN vocabulary, so its keys ARE the choice list** — sorted by sync.js,
  and `extractKeywords` just takes `Object.keys`. There is one list, so the choices and the
  numbers cannot disagree.
- **`badges` is CLOSED** (`GL.TAG_COLORS`), and the browser still owns that vocabulary; only
  the numbers come from the manifest. A value nobody used has no key and reads as `(0)`.
  **The zero is deliberate and the option is not hidden** — a closed vocabulary showing a zero
  is advertising room the data has not used yet, not a dead choice.
- **`access` counts the DERIVED road badge**, with unmeasured rows under the key `"unknown"`
  (never a road value, so it cannot collide). Deriving it costs sync.js a small mirror of
  `GL.deriveRoadBadge` — the browser keeps the render-time derivation, `deriveRoad` in sync.js
  exists only to count. It can be the simpler of the two because `validateLegs` has already
  failed the build on any leg it would have had to reject.
- **The access numbers are CUMULATIVE, and the accumulation happens in the browser.** The
  control is a threshold — picking "dirt" keeps pavement and unpaved rows too — so each option
  shows the running total down `roadOrder()`, seeded with the `unknown` rows because an
  unmeasured road passes every threshold. Sync ships per-value counts and nothing else: the
  running total is threshold semantics, and the threshold lives in `buildAccessSelect`.

## Errors: say what happened, do not comfort

`fetchJson(url)` is the single fetch path, and **every failure message names the URL** —
unreachable, HTTP status, or not valid JSON. "HTTP 404" alone never says which of the two
files was missing.

`pickDataset(datasetList, id)` returns the entry or throws `"Unknown dataset <id>"`. Throwing
is what keeps phase 2 to two statements: the not-found case lives in the helper instead of a
branch interrupting the flow, and the single catch already reports.

The catch does `el.textContent = err.message` — the same text on screen and in the console.
No generic string, and **no "Content is temporarily unavailable"**. It is not correct: a
missing file in uploads never loads on a retry, so "temporarily" is a false claim about the
future. And it is not useful: it tells the visitor nothing actionable and tells Pierre
nothing about what broke, while the file name says instantly whether it was a sync miss, a
rename, or a bad `file` in `datasets.json`.

A `showToVisitor` flag on the Error, to pick between a "safe" and an "internal" message, was
proposed and did not survive. The distinction it protects is real in an app where error text
leaks stacks or private paths; it is not real here. Both files reaching the catch are public
URLs the browser already fetches on every page load, and the only non-project input, the
dataset id, goes in via `textContent`, so it is inert. **Before adding a mechanism, ask what
this code actually has to distinguish**, rather than importing a habit from bigger apps.

## The table breakout

`max-width` **cannot** break an element out of a constrained parent — it only caps. The table
wrapper fills the block element, which the WP block theme constrains by styling the direct
children of the content container, so any larger `max-width` on it never binds.

The fix is a real breakout on the table wrapper only: `width:1180px; margin-inline:-140px`
(1180 − 900 = 280, so −140 a side centers the extra room). `margin-inline` is the horizontal
pair by definition and cannot touch the vertical margins. Footnotes sit OUTSIDE the breakout
div, in an outer standard-width div, so only the table is wide.

The rejected alternative was putting the override on the block element itself: it works, but
it widens everything inside — options row, count, footnotes — all left-justified across the
extra width.

**Known limitation:** `width:1180px` is fixed, so on a viewport narrower than ~1180 the
wrapper forces horizontal page scroll. A `min()` width or a media query would guard it.

## Settled — do not re-raise

- **Param validation is DROPPED.** It would have to happen in phase 1, where `access`'s
  vocabulary is known but `keywords`' is not, since that comes from phase 2 data — and
  different handling for the two is not acceptable. An invalid value requires hand-typing a
  URL or following an obsolete link, and recovery is trivial. The general case: *"if you try
  hard enough to fail, you will succeed"* — the argument against defending a read-only
  client-side page.
- **A badges any/all toggle** was designed, deferred, then dropped.
- **The `<details>` light-dismiss** was dropped.
- Losing the independence of the options row from the dataset — either fetch failing now
  kills both — was judged a non-issue.

## Gotcha

`list_browser.jst` executes BEFORE `gl-constants.jst` defines `window.GL`. Anything touching
`GL` must be inside a function that runs after a fetch — a top-level
`Object.keys(GL.ROAD_COLORS)` throws. Hence `roadOrder()`.

## The WP nav menu

One `wp_navigation` post, **id 5**, edited via Appearance → Editor → Navigation → ⋮ → Edit,
the block code editor. Menu entries carry `?dataset=…&view=…` explicitly, and a booklet
entry must also carry `&booklet=…` or no download button appears.

Related: [docs/projects/schema-unification.md](../projects/schema-unification.md),
[docs/projects/destinations-overview.md](../projects/destinations-overview.md).
