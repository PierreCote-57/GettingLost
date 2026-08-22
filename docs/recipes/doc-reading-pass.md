# The doc reading pass

The half of validation no script does: **reading each doc against the code and the data it
describes.** [doc-validation.md](doc-validation.md) covers the mechanical half — run that
first, so the reading is about meaning rather than broken pointers.

## Two rules, both of them from failing at this

**A FINDING NEVER ENDS THE PASS.** Record it and keep reading. On 2026-08-21 a single root
cause turned up — `logs/` is synced to WP, and eleven statements across seven files said or
implied otherwise — and chasing it ended the sweep with about twenty files unread. The
eleven were reported as though they were the result. A pass that converges on one root cause
has almost certainly stopped early.

**DONE IS A COUNT, NOT A FEELING.** Work the list below and tick each file. Judging that the
docs "look right" has been wrong every time it has been tried.

## Both directions, or it is not a pass

**Doc-first** — read a file, hold each claim against the thing it describes. This finds
WRONG STATEMENTS. It structurally cannot find a fact no doc mentions.

**Code-first** — walk the source and the data, and for each thing ask what the docs say
about it. This finds OMISSIONS. It structurally cannot find a doc pointing at the wrong doc.

Proved 2026-08-21 by running them separately: code-first found `syncLogs` and
`buildExcludedSet`, neither of which any doc mentioned; doc-first found a recipe citing the
wrong companion doc and a rule contradicting `CLAUDE.md`. Neither traversal saw the other's
findings. The overlap between them carries no information — only what one finds and the
other misses does.

The five things a pass checks, in Pierre's words (2026-08-22):

1. Read EVERY file, from disk. Never from memory of an earlier read.
2. Consistency of the md with the code **and the data**.
3. Consistency of the md with itself and with the other md.
4. Completeness of the md against the code **and the data** — the code-first direction.
5. Very limited caching.

## What to hold each file against

- The code it names — open the function, don't recall it.
- The data it describes — query the JSON, don't quote a number.
- The other docs stating the same fact. Duplication is where contradictions live, and a fact
  written in four places means one change makes three lies.
- Its own earlier paragraphs. Several files have contradicted themselves.
- **Anything changed earlier in the same session.** The highest-yield read is the diff of
  edits just made; new prose is unverified prose.

## The files

Reset the ticks at the start of a pass.

- [ ] CLAUDE.md
- [ ] README.md
- [ ] docs/README.md
- [ ] docs/conventions/document-footers.md
- [ ] docs/conventions/fishing-links.md
- [ ] docs/conventions/folders.md
- [ ] docs/conventions/github-workflow.md
- [ ] docs/conventions/json-format.md
- [ ] docs/conventions/keywords.md
- [ ] docs/conventions/site.md
- [ ] docs/conventions/theme-tokens.md
- [ ] docs/overview.md
- [ ] docs/projects/README.md
- [ ] docs/projects/checklists-booklet.md
- [ ] docs/projects/destinations-overview.md
- [ ] docs/projects/images.md
- [ ] docs/projects/logs-travel.md
- [ ] docs/projects/map-model.md
- [ ] docs/projects/schema-unification.md
- [ ] docs/projects/slug-rebuild.md
- [ ] docs/recipes/charting.md
- [ ] docs/recipes/crossref-check.md
- [ ] docs/recipes/data-fill.md
- [ ] docs/recipes/doc-validation.md
- [ ] docs/recipes/image-editing.md
- [ ] docs/recipes/lake-page.md
- [ ] docs/reference/bc-rest-stops.md
- [ ] docs/reference/filebird-api.md
- [ ] docs/reference/fishing-images.md
- [ ] docs/reference/lakedata.md
- [ ] docs/reference/rstbc-suggestions.md
- [ ] docs/reference/van-hardware.md
- [ ] docs/rendering/blocks.md
- [ ] docs/rendering/list-browser.md
- [ ] docs/rendering/wp-templates.md
- [ ] docs/schema/access.md
- [ ] docs/schema/badges-road.md
- [ ] docs/schema/image.md
- [ ] docs/schema/links.md
- [ ] docs/schema/map-pins-location.md
- [ ] docs/schema/slug-vs-title.md
- [ ] docs/schema/types.md
- [ ] docs/schema/wp-title-date.md
- [ ] docs/schema/wpsettings-comments.md
- [ ] docs/site-move.md
- [ ] docs/skills/keyword-validation.md
- [ ] docs/todo.md
- [ ] docs/toolchain.md
- [ ] local/charting/README.md
