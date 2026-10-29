"""Export final_report.md to DOCX/PDF through installed Microsoft Word."""
from pathlib import Path
import re
import argparse

import markdown
import win32com.client as win32

DOCS = Path(__file__).resolve().parent
MD = DOCS / "final_report.md"
DOCX = DOCS / "IT5427_Final_Report.docx"
PDF = DOCS / "IT5427_Final_Report.pdf"
HTML = DOCS / ".final_report_word_import.html"

CSS = """
@page { size: A4; margin: 17mm 18mm 18mm 18mm; }
body { font-family: Arial, sans-serif; font-size: 10pt; color: #243244; line-height: 1.12; }
h1 { color: #162d48; font-size: 19pt; margin: 0 0 8pt; }
h2 { color: #1e4467; font-size: 14pt; margin: 12pt 0 5pt; page-break-after: avoid; }
h3 { color: #287b7c; font-size: 11pt; margin: 9pt 0 4pt; page-break-after: avoid; }
p { margin: 0 0 5pt; }
ul, ol { margin-top: 2pt; margin-bottom: 6pt; }
li { margin-bottom: 2pt; }
table { border-collapse: collapse; width: 100%; font-size: 8pt; margin: 5pt 0 8pt; }
th { background: #e7eef5; color: #18334f; font-weight: bold; }
td, th { border: 0.5pt solid #aebbc8; padding: 3pt 4pt; vertical-align: top; }
pre { background: #f2f5f8; border: 0.5pt solid #d6dfe7; padding: 5pt; font-size: 8pt; white-space: pre-wrap; }
code { font-family: Consolas, monospace; font-size: 9pt; }
img { max-width: 100%; height: auto; }
p.report-figure { text-align: center; margin: 7pt 0 2pt; page-break-after: avoid; }
p.caption { text-align: center; font-size: 9pt; color: #36485c; margin: 1pt 0 7pt; page-break-before: avoid; }
"""


def build_html(html_path):
    source = MD.read_text(encoding="utf-8")
    body = markdown.markdown(source, extensions=["tables", "fenced_code", "sane_lists"])
    base = DOCS.as_uri() + "/"
    body = body.replace('src="figures/', f'src="{base}figures/')
    body = re.sub(r"<p><img\b", '<p class="report-figure"><img', body)
    body = re.sub(r"<p><strong>(Hình [123]\.)", r'<p class="caption"><strong>\1', body)
    html_path.write_text(
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        + CSS
        + "</style></head><body>"
        + body
        + "</body></html>",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DOCS)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    docx_path = args.output_dir / "IT5427_Final_Report.docx"
    pdf_path = args.output_dir / "IT5427_Final_Report.pdf"
    html_path = args.output_dir / ".final_report_word_import.html"
    build_html(html_path)
    app = win32.DispatchEx("Word.Application")
    try:
        app.Visible = False
    except Exception:
        app.Visible = True
        try:
            app.WindowState = 2
        except Exception:
            pass
    app.DisplayAlerts = 0
    doc = None
    try:
        doc = app.Documents.Open(str(html_path), ReadOnly=False, AddToRecentFiles=False)
        for section in doc.Sections:
            setup = section.PageSetup
            setup.PaperSize = 7  # A4
            setup.Orientation = 0  # portrait
            setup.TopMargin = 48
            setup.BottomMargin = 48
            setup.LeftMargin = 50
            setup.RightMargin = 50

        for i in range(1, doc.Paragraphs.Count + 1):
            paragraph = doc.Paragraphs(i)
            value = paragraph.Range.Text.replace("\r", "").strip()
            try:
                if paragraph.Range.InlineShapes.Count:
                    paragraph.Alignment = 1
                    paragraph.Format.KeepWithNext = True
                if value.startswith("Hình "):
                    paragraph.Alignment = 1
                    paragraph.Range.Font.Name = "Arial"
                    paragraph.Range.Font.Size = 9
                    paragraph.Range.Font.Italic = True
                    paragraph.Format.KeepWithNext = True
                elif value and value.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "11.", "12.")):
                    pass
                style = paragraph.Range.Style.NameLocal
                if style.startswith("Heading"):
                    paragraph.Format.KeepWithNext = True
            except Exception:
                pass

        for i in range(1, doc.InlineShapes.Count + 1):
            inline = doc.InlineShapes(i)
            inline.LockAspectRatio = -1
            if inline.Width > 490:
                inline.Width = 490
            try:
                # Word imports file:// images as linked shapes unless asked to
                # store the source image inside the document package.
                inline.LinkFormat.SavePictureWithDocument = True
                inline.LinkFormat.BreakLink()
            except Exception:
                pass

        for i in range(1, doc.Tables.Count + 1):
            table = doc.Tables(i)
            table.AllowAutoFit = True
            table.AutoFitBehavior(2)  # fit to page width
            table.Range.Font.Name = "Arial"
            table.Range.Font.Size = 8
            try:
                table.Rows.AllowBreakAcrossPages = False
            except Exception:
                pass

        # A small page number footer; the report content and figures remain editable.
        try:
            footer = doc.Sections(1).Footers(1).Range
            footer.Text = "IT5427  •  2026-10-29  •  "
            footer.Collapse(0)
            footer.Fields.Add(footer, 33)  # PAGE field
            footer.ParagraphFormat.Alignment = 2
            footer.Font.Name = "Arial"
            footer.Font.Size = 8
            footer.Font.Color = 0x806F5E
        except Exception:
            pass

        doc.SaveAs2(str(docx_path), FileFormat=16)
        pages = doc.ComputeStatistics(2)
        doc.ExportAsFixedFormat(str(pdf_path), 17)
    finally:
        if doc is not None:
            doc.Close(SaveChanges=0)
        app.Quit()
        try:
            html_path.unlink()
        except FileNotFoundError:
            pass
    print(f"DOCX: {docx_path} ({docx_path.stat().st_size:,} bytes)")
    print(f"PDF:  {pdf_path} ({pdf_path.stat().st_size:,} bytes)")
    print(f"Word page count: {pages}; embedded figures: 3; tables: 5")


if __name__ == "__main__":
    main()
