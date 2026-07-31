# List browser

The display×data unified page that replaced the separate gallery and
destinations-overview pages. Two records, not yet consolidated — the top-level
rewrite below supersedes the four-step model described in the refactor record.

## Top-level rewrite (BUILT 2026-07-26) — current

This is the model in force.

Designed, agreed AND **BUILT** 2026-07-26 (two changes the same day: first the
block-renderer conversion, then this). Replaces the 4-step render model in
[docs/rendering/list-browser.md](list-browser.md) at the top level — the filter/control patterns there
still hold.

### What shipped
- `list_browser.jst` registers `blockRenderers.list_browser`; nothing runs on load. See
  [docs/rendering/blocks.md](blocks.md) "THE INVARIANT". **The load-order constraint is GONE** — all four
  phases run inside the renderer, long after `window.GL` exists. Param validation
  against `ROAD_COLORS`/`TAG_COLORS` is now possible; do not re-import the old worry.
- **Nothing holds page state at module scope any more.** `optionsEl`, `dataEl`,
  `effectiveParams`, `datasetId`, `view`, `vocabRows`, `showOptions`, `showDataset` are
  all GONE.
- **The duplicate fetch is gone**: two files, two requests.
- `fetchJson(url)` is the single fetch path, and **every failure message names the URL**
  (unreachable / HTTP status / not valid JSON) — Pierre asked for this explicitly,
  because "HTTP 404" never says which of the two files was missing.
- `pickDataset(datasetList, id)` returns the entry or THROWS `"Unknown dataset <id>"`.
  Throwing is what keeps phase 2 to two statements — the not-found case lives in the
  helper instead of a branch interrupting the flow, and the single catch already reports.

### Error messages: say what happened, do not comfort
The catch does `el.textContent = err.message` — the same text on screen and in the
console. No generic string, and **no "Content is temporarily unavailable"**: Pierre had
me rate that against naming the file, and it loses on both counts. It is not CORRECT (a
missing file in uploads never loads on a retry — "temporarily" is a false claim about
the future) and it is not USEFUL (it tells the visitor nothing actionable and tells
Pierre nothing about what broke, while the file name says instantly whether it is a sync
miss, a rename, or a bad `file` in datasets.json).

**I invented a `showToVisitor` flag on the Error to pick between a "safe" and an
"internal" message; Pierre asked what its real purpose was and it did not survive.** The
distinction it protects is real in an app where error text leaks stacks or private paths
— it is not real here: both files that reach the catch are public URLs the browser
already fetches on every page load and shows in the network tab, and the only
non-project input (the dataset id) goes in via `textContent`, so it is inert. Lesson to
carry: before adding a mechanism, ask what THIS code actually has to distinguish, rather
than importing a habit from bigger apps.
- `navigate(known, patch)` is the ONE non-display function that also takes the bag: it
  clones `known.params` to build the next URL, and controls call it from their handlers.
- **Per-view width styling is GONE** — `getGridStyle`/`getTableStyle`/`applyStyle` were
  deleted. The table now breaks out on its own inside `renderTable`, so nothing outside
  it knows about widths and there is no state to set on one view and clear on the other.

### The table breakout (Pierre's call, and the CSS rule behind it)
`max-width` CANNOT break an element out of a constrained parent — it only caps. The
table wrapper fills the block element (which the WP block theme constrains by styling
the direct children of the content container), so any larger `max-width` on it simply
never binds. Two ways out, and Pierre picked the second:
1. Put the override on the BLOCK ELEMENT (the thing the theme constrains). Works, but it
   widens everything inside — options row, count, footnotes — all left-justified across
   the extra width. **Pierre rejected this: "everything is left justified on the extra
   width, I don't like."**
2. A REAL breakout on the table wrapper only: `width:1180px; margin-inline:-140px`
   (1180 − 900 = 280, so −140 a side centers the extra room). `margin-inline` is the
   horizontal pair by definition and cannot touch the vertical margins — Pierre asked
   explicitly for that guarantee. The footnotes were moved OUT of the breakout div into
   an outer standard-width div, so only the table itself is wide.

**Known limitation, flagged and not yet addressed:** `width:1180px` is a fixed width, so
on a viewport narrower than ~1180 the table wrapper forces horizontal page scroll — the
old `max-width` version degraded gracefully there. Guard would be a `min()` width or a
media query if it ever matters.

### The problem being solved
`list_browser.jst` today runs three `fetch/.then` chains across three functions — top
level, `showOptions`, `showDataset` — and the same data file is fetched TWICE (two
distinct URLs, three requests). The sequence lives in the nesting, not in anything you
can read top to bottom. `showDataset` also merges load + filter + count + render.
Pierre's standing goal: **easy-to-read code**, which he says most JS fails.

