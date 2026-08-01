# Document conventions

## Footers

Every document Pierre produces uses the footer format **"Page n of N"** on all pages.

The footer is centered and appears on every page. Counting includes the cover and any front
matter, so the cover reads "Page 1 of N". Where a document has a Table of Contents, its page
numbers must match the printed footers — a ToC number is only usable if the physical page
carries the same one.

The two-pass reportlab implementation is the `NumberedCanvas` class in
[local/tools/build_booklet_pdf.py](../../local/tools/build_booklet_pdf.py).

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
