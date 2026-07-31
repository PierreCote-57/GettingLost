# Checklists booklet

One builder now makes **both** booklets — checklists and howto — from
[local/tools/build_booklet_pdf.py](local/tools/build_booklet_pdf.py) (renamed
2026-07-16 from `build_checklists_pdf.py`). A `BOOKLETS` config dict holds the
only per-booklet differences: `source_dir`, `data_dir`, `cover_title`,
`cover_subtitle`, `step_style` ("checkbox" for checklists, "number" for howto).
CLI: `python3 local/tools/build_booklet_pdf.py <checklists|howto> [output.pdf]`;
defaults write to `media/data/van/<kind>/<kind>.pdf`. Pages developed
**structure/format first**; wording is placeholder.

**How to apply:** Don't polish/debate content or structure — that's the **author's
job**, not the builder's (see `docs/rendering/blocks.md`). The renderer
renders exactly what's in the `<section data-howto-section="howto">`, whatever it
is; no section → title-only page; empty/malformed block → author's problem.

Builder facts: half-letter (5.5x8.5). Page **title comes from the sibling JSON
`title`** (`<data_dir>/<slug>/<slug>.json`), NOT the section h2 (howto h2s are the
generic "How to"); the section's own heading h2 is skipped. Generic renderer walks
the section's children in order, dispatched by tag: h2/h3→heading, p→paragraph,
ol→numbered (or checkbox), ul→bullets (nested recursively), table→gridded table,
`<details>`→summary-as-heading + contents expanded, warning block→callout,
photoRef→its caption text inline, photoGallery→ignored (images out of scope).
Globs `*.html` so new pages auto-join, sorted alpha by title, cover + ToC +
one-or-more pages each, "Page n of N" footers (also on the cover). See
[docs/conventions/document-footers.md](../conventions/document-footers.md).

**Deploy (added 2026-07-16):** the built PDFs (`media/data/van/checklists/checklists.pdf`,
`media/data/van/howto/howto.pdf`) now sync to WP via sync.js's FILES pass — `.pdf`
was added to three spots (the `syncFiles` extension filter, `guessMimeFromExt`
→ `application/pdf`, and the `findExistingMediaIdByFilename` strip regex). They land
flat at `/wp-content/uploads/<name>.pdf` (same convention as the JSON files) and file
into their FileBird `data/van/...` folders. The `media/**` push trigger already covers
them; no yml change.

**The "Download booklet (PDF)" button** — lost in the 2026-07-25 cutover (it lived in the
retired `gallery.jst` as a `PDF_BY_FILE` map and nothing carried it over), RESTORED the
same day as the `booklet` options token: `datasets.json` lists a bare `"booklet"` on the
two van datasets (a booklet is POSSIBLE here), and the URL decides — `?booklet=howto`
renders the button, no parameter renders nothing. The builder makes the URL
(`/wp-content/uploads/<value>.pdf`), so the parameter names the BOOKLET, not the file.
**The nav-menu links must carry `&booklet=…`** or no button appears. Right-justified at the end of the options bar
via `margin-left:auto` on `.gl-lb-booklet`, reusing `.gl-pdf-button`'s brown filled look.
The old title-line placement (`.gl-title-with-pdf`, a flex row on `.wp-block-post-title`)
is still in gettinglost.cst, unused, one class away if it's ever wanted back. The word
"printable" was dropped from the label. See [docs/rendering/list-browser.md](../rendering/list-browser.md), [docs/rendering/blocks.md](../rendering/blocks.md).
