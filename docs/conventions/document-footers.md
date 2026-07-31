# Document conventions

## Footers

Every document Pierre produces uses the footer format **"Page n of N"** on all pages.

**Why:** It's his standing convention across his documents; a ToC page number is only usable if the physical pages carry matching numbers.

**How to apply:** Any generated PDF/doc gets a centered "Page n of N" footer on every page. Counting includes the cover and any front matter (cover = "Page 1 of N"). If a doc has a Table of Contents, the ToC page numbers must match these printed footers. See the `NumberedCanvas` pattern in [local/tools/build_checklists_pdf.py](local/tools/build_checklists_pdf.py) for the two-pass reportlab implementation.

## Marking numbers that aren't measured

In any table of figures Pierre hasn't measured (the power-consumption tables in
`howto-power.html` are the case that set this):

- **Measured** — his real observed figures — carry no marker.
- **Estimated or not yet measured** — mark "to be validated" with a **numbered superscript
  footnote**. He chose numbered superscripts over symbols or abbreviations.
- Every footnote must be referenced by a cell. No orphan notes, no gaps in the numbering.
- Where a spec is simply unknown, use a "To be researched" placeholder rather than
  inventing precision — the same placeholder convention as the supplier-doc rows.

`typ.` means **typical** — a real nominal spec value. It does not mean "best guess" and it
does not mean "to be validated." The general rule is in `~/Claude/working-with-pierre.md` §7;
this is the presentation convention for site documents.
