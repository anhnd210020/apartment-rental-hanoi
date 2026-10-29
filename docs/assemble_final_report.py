"""Combine the user's cover with the latest verified report body.

The original DOCX remains read only. Word renders the assembled document and
PDF so it calculates pagination and the PAGE field.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

import win32com.client as win32
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.text.paragraph import Paragraph


PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
DEFAULT_COVER = PROJECT.parent.parent / "20261A_IT5427.docx"
DEFAULT_BODY = DOCS / "IT5427_Final_Report.docx"


def assemble(cover_path: Path, body_path: Path, output_path: Path) -> None:
    cover = Document(cover_path)
    body_doc = Document(body_path)
    first_body_index = next(
        i for i, paragraph in enumerate(cover.paragraphs)
        if paragraph.text.strip().startswith("MỞ ĐẦU")
    )

    # Keep the user's cover paragraphs and floating vector artwork. Recreate
    # the final date line so its old section relationships are not carried to
    # the new package; the current body starts on a new page below it.
    cover_nodes = [
        deepcopy(p._p) for p in cover.paragraphs[: first_body_index - 1]
    ]
    for paragraph in list(body_doc.paragraphs[:2]):
        paragraph._element.getparent().remove(paragraph._element)

    body = body_doc.element.body
    first_content = next(child for child in body if child.tag.endswith("}p"))
    index = body.index(first_content)
    for node in cover_nodes:
        body.insert(index, node)
        index += 1

    date = body_doc.add_paragraph("Hanoi, tháng 10 năm 2026")
    date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    date.style = "Normal"
    date.runs[0].font.name = "Times New Roman"
    date.runs[0].font.size = 14
    body.insert(index, date._p)
    Paragraph(first_content, body_doc._body).paragraph_format.page_break_before = True

    output_path.parent.mkdir(parents=True, exist_ok=True)
    body_doc.save(output_path)


def render_with_word(docx_path: Path, pdf_path: Path) -> int:
    app = win32.DispatchEx("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0
    doc = None
    try:
        doc = app.Documents.Open(str(docx_path), ReadOnly=False, AddToRecentFiles=False)
        doc.Repaginate()
        doc.Fields.Update()
        for section in doc.Sections:
            for footer in section.Footers:
                footer.Range.Fields.Update()
        doc.Save()
        pages = doc.ComputeStatistics(2)
        doc.ExportAsFixedFormat(str(pdf_path), 17)
        return pages
    finally:
        if doc is not None:
            doc.Close(SaveChanges=0)
        app.Quit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cover-docx", type=Path, default=DEFAULT_COVER)
    parser.add_argument("--body-docx", type=Path, default=DEFAULT_BODY)
    parser.add_argument("--output-dir", type=Path, default=DOCS)
    parser.add_argument("--stem", default="IT5427_Final_Report_2026-10-29")
    args = parser.parse_args()
    output_docx = args.output_dir / f"{args.stem}.docx"
    output_pdf = args.output_dir / f"{args.stem}.pdf"
    assemble(args.cover_docx, args.body_docx, output_docx)
    pages = render_with_word(output_docx, output_pdf)
    print(f"DOCX: {output_docx} ({output_docx.stat().st_size:,} bytes)")
    print(f"PDF:  {output_pdf} ({output_pdf.stat().st_size:,} bytes)")
    print(f"Word page count: {pages}")


if __name__ == "__main__":
    main()
