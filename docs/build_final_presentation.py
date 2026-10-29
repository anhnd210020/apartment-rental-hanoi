"""Rebuild the IT5427 deck with the latest verified local results.

Uses installed Microsoft PowerPoint through COM and embeds the report figures.
Run with a Python installation that has pywin32 and Microsoft Office available.
"""
from pathlib import Path
import tempfile
import argparse

import win32com.client as win32
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "docs" / "figures"
DEFAULT_TARGET = ROOT / "docs" / "IT5427_final_presentation.pptx"

W, H = 960, 540
NAVY = (20, 39, 63)
BLUE = (47, 92, 137)
TEAL = (38, 137, 137)
GOLD = (222, 166, 69)
RED = (181, 83, 78)
INK = (34, 50, 69)
MUTED = (94, 111, 128)
PAPER = (248, 250, 252)
WHITE = (255, 255, 255)
PALE_BLUE = (232, 241, 251)
PALE_TEAL = (231, 245, 243)
PALE_GOLD = (255, 246, 226)
PALE_RED = (250, 237, 235)


def rgb(color):
    r, g, b = color
    return r + (g << 8) + (b << 16)


def set_bg(slide, color):
    slide.FollowMasterBackground = False
    slide.Background.Fill.Solid()
    slide.Background.Fill.ForeColor.RGB = rgb(color)


def text(slide, value, x, y, w, h, size=18, color=INK, bold=False,
         align=1, font="Aptos", valign=1, margin=4):
    shape = slide.Shapes.AddTextbox(1, x, y, w, h)
    shape.Line.Visible = 0
    tf = shape.TextFrame
    tf.WordWrap = True
    tf.AutoSize = 0
    tf.MarginLeft = margin
    tf.MarginRight = margin
    tf.MarginTop = 2
    tf.MarginBottom = 2
    tf.VerticalAnchor = valign
    tr = tf.TextRange
    tr.Text = value
    tr.Font.Name = font
    tr.Font.Size = size
    tr.Font.Bold = bold
    tr.Font.Color.RGB = rgb(color)
    tr.ParagraphFormat.Alignment = align
    return shape


def rect(slide, x, y, w, h, fill, line=None, rounded=True):
    kind = 5 if rounded else 1
    shape = slide.Shapes.AddShape(kind, x, y, w, h)
    shape.Fill.Solid()
    shape.Fill.ForeColor.RGB = rgb(fill)
    shape.Line.Visible = 1 if line else 0
    if line:
        shape.Line.ForeColor.RGB = rgb(line)
        shape.Line.Weight = 1
    return shape


def card(slide, x, y, w, h, title, body, accent=TEAL, fill=WHITE,
         title_size=17, body_size=14):
    rect(slide, x, y, w, h, fill, (222, 229, 236))
    rect(slide, x, y, 7, h, accent, None, rounded=False)
    text(slide, title, x + 18, y + 12, w - 32, 30, title_size, accent, True)
    text(slide, body, x + 18, y + 47, w - 32, h - 58, body_size, INK)


def add_slide(pres, section, title, subtitle=None):
    slide = pres.Slides.Add(pres.Slides.Count + 1, 12)
    set_bg(slide, PAPER)
    rect(slide, 0, 0, W, 7, TEAL, None, rounded=False)
    text(slide, section.upper(), 38, 20, 880, 18, 10, TEAL, True)
    text(slide, title, 36, 42, 888, 45, 27, NAVY, True)
    if subtitle:
        text(slide, subtitle, 38, 87, 885, 28, 12, MUTED)
    rect(slide, 38, 513, 884, 1, (219, 226, 234), None, rounded=False)
    text(slide, "IT5427  •  Hanoi  •  Local exploratory prototype", 40, 518,
         760, 16, 9, MUTED)
    text(slide, f"{pres.Slides.Count:02d} / 11", 850, 518, 70, 16,
         9, MUTED, align=3)
    return slide


