# Booklet builder

One builder makes **both** booklets — checklists and howto — from
[local/tools/build_booklet_pdf.py](../../local/tools/build_booklet_pdf.py). A `BOOKLETS`
config dict holds the only per-booklet differences: `source_dir`, `data_dir`,
`cover_title`, `cover_subtitle`, `cover_image` and `default_output`.

**List style is NOT in that config.** How a list renders — checkbox, number or bullet —
follows the MARKUP, exactly like the web: a `class="gl-checklist"` list gets checkboxes,
otherwise `<ol>` is numbered and `<ul>` is bulleted. One authoring convention drives both the
page and the PDF, so there is nothing to keep in step
([docs/rendering/blocks.md](../rendering/blocks.md)).

```bash
python3 local/tools/build_booklet_pdf.py <checklists|howto> [output.pdf]
```

Defaults write to `media/data/van/<kind>/<kind>.pdf`.

## What the builder does

Half-letter pages (5.5 × 8.5). It globs `*.html` so new pages join automatically, sorts
alphabetically by title, and emits a cover, a table of contents, and one or more pages per
source page, with "Page n of N" footers including on the cover — see
[docs/conventions/document-footers.md](../conventions/document-footers.md).

A page's **title comes from the sibling JSON** (`<data_dir>/<name>/<name>.json`), not the
section `h2` — howto `h2`s are all the generic "How to". The section's own heading is
skipped. The builder reads the `name` key, falling back to the filename when a JSON has none.

The renderer walks the section's children in order and dispatches by tag: `h2`/`h3` →
heading, `p` → paragraph, `ol` → numbered or checkbox, `ul` → bullets (recursive),
`table` → gridded table, `<details>` → summary-as-heading plus expanded contents, warning
block → callout, `photoRef` → its caption text inline, `photoGallery` → ignored, images
being out of scope.

Two inline tags carry meaning but no text, so they are swapped for markers before a node is
collapsed to its text and turned into markup afterwards: `<br>` → a real line break, and
`<input>` → a write-on blank, an underlined run of `size` (or `width`) non-breaking spaces,
6 when neither is given. **`size` is in characters, so `size="2"` prints a two-character
rule** — widen the attribute, not the builder, when a blank needs more room.

**Box characters need a Unicode font.** The booklet is set in Helvetica, a base-14 font
whose WinAnsi encoding has no ballot box, so `☐` and friends printed as the notdef glyph —
a solid black square. `BOX_CHARS` (U+2610-2612, U+25A1-25A2, U+274F-2752) are switched to
`Arial Unicode.ttf` and nothing else is, keeping the rest of the booklet in Helvetica. The
font is macOS-only; if it is missing the build still runs and warns on stderr, and the boxes
go back to solid.

**Render what's there.** Content and structure are the author's job, not the builder's — no
section means a title-only page, an empty or malformed block is the author's problem. See
[docs/rendering/blocks.md](../rendering/blocks.md).

## Deployment

The built PDFs sync to WP through `sync.js`'s files pass: `.pdf` appears in the `syncFiles`
extension filter, in `guessMimeFromExt` → `application/pdf`, and in the
`findExistingMediaIdByFilename` strip regex. They land flat at
`/wp-content/uploads/<name>.pdf`, the same convention as the JSON files, and file into their
FileBird `data/van/…` folders. The existing `media/**` push trigger covers them.

## The "Download booklet (PDF)" button

A `booklet` options token. `datasets.json` lists a bare `"booklet"` on the two van datasets,
meaning a booklet is *possible* here; the URL decides — `?booklet=howto` renders the button,
no parameter renders nothing. The builder makes the URL
(`/wp-content/uploads/<value>.pdf`), so **the parameter names the booklet, not the file**.

**Nav-menu links must carry `&booklet=…`** or no button appears.

Right-justified at the end of the options bar via `margin-left:auto` on `.gl-lb-booklet`,
reusing `.gl-pdf-button`'s brown filled look. An alternative title-line placement
(`.gl-title-with-pdf`, a flex row on `.wp-block-post-title`) still exists in
`gettinglost.cst`, unused, one class away if it is ever wanted.

See [docs/rendering/list-browser.md](../rendering/list-browser.md).
