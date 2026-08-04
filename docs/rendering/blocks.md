# Block rendering

> **PARTLY STALE (2026-07-20 schema unification) — see [docs/projects/schema-unification.md](../projects/schema-unification.md) for current shapes.** Changed since: new shared `linkRow` + `onLostHref` and a new `links` block renderer; the `notes` renderer resolves scheme-less `*.html` urls to internal pages; the lake `destinations` renderer + block are RETIRED (folded into a `notes` "Destinations" section). The dispatch/registry/filename-master mechanics below are still accurate.
>
> **Links changed again on 2026-08-01:** `campground.links` was merged up into one flat `links[]`, and a closed `type` (`homepage` / `map` / `reservation`, optional) replaced the label as the key every renderer selects by. The `OnLost` *label* is gone — a page on this site is signalled by the presence of `file`. [docs/schema/links.md](../schema/links.md) is current; the `campground` entry below is rewritten, the `links` sections in schema-unification.md are not.

## THE INVARIANT (established 2026-07-26 — Pierre's rule)
**Everything a script puts on a page goes through ONE path: `[data-block-type]`.** There is no second, class-driven mechanism. `init()` is now exactly `injectGettingLostCss()` + `initBlocks()` — the CSS is the only non-block, because it has no element to hang off.

Pierre's diagnosis, worth keeping: **load-order problems are a SYMPTOM of pattern breaks.** Two breaks existed and both are fixed — (1) `init()` ran its own `querySelectorAll` loops for `.gl-photo` / `.gl-featured` / `.gl-checklist`, (2) `list_browser.jst` executed its work on load instead of registering a renderer. "Follow the pattern" made the load-order question disappear rather than be worked around.

**A script that registers instead of executing is order-independent.** `list_browser.jst` and `lakes.jst` are plain `<script src>` in the page BODY, so they execute BEFORE `gl-constants.jst` and `gettinglost.jst` (Footer template). They survive by (a) creating the registry defensively — `window.GL = window.GL || {}; window.GL.blockRenderers = window.GL.blockRenderers || {};` — and (b) only ever touching `window.GL` from inside a renderer, which `renderBlocks()` calls long after both footer scripts have run. Never move a `GL.*` read to execute time in those files.

## Overview
`gettinglost.jst` is loaded sitewide via the Footer template (with `gl-constants.jst` loaded on the line ABOVE it — sitewide ALL-CAPS constants: `GL.PIN_ICONS`/`TAG_COLORS`/`TAG_FALLBACK`/`MAP_CONFIG`; see [docs/schema/map-pins-location.md](../schema/map-pins-location.md)). Registry: `window.GL.blockRenderers`. Any `<div data-block-type="X">` is rendered once the page's data JSON loads (the page derives its `<base>.json` from its URL slug — see "Filename is master" below). Zero blocks on a page = no fetch at all. Unregistered type or thrown error = that block skipped + console-logged, others unaffected.

## Render what's there — don't second-guess the author

A renderer or parser renders **the content of the block as-is**, whatever it is:
table→table, image→image, list→list, `<details>`→heading + contents. Walk the section's
children in order and dispatch by tag. Do **not** hunt for one expected shape — the old
`for h3 … find_next_sibling("ol")` pattern in the booklet builder is the anti-example — and
silently drop everything else.

Content and its structure are the **author's responsibility**. An empty or malformed block
is the author's problem; the renderer still renders what's there (empty block → title only).
No special-casing for structures you imagine the author *should* have used, no scoping
things out on your own judgment, no editorializing about their content choices. Pierre spent
an hour on this while "what if the structure is X" caveats kept coming; it is
over-complicating, not thoroughness.

Applies to the booklet PDF builder as much as the page renderers — see
[docs/projects/checklists-booklet.md](../projects/checklists-booklet.md).

## Console Logging Convention
- `console.error` / throw = genuine broken reference a visitor could hit
- `console.warn` = present but incomplete (to-do flag, nothing broken)
- Fully silent = top-level JSON key simply absent — valid deliberate state
Apply this same test when adding any new validation logic.