### The agreed shape — four phases, in order
1. **Process/validate request parameters.**
2. **Load data** — `datasets.json`, then the selected dataset's file. Sequential because
   the first names the second; if either fails nothing useful can happen, so error
   handling collapses to one place. Done as nested `fetch/.then` (standard pattern, kept
   in one place) — NOT async/await, the file keeps its current ES5-ish idiom. **Two
   distinct files, two requests** — today it is three requests for those two URLs.
3. **Processing** — all of it, up front. Nothing is gained by sequencing work between
   display calls. Includes filtering AND deriving the keyword list.
4. **Display** — `displayOptionsRow` and `displayDataset` are two different views on
   "all that is known".

### The property bag — `known`
One map owned by the top level, starting empty, accumulating per phase:
- phase 1 adds `params`
- phase 2 adds `datasetList`, `dataset`, `rawRows`
- phase 3 adds `filteredRows` (and the keyword list)

Five properties total. A comment above each phase states what that phase adds; that is
the complete map, and it stays complete because of the read-only rule below.

**Why a bag and not explicit arguments:** the display functions are parallel siblings
with drastically different needs (`displayViewOptions` vs `displayKeywordOptions`). Any
explicit signature serving all of them would just be the union of everyone's needs. The
bag says "I don't know what you need, here is what I know, use what you want." Pierre
uses property bags when they make sense; this is such a case.

### Conventions that make it work
- **Every display function has the same signature: `displayX(known)`.**
- **Unpack at the top.** Each function opens with a `// what I need from what is known`
  block naming the values it uses — this documents dependencies at the point of use,
  better than an argument list does.
- **Phases 1–3 WRITE the bag; phase 4 only READS it.** Reason: display functions are
  meant to be independent views, and if either could add a key the other might see it,
  making their order matter — the same implicit sequencing being removed from the top
  level, one layer down where it is harder to see. Secondary: the phase comments stay a
  complete map of the bag.
- **`known` holds KNOWLEDGE, never DOM, and the display functions are PURE
  `known -> DOM node`.** The block element is a plain local of the renderer; the two
  `el.appendChild(displayX(known))` calls are the only place the page is touched.
  Pierre caught the first version, which put `el` in the bag and let each display
  function append to it: that keeps the LETTER of "display never writes the bag" while
  losing what the rule is FOR, because the options row then has to run before the
  dataset or it lands underneath it — exactly the hidden ordering the phases exist to
  remove. Test to apply: not "does it write the bag" but "could these two run in either
  order".
- **Filter moves OUT of display.** Separate operations. Renderers become pure
  `rows -> DOM node`; the count becomes a plain value at top level.
- **The keyword list is a PROCESSING step, not a display concern.** Derived from
  `rawRows` today, possibly read from the dataset definition later — either way it is
  one function in phase 3. Consequence: `displayKeywordOptions` reads the finished list,
  never `rawRows`, so the later migration touches one processing step and no view. This
  is what reduces todo item 7 (options row shouldn't need the dataset rows) to swapping
  one step's implementation, and it removes `vocabRows` entirely.

### Settled during the discussion, do not re-raise
- Losing the current independence of the options row and the dataset (either fetch
  failing now kills both) — judged a non-issue and dropped.
- `view` being read by both filter and display — dissolved by the bag.
- Property-bag "rot" — answered by five properties plus per-phase comments.

### Related todo items
Refer to `docs/todo.md` items by TEXT, never number — the list gets renumbered and pruned.
Still open and served by this work: the on-demand keyword validation pass.
DELETED 2026-07-26 (dropped by Pierre, not done): the `<details>` light-dismiss, the
`.gl-lb-search` width (already fixed by later style tweaks), and the badges any/all toggle.

**Param validation is DROPPED, 2026-07-27 — do not re-propose it.** Pierre's reasoning:
validation would have to happen in phase 1, where `access`'s vocabulary is known but
`keywords`' is not (it comes from phase 2 data) — and *different handling for the two is
not acceptable*. An invalid value requires hand-typing a URL or following an obsolete
link, and recovery is trivial. His saying for the general case: "if you try hard enough
to fail, you will succeed" — the argument against defending a read-only client-side page.
Also dropped as out of scope for `docs/todo.md`: anything that is content authoring.

**Numbering trap, cost real time on 2026-07-26:** a markdown ordered list written with
non-sequential numbers (`2.` `4.` `5.` …) is RESEQUENCED by the renderer to 2,3,4,5 —
so the numbers Pierre sees are not the numbers in the file, and he rightly answers using
what he was shown. When showing a list whose numbers carry meaning, do not use a markdown
ordered list.

## Refactor record (COMPLETE 2026-07-25)

Kept for the filter semantics and the two-switch pattern. Its "4-step render
model" section is superseded by the four phases above.

Multi-phase refactor (2026-07-23 → 2026-07-25): the destinations-overview page AND
the gallery page were replaced by ONE param-driven page, `list_browser`
(pages/shared/), with two independent axes — display (table/grid) × data — driven
by URL query parameters. **DONE.** Remaining ideas live in `docs/todo.md` — refer to
them by TEXT, not number: the list was renumbered 2026-07-25 and pruned again
2026-07-26, so every number this memory originally cited is dead.

**The 4-step model below was superseded at the TOP LEVEL on 2026-07-26** by a
four-phase + property-bag design — see [docs/rendering/list-browser.md](list-browser.md). The filter
semantics, the two-switch pattern, and the gotcha here all still hold.

### The model — rendering a page is four steps
1. `processParams(location.search)` → `effectiveParams`. The ONE place the raw
   query string becomes what the page acts on. Today it only fills defaults; it is
   the designated home for validation (still an open todo). **Everything** reads the result,
   including `navigate()` — so a default it filled in lands in the next URL. That
   is deliberate and matches the nav menu, which already emits explicit `view=grid`.
2. `filterRows(rows, effectiveParams)` — walk the PARAMS, `switch` on the key, each
   case narrows: `filterX(value, shortList) -> shortList`. Chaining is what makes
   AND across controls; OR within a control is internal to each filter.
3. Options row — walk the dataset's `options` recipe from `datasets.json` (order =
   layout), `switch` on the token, each builder is `build(effectiveParams)`.
