# Documentation index

Durable project knowledge lives here — schemas, conventions, renderer behavior, recipes,
external APIs, project records. Versioned with the code, readable in IntelliJ.

`CLAUDE.md` holds the working agreement (rules). [toolchain.md](toolchain.md) holds Claude's setup
— permissions, session-start checks, browser gotchas. Claude's memory holds only what cannot
be published: the FileBird token, and the *why* behind rules that live elsewhere. Who Pierre
is and how to work with him are in `~/Claude/` (`pierre.md`, `working-with-pierre.md`),
imported into every project by `~/.claude/CLAUDE.md`. None of
them duplicate what is documented here: **when this file and a memory disagree, this file
wins.**

Migrated out of Claude's memory directory 2026-07-30.

## These files are not a cache of the repo (2026-08-21)

**Anything derivable from the true source is READ FROM THE SOURCE, never copied here.**
Folder trees, file lists, which objects exist, counts — the repo, the JSON and the API
already hold them, and a copy in markdown is a cache with no invalidation: nothing detects
that it went stale, and the reader cannot tell a hit from a stale hit. The two questions
that justify any cache both fail here — the master is free to read (`ls`, `grep`, one
query), and the obsolescence is unbounded.

What belongs here is what has no master: decisions, rationale, conventions, the why. Those
are not cached in `docs/` — they are *sourced* here, which is why the staleness question
does not apply to them.

The commonest instance:

**A count of what the data holds right now is MEASURED when it is needed, never written
down here.** "24 of 214 rows", "116 of 116", "five destinations" — every one of those is
true for a day and then quietly wrong, and a doc cannot announce that it went stale. Say
the relationship instead ("the minority of rows", "most of the tagging"), and query the
JSON for the number. Same reasoning as FileBird folder ids in
[conventions/folders.md](conventions/folders.md).

A count *inside a dated record of a migration* is different — that is history, and it
stays true. `docs/projects/` may say what a pass moved on the day it ran.

[overview.md](overview.md) — what the project is: the GitHub-mastered sync pipeline,
per-page JSON as source of truth, the one param-driven list browser.

## schema/ — the shape of the data

| File | Covers |
| --- | --- |
| [image.md](schema/image.md) | `featuredImage`, null rules, `formatImageUrl`, filename reuse |
| [access.md](schema/access.md) | `access{haversine,driving,legs}`, leg vocabulary, km rounding |
| [badges-road.md](schema/badges-road.md) | authored `tags.badges`, the derived road chip, `ROAD_COLORS` |
| [types.md](schema/types.md) | `tags.types` — the closed destination-type facet, why it is optional |
| [links.md](schema/links.md) | `links[]` — one flat list, `type` is the key, the label is display text |
| [map-pins-location.md](schema/map-pins-location.md) | the one shape shared by `location`, a named `googleMap` and a `pin`; resolution, icon vocabulary |
| [wpsettings-comments.md](schema/wpsettings-comments.md) | `wpSettings{published,comments}` |
| [wp-title-date.md](schema/wp-title-date.md) | tab title, post date/modified, backdating |
| [slug-vs-title.md](schema/slug-vs-title.md) | slug = id, title = display name |

## conventions/ — how the site is built

| File | Covers |
| --- | --- |
| [site.md](conventions/site.md) | standing conventions, filename-master, destination types, FileBird folders |
| [json-format.md](conventions/json-format.md) | the JSON house format — tabs, one field per line, written through `jsonio.py` |
| [keywords.md](conventions/keywords.md) | `tags.keywords` as an OPEN vocabulary: authoring, and never normalizing in the filter |
| [folders.md](conventions/folders.md) | what mirrors what across the repo, WP and FileBird; why the tree and the folder ids are never written down |
| [github-workflow.md](conventions/github-workflow.md) | repo SOP, sync workflows, token policy |
| [fishing-links.md](conventions/fishing-links.md) | Go Fish BC stocking reports, further-readings placement |
| [theme-tokens.md](conventions/theme-tokens.md) | palette, fonts, why `gettinglost.cst` uses no theme `var()`s |
| [document-footers.md](conventions/document-footers.md) | "Page n of N" footers, ToC numbering |

## rendering/ — how a page becomes HTML

| File | Covers |
| --- | --- |
| [blocks.md](rendering/blocks.md) | THE INVARIANT, every renderer, load order |
| [list-browser.md](rendering/list-browser.md) | the four phases, the `known` bag, the three views (table/grid/map), adding a control or filter |
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
| [charting.md](recipes/charting.md) | `gen-chart.py` — the flags, and the invariants the bands hold to |
| [doc-reading-pass.md](recipes/doc-reading-pass.md) | the reading half: the per-file checklist, and why a finding never ends a pass |
| [doc-validation.md](recipes/doc-validation.md) | `check_docs.py` — the six checks, and what the pass deliberately does not check |
| [crossref-check.md](recipes/crossref-check.md) | `crossref_check.py` — the five checks over the `file` link graph, `location` blocks and the registry |

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

[projects/README.md](projects/README.md) indexes every project and is the **only** place a
project's status is recorded. Each project file describes the work as it stands, with no
status or history in it.

[todo.md](todo.md) — parked work.

[site-move.md](site-move.md) — what has to be dealt with when the site leaves
`wpcomstaging.com` for the production domain.
