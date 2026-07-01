from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "case-study.md"
OUTPUT = ROOT / "docs" / "case-study.pdf"


def clean_inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2' color='#1d4ed8'>\1</a>", text)
    return text.replace("&", "&amp;").replace("&amp;lt;", "&lt;").replace("&amp;gt;", "&gt;")


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#172033"),
            spaceAfter=18,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4b5870"),
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "Heading1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=22,
            textColor=colors.HexColor("#172033"),
            spaceBefore=8,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#263244"),
            spaceBefore=6,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.6,
            leading=13.2,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#172033"),
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=12.8,
            leftIndent=18,
            firstLineIndent=-9,
            spaceAfter=4,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.5,
            leading=10,
            backColor=colors.HexColor("#f1f5f9"),
            borderColor=colors.HexColor("#d9dee8"),
            borderWidth=0.5,
            borderPadding=5,
            spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#4b5870"),
            spaceAfter=4,
        ),
    }


def table_from_lines(lines: list[str], styles: dict) -> Table:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        rows.append([Paragraph(clean_inline(cell), styles["small"]) for cell in cells])
    col_count = max(len(row) for row in rows)
    width = 6.9 * inch
    col_widths = [width / col_count] * col_count
    table = Table(rows, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#172033")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9dee8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def markdown_to_flowables(markdown: str) -> list:
    styles = build_styles()
    story = []
    lines = markdown.splitlines()
    i = 0
    in_code = False
    code_lines: list[str] = []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped == "<!-- pagebreak -->":
            story.append(PageBreak())
        elif stripped.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["code"]))
                code_lines = []
                in_code = False
            else:
                in_code = True
        elif in_code:
            code_lines.append(line)
        elif stripped.startswith("|") and "|" in stripped[1:]:
            table_lines = [stripped]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            i -= 1
            story.append(table_from_lines(table_lines, styles))
            story.append(Spacer(1, 8))
        elif stripped.startswith("# "):
            story.append(Paragraph(clean_inline(stripped[2:]), styles["title"]))
        elif stripped.startswith("## "):
            story.append(Paragraph(clean_inline(stripped[3:]), styles["h1"]))
        elif stripped.startswith("### "):
            story.append(Paragraph(clean_inline(stripped[4:]), styles["h2"]))
        elif stripped.startswith("- "):
            story.append(Paragraph("- " + clean_inline(stripped[2:]), styles["bullet"]))
        elif re.match(r"^\d+\. ", stripped):
            story.append(Paragraph(clean_inline(stripped), styles["bullet"]))
        elif stripped:
            style = styles["subtitle"] if len(story) < 4 else styles["body"]
            story.append(Paragraph(clean_inline(stripped), style))
        else:
            story.append(Spacer(1, 4))
        i += 1
    return story


class NumberedCanvas:
    def __init__(self, canvas, doc):
        self.canvas = canvas
        self.doc = doc

    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#647084"))
        canvas.drawString(0.72 * inch, 0.45 * inch, "Visual Test Oracle - Engineering Case Study")
        canvas.drawRightString(7.78 * inch, 0.45 * inch, f"Page {doc.page}")
        canvas.restoreState()


def main() -> None:
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=LETTER,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.72 * inch,
        title="Visual Test Oracle Engineering Case Study",
        pageCompression=0,
    )
    story = markdown_to_flowables(SOURCE.read_text(encoding="utf-8"))
    footer = NumberedCanvas(None, None)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    page_count = len(PdfReader(str(OUTPUT)).pages)
    if page_count < 12:
        raise SystemExit(f"Expected at least 12 pages, produced {page_count}")
    print(f"Wrote {OUTPUT} ({page_count} pages)")


if __name__ == "__main__":
    main()
