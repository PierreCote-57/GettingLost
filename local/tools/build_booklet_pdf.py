#!/usr/bin/env python3
"""Build a half-letter (5.5 x 8.5 in) booklet: cover + one page per source page.

All content (title, intro, group headings, steps) is read live from the page
HTML in pages/van/<kind>/*.html -- nothing is duplicated here. Only the
<section data-howto-section="howto"> block of each page is used; images and the
collapsed "details" sections are ignored. A page with no such section simply
drops out of the booklet (producing the block is the page author's job).

Two booklets are defined in BOOKLETS below and selected on the command line:

    python3 local/tools/build_booklet_pdf.py checklists
    python3 local/tools/build_booklet_pdf.py howto

Add a path to override the default output:

    python3 local/tools/build_booklet_pdf.py howto media/data/van/howto/howto.pdf

Requires: reportlab, beautifulsoup4
    pip install --user reportlab beautifulsoup4
"""

import glob
import json
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
    SimpleDocTemplate, Paragraph, PageBreak, Table, TableStyle, Flowable, Spacer
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.utils import ImageReader

HALF_LETTER = (5.5 * inch, 8.5 * inch)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Booklet images (cover art, in-page pictures) live under here, addressed by
# bare filename and located by search -- the folder layout doesn't matter.
PICTURES_BASE = os.path.expanduser("~/Pictures/GettingLost")


def _p(*parts):
    return os.path.join(REPO_ROOT, *parts)


# ---------------------------------------------------------------------------
# Per-booklet config. These are the ONLY literal cover strings in the file, and
# the only things that differ between booklets: where to read pages and what the
# cover says. How a list renders (checkbox / number / bullet) is decided by the
# page markup, not here -- the renderer doesn't know which booklet it's in.
# ---------------------------------------------------------------------------
BOOKLETS = {
    "checklists": {
        "source_dir": _p("pages", "van", "checklists"),
        "data_dir": _p("media", "data", "van", "checklists"),
        "cover_title": "Checklists",
        "cover_subtitle": "Quick checklists, refer to howto for more details",
        "cover_image": "IMG_2773_crop.jpg",
        "default_output": _p("media", "data", "van", "checklists", "checklists.pdf"),
    },
    "howto": {
        "source_dir": _p("pages", "van", "howto"),
        "data_dir": _p("media", "data", "van", "howto"),
        "cover_title": "How To",
        "cover_subtitle": "Step-by-step instructions",
        "cover_image": "IMG_2773_crop.jpg",
        "default_output": _p("media", "data", "van", "howto", "howto.pdf"),
    },
}

COVER_KICKER = "GETTING LOST IN CANADA"

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
    fontSize=24, leading=28, textColor=INK, alignment=TA_CENTER, spaceAfter=4)
page_subtitle = ParagraphStyle(
    "PageSubtitle", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=13, leading=16, textColor=AMBER, alignment=TA_CENTER, spaceAfter=8)
intro = ParagraphStyle(
    "Intro", parent=styles["Normal"], fontSize=9, leading=11.5,
    textColor=MUTED, spaceAfter=5)
group = ParagraphStyle(
    "Group", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=10, leading=12, textColor=AMBER, spaceBefore=5, spaceAfter=2)
item = ParagraphStyle(
    "Item", parent=styles["Normal"], fontSize=9, leading=11.5, textColor=INK)
warn = ParagraphStyle(
    "Warn", parent=styles["Normal"], fontSize=9, leading=11.5,
    textColor=AMBER, spaceBefore=3, spaceAfter=3)
cell = ParagraphStyle(
    "Cell", parent=styles["Normal"], fontSize=8, leading=10, textColor=INK)

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
            # Sections from one page share a main title, so the ToC uses the
            # combined "title — subtitle" stashed on the paragraph.
            text = getattr(flowable, "_toc_text", None) or flowable.getPlainText()
            self.notify("TOCEntry", (0, text, self.page))


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


def _marker(checklist, ordered, n):
    """The left-column marker for a list item: a checkbox (gl-checklist list),
    a "n." number (ordered list), or a bullet (unordered list)."""
    if checklist:
        return CheckBox()
    if ordered:
        return Paragraph("%d." % n, item)
    return Paragraph("•", item)