4. Render `shortList` (table or grid per `view`) + a `"N found"` count.

### The pattern that matters (Pierre's design, hold onto it)
- **Two switches, related but NOT the same vocabulary.** One option can emit several
  query params (a shortcut preset like "lake camping with van") or none (`viewMode`
  concise/verbose). `view` does both — it displays AND filters.
- **Silence on both sides is correct, never an error.** A token with no builder
  builds nothing; a param with no filter filters nothing. Legitimate states: staged
  rollout (see the control before wiring the filter), under test, retired-but-kept.
  The old `console.error` on an unknown token was REMOVED for this reason.
- **Adding a filter = one function + one line in the switch.** Same for a control.
- **VALUES LIVE IN THE QUERY STRING, NOWHERE ELSE.** An options token is a plain name;
  it never carries a value and the dataset entry never holds one. `options` says a
  control is POSSIBLE for this dataset; the URL says what to do about it. So a builder
  may legitimately return NOTHING — `booklet` renders a download button when
  `?booklet=howto` is present and nothing at all when it isn't, the same way a filter
  applies nothing when its parameter is absent. Pierre rejected both `"booklet=howto"`
  as a token and a `pdf` field on the dataset entry, for the same reason: a second home
  for values breaks the pattern that has been simplifying everything else. **He HATES
  breaking patterns** — check the pattern before reaching for a special case.
- The filter loop is driven by the URL, not by `options`, so a hand-typed or shared
  URL filters even for controls that dataset doesn't display.

### Filter semantics as shipped
- OR within a control, AND across controls. (A badges any/all toggle was designed,
  deferred, and then DROPPED by Pierre on 2026-07-26 — do not resurrect it.)
- `filterView`: `view=grid` keeps `wpSettings.published === true`. Moved OUT of
  renderGrid so the count can't disagree with what you see; both renderers are now
  pure `rows -> DOM node`.
- `filterAccess`: ordinal threshold over `Object.keys(GL.ROAD_COLORS)` (worst road
  you'll accept). **Unknown PASSES** — only the 18 GL pages have authored legs, so
  a strict rule would drop the other 98; an unmeasured road isn't evidence of a bad one.
- `filterKeywords`/`filterBadges`: tag membership; **absence FAILS**. Consequence:
  no catalog row carries badges, so any badge filter narrows to the GL pages.
- `filterSearch`: `JSON.stringify(row)` substring — broad on purpose (sees keys and
  URLs too, so "map" matches every row with a map link).
- Keyword vocabulary is derived client-side from the UNFILTERED rows (`vocabRows`,
  set by showOptions' own fetch). Never pass the filtered list to `fieldVocab` — it
  would delete the choices you need to widen the search next. (The RULE survives the
  top-level rewrite; `vocabRows` itself does not — see [docs/rendering/list-browser.md](list-browser.md).)

### Gotcha
`list_browser.jst` executes BEFORE `gl-constants.jst` defines `window.GL`. Anything
touching `GL` must be inside a function that runs after a fetch — a top-level
`Object.keys(GL.ROAD_COLORS)` throws. Hence `roadOrder()`.

### Stale memories to disregard
Anything referencing `lists/all|known`, gallery GENERATION, flat top-level `badges`,
`destinations-overview` as the live page, or a dataset dropdown (the dataset comes
from the nav menu; the "true filter" idea that would have narrowed such a dropdown
is moot). WP nav menu = one `wp_navigation` post, **id 5**, edited via Appearance →
Editor → Navigation → ⋮ → Edit (the block CODE editor).

Working style during this refactor: Pierre LEADS, one step at a time; a question is
never a go; do exactly the named scope and STOP; park side issues in `docs/todo.md`
instead of raising them inline. Related: `~/Claude/working-with-pierre.md §1`,
`~/Claude/working-with-pierre.md §5`, [docs/projects/schema-unification.md](../projects/schema-unification.md).
