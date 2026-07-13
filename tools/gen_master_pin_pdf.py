#!/usr/bin/env python3
# Builds the Johnny 4 MASTER PIN DIAGRAM PDF: one full letter page per board,
# in signal-chain order. Content is pulled live from each repo's README
# ("## Pin diagram" fenced block + "## Pin assignments" markdown table) so the
# master document always matches the repos. Also regenerates the standalone
# j4_controller_pin_diagram.pdf with the identical page so the two never drift.
#
# Table style matches the original per-repo PDFs: dark header row with white
# bold text, thin grey gridlines, and alternating white / light-grey body rows.

import html
import os
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

W, H = letter
# This script lives in johnny_4_docs/tools/; the board repos are expected to
# be checked out as siblings of johnny_4_docs.
DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS = os.path.dirname(DOCS_DIR)
OUT = os.path.join(DOCS_DIR, "j4_master_pin_diagram.pdf")

TABLE_X = 60                 # table left edge
TABLE_W = W - 2 * TABLE_X    # table width
PIN_COL_W = 95               # first column width

BOARDS = [
    ("j4_controller",    "TTGO T-Display v1.1, rails visible, USB-C at the TOP (as mounted)"),
    ("j4_receiver",      "TTGO T-Display v1.1, rails visible, USB-C at the TOP (as mounted)"),
    ("j4_stepper_neck",  "ESP32-D0WD (LOLIN32-Lite style), component side up, USB-C at the BOTTOM"),
    ("j4_stepper_eyes",  "ESP32-D0WD (LOLIN32-Lite style), component side up, USB-C at the BOTTOM"),
    ("j4_talk",          "Teensy 4.1 + Audio Shield Rev D, component side up, USB at the TOP"),
    ("j4_display_left",  "SeeedStudio XIAO ESP32S3, component side up, USB-C at the TOP"),
    ("j4_display_right", "SeeedStudio XIAO ESP32S3, component side up, USB-C at the TOP"),
]


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def diagram_block(md):
    """First fenced code block after the '## Pin diagram' heading."""
    m = re.search(r"^## Pin diagram.*?^```\n(.*?)^```", md, re.S | re.M)
    if not m:
        raise SystemExit("no pin diagram fence found")
    return m.group(1).rstrip("\n").split("\n")


def ads_block(md):
    """First fenced code block after the optional '## ADS1115 pin diagram(s)'
    heading. Boards with local ADS1115 ADCs get an extra page from it."""
    m = re.search(r"^## ADS1115 pin diagrams?.*?^```\n(.*?)^```", md, re.S | re.M)
    if not m:
        return None
    return m.group(1).rstrip("\n").split("\n")


def pin_table(md):
    """Rows of the markdown table under '## Pin assignments'.
    3-column display tables collapse to 'D0 (GPIO1)' style pin labels."""
    m = re.search(r"^## Pin assignments\n(.*?)(?=^## )", md, re.S | re.M)
    if not m:
        raise SystemExit("no pin assignments section found")
    rows = []
    for line in m.group(1).split("\n"):
        line = line.strip()
        if not line.startswith("|") or re.match(r"^\|[\s\-|]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == 3:
            cells = [f"{cells[0]} ({cells[1]})", cells[2]]
        rows.append(cells[:2])
    return rows


def build_table(rows, size):
    """Zebra-striped table like the original per-repo pin diagram PDFs."""
    hdr = ParagraphStyle("hdr", fontName="Helvetica-Bold", fontSize=size + 1,
                         leading=size + 3, textColor=colors.white)
    body = ParagraphStyle("body", fontName="Helvetica", fontSize=size,
                          leading=size + 2)
    data = [[Paragraph(html.escape(cell), hdr if i == 0 else body)
             for cell in row]
            for i, row in enumerate(rows)]
    t = Table(data, colWidths=[PIN_COL_W, TABLE_W - PIN_COL_W])
    style = [
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#3b3b3b")),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#9a9a9a")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]
    for i in range(2, len(rows), 2):   # every other body row, light grey
        style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#e9e9e9")))
    t.setStyle(TableStyle(style))
    return t


def draw_page(c, name, subtitle, diagram, rows):
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, H - 55, f"{name} -- pin diagram")
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, H - 72, subtitle)

    # Auto-fit: shrink the diagram and table together until the page holds both.
    for dsize, dlead, tsize in ((9, 12.5, 9), (8.5, 11.5, 8.5), (8, 10.5, 8), (7, 9.5, 7.5)):
        t = build_table(rows, tsize)
        _, th = t.wrapOn(c, TABLE_W, H)
        needed = 105 + len(diagram) * dlead + 22 + th + 25
        if needed <= H:
            break

    # Longest diagram line decides the left margin so wide pages stay centered.
    width = max(len(l) for l in diagram)
    x = max(30, (W - width * dsize * 0.6) / 2)

    y = H - 105
    c.setFont("Courier", dsize)
    for line in diagram:
        c.drawString(x, y, line)
        y -= dlead

    t.drawOn(c, TABLE_X, y - 22 - th)
    c.showPage()


def draw_ads_page(c, name, diagram):
    """Extra diagram-only page: the board's ADS1115 module pinouts."""
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, H - 55, f"{name} -- ADS1115 pin diagrams")
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, H - 72,
                        "pot wiper to the A-pin; outer legs to 3.3V and GND")

    # Auto-fit: shrink until the page holds the whole block.
    for dsize, dlead in ((9, 12.5), (8.5, 11.5), (8, 10.5), (7, 9.5)):
        if 105 + len(diagram) * dlead + 25 <= H:
            break

    width = max(len(l) for l in diagram)
    x = max(30, (W - width * dsize * 0.6) / 2)

    y = H - 105
    c.setFont("Courier", dsize)
    for line in diagram:
        c.drawString(x, y, line)
        y -= dlead
    c.showPage()


pages = []
for name, subtitle in BOARDS:
    md = read(f"{PROJECTS}/{name}/README.md")
    pages.append((name, subtitle, diagram_block(md), pin_table(md), ads_block(md)))

c = canvas.Canvas(OUT, pagesize=letter)
c.setTitle("Johnny 4 -- master pin diagram")
for name, subtitle, diagram, rows, ads in pages:
    draw_page(c, name, subtitle, diagram, rows)
    if ads:
        draw_ads_page(c, name, ads)
c.save()
print("wrote", OUT)

# Standalone controller PDF, same page(s) as in the master document.
solo = f"{PROJECTS}/j4_controller/j4_controller_pin_diagram.pdf"
c = canvas.Canvas(solo, pagesize=letter)
c.setTitle("j4_controller -- pin diagram")
name, subtitle, diagram, rows, ads = pages[0]
draw_page(c, name, subtitle, diagram, rows)
if ads:
    draw_ads_page(c, name, ads)
c.save()
print("wrote", solo)
