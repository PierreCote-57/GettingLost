# FileBird REST API

## Access

- **Use curl via Bash** — NOT the WP MCP tools. FileBird is not exposed through WP MCP.
- Folders endpoint: `https://gettinglostonvi.wpcomstaging.com/wp-json/filebird/public/v1/folders`
- Auth: a bearer token. **The token is deliberately NOT in this repo** — it lives in
  Claude's `feedback-session-start` memory, since this file is pushed to GitHub.
- **URL first, flags after** — `curl "<url>" -s -H "Authorization: Bearer <token>"`.
  Putting `-s` before the URL breaks the permission allow-rule glob and forces a prompt.
  Piping to anything (`| python3 …`) is a different command string and needs its own rule.
- A healthy response is `{"success":true,"data":{"folders":[…]}}` with the Images (id 52)
  and Data (id 56) roots.
- Vendor docs: https://ninjateam.gitbook.io/filebird/integrations/developer-zone/post-type-folders-api

## Parameter quirks

**Validate every FileBird API call against the docs before writing code** — parameter names are inconsistent across endpoints (e.g. `parent_id` for create folder, `folder` for set-attachment, `folderId` for set-posts). Never assume a parameter name carries over from one endpoint to another.

**Why:** The original sync.js used wrong param names (`folder_id` and `attachment_ids` instead of `folder` and `ids`) for `set-attachment`, causing silent "Validation failed" errors. Fixed 2026-06-30.

**How to apply:** When writing or reviewing any FileBird API call, cross-check param names against the docs at [docs/conventions/site.md](../conventions/site.md). Don't copy param names from one endpoint to another.

---

**FileBird folder lookups must be case-insensitive** — FileBird stores folder names in Title Case (e.g. "Data") but repo paths are lowercase (e.g. "data"). Without `.toLowerCase()` on cache keys, the sync creates duplicate folders like "data (1)".

**Why:** sync.js had case-insensitive lookups for page folders but not media folders, causing duplicates on every sync run. Fixed 2026-06-30.

**How to apply:** Both `loadFileBirdFolderTree` and `ensureFileBirdFolderPath` in sync.js now use `.toLowerCase()` cache keys, matching the page folder pattern. Maintain this if touching either function.
