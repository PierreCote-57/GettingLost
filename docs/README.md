# Documentation index

Durable project knowledge lives here — schemas, conventions, renderer behavior, recipes,
external APIs, project records. Versioned with the code, readable in IntelliJ.

`CLAUDE.md` holds the working agreement (rules). [toolchain.md](toolchain.md) holds Claude's setup
— permissions, session-start checks, browser gotchas. Claude's memory holds only what cannot
be published: who Pierre is, the *why* behind the rules, and the FileBird token. None of
them duplicate what is documented here: **when this file and a memory disagree, this file
wins.**

Migrated out of Claude's memory directory 2026-07-30.

[overview.md](overview.md) — what the project is: the GitHub-mastered sync pipeline,
per-page JSON as source of truth, auto-generated galleries.

## schema/ — the shape of the data

| File | Covers |
| --- | --- |
| [image.md](schema/image.md) | `featuredImage`, null rules, `formatImageUrl`, filename reuse |
| [access.md](schema/access.md) | `access{haversine,driving,legs}`, leg vocabulary, km rounding |
| [badges-road.md](schema/badges-road.md) | authored `badges.tags`, derived `badges.road`, `ROAD_COLORS` |
| [map-pins-location.md](schema/map-pins-location.md) | `location{lat,lng,pin,zoom}`, pin vocabulary, `googleMap` block |
| [wpsettings-comments.md](schema/wpsettings-comments.md) | `wpSettings{published,comments}` |
| [wp-title-date.md](schema/wp-title-date.md) | tab title, post date/modified, backdating |
| [slug-vs-title.md](schema/slug-vs-title.md) | slug = id, title = display name |

## conventions/ — how the site is built

| File | Covers |
| --- | --- |
| [site.md](conventions/site.md) | standing conventions, filename-master, destination types, FileBird folders |
| [json-format.md](conventions/json-format.md) | the JSON house format — tabs, one field per line, written through `jsonio.py` |
| [keywords.md](conventions/keywords.md) | `tags.keywords` as an OPEN vocabulary: authoring, and never normalizing in the filter |
| [folders.md](conventions/folders.md) | folder structure across the 4 locations, FileBird IDs |
| [github-workflow.md](conventions/github-workflow.md) | repo SOP, sync workflows, token policy |
| [fishing-links.md](conventions/fishing-links.md) | Go Fish BC stocking reports, further-readings placement |
| [theme-tokens.md](conventions/theme-tokens.md) | palette, fonts, why `gettinglost.cst` uses no theme `var()`s |
| [document-footers.md](conventions/document-footers.md) | "Page n of N" footers, ToC numbering |

## rendering/ — how a page becomes HTML

| File | Covers |
| --- | --- |
| [blocks.md](rendering/blocks.md) | THE INVARIANT, every renderer, load order |
| [list-browser.md](rendering/list-browser.md) | the four phases, the `known` bag, adding a control or filter |
| [wp-templates.md](rendering/wp-templates.md) | editing Twenty Twenty-Five templates via the wpcom MCP |

## skills/ — procedures to follow, not background to read

A file here is followed step by step when Pierre asks for what it covers, exactly as an
installed skill would be. `CLAUDE.md` points at them so they are known every session.

| File | Covers |
| --- | --- |
| [keyword-validation.md](skills/keyword-validation.md) | the keyword validation pass: the script, the report format, the standing rulings |

## recipes/ — how to do a thing

| File | Covers |
| --- | --- |
| [lake-page.md](recipes/lake-page.md) | fishing folder → lake page + rec-site page, end to end |
| [data-fill.md](recipes/data-fill.md) | geocoding, haversine, per-park scraping, `jsonio.py` |
| [image-editing.md](recipes/image-editing.md) | crop, EXIF orientation, donor-clone removal |
| [charting.md](recipes/charting.md) | `gen-chart.py`, the locked cabin-climate chart |

## reference/ — external sources

| File | Covers |
| --- | --- |
| [filebird-api.md](reference/filebird-api.md) | endpoint, curl format, param quirks (token is not in the repo) |
| [rstbc-suggestions.md](reference/rstbc-suggestions.md) | rec-site name lookup |
| [lakedata.md](reference/lakedata.md) | `local/data/LakeData.json` — read this first for a new lake page |
| [bc-rest-stops.md](reference/bc-rest-stops.md) | `local/data/bc-rest-stop.json` |
| [fishing-images.md](reference/fishing-images.md) | `~/Working/Fishing/Images/` |
| [van-hardware.md](reference/van-hardware.md) | Truma hardware, sourcing conventions |

## projects/ — records of work

[projects/README.md](projects/README.md) indexes all six and is the **only** place a
project's status is recorded. Each project file describes the work as it stands, with no
status or history in it.

[todo.md](todo.md) — parked work.

[site-move.md](site-move.md) — what has to be dealt with when the site leaves
`wpcomstaging.com` for the production domain.