## Filename is master (2026-07-08) — full model in [docs/conventions/site.md](../conventions/site.md)
The github filename is the master; a slug is ALWAYS derived, never authored or stored as truth. Two inverse transforms exist byte-identically in BOTH `sync.js` and `gettinglost.jst`:
- `fileToSlug(filename)` = replace last `.`→`_`, then WP-sanitise. `amor-lake.html` → `amor-lake_html`.
- `slugToFilename(slug)` = replace last `_`→`.`. `amor-lake_html` → `amor-lake.html`.

Block-rendering implications:
- A page loads its own data by reversing its URL slug: `slugToFilename(urlSlug)` → base → fetch `<base>.json` (`fetchPageData`).
- Gallery / `featured`-block entries carry **`file`** (the page filename), NOT `slug`; `renderCard` builds `href = "/" + fileToSlug(entry.file) + "/"`.
- `PageMap.json` is keyed by page **filename** (`amor-lake.html`), value `{title}`.
- Authors reference other pages/files by FILENAME (`data-file`, references `file`) — never a slug. `window.GL.fileToSlug` is exposed so lakes.jst (and any consumer) derives slugs identically.

## Generic Renderers

**tags** (2026-08-01) — the destination's own vocabularies, **first on the page**, above the campground row: identity, then actions. Block `<div data-block-type="tags"></div>`, on all 18 destination pages and both templates.
- **badges LEFT, road badge RIGHT** on one line (`justify-content: space-between`), **keywords BELOW** on their own line. Left and right are different KINDS of fact — what you would do there vs what it costs you to get there — so they read as two things rather than one row. Keywords sit under because they are the OPEN vocabulary: most numerous, least authoritative, and the only one that grows without warning.
- **The road badge carries a distance**: every leg OF THE BADGE'S TYPE, summed (`roadBadgeKm`). Legs `[potholes 3, dirt 5, potholes 2, dirt 1]` → **potholes 5 km** — worst type wins the badge, and all of that type counts even though the last leg is dirt. `pavement` has no legs so it gets no distance; `back_country` sums the non-drive legs, i.e. how far you are not in the van. The km is plain grey text, not a pill — it is a measurement, not a vocabulary word.
- **`tags.types` is deliberately absent.** It filters; the page already says what kind of place it is (Pierre, 2026-08-01).
- Keywords render black-on-white (`.gl-tag.gl-plain`) — a vocabulary with no colour of its own, where `TAG_FALLBACK`'s grey would read as "unknown value" rather than "no colour".
- **Same pill as the gallery cards.** `renderTags`/`renderRoad` gained an optional wrapper/class argument, so the cards keep their absolutely-positioned corner stack and the page gets a plain inline group — one pill definition, two layouts, no drift.
- Renders **nothing at all** when there is nothing to say, rather than an empty band.

**campground** (CURRENT, 2026-08-01) — the logistics row rendered right **under the page title** (standardized top-of-page slot), one `· `-separated line selected **by `links[].type`**, never by label: **Website · every map · every reservation**. See [docs/schema/links.md](../schema/links.md); `campground.links` no longer exists, everything lives in one flat `links[]`.
- **Website** = the `type: "homepage"` entry (displayed "Website"); the place's official page (BC Parks etc.). Do NOT also duplicate in Further readings.
- **maps** = every `type: "map"` entry, each shown under its own label (an external gov PDF URL is fine here — this is where a map belongs, not Further readings). A park map and a campground map differ: park map = whole-park view (boundary, trails, day-use); campground map = campsite loops/numbered sites for booking. The label follows what the PDF depicts — `Campground`, `Park`, `Trail`. **All of them render**; the old exact-label lookup showed only the campground one, so five destinations had a second map that appeared in the list browser and never on their own page.
- **reservations** = every `type: "reservation"` entry — a pre-populated booking URL (camping.bcparks.ca `create-booking/results?resourceLocationId=…`). Trim ephemeral params (transactionLocationId/startDate/endDate/searchTime/flexibleSearch); keep the stable ones. `subEquipmentId=-32765` = Van/Camper.
An **untyped** link is a general link for the `links` block, not part of this row. Reservation status with no booking url is not a link at all — it lives in a `Reservation notes` notes section.

