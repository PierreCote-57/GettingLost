#!/usr/bin/env python3
"""Build a half-letter (5.5 x 8.5 in) booklet: cover + one page per checklist.

All checklist content (title, intro, group headings, steps) is read live from
the page HTML in pages/van/checklists/*.html -- nothing is duplicated here.
Only the howto section of each page is used; images and the collapsed
"details" section are ignored.

Regenerate from the repo root:
    python3 local/tools/build_checklists_pdf.py media/data/van/checklists/checklists.pdf

Requires: reportlab, beautifulsoup4
    pip install --user reportlab beautifulsoup4
"""

import glob
import os
import re
import sys
from xml.sax.saxutils import escape as xml_escape

from bs4 import BeautifulSoup
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, PageBreak, Table, TableStyle, Flowable
)
from reportlab.platypus.tableofcontents import TableOfContents

HALF_LETTER = (5.5 * inch, 8.5 * inch)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKLIST_DIR = os.path.join(REPO_ROOT, "pages", "van", "checklists")

# ---------------------------------------------------------------------------
# Cover chrome. These are the ONLY literal strings in the file: there is no
# checklist-HTML source for them. Adjust here (or wire to a config later).
# ---------------------------------------------------------------------------
COVER_KICKER = "GETTING LOST IN CANADA"
COVER_TITLE = "Checklists"
COVER_SUBTITLE = ("The van: Truma Aventa eco AC &middot; Truma Combi heat/hot "
                  "water &middot; Carefree Eclipse awning")

# ----- palette (site amber accent) -----
AMBER = colors.HexColor("#c98a3e")
INK = colors.HexColor("#333333")
MUTED = colors.HexColor("#555555")

styles = getSampleStyleSheet()