def render_list(list_el):
    """Render an <ol>/<ul> as a Table of [marker, content] rows. The marker
    follows the markup, exactly like the web: a class="gl-checklist" list gets
    checkboxes, otherwise <ol> is numbered and <ul> is bulleted. Nested lists
    recurse, each deciding by its own class."""
    ordered = list_el.name == "ol"
    checklist = "gl-checklist" in (list_el.get("class") or [])
    rows = []
    n = 0
    for li in list_el.find_all("li", recursive=False):
        n += 1
        # Pull nested lists out first so the item's own text reads cleanly,
        # then render them indented beneath it.
        nested = [sub.extract() for sub in li.find_all(["ol", "ul"], recursive=False)]
        content = []
        text = _text(li)
        if text:
            content.append(Paragraph(text, item))
        for sub in nested:
            content.append(render_list(sub))
        rows.append([_marker(checklist, ordered, n), content or [Paragraph("", item)]])

    marker_top_pad = 2.6 if checklist else 1.7  # nudge box onto line
    t = Table(rows, colWidths=[0.26 * inch, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.7),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("TOPPADDING", (0, 0), (0, -1), marker_top_pad),
    ]))
    return t


def render_table(table_el):
    """Render an HTML <table> as a gridded reportlab Table."""
    data = []
    for tr in table_el.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if cells:
            data.append([Paragraph(_text(c), cell) for c in cells])
    if not data:
        return Spacer(0, 0)
    t = Table(data)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, MUTED),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


# ---------------------------------------------------------------------------
# Parsing: pull the howto section out of a page.
# ---------------------------------------------------------------------------

def _text(node):
    """Collapsed, XML-escaped text of a node (safe for reportlab Paragraph)."""
    return xml_escape(re.sub(r"\s+", " ", node.get_text(" ", strip=True)))


def _load_data(html_path, data_dir):
    """The page's sibling JSON (<data_dir>/<slug>/<slug>.json), or {}."""
    slug = os.path.splitext(os.path.basename(html_path))[0]
    json_path = os.path.join(data_dir, slug, slug + ".json")
    try:
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _photoref_label(data_id, galleries):
    """The caption text for a photoRef data-id ("<gallery>/<itemId>")."""
    if not data_id or "/" not in data_id:
        return None
    gkey, iid = data_id.split("/", 1)
    for it in (galleries.get(gkey) or {}).get("items", []):
        if str(it.get("id")) == iid:
            return it.get("label")
    return None


def _clean_inline(section, galleries):
    """In place: replace inline photoRef spans with their caption text, and
    drop photoGallery blocks. Images are out of scope; text stays inline."""
    for span in section.find_all("span", attrs={"data-block-type": "photoRef"}):
        span.replace_with(_photoref_label(span.get("data-id"), galleries)
                          or span.get_text(strip=True) or "")
    for div in section.find_all("div", attrs={"data-block-type": "photoGallery"}):
        div.decompose()


def render_element(el):
    """Render one block-level element from inside the section into a list of
    flowables, recursing into <details> (expanded) and nested content."""
    name = el.name
    if name in ("h2", "h3", "h4", "h5"):
        return [Paragraph(_text(el), group)]
    if name == "p":
        return [Paragraph(_text(el), intro)]
    if name in ("ol", "ul"):
        return [render_list(el)]
    if name == "table":
        return [render_table(el)]
    if name == "details":
        out = []
        summary = el.find("summary")
        if summary:
            out.append(Paragraph(_text(summary), group))
        for child in el.children:
            if getattr(child, "name", None) and child.name != "summary":
                out.extend(render_element(child))
        return out
    if name == "div" and el.get("data-block-type") == "warning":
        txt = el.get("data-text", "")
        return [Paragraph("⚠ " + xml_escape(txt), warn)] if txt else []
    # Anything else: render whatever text it carries, else nothing.
    txt = _text(el)
    return [Paragraph(txt, intro)] if txt else []


def build_page(path, data_dir):
    """Return a list of (title, subtitle, [flowables]) — one booklet page per
    <section data-howto-section="howto"> on the page. The title is the page's
    actual title (JSON), shared by every section; the subtitle is that section's
    own heading (via aria-labelledby). A page with no section still yields one
    title-only entry (producing the block is the author's job)."""
    data = _load_data(path, data_dir)
    title = xml_escape(data.get("title") or os.path.splitext(os.path.basename(path))[0])
    galleries = data.get("photoGalleries", {})

    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    sections = soup.find_all("section", attrs={"data-howto-section": "howto"})

    if not sections:
        return [(title, "", [])]

    entries = []
    for section in sections:
        _clean_inline(section, galleries)
        heading_id = section.get("aria-labelledby")
        heading_el = section.find(id=heading_id) if heading_id else None
        subtitle = _text(heading_el) if heading_el else ""

        flowables = []
        for child in section.children:
            name = getattr(child, "name", None)
            if not name:
                continue
            # The section's own heading becomes the subtitle, not body content.
            if heading_id and child.get("id") == heading_id:
                continue
            flowables.extend(render_element(child))
        entries.append((title, subtitle, flowables))

    return entries


def _find_image(name):
    """First file named <name> (case-insensitive) anywhere under PICTURES_BASE,
    or None. The folder layout is the author's business; we just locate it."""
    if not name:
        return None
    low = name.lower()
    for root, _dirs, files in os.walk(PICTURES_BASE):
        for f in files:
            if f.lower() == low:
                return os.path.join(root, f)
    return None


