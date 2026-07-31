## Masters

| Component | Master |
|---|---|
| Page HTML | GitHub (`pages/`) |
| Media data (JSON/JST) | GitHub (`media/data/`) |
| Media images | Local (`~/Pictures/GettingLost/Images/`) |
| Page metadata (featured image, WP template, slug, status) | WordPress |
| Navigation/menus | WordPress |

**Key principle:** WordPress is the objective/destination, not the master of content. Only page metadata and navigation live there as master. Everything else has an external master that gets pushed in.

**WP template** (which layout a page uses) is page metadata — mastered in WordPress, never touched by sync.js.

## Folder Structure (IMPLEMENTED 2026-06-30)

All four locations mirror the same hierarchy:

```
pages/                              ← GitHub, page HTML
media/data/                         ← GitHub, page JSON data
~/Pictures/GettingLost/Images/      ← local, source images
FileBird Images/ and Data/          ← WordPress media library
```

```
about/
  about/
  useful-contacts/
  useful-links/
destinations/
  campgrounds/
    pacific-playgrounds-resort/
    salmon-point-resort/
  lakes/
    amor-lake/
    echo-lake/
    gosling-lake/
    keogh-lake/
    muchalat-lake/
    roberts-lake/
    sproat-lake/
  parks/
    elk-falls-quinsam-campground/
shared/
  gallery/
  home/
templates/
  campground-template/
  howto-template/
  lake-template/
  park-template/
  van-template/
van/
  van-overview/
  checklists/
    checklist-arriving-campsite/
    checklist-leaving-campsite/
  howto/
    howto-awning/
    howto-shower/
    howto-temperature-control/
    howto-water/
  maintenance/
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

## Implementation Status (updated 2026-07-01)

### DONE
- GitHub `pages/` reorganized to match structure (pushed, synced to WP)
- GitHub `media/data/` reorganized to match structure (pushed, synced to WP)
- `~/Pictures/GettingLost/Images/` full folder tree created
- FileBird Data tree reorganized and validated — matches GitHub exactly
- FileBird Images tree reorganized and validated (2026-07-01) — matches target structure
- FileBird Page folder tree validated (2026-07-01) — matches GitHub
- Template JSON files created (lake-template, campground-template, park-template, van-template)
- Lake images copied from `~/Working/Fishing/Images/` to Pictures folder:
  - amor-lake (28 images, from 00324SALM)
  - echo-lake (24 images, from 00126CAMB)
  - gosling-lake (3 images, from 00040CAMB)
  - muchalat-lake (12 images, from 00197GOLD)
  - roberts-lake (22 images, from 00155SALM)
- Total: 89 lake images copied
- Van images and howto images assigned in WP admin (2026-07-01)

### NOT DONE / PENDING
- keogh-lake and sproat-lake — no source images in ~/Working/Fishing/Images/
- `glmedia.py` image pipeline (planned, not built)
- Posts strategy (deferred)

## Lake ID Mapping
| lakeId | Slug | Fishing Images Folder |
|--------|------|-----------------------|
| 00040CAMB | gosling-lake | ~/Working/Fishing/Images/00040CAMB |
| 00126CAMB | echo-lake | ~/Working/Fishing/Images/00126CAMB |
| 00155SALM | roberts-lake | ~/Working/Fishing/Images/00155SALM |
| 00197GOLD | muchalat-lake | ~/Working/Fishing/Images/00197GOLD |
| 00216NIMP | keogh-lake | NOT FOUND |
| 00324SALM | amor-lake | ~/Working/Fishing/Images/00324SALM |
| 01128ALBN | sproat-lake | NOT FOUND |

## FileBird Post-Type API (pages — working)
- `GET /wp-json/filebird/public/v1/post-type-folders/?post_type=page`
- `POST /wp-json/filebird/public/v1/post-type-folders` — create (`post_type`, `title`, `parent`)
- `POST /wp-json/filebird/public/v1/post-type-folder/update` — rename/move
- `POST /wp-json/filebird/public/v1/post-type-folder/delete`
- `POST /wp-json/filebird/public/v1/post-type-folder/set-posts` — assign pages
- No "read folder contents" endpoint — validation must be done visually in WP Admin

## FileBird Media API (broken)
- `set-attachment` returns "Validation failed" regardless of param format or auth — all media folder assignments are manual

## Current FileBird Data Folder Structure (confirmed 2026-06-30 evening)
```
Data (id:56)
  about (id:80)
    about (id:81)
    useful-contacts (id:82)
    useful-links (id:83)
  destinations (id:90)
    campgrounds (id:91)
      pacific-playgrounds-resort (id:92)
      salmon-point-resort (id:93)
    lakes (id:94)
      amor-lake (id:95)
      echo-lake (id:96)
      gosling-lake (id:97)
      keogh-lake (id:98)
      muchalat-lake (id:99)
      roberts-lake (id:100)
      sproat-lake (id:101)
    parks (id:102)
      elk-falls-quinsam-campground (id:103)
  scripts (id:60)
  shared (id:84)
    gallery (id:85)
  templates (id:113)
    campground-template (id:114)
    howto-template (id:87)
    lake-template (id:115)
    park-template (id:116)
    van-template (id:117)
  van (id:88)
    checklists (id:104)
      checklist-arriving-campsite (id:105)
      checklist-leaving-campsite (id:106)
    instructions (id:107)
      howto-awning (id:108)
      howto-shower (id:109)
      howto-temperature-control (id:110)
      howto-water (id:111)
    van-overview (id:89)
```

## Current FileBird Images Folder Structure (confirmed 2026-07-01)
```
Images/ (id:52)
  About/ (id:160)
  Destinations/ (id:159)
    Campgrounds/ (id:29)
      pacific-playgrounds-resort/ (id:31)
      salmon-point-resort/ (id:32)
    Lakes/ (id:1)
      amor-lake/ (id:9)
      ... (20 lake subfolders)
      sproat-lake/ (id:28)
    Parks/ (id:3)
      elk-falls-quinsam-campground/ (id:51)
  Shared/ (id:37)
  Posts/ (id:63)
    every-journey-has-a-first-step/ (id:45)
  Van/ (id:65)
    checklists/ (id:162)
    howto/ (id:163)  (renamed from instructions/ 2026-07-04)
      howto-temperature-control/ (id:66)
      howto-awning/ (id:69)
    maintenance/ (id:166)
    van-overview/ (id:164)
```
