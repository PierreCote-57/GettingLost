# TODO

Work parked for later: small issues found while working on something bigger, plus
planned passes. Noted, not fixed. Delete a line when it's done.

**What this file is FOR: so the thing is not forgotten AND we stop spending time on it
now.** Parking it is the whole transaction. So — write the entry without asking, and
then drop it. Do NOT come back to discuss a parked item mid-task: not to refine its
wording, not to check whether it's framed right, not to ask a question about it. Every
one of those spends the time the parking was meant to save, and pulls Pierre out of the
task he's actually in. Questions about a parked item get asked WHEN WE WORK ON IT
(2026-07-30).

Code and data-integrity work only. **Content authoring does not belong here** (2026-07-27).

Numbers are sequential and unique. Renumbered 2026-07-28 (completed entries deleted
per the rule above); old numbers are gone, so refer to items by their text if an
older note cites a number.

## List browser

1. **On-demand keyword validation pass (2026-07-25).** Unlike badges and access, the
   keyword vocabulary is open and derived from the data, so it drifts. Loose authoring
   rules: singular/plural are the same word — pick one; synonyms are the same word —
   pick one. Wanted: a pass, run on demand (not in the build, not in the filter), that
   walks every `tags.keywords` value across the datasets and SURFACES suspects — near-
   duplicates, plural/singular pairs, one-off values used a single time. It reports; a
   human decides. Do NOT normalize in the filter (stemming/synonym maps) — that would
   hide exactly the drift this is meant to expose.

3. **Add count to keywords in `datasets.json`, for display in the dropdown (2026-07-30).**
   `collectKeywords()` already walks every hydrated row to build the distinct list —
   counting there instead of de-duplicating is the same walk. The dropdown then shows
   how many rows each choice would match before it's clicked. Changes the published
   manifest's `keywords` shape, so `buildCheckboxDropdown` changes with it.

4. **Ponder count in the structured dropdowns too — badges & access (2026-07-30).**
   Not the same problem as keywords: those vocabularies are CLOSED, so a count of zero
   is possible and meaningful (an option that guarantees no results). Decide whether a
   zero renders as `(0)` or hides the option.

5. **Should destination type be its own facet rather than a keyword (2026-07-30)?**
   `lake`/`park`/`rec-site`/`campground` are carried as keywords because nothing else
   on a row states the type — for per-page rows it is implied by the folder, for inline
   dataset rows by nothing at all. So the keyword is load-bearing: drop it and lakes
   become unselectable. Surfaced by the keyword pass, which flagged them as redundant;
   they are not. The question is whether type deserves a structured facet of its own.

## Knowledge reorg

6. **Does a completed project record stay in `docs/projects/` (2026-07-30)?**
   `docs/projects/slug-rebuild.md` documents work finished 2026-07-08; the live rule it
   produced (universal `<base>_<ext>` slugs, github-filename-as-master) is already in
   `docs/conventions/site.md`, so the record is history, not work. Decide the general
   policy — keep finished records as history, or delete them once their rules have
   graduated to the conventions — then apply it to this one. No `archive/` folder either
   way; that was already ruled out.

8. **Consolidate the two merged docs (2026-07-30).** `rendering/list-browser.md` and
   `projects/schema-unification.md` were each assembled by concatenating two overlapping
   records under `##` headings — nothing was lost, nothing was reconciled. Both still
   describe the same thing twice, and in list-browser's case one half is explicitly
   superseded. Merge them properly when either is next touched.

9. **`[[project-posts-featured-backfill]]` in `docs/schema/image.md` points at nothing
   (2026-07-30).** Every other cross-reference was rewritten to a relative link during
   the migration; this slug has no memory file and no doc. Either the record was deleted
   or the link was always wrong. Resolve or drop the reference.

11. **`backToGallery` is documented two ways (2026-07-30).** `docs/rendering/blocks.md`
    says the block now takes **no attributes at all** and that `data-dataset` was removed
    from all 29 pages ("do not re-add it"), while `docs/conventions/site.md` and
    `docs/recipes/lake-page.md` both still say every destination page's `backToGallery`
    carries `data-dataset="destinations"`. One is stale. Check the markup and fix the
    losers.

12. **Untracked leftovers in `local/` (2026-07-31).** `local/charting/cabin-indoor-storage.svg`
    and `local/charting/cabin-outdoors.svg` are working files from a charting session — per
    the charting lifecycle only the CSV persists, so these should go. Pierre's cleanup.
    `local/tools/keyword_validation.py` is also untracked but is real tooling; decide
    whether it gets committed.

## Data integrity

2. **Cross-reference validation pass.** Walk the cross-referenced pages against each
   other and confirm they agree. Only the rows carrying a `file` link are in scope —
   a catalog-only row has nothing to check against.
