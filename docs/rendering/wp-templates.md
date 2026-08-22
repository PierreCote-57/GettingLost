# WP template editing

The site runs the **Twenty Twenty-Five** block theme. Page/post structure (header, title, featured image, content, footer, listing query loops) lives in WP **templates**, NOT in the GitHub repo — templates are outside the sync pipeline. Editing them is a one-time WP-side change.

## Editing templates from a session
Use the WordPress.com MCP tool `wpcom-mcp-site-editing` (load via ToolSearch; it's deferred).
- **Site:** `gettinglostonvi.wpcomstaging.com`, blog_id **255518505** (atomic). Find via `wpcom-user-sites`.
- Template id format: `{theme}//{slug}`, e.g. `twentytwentyfive//page`, `twentytwentyfive//single`, `twentytwentyfive//home`, `twentytwentyfive//index`, `twentytwentyfive//archive`, `twentytwentyfive//search`.
- Flow: `action:"execute", operation:"templates.list"` to fetch all (returns full `content.raw` block markup) → edit the raw string → `operation:"templates.update"` with `params:{ id, content:{raw:"..."}, user_confirmed:true }`. `user_confirmed:true` is required for writes (site-wide impact). Reads (`templates.list`/`.get`) are safe.
- **Revert:** any customized template shows **"Clear customizations"** in the Site Editor → snaps back to the theme's original file. Non-destructive.
- Companion tool `wpcom-mcp-site-editor-context` gives theme presets/tokens/allowed blocks.

## Change made 2026-07-04 (featured-image redesign — see [docs/schema/image.md](../schema/image.md))
Removed the top-of-page **`wp:post-featured-image`** block from two templates so pages/posts show no image at the top (title is now first):
- `twentytwentyfive//page` — was `post-featured-image → post-title → post-content`; now `post-title → post-content`.
- `twentytwentyfive//single` — was `post-title → post-featured-image → byline → post-content`; now `post-title → byline → post-content`.
The featured-image blocks inside the **listing query loops** (home/index/archive/search "recent/more posts") were left intact — those still show grid thumbnails from `featured_media`.

## Change made 2026-07-15 (comments block added to Page template — see [docs/schema/wpsettings-comments.md](../schema/wpsettings-comments.md))
Inserted the full `wp:comments` block (comment list, pagination, form — copied verbatim from `twentytwentyfive//single`) after `post-content` in **`twentytwentyfive//page`**, so pages can show comments. `Page No Title` template was left without one. Pairs with the new `wpSettings.comments` field that drives each page's `comment_status` during sync.

## Sitewide script injection lives in the Footer template part (2026-07-08)
The core scripts are injected via a **Custom HTML block at the TOP of the Footer template part** (first child, above the visible footer group) — NOT the repo. Order is load-bearing:
```
<script src="/wp-content/uploads/gl-constants.jst"></script>   (globals — added 2026-07-08)
<script src="/wp-content/uploads/gettinglost.jst"></script>    (core, reads those globals)
```
`gl-constants.jst` MUST stay directly above `gettinglost.jst`. Editing: Site Editor → Patterns → Template Parts → Footer, use LIST VIEW (script-only Custom HTML renders invisibly), or via the site-editing MCP. Per-page scripts (`lakes.jst`, `list_browser.jst`, `maintenance.jst`) are inline `<script>` in the page CONTENT, not the footer — which is why `list_browser.jst` runs BEFORE `gl-constants.jst` defines `window.GL`. All `.jst`/`.cst` upload to `wp-content/uploads` via the sync pipeline. See [docs/schema/map-pins-location.md](../schema/map-pins-location.md).

## Two-up photo row (how the editor adds top images now)
Two side-by-side images in body content: `<div data-block-type="photo" style="width:45%;float:left;" data-img="a.jpg"></div>` + a second with `float:right`, both before the text, then `<div style="clear:both;"></div>` if you don't want following text filling the center gap. It is float-based; renderer at [docs/rendering/blocks.md](blocks.md) / gettinglost.jst `blockRenderers.photo`. **The old `class="gl-photo"` hook is gone** (2026-07-26) — it carried no CSS and nothing reads it any more, so a div still carrying it renders nothing.