def _cover_image(name, width):
    """(path, height) for the cover image scaled to <width>. If the file isn't
    found, (None, <placeholder height>)."""
    path = _find_image(name)
    if path:
        iw, ih = ImageReader(path).getSize()
        return path, width * ih / float(iw)
    return None, 2.5 * inch


def _draw_cover_image(c, path, img_h, y, width):
    """Draw the cover image (or a 'Missing picture' placeholder) <width> wide,
    with its bottom at y, horizontally centered."""
    x = (HALF_LETTER[0] - width) / 2.0
    if path:
        c.drawImage(path, x, y, width=width, height=img_h,
                    preserveAspectRatio=True, mask="auto")
    else:
        c.setStrokeColor(MUTED)
        c.setLineWidth(0.8)
        c.rect(x, y, width, img_h, stroke=1, fill=0)
        c.setFillColor(MUTED)
        c.setFont("Helvetica-Oblique", 11)
        c.drawCentredString(HALF_LETTER[0] / 2.0, y + img_h / 2.0 - 4, "Missing picture")


def make_cover_drawer(cfg):
    """Return an onFirstPage callback that paints the cover: image centered on
    the page, and each title centered in its own white band (main above the
    image, subtitle below)."""
    def draw_cover(c, doc):
        w, h = HALF_LETTER
        avail = w - doc.leftMargin - doc.rightMargin

        kicker = Paragraph(COVER_KICKER, cover_kicker)
        title = Paragraph(cfg["cover_title"], cover_title)
        subtitle = Paragraph(cfg["cover_subtitle"], cover_sub)

        _, title_h = title.wrap(avail, h)
        _, kicker_h = kicker.wrap(avail, h)
        _, sub_h = subtitle.wrap(avail, h)

        # Image: 4" wide, vertically centered on the page.
        width = 4 * inch
        path, img_h = _cover_image(cfg.get("cover_image"), width)
        img_bottom = h / 2.0 - img_h / 2.0
        img_top = h / 2.0 + img_h / 2.0
        _draw_cover_image(c, path, img_h, img_bottom, width)

        # Main block (kicker above title) centered in the band above the image.
        gap = 8
        block_h = title_h + gap + kicker_h
        block_bottom = (img_top + (h - doc.topMargin)) / 2.0 - block_h / 2.0
        title.drawOn(c, doc.leftMargin, block_bottom)
        kicker.drawOn(c, doc.leftMargin, block_bottom + title_h + gap)

        # Subtitle centered in the band below the image.
        subtitle.drawOn(c, doc.leftMargin,
                        (doc.bottomMargin + img_bottom) / 2.0 - sub_h / 2.0)

    return draw_cover


def instruction_page(story, title, subtitle, flowables):
    tp = Paragraph(title, page_title)
    tp._toc_text = title + (" — " + subtitle if subtitle else "")
    story.append(tp)
    if subtitle:
        story.append(Paragraph(subtitle, page_subtitle))
    story.extend(flowables)


def build(cfg, path):
    files = glob.glob(os.path.join(cfg["source_dir"], "*.html"))
    pages = []
    for p in files:
        pages.extend(build_page(p, cfg["data_dir"]))
    if not pages:
        sys.exit("No pages found in " + cfg["source_dir"])
    # Stable sort by title keeps multiple sections from one page in document order.
    pages.sort(key=lambda e: e[0].lower())

    doc = BookletDoc(
        path, pagesize=HALF_LETTER,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
        title=cfg["cover_title"], author=COVER_KICKER.title())

    story = []

    # Page 1 is the cover, painted by the cover drawer; leave its frame empty.
    story.append(PageBreak())

    # Table of contents
    story.append(Paragraph("Table of Contents", toc_title))
    toc = TableOfContents()
    toc.levelStyles = [toc_entry]
    story.append(toc)

    # One booklet page per section (alpha by title, doc order within a title)
    for title, subtitle, flowables in pages:
        story.append(PageBreak())
        instruction_page(story, title, subtitle, flowables)

    # multiBuild: two passes so the ToC page numbers resolve; NumberedCanvas
    # stamps the "Page n of N" footers on the final pass.
    doc.multiBuild(story, onFirstPage=make_cover_drawer(cfg),
                   canvasmaker=NumberedCanvas)
    print("wrote", path, "(%d pages)" % len(pages))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in BOOKLETS:
        sys.exit("usage: build_booklet_pdf.py <%s> [output.pdf]"
                 % "|".join(BOOKLETS))
    cfg = BOOKLETS[sys.argv[1]]
    out = sys.argv[2] if len(sys.argv) > 2 else cfg["default_output"]
    build(cfg, out)
