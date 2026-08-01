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

**Parameter names are inconsistent across endpoints and do not carry over.** The folder id is
`parent_id` when creating a folder, `folder` for `set-attachment`, and `folderId` for
`set-posts`. Check the name against the endpoint list in
[docs/conventions/site.md](../conventions/site.md) before writing the call — a wrong name
returns a "Validation failed" that says nothing about which parameter it disliked. `sync.js`
sent `folder_id` and `attachment_ids` to `set-attachment` for exactly that reason until
2026-06-30.

## Folder lookups are case-insensitive

FileBird stores folder names in Title Case ("Data"); repo paths are lowercase ("data"). Both
`loadFileBirdFolderTree` and `ensureFileBirdFolderPath` in `sync.js` key their caches on
`.toLowerCase()`, so a repo path matches the folder that already exists. Without it the sync
creates a duplicate — "data (1)" — on every run, which is what media folders did until
2026-06-30; page folders had the lowercasing from the start.