**googleMap** — MERGED renderer (2026-07-21; `googleRoadMap` deleted, folded in). One renderer, mode chosen by the div's `data-map` attribute (like `photoGallery`'s `data-gallery`); a page can carry MULTIPLE maps.
- **No `data-map`** → single plain marker synthesized from `pageData.location = {lat,lng,pin,zoom?}` (icon via `pinIcon()`/`GL.PIN_ICONS`, unknown/absent→default pin; hover title from `name`). The ~25 single-marker pages are untouched.
- **`data-map="road"`** → `pageData.googleMap.road = {lat?, lng?, zoom?, pins}`. `lat`/`lng` are **flat peers** (Pierre: "lat/lng/zoom should be peers" — NOT a nested `center`), fall back to `location`; `zoom`→`MAP_CONFIG.mapZoom`. NO reserved "default" map name (scrapped as klunky).
- **Unified pin** `{pin?, label?, img?, lat, lng}` (lat/lng required; `id` DROPPED): `img` with `/` = `"galleryKey/itemId"` gallery ref (pulls img via `formatImageUrl(img,320,240)` + label); without `/` = direct file. `pin`→icon else default; resolved `img`→click InfoWindow (label in `setHeaderContent` — the `.gm-style-iw-ch` header reserves blank space otherwise); label-only→hover `title`; neither→plain marker. label chain: `pin.label`→gallery label→the `img` string→none. Pins missing numeric lat/lng skipped.
- **Live center/zoom caption** under EVERY map (no width gate): centered `<div>` wired to the map's `idle` event, `Center = (lat, lng) · Zoom = n`, 6-decimal. Authoring aid to dial in lat/lng/zoom; "public for now, hide later." `location` stays top-level (overview reads it — see [docs/schema/map-pins-location.md](../schema/map-pins-location.md)).
- **The block div is a WRAPPER; the map and the caption are both children of it** (fixed 2026-08-01). The caption used to be a *sibling* inserted `afterend`, faking containment by copying the map's inline `float` and `width` onto itself. That only held while those two properties described the layout — with `float:none` and a pixel width (the `<details>` road maps) the caption went back to the main column at full page width, under nothing. Now the authored inline styles stay on the wrapper, the height moves to the inner map div, and the wrapper's height goes `auto` so it grows to fit the caption. The caption is as wide as the map because it is *in* the map's box.
- `google.maps.Marker` now emits a **deprecation console warning** (→AdvancedMarkerElement); parked — needs a Map ID + kills inline `mapStyles`.

**Map size/float/margin are overridable defaults** — the renderer sets width `45%` / height `400px` / float `right` / margin only via `if (!el.style.X)` guards, so any per-page override is just inline `style` on the block div. Don't add `data-width`/`data-height` — inline `style` IS the per-block definition and wins. Legal `float`: left / right / none. (Merged renderer's single default float is `right`; the old googleRoadMap defaulted left — the road divs set `float:none` inline so no visual change.)

