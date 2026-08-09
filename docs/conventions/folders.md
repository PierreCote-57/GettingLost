## Masters

| Component | Master |
|---|---|
| Page HTML | GitHub (`pages/`) |
| Media data (JSON/JST) | GitHub (`media/data/`) |
| Media images | **Pierre** — the image half of the WP media library is his, no external master |
| Page metadata (featured image, WP template, slug, status) | WordPress |
| Navigation/menus | WordPress |

**Key principle:** WordPress is the objective/destination, not the master of content. Only page metadata and navigation live there as master. Everything else has an external master that gets pushed in.

**WP template** (which layout a page uses) is page metadata — mastered in WordPress, never touched by sync.js.

## Folder Structure (IMPLEMENTED 2026-06-30)

These locations follow the same hierarchy:

```
pages/                              ← GitHub, page HTML
media/data/                         ← GitHub, page JSON data
FileBird Data/                      ← WordPress media library, synced from media/data/
FileBird Images/                    ← WordPress media library, PIERRE'S (see below)
~/Pictures/GettingLost/Images/      ← Pierre's utility folder, not a master and not a mirror
```

```
about/
  about/
  logging/
  useful-contacts/
  useful-links/
destinations/                       ← refreshed from the repo 2026-08-02
  campgrounds/
    pacific-playgrounds-resort/
    salmon-point-resort/
  lakes/
    amor-lake/
    beavertail-lake/
    brewster-lake/
    echo-lake/
    gosling-lake/
    keogh-lake/
    mohun-lake/
    morton-lake/
    muchalat-lake/
    roberts-lake/
    sproat-lake/
  parks/
    elk-falls-quinsam-campground/
    morton-lake-park/
    sproat-lake-provincial-park/
  rec-sites/
    amor-lake-rec0174/
    beavertail-lake-dayuse/
    echo-lake-dayuse/
    keogh-lake-rec16077/
    mohun-lake-rec0184/
    muchalat-lake-rec0258/
    roberts-lake-rec0191/
    twin-lake-rec0185/
shared/
  gallery/                          ← WP only: where sync puts the generated PageMap.json
  home/
  list_browser/
templates/
  destination-template/
  howto-template/
  lake-template/
  van-template/
van/
  van-overview/
  bronco/
  checklists/
    checklist-arriving-campsite/
    checklist-leaving-campsite/
  howto/
    howto-awning/
    howto-climate/
    howto-dump/
    howto-power/
    howto-water/
  maintenance/
    van-maintenance/
    bronco-maintenance/
```

Additional folders not mirrored everywhere:
- `media/data/scripts/` — data-only, no pages or images
- `posts/` — future, peer of `pages/`

- Folder names are practical identifiers, not display labels
- Structure mirrors the menu hierarchy at every level
- Folder names are case-insensitive; lowercase in GitHub/local, mixed case in FileBird per Pierre's taste

## WP Media Top Level
Two roots only: `Images/` and `Data/`

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
| lakeId | Page name | Fishing Images Folder |
|--------|-----------|-----------------------|
| 00040CAMB | gosling-lake | ~/Working/Fishing/Images/00040CAMB |
| 00126CAMB | echo-lake | ~/Working/Fishing/Images/00126CAMB |
| 00155SALM | roberts-lake | ~/Working/Fishing/Images/00155SALM |
| 00197GOLD | muchalat-lake | ~/Working/Fishing/Images/00197GOLD |
| 00216NIMP | keogh-lake | NOT FOUND |
| 00324SALM | amor-lake | ~/Working/Fishing/Images/00324SALM |
| 01128ALBN | sproat-lake | NOT FOUND |

## FileBird folder ids are NEVER stored here (Pierre, 2026-08-09)

**A FileBird folder id is read from WordPress at the moment it is needed, never written
down in this repo.** WordPress is the master of that tree: ids change when a folder is
recreated, and a number committed to GitHub cannot announce that it went stale — it just
sits there being wrong until something is filed into the wrong folder. Assume any id you
remember has changed underneath you.

The same goes for the shape of either tree, Data or Images. Neither is recorded here; walk
`GET /folders` or `GET /post-type-folders/?post_type=page` and read what is actually there.
Endpoints, curl format and param quirks: [../reference/filebird-api.md](../reference/filebird-api.md),
which is the only copy.

Two facts about the trees that are not ids, and so do belong here:

- **Two media roots only** — `Images/` and `Data/`, peers. `Data/` mirrors `media/data/`;
  `Images/` is Pierre's (above).
- **There is no "read folder contents" endpoint for post-type folders**, so page-folder
  filing is validated visually in WP Admin.
- **The media `set-attachment` endpoint is broken** — returns "Validation failed" whatever
  the params or auth — so media folder assignment is manual in WP Admin.

The 2026-06-30 Data snapshot that used to sit here was deleted 2026-08-09, along with the
root ids in `site.md`. It had already rotted: it still showed `instructions/`,
`howto-shower/` and `park-template/`, none of which have existed for weeks. The Images
snapshot went the same way on 2026-08-07 when the reconciliation it supported was cancelled.