def add_image_contain(slide, path, x, y, w, h):
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    sw, sh = iw * scale, ih * scale
    left, top = x + (w - sw) / 2, y + (h - sh) / 2
    return slide.Shapes.AddPicture(str(path), False, True, left, top, sw, sh)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_TARGET.parent)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    target = args.output_dir / DEFAULT_TARGET.name
    app = win32.DispatchEx("PowerPoint.Application")
    # PowerPoint's COM server rejects Visible=False; keep it minimized during export.
    app.Visible = True
    try:
        app.WindowState = 2
    except Exception:
        pass
    pres = app.Presentations.Add()
    try:
        pres.PageSetup.SlideSize = 7  # custom 16:9 canvas in points
        pres.PageSetup.SlideWidth = W
        pres.PageSetup.SlideHeight = H
        while pres.Slides.Count:
            pres.Slides(pres.Slides.Count).Delete()

        # 1 — Title and scope
        s = pres.Slides.Add(1, 12)
        set_bg(s, NAVY)
        rect(s, 0, 0, 12, H, TEAL, None, rounded=False)
        text(s, "IT5427  •  FINAL PRESENTATION", 60, 50, 820, 24, 13,
             (135, 213, 207), True)
        text(s, "HANOI APARTMENT\nRENTAL DATA INTEGRATION", 58, 111,
             830, 142, 32, WHITE, True)
        text(s, "A locally runnable PySpark prototype with city-grain context",
             62, 267, 820, 34, 18, (215, 226, 237))
        rect(s, 62, 332, 835, 2, (68, 91, 116), None, rounded=False)
        text(s, "29 OCT 2026   •   VERIFIED RUN: public-20261029T083945Z",
             62, 353, 830, 30, 13, (217, 227, 237), True)
        card(s, 62, 414, 254, 76, "1 listing source", "Kaggle rental-oriented rows", TEAL, (31, 57, 82), 16, 12)
        card(s, 335, 414, 254, 76, "1 aggregate source", "NEST • optional, separate", (170, 136, 205), (31, 57, 82), 16, 12)
        card(s, 608, 414, 289, 76, "2 context sources", "OSM + WorldPop • city grain", GOLD, (31, 57, 82), 16, 12)
        text(s, "Exploratory prototype • not a market-wide estimate • no streaming",
             62, 500, 835, 22, 12, (226, 194, 129), True)

        # 2 — Problem and scope
        s = add_slide(pres, "01 / Scope", "A clear integration problem with explicit limits",
                      "Listing titles and prices are inconsistent; only reliable shared keys are used.")
        card(s, 42, 146, 270, 222, "Input problem",
             "• Apartment and transaction type are not structured\n\n• Most amounts have no time basis\n\n• Listing geography is free text",
             BLUE, WHITE, 17, 14)
        card(s, 345, 146, 270, 222, "Implemented",
             "• Separate synthetic, public and optional NEST paths\n\n• PySpark validation, review labels and Parquet\n\n• OSM + WorldPop city context",
             TEAL, WHITE, 17, 14)
        card(s, 648, 146, 270, 222, "Interpretation",
             "• 102 title-reviewed likely rentals with usable amount and area\n\n• Monthly statistics use verified records only\n\n• No neighborhood or market-wide claims",
             GOLD, WHITE, 17, 14)
        rect(s, 42, 398, 876, 72, PALE_GOLD, None)
        text(s, "Kaggle is one listing dataset; NEST is an independent aggregate rental source.",
             62, 412, 836, 24, 17, NAVY, True, align=2)
        text(s, "OSM and WorldPop are geographic context. NEST is not joined to listing rows or the Kaggle city mart.",
             62, 439, 836, 20, 11, MUTED, align=2)

        # 3 — Sources and provenance
        s = add_slide(pres, "02 / Data sources", "Four sources, three distinct roles",
                      "Kaggle listings • NEST rental aggregates • OSM and WorldPop geographic context.")
        cards = [
            (42, "Kaggle listings", "Vietnam House Rent Dataset\n\n13,785 source rows; 3,284 Hanoi rows\n\nOne rental-oriented listing dataset. Uploader declares CC0; upstream rights remain unresolved.", BLUE),
            (267, "NEST aggregates", "Hanoi Rent Index CSV\n\n45 cells; 28 published; 17 suppressed\n\nNEST's own monthly asking rents. Terms state no open reuse license; optional local input.", (133, 91, 165)),
            (492, "OpenStreetMap", "Geofabrik Vietnam PBF\n\nSnapshot 2026-09-30\n\nODbL 1.0; attribute contributors. One prepared Hanoi context aggregate.", TEAL),
            (717, "WorldPop", "Vietnam population count\n\nReference year 2020; 408,151 valid cells\n\nCC BY 4.0; University of Southampton.", GOLD),
        ]
        for x, title_, body, accent in cards:
            card(s, x, 139, 201, 251, title_, body, accent, WHITE, 14, 11)
        rect(s, 42, 400, 876, 73, PALE_RED, None)
        text(s, "NEST aggregate rows are not listing records. TiniX is excluded because rental-versus-sale status is unvalidated; the three-record Batdongsan pilot is not in the public manifest.",
             61, 412, 836, 50, 12, INK, align=2)

        # 4 — 3V evidence
        s = add_slide(pres, "03 / 3V evidence", "Volume and variety are demonstrated; listing Velocity is open",
                      "Counts include separate context inputs and must not be presented as rental listings.")
        card(s, 42, 150, 276, 225, "Volume",
             "13,785 Kaggle source rows\n3,284 Hanoi rows\n102 curated listing rows\n45 NEST aggregate cells\n408,151 WorldPop cells",
             BLUE, WHITE, 17, 14)
        card(s, 342, 150, 276, 225, "Variety",
             "Kaggle listing CSV\nNEST aggregate CSV\nOSM PBF, prepared JSON and batch diff\nWorldPop GeoTIFF and CSV.gz\nSeparate Spark Parquet marts",
             TEAL, WHITE, 17, 14)
        card(s, 642, 150, 276, 225, "Velocity",
             "OSM seq. 4926: 9,555 / 6,385 / 1,969\nOSM seq. 4927: 14,572 / 5,901 / 2,284\n(create / modify / delete)\n\nBatch evidence only; no rental feed or repeat listing snapshot.",
             GOLD, WHITE, 17, 13)
        text(s, "NEST: 7 of 45 aggregate cells changed across two captures; 38 unchanged, 0 added/removed. Not listing Velocity.",
             52, 406, 856, 26, 13, MUTED, True, align=2)
        text(s, "OSM batch changes do not establish streaming or rental-listing Velocity.",
             52, 438, 856, 30, 15, RED, True, align=2)

        # 5 — Architecture
        s = add_slide(pres, "04 / Architecture", "Separate source grains through to the dashboard",
                      "Only OSM, WorldPop and the Kaggle summary join at Hanoi city grain; NEST stays separate.")
        add_image_contain(s, FIG / "architecture_diagram.png", 44, 124, 872, 360)

        # 6 — Quality funnel
        s = add_slide(pres, "05 / Data quality", "Screening counts show where review narrows the dataset",
                      "Manual review covers 303 apartment-cue candidates, not the full Hanoi partition.")
        add_image_contain(s, FIG / "data_quality_funnel.png", 42, 123, 876, 361)

        # 7 — Spark, lineage and timings
        s = add_slide(pres, "06 / Spark and storage", "Latest public run: 109.395 s Spark time; 119.97 s elapsed",
                      "Manifest public-20261029T083945Z • PySpark 3.5.9 • local[2] • two shuffle partitions")
        items = [
            ("Kaggle listings", "13,785 input rows → 102 curated rows\n2,491,539 source bytes • 13,883 Parquet bytes", "73.635 s", BLUE),
            ("OSM context", "1 prepared Hanoi JSON row → 1 city row\nPBF processed before Spark • 7,034 Parquet bytes", "1.545 s", TEAL),
            ("WorldPop", "408,151 valid raster cells\n3,410,996 Parquet bytes • city aggregate: 1 row", "6.391 s", GOLD),
            ("City integration", "OSM + WorldPop + listing summary\ncity_key=VN-HN • integrated output: 1 row", "26.073 s", RED),
        ]
        for i,(title_,body,time_,color) in enumerate(items):
            x=42+(i%2)*444; y=137+(i//2)*146
            card(s,x,y,420,124,title_,body,color,WHITE,16,12)
            text(s,time_,x+315,y+14,92,28,19,color,True,align=3)
        rect(s, 42, 438, 876, 54, NAVY, None)
        text(s, "Spark total 109.395 s   •   manifest elapsed 119.97 s   •   one local run, not a benchmark",
             54, 450, 852, 28, 14, WHITE, True, align=2)

        # 8 — Deduplication and entity resolution
        s = add_slide(pres, "07 / Entity handling", "Deduplication claims are limited to what the data supports",
                      "A public fingerprint links review rows; it is not a stable listing ID or a deduplication key.")
        card(s, 54, 154, 405, 244, "Synthetic fixtures",
             "• Drop duplicates by (source, source_listing_id)\n\n• Fixture IDs are generated for pipeline demonstration\n\n• Pilot Batdongsan check is only three records",
             TEAL, WHITE, 18, 15)
        card(s, 501, 154, 405, 244, "Public Kaggle path",
             "• No stable listing ID is present\n\n• SHA-256 fingerprint links titles to the review ledger\n\n• Fingerprint is not used to deduplicate\n\n• No cross-platform entity resolution",
             BLUE, WHITE, 18, 15)
        rect(s, 54, 427, 852, 56, PALE_GOLD, None)
        text(s, "No listing is matched across Kaggle, Batdongsan or TiniX.",
             70, 441, 820, 25, 17, NAVY, True, align=2)

        # 9 — Dashboard and descriptive results
        s = add_slide(pres, "08 / Dashboard", "NEST monthly aggregates show coverage and sample sizes",
                      "Latest 2026-10-29 capture plus aggregate-cell comparison; Kaggle's n=9 monthly subset remains separate.")
        add_image_contain(s, FIG / "nest_rent_aggregates.png", 52, 121, 856, 380)

        # 10 — Verification and OSM batch result
        s = add_slide(pres, "09 / Verification", "Spark paths and both dashboard views passed local checks",
                      "Pipelines, NEST comparison and AppTest checks recorded on 2026-10-29.")
        card(s, 42, 145, 425, 233, "Pipeline and dashboard",
             "Synthetic: 7 raw / 7 active / 5 valid / 4 unique\n\nPublic: 13,785 raw / 3,284 Hanoi / 102 curated / 408,151 WorldPop cells / 1 integrated city row\n\nNEST: 45 cells / 28 published / 17 suppressed\n\nAppTest: both views pass",
             TEAL, WHITE, 17, 14)
        card(s, 492, 145, 425, 233, "Recorded OSM update",
             "Seq. 4926 → 4927\n\n14,572 creates\n5,901 modifies\n2,284 deletes\n22,757 unique operations; no duplicates\n\nThis is Vietnam-wide OSM batch evidence.",
             GOLD, WHITE, 17, 14)
        rect(s, 42, 403, 875, 74, PALE_RED, None)
        text(s, "NEST: 2 captures; 7/45 cells changed, 38 unchanged, 0 added/removed • Aggregate and OSM changes are not rental-listing Velocity",
             58, 421, 843, 34, 16, RED, True, align=2)

        # 11 — Conclusion and limitations
        s = add_slide(pres, "10 / Conclusion", "A runnable prototype with city-level joins and known limits",
                      "The verified work supports a cautious demonstration, not a market estimate.")
        card(s, 42, 150, 276, 225, "What works",
             "• Reproducible local Spark paths\n\n• Saved quality dispositions and lineage\n\n• Separate NEST aggregate marts\n\n• OSM / WorldPop joined at city grain",
             TEAL, WHITE, 16, 14)
        card(s, 342, 150, 276, 225, "What remains unresolved",
             "• Kaggle upstream rights\n\n• NEST CSV reuse grant is unstated\n\n• Most Kaggle amounts have unknown time basis\n\n• NEST differences are aggregate-cell only; no listing Velocity",
             RED, WHITE, 16, 14)
        card(s, 642, 150, 276, 225, "Next decision",
             "Confirm the course definition of multi-source.\n\nIf another listing source is required, obtain permitted listing rows with documented provenance; NEST is aggregate-only.",
             GOLD, WHITE, 16, 14)
        rect(s, 42, 407, 876, 62, NAVY, None)
        text(s, "Conclusion: one listing dataset + one independent aggregate rental source + geographic context; no three-platform claim.",
             58, 423, 842, 29, 16, WHITE, True, align=2)

        pres.SaveAs(str(target))
        render = Path(tempfile.gettempdir()) / "it5427_presentation_render"
        render.mkdir(parents=True, exist_ok=True)
        pres.Export(str(render), "PNG", 1920, 1080)
        print(f"Saved {target} ({target.stat().st_size:,} bytes)")
        print(f"Slides: {pres.Slides.Count}; rendered: {render}")
    finally:
        pres.Close()
        app.Quit()


if __name__ == "__main__":
    main()