**Map inside a `<details>` (Pierre's road-map pattern)** — collapsed by default, full width, no float, taller:
```html
<details>
  <summary><h2 style="display:inline;">Road map</h2></summary>
  <div data-block-type="googleMap" data-map="road" style="width:100%;height:600px;float:none;"></div>
</details>
```
(`h2 display:inline` sits it on the summary row.) CAVEAT confirmed 2026-07-21: a map initialized inside a *closed* `<details>` inits **0×0**, so it never fires `idle` → the live caption stays frozen and tiles may not draw until a resize. The block renderer runs at page load regardless of details state. If it bites, recenter + `google.maps.event.trigger(map,"resize")` on the details `toggle` event. (Not yet worked around — accepted for now.)

**notes** — `pageData.notes = [{sectionName, list: [{name, url|file, description:[...]}]}]` → heading + 2-col table per section. Each item is an **internal** link when it has `file` (a page filename → same-tab, href via `fileToSlug`), an **external** link when it has `url` (new tab), else plain text. "Further reading" is just a `notes` section (`sectionName:"Further readings"`). `furtherReading` renderer is fully retired and replaced by this.
- **`description` is HTML, not text** (2026-08-03): the joined strings go in via `innerHTML`. Write `<b>`, `<a>`, or a block span straight into the JSON — author is author, no escaping and no markup vocabulary. `name` is still plain text (it's the link label). An invalid tag renders as the browser sees fit; that's the author's problem, not the renderer's.
- Because it's HTML, a `description` can carry a **block** — `<span data-block-type="photoRef" data-id="key/id"></span>` is the intended case. It renders on the dispatcher's next pass, identically to one written in the page HTML. Nothing about nesting is special-cased.

**pageLink** — inline cross-page link: `<span data-block-type="pageLink" data-file="foo.html">fallback</span>`. `data-file` = target page's FILENAME (was `data-slug="foo"` pre-2026-07-08). Title from `PageMap[data-file]`; `href = "/" + fileToSlug(data-file) + "/"`; falls back to element text if not in PageMap.

**backToGallery** — REWRITTEN AGAIN 2026-07-26: now takes **NO attributes at all** and reads no pageData. `data-dataset` was removed from all 29 pages/templates — do not re-add it. The link is derived from where the visitor came from: if `document.referrer` is same-origin AND its path is the list_browser page, the referrer IS the href verbatim (so dataset, view and every filter come back with them) and its `view` picks the label from a whitelist map (`grid`→"Back to gallery", `table`→"Back to list view"). Anything else — no referrer, off-site, or another GL page — falls back to "← Back to destination gallery" → `?dataset=destinations&view=grid`, deliberately the site's front door regardless of which page the visitor landed on. Label literals always come from the map, never from referrer text; the referrer URL reaches the href escaped. Page URL still DERIVED via `fileToSlug("list_browser.html")` → `/list_browser_html/`. See [docs/rendering/list-browser.md](list-browser.md).

**photo / featured / checklist** — converted from class hooks to block renderers 2026-07-26 (see THE INVARIANT above). All three take only the element and read no pageData.
- `photo` (was `.gl-photo`): `<div data-block-type="photo" data-img="…" style="width:25%;float:left;" data-lat data-lng>`. The class is GONE — it carried no CSS, it was only a JS hook.
- `featured` (was `.gl-featured`): `<div data-block-type="featured" data-count="3">`. Class gone, same reason.
- `checklist` (was `.gl-checklist` / `.gl-numcheck`): `<ol class="gl-numcheck" data-block-type="checklist">`. **The class STAYS** — unlike the other two it carries real CSS (checkbox rows, the numbering counter) and it also selects the variant (`classList.contains("gl-numcheck")`). One block type with two looks, not two block types.
- Timing change accepted: these now render after the page-data fetch instead of at DOMContentLoaded, same as every other block.

**list_browser** (in `list_browser.jst`, 2026-07-26) — `<div data-block-type="list_browser"></div>` is the ENTIRE page markup. The renderer creates the two divs it fills (controls, then data) inside its own element, so the HTML carries no structure the renderer must find. Takes no attributes, reads no pageData — the whole state is the URL.

**warning** — fully attribute-driven: `<div data-block-type="warning" data-text="..." data-label="Warning"></div>` → amber callout box with ⚠ icon. `data-label` optional (e.g. "Caution"/"Note"). `data-text` required or throws. First used on howto-awning Instructions section.

**photoGallery** — `pageData.photoGalleries = {key: {name, items: [{id, img, label}]}}`. Block: `<div data-block-type="photoGallery" data-gallery="key"></div>` → thumbnail grid with `name` as h3 heading. Empty `items: []` is valid — renders heading with no photos. Optional `data-collapsible="true"` (default false) wraps the whole mini-gallery in a `<details>` with `name` as the `<summary>` heading — the renderer owns the wrapper, so no duplicate-heading problem. Added 2026-07-04; first used on van-overview "Listing pictures".

**Lightbox (shared pop-up viewer)** — clicking a gallery thumbnail OR an inline `photo` block now opens a shared in-page overlay (built once, lazily; `var lightbox` IIFE in gettinglost.jst) instead of a new tab. Backdrop/✕/Esc close; ←/→ + prev/next buttons + "n / total" counter page through the whole mini-gallery (single image for a `photo` block). Anchors keep their `href` + `target=_blank` as a no-JS fallback; click handlers `preventDefault()` only when it opens. Right-click still gives native open/save. Sizing gotcha (fixed 2026-07): the overlay image is a flex item in a `flex-direction:column` figure, so it needs **`min-height: 0`** (on both figure and img) or `max-height:75vh` won't bind and tall/portrait images balloon + clip at top. Z-index gotcha (fixed 2026-07): overlay must be **`z-index: 100000`** (> WP admin bar's 99999) or, for logged-in users, the admin bar covers the top ✕/counter. Any future full-screen overlay on this site has the same constraint. `src` still flows through `formatImageUrl` — the resize seam.

**photoRef** — inline: `<span data-block-type="photoRef" data-id="key/id"></span>` → `<a href="#gl-photo-key-id">{label}</a>`. Label always pulled live from JSON — renaming a caption never requires touching inline text. Valid in a `notes` `description` as well as in page HTML.

## Dispatch: blocks can contain blocks (2026-08-03)
`renderBlocks` **repeats** until no `[data-block-type]` elements are left, max 3 passes then a console.error naming the leftover types. Why it has to: `querySelectorAll` returns a *static* NodeList — a snapshot — so elements a renderer creates (a photoRef span written into a notes description) were never in the list the loop is walking. Re-query, don't reorder: a type-priority order over one snapshot cannot see elements that do not exist yet.
- The dispatcher **removes `data-block-type`** from each element as it processes it, *before* calling the renderer. That is what makes the re-query return only unprocessed blocks. Renderers FILL their element (`el.textContent = ""` + append, or `el.innerHTML =`), they never replace it, so the wrapper and its author-supplied `style`/`class`/`data-*` inputs survive — only the routing attribute goes. Removing before the call also stops a throwing renderer being retried every pass.
- The attribute is dispatcher-private: no CSS selector and no other script reads it (verified 2026-08-03). Cost of removing it is only that DevTools no longer shows which renderer produced a given div.
- Nesting needs nothing from the renderer that emits the block, and nothing from the one that consumes it. Don't add per-type ordering.

## photoGalleries Design Decisions
- `galleryKey` is for lookup only; `name` is the freely-editable display heading
- `id` is a stable slug, only needs to be unique within its own mini-gallery (not page-wide)
- Same photo filename can appear in multiple mini-galleries under different ids/labels — intended duplication, not a workaround
- No backward-compat fallback — every photoGallery block requires `data-gallery`, every photoRef requires a valid "gallery/id" `data-id`

## STANDING PRACTICE
Before delivering any page using photoRef/photoGallery, validate every gallery key + id against the JSON and report results. Pierre's framing: "equivalent of a dead link."
**Scan the JSON too, not just the page HTML** (2026-08-03): a photoRef can now live inside a `notes` `description`, so grep the page's `.json` for `data-block-type` alongside the `.html`.

## How-To naming split (renamed from "instructions" 2026-07-04)
The van how-to section lives at `pages/van/howto/` + `media/data/van/howto/` (was `van/instructions/`). Two distinct casings, don't conflate:
- **`howto` (lowercase) = the machine token** — folder names, `data-howto-section="howto"`, `data-gallery="howto"`, the `photoGalleries` key, and the `data-id="howto/…"` half of photoRefs. HTML `data-gallery`/`data-id` must match the JSON `photoGalleries` key per page or the block throws.
- **"How to" (display) = the human label** — the WP nav item under *The Van*, and the `title` of the `van-howto` dataset in `datasets.json`. (The old `backToGallery data-title="How to"` is gone; the label is static now. Historical trap worth remembering: a find/replace once lowercased that label and shipped "Back to howto".)

## How-To Page Structure Convention
1. Always-visible "How to" section (`data-howto-section="howto"`)
2. Collapsed `<details>` → "The details"
3. Collapsed `<details>` → "Supplier documentation" (wraps the `notes` block)
4. `<br/>` + `backToGallery`

`<ol>` preferred over `<ul>` for steps.

Sitewide CSS: `ul/ol` have no top margin; `[data-howto-section]` has 2.5rem bottom margin.

## Interactive checklist list-styles (the "checklist" block renderer + gettinglost.cst)
The `checklist` block renderer (gettinglost.jst; was the standalone `enhanceChecklist()` until 2026-07-26) wraps each bare `<li>`'s content so the whole row toggles a checkbox; authors write only plain `<li>` lines. Three authoring styles:
- **`<ol>` / `<ul>` plain** — native numbers/bullets, no interaction.
- **`.gl-checklist`** — `<li>` → `<label><input type=checkbox><span>text</span></label>`. On check: text strike-through + dim (`#999`). (A common to-do-app convention I applied by choice, not a project spec — Pierre asked once why it dims; answer is "done item de-emphasized"; he chose to keep it.)
- **`.gl-numcheck`** (added 2026-07-17) — checkbox, then an auto-number, then text (order: ☐ 1. text). The renderer inserts an empty `<span class="gl-num">` between checkbox and text; the digit is a CSS counter (`ol.gl-numcheck{counter-reset:gl-numcheck}` / `li{counter-increment}` / `.gl-num::before{content:counter(gl-numcheck) "."}`), so numbering stays automatic and **each `<ol class="gl-numcheck">` restarts at 1** (per-list; no cross-list continuation). On check: the text span strikes+dims (`input:checked ~ span:not(.gl-num)`), the number stays solid. Flat lists only. NOTE: a "named groups" variant (`data-seq="foo"` → same name continues 1,2,3 across separate `<ol>`s, different name restarts, via JS-assigned numbers instead of the CSS counter) was designed and **declined** in favour of the simple per-list version — revisit that design if cross-list continuation is ever wanted.

## Gallery Card Tag Badges (Phase 3A — done 2026-07-01)
- `renderCard()` in gettinglost.jst renders colored pills over the card image, upper-right corner, stacking down
- Tags sorted alphabetically, packed (no empty slots for missing tags)
- Color map in `TAG_COLORS`: camping=teal/green, fishing=blue, hiking=coral, picnic=amber (TAG_COLORS/TAG_FALLBACK MOVED to `gl-constants.jst` 2026-07-08 — see [docs/schema/map-pins-location.md](../schema/map-pins-location.md))
- Unknown tags fall back to gray (`TAG_FALLBACK`)
- Pills have semi-transparent background (0.88 opacity), white semi-transparent border, 10px border-radius
- `renderCard` is exposed as `window.GL.renderCard`, shared by list_browser.jst's grid view and `featured` blocks (home page etc.)
- Current tags in use: camping, fishing, hiking, picnic

## Image resizing via Jetpack Photon (implemented 2026-07-03, in working tree pending push)
`formatImageUrl(img, w, h)` in gettinglost.jst returns `https://i0.wp.com/{location.host}/wp-content/uploads/{img}?fit={w},{h}&quality=80`. `fit`=contain (no crop), w/h default 1920. sync.js copy NOT changed (lookup key). Full rationale: [docs/schema/image.md](../schema/image.md).
- **Callers & sizes:** gallery card (renderCard) `600,400`; custom `photo` block inline `480,480`; mini-gallery thumb `360,220`; anything feeding the lightbox `1920,1920`.
- **Two DUAL-WINDOW callers** feed an on-page image AND the lightbox from what was one URL, so each was split into two `formatImageUrl` calls: (1) the `photo` renderer → `displaySrc` (480) for `<img>`, `fullSrc` (1920) for `<a href>`+lightbox; (2) photoGallery renderer → `thumbSrc` (360×220) for the grid `<img>`, full-size `entries[].src` (1920) for lightbox + href fallback. The no-JS `<a href>` fallback always points at the full-size image.
- quality=80 cuts the 1920 lightbox ~876KB→651KB; 72→542KB, 60→440KB if smaller wanted (change the constant in formatImageUrl).
- WP featured image is theme-rendered + already Photon'd by Jetpack srcset — separate, not our code.

## Gallery Card Image Fit (decided 2026-07-03)
- `.gl-gallery-card-img` (main gallery cards, ~line 190) uses **`object-fit: contain`**, NOT `cover` — deliberate. Cards are `width:100% × height:200px`; `contain` shows the WHOLE image uncropped, letterboxing off-ratio images (e.g. Gosling's portrait `ActiveWorksite.jpg`) with transparent gutters that reveal the page background. Chosen over `cover` because Pierre would rather see full images than crop portraits. Do NOT "fix" back to `cover`.
- The 110px small-card variant (~line 250) stays `cover`; lightbox (~line 338) is `contain`.
- `object-position` is the lever if a specific card ever needs its crop/placement nudged.

## lakes.jst
Lake-specific, loaded via inline `<script src>` (not footer), so it runs before gettinglost.jst's render. Adds ONE renderer: **`fishingReferences`**. Its old private `buildHeading` duplicate was deleted 2026-07-04 — now calls `window.GL.buildGlHeading` (safe: its renderers fire during gettinglost's render pass, after GL is set up). `buildReferencesCell` supports internal `file` (same-tab, via `window.GL.fileToSlug`) vs external `url` (new tab) — same convention as `notes` (2026-07-08).

**The `destinations` renderer is RETIRED** (2026-07-20 schema unification; verified against the live site 2026-08-01). It read `pageData.destinations` and drew a Name / Type / References table; a lake's nearby places are now a **`notes` section named "Destinations"**, rendered by the generic notes renderer as `{name, url, description}` entries. Nothing registers the renderer and no page carries `<div data-block-type="destinations">` — do not author one. It had itself replaced `recSites` (2026-07-18), and its removed **ID (`recId`)**, **Site map (`siteMap`)** and **Reservation (`reservationUrl`/`reservationLabel`)** columns may still sit in some lake JSONs as now-ignored data; when one held a useful link (e.g. keogh's letscamp reservation), move it into that lake page's `notes` Further readings. The campground/reservation *details* for a nearby place live on that place's own page, not in the lake's list.