cover_title = ParagraphStyle(
    "CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=24, leading=28, textColor=INK, alignment=TA_CENTER)
cover_sub = ParagraphStyle(
    "CoverSub", parent=styles["Normal"], fontSize=12, leading=16,
    textColor=MUTED, alignment=TA_CENTER)
cover_kicker = ParagraphStyle(
    "CoverKicker", parent=styles["Normal"], fontSize=10, leading=14,
    textColor=AMBER, alignment=TA_CENTER, fontName="Helvetica-Bold")

page_title = ParagraphStyle(
    "PageTitle", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=24, leading=28, textColor=INK, alignment=TA_CENTER, spaceAfter=8)
intro = ParagraphStyle(
    "Intro", parent=styles["Normal"], fontSize=9, leading=11.5,
    textColor=MUTED, spaceAfter=5)
group = ParagraphStyle(
    "Group", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=10, leading=12, textColor=AMBER, spaceBefore=5, spaceAfter=2)
item = ParagraphStyle(
    "Item", parent=styles["Normal"], fontSize=9, leading=11.5, textColor=INK)

toc_title = ParagraphStyle(
    "TocTitle", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=24, leading=28, textColor=INK, alignment=TA_CENTER, spaceAfter=12)
toc_entry = ParagraphStyle(
    "TocEntry", parent=styles["Normal"], fontName="Helvetica",
    fontSize=9, leading=11.5, textColor=INK)


class BookletDoc(SimpleDocTemplate):
    """SimpleDocTemplate that feeds page titles into the Table of Contents."""
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "PageTitle":
            self.notify("TOCEntry", (0, flowable.getPlainText(), self.page))


class NumberedCanvas(canvas.Canvas):
    """Stamps a 'Page n of N' footer on every page (needs the final page
    count, so it defers drawing until save())."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for n, state in enumerate(self._saved_page_states, start=1):
            self.__dict__.update(state)
            self._draw_footer(n, total)
            super().showPage()
        super().save()

    def _draw_footer(self, n, total):
        self.setFont("Helvetica", 9)
        self.setFillColor(MUTED)
        self.drawCentredString(HALF_LETTER[0] / 2, 0.3 * inch,
                               "Page %d of %d" % (n, total))


class CheckBox(Flowable):
    """A small empty square, baseline-aligned with the first text line."""
    def __init__(self, size=8):
        super().__init__()
        self.size = size
        self.width = size
        self.height = size

    def draw(self):
        c = self.canv
        c.setStrokeColor(AMBER)
        c.setLineWidth(0.9)
        c.rect(0, 0, self.size, self.size, stroke=1, fill=0)


def checklist_table(steps):
    """Return a Table of [checkbox, text] rows."""
    rows = [[CheckBox(), Paragraph(s, item)] for s in steps]
    t = Table(rows, colWidths=[0.24 * inch, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (0, -1), "TOP"),
        ("VALIGN", (1, 0), (1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.7),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("TOPPADDING", (0, 0), (0, -1), 2.6),  # nudge box onto first line
    ]))
    return t


# ---------------------------------------------------------------------------
# Parsing: pull the howto section out of a checklist page.
# ---------------------------------------------------------------------------

def _text(node):
    """Collapsed, XML-escaped text of a node (safe for reportlab Paragraph)."""
    return xml_escape(re.sub(r"\s+", " ", node.get_text(" ", strip=True)))


def parse_checklist(path):
    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    section = soup.find("section", attrs={"data-howto-section": "howto"})
    if section is None:
        return None

    h2 = section.find("h2", id="checklist-heading")
    p = section.find("p")

    groups = []
    for h3 in section.find_all("h3"):
        ol = h3.find_next_sibling("ol")
        if ol is None:
            continue
        steps = []
        for li in ol.find_all("li", recursive=False):
            # Drop any inline image reference before reading the text.
            for span in li.find_all("span", attrs={"data-block-type": "photoRef"}):
                span.decompose()
            text = _text(li)
            if text:
                steps.append(text)
        groups.append((_text(h3), steps))

    return {
        "title": _text(h2) if h2 else os.path.splitext(os.path.basename(path))[0],
        "intro": _text(p) if p else "",
        "groups": groups,
    }


def draw_cover(c, doc):
    """Cover art, drawn directly on page 1 so the subtitle can be pinned at
    1/3 of the page height from the bottom (paragraphs still wrap)."""
    w, h = HALF_LETTER
    avail = w - doc.leftMargin - doc.rightMargin

    kicker = Paragraph(COVER_KICKER, cover_kicker)
    title = Paragraph(COVER_TITLE, cover_title)
    subtitle = Paragraph(COVER_SUBTITLE, cover_sub)

    _, title_h = title.wrap(avail, h)
    kicker.wrap(avail, h)
    subtitle.wrap(avail, h)

    y_title = h * 0.60
    title.drawOn(c, doc.leftMargin, y_title)
    kicker.drawOn(c, doc.leftMargin, y_title + title_h + 8)
    subtitle.drawOn(c, doc.leftMargin, h / 3.0)


def instruction_page(story, data):
    story.append(Paragraph(data["title"], page_title))
    if data["intro"]:
        story.append(Paragraph(data["intro"], intro))
    for name, steps in data["groups"]:
        story.append(Paragraph(name, group))
        story.append(checklist_table(steps))


def build(path):
    files = glob.glob(os.path.join(CHECKLIST_DIR, "*.html"))
    checklists = [c for c in (parse_checklist(p) for p in files) if c]
    if not checklists:
        sys.exit("No checklist howto sections found in " + CHECKLIST_DIR)
    checklists.sort(key=lambda c: c["title"].lower())

    doc = BookletDoc(
        path, pagesize=HALF_LETTER,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
        title=COVER_TITLE, author=COVER_KICKER.title())

    story = []

    # Page 1 is the cover, painted by draw_cover(); leave its frame empty.
    story.append(PageBreak())

    # Table of contents
    story.append(Paragraph("Table of Contents", toc_title))
    toc = TableOfContents()
    toc.levelStyles = [toc_entry]
    story.append(toc)

    # One page per checklist (alpha by title)
    for data in checklists:
        story.append(PageBreak())
        instruction_page(story, data)

    # multiBuild: two passes so the ToC page numbers resolve; NumberedCanvas
    # stamps the "Page n of N" footers on the final pass.
    doc.multiBuild(story, onFirstPage=draw_cover, canvasmaker=NumberedCanvas)
    print("wrote", path, "(%d checklists)" % len(checklists))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "checklists.pdf"
    build(out)
