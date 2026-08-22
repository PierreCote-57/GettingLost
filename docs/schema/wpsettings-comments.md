# wpSettings and comments

Added 2026-07-15. Consolidates per-page WordPress settings into one JSON block and turns comments on for pages.

## Schema — `wpSettings` (replaces top-level `published`)
Every page/post data file carries:
```json
"wpSettings": { "published": true, "comments": "open" }
```
- `published`: boolean → WP status (`true`→publish, `false`→draft). Absent → sync leaves status unset, create falls back to draft.
- `comments`: **string** `"open"` | `"closed"` (WP's own `comment_status` value, passed through). **Default when absent = "open"** — only an explicit `"closed"` turns comments off.
- Migrated every page/post JSON on 2026-07-15 (format-preserving inline swap). Which pages carry `"closed"` is data — grep `media/data` for it rather than reading a list here.

## Sync behaviour (`local/sync/sync.js`)
- Helpers `wpStatusFromData()` / `wpCommentStatusFromData()` read the block.
- `comment_status` is asserted on **every create AND update** for both pages and posts (GitHub-master, same pattern as `featured_media`) — so closing comments on a page in WP by hand gets reverted on next sync; the JSON is the only place to set it.
- The old hardcodes (create page→"closed", create post→"open") were removed.
- Gallery + PageMap "is it published?" filters now use `wpStatusFromData(data) !== "publish"`.
- `local/sync/pull-posts.js` writes `wpSettings: { published, comments }` on pull (comments mirrored from WP `comment_status`), so round-trips keep the new shape.

## Display side — comments block in the Page template
Enabling `comment_status` alone renders nothing in a block theme: the **template** must contain a `wp:comments` block. On 2026-07-15 the full comments block (comment list, pagination, form — copied verbatim from `twentytwentyfive//single`) was inserted after `post-content` in the **`twentytwentyfive//page`** template via the site-editing MCP. `Page No Title` template was NOT given one. See [docs/rendering/wp-templates.md](../rendering/wp-templates.md).

Related: [docs/projects/destinations-overview.md](../projects/destinations-overview.md), [docs/conventions/site.md](../conventions/site.md), [docs/conventions/github-workflow.md](../conventions/github-workflow.md).