## CSS delivery — external gettinglost.cst (2026-07-04)
Sitewide CSS moved OUT of the inline `<style>` string in gettinglost.jst into a real stylesheet `media/data/scripts/gettinglost.cst`. Loaded by `injectGettingLostCss()` (renamed from `injectGalleryCss`): it `fetch()`es the .cst as text and injects it into a `<style>` tag. fetch ignores Content-Type, so the file's served MIME is irrelevant — sidesteps the browser's strict-mode `text/css` requirement for `<link>` entirely (that requirement is standards-mode/DOCTYPE-driven, enforced by the browser, not WP). Extension is `.cst` NOT `.css` — the allowed-through-the-pipeline trick, same reason scripts are `.jst`. `sync.js` now syncs `.cst` (added to the file filter, `guessMimeFromExt`→`text/css`, and the title-strip regex). One-time FOUC (a fetch after the JST runs) accepted — for-fun site. Pierre moves/renames files manually during tests; ask him to delete/move rather than running clever scripts.

## Shared heading — .gl-heading + window.GL.buildGlHeading (2026-07-04)
One heading definition. `.gl-heading` CSS lives in gettinglost.cst. `buildGlHeading` (gettinglost.jst) now just sets `className="gl-heading"` (no inline styles) and is exposed on `window.GL.buildGlHeading` so lakes.jst and the block renderers all produce the identical bordered section heading. Authored HTML that wants that style uses `<h3 class="gl-heading">`. Howto/checklist SUB-headings deliberately left on the theme default (author's call) — gl-heading = "section", not sub-section. Also added: `summary:focus:not(:focus-visible) { outline: none }` (drops the click focus box, keeps keyboard Tab ring).
