## Masters

| Component | Master |
|---|---|
| Page HTML | GitHub (`pages/`) |
| Media data (JSON/JST) | GitHub (`media/data/`) |
| Logs (travel, locations, fuel) | GitHub (`logs/`) — synced to WP, see [../projects/logs-travel.md](../projects/logs-travel.md) |
| Media images | **Pierre** — the image half of the WP media library is his, no external master |
| Page metadata (featured image, WP template, slug, status) | WordPress |
| Navigation/menus | WordPress |

**Key principle:** WordPress is the objective/destination, not the master of content. Only page metadata and navigation live there as master. Everything else has an external master that gets pushed in.

**WP template** (which layout a page uses) is page metadata — mastered in WordPress, never touched by sync.js.

## Folder Structure (IMPLEMENTED 2026-06-30)

The locations that mirror each other:

```
pages/                              ← GitHub, page HTML
media/data/                         ← GitHub, page JSON data
FileBird Data/                      ← WordPress media library, synced from media/data/
FileBird Images/                    ← WordPress media library, PIERRE'S (see below)
~/Pictures/GettingLost/Images/      ← Pierre's utility folder, not a master and not a mirror
```

**The tree itself is not written out here** — `ls` it. A copy in markdown is a cache of the
disk with nothing to invalidate it, and it went stale on every page added
([../README.md](../README.md), "These files are not a cache of the repo"). The rules that
are *not* on the disk:

- `media/data/` mirrors `pages/` one folder per page, plus `scripts/` (data-only, no pages
  or images) and `posts/`, peer of `pages/`.
- `shared/gallery/` exists in WordPress only — sync writes the generated `PageMap.json`
  there and nothing in the repo mirrors it.
- Structure mirrors the menu hierarchy at every level.
- Folder names are practical identifiers, not display labels.
- Folder names are case-insensitive; lowercase in GitHub/local, mixed case in FileBird per
  Pierre's taste.
- An empty folder is legitimate — it is scaffolding for something not built yet.

## WP Media Top Level
Three roots: `Images/`, `Data/` and `logs/` — peers.

## Working Model
- Claude makes file changes locally; Pierre reviews and pushes to GitHub
- Claude handles FileBird page folder assignment via post-type API; Pierre validates visually in WP Admin
- FileBird media folder (`set-attachment`) API broken — media folder assignment is manual in WP Admin

### Images are Pierre's (2026-08-07)
**The image portion of WP media belongs to Pierre.** It has no external master, it is not
reconciled against anything, and its folder layout is his to decide. `~/Pictures/GettingLost/`
is a utility folder he keeps for his own convenience — practical for storing some images,
never intended as the GitHub-side master.

Claude's whole job with images is **on demand**: verify a file the site references is present
and findable, and handle ad-hoc requests (crop, retouch, locate, rename on request — see
[recipes/image-editing.md](../recipes/image-editing.md)). Do not audit the image tree, do not
diff it against anything, do not propose renames or a reorganization, and do not report drift
as a finding. This cancelled todo #14, a FileBird↔local reconciliation built on the wrong
premise.

## Lake ID Mapping

Not tabulated here — it is derivable, and a copy goes stale as lakes are added.

- **id → page:** each lake's own JSON carries it, at
  `media/data/destinations/lakes/<name>/<name>.json` → `fishingReferences.bcIdentifier`.
- **id → source images:** `~/Working/Fishing/Images/<id>/`, when the folder exists — many
  lakes have none. `ls` it rather than assuming either way.

## FileBird folder ids are NEVER stored here (Pierre, 2026-08-09)

**A FileBird folder id is read from WordPress at the moment it is needed, never written
down in this repo.** WordPress is the master of that tree: ids change when a folder is
recreated, and a number committed to GitHub cannot announce that it went stale — it just
sits there being wrong until something is filed into the wrong folder. Assume any id you
remember has changed underneath you.

The same goes for the shape of either tree, Data or Images. Neither is recorded here; walk
`GET /folders` or `GET /post-type-folders/?post_type=page` and read what is actually there.
The **endpoint list** is in [site.md](site.md); how to reach the API — auth, curl form, the
param quirks — is in [../reference/filebird-api.md](../reference/filebird-api.md).

What is not an id, and so does belong here:

- **Three media roots** — `Images/`, `Data/` and `logs/`, peers. `Data/` mirrors
  `media/data/`; `logs/` is written by `syncLogs` from the repo's `logs/` tree
  ([../projects/logs-travel.md](../projects/logs-travel.md)); `Images/` is Pierre's (above).
- **There is no "read folder contents" endpoint for post-type folders**, so page-folder
  filing is validated visually in WP Admin.
- **The media `set-attachment` endpoint is broken** — returns "Validation failed" whatever
  the params or auth — so media folder assignment is manual in WP Admin.

The 2026-06-30 Data snapshot that used to sit here was deleted 2026-08-09, along with the
root ids in `site.md`. It had already rotted: it still showed `instructions/`,
`howto-shower/` and `park-template/`, none of which have existed for weeks. The Images
snapshot went the same way on 2026-08-07 when the reconciliation it supported was cancelled.
