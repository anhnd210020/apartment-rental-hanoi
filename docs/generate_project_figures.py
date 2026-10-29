"""Regenerate the report's architecture and NEST aggregate figures.

The NEST chart reads the registered local CSV and fails if it is unavailable;
it never fetches source data. Raw CSV stays under the ignored data/raw folder.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
FIGURES = Path(__file__).resolve().parent / "figures"
LATEST = ROOT / "data" / "public_pilot" / "mart" / "nest_rent_index" / "latest.json"
NAVY = "#17324d"
BLUE = "#3478a8"
TEAL = "#27847f"
GOLD = "#c68b2d"
PURPLE = "#7857a5"
INK = "#243244"
MUTED = "#596b7d"
PALE = "#f3f6f8"
LINE = "#b8c5d0"


def rounded_box(ax, xy, width, height, title, body, edge, fill="white", title_size=11, body_size=8.4):
    x, y = xy
    box = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.02,rounding_size=0.09",
        linewidth=1.5, edgecolor=edge, facecolor=fill, zorder=2,
    )
    ax.add_patch(box)
    title_y = y + (height - 0.18 if height < 0.7 else height - 0.25)
    body_y = y + (0.18 if height < 0.7 else height - 0.48)
    ax.text(x + 0.16, title_y, title, ha="left", va="top",
            fontsize=title_size, weight="bold", color=INK, zorder=3)
    ax.text(x + 0.16, body_y, body, ha="left", va="top",
            fontsize=body_size, color=MUTED, linespacing=1.25, zorder=3)


def arrow(ax, start, end, color=LINE, style="-", rad=0):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=12, linewidth=1.5,
        color=color, linestyle=style, connectionstyle=f"arc3,rad={rad}", zorder=1,
    ))


def architecture_png() -> None:
    fig, ax = plt.subplots(figsize=(14.2, 8.4), dpi=180)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 14.2)
    ax.set_ylim(-0.95, 7.7)
    ax.axis("off")
    ax.text(0.35, 7.38, "Apartment rental data prototype — implemented data paths",
            fontsize=18, weight="bold", color=NAVY)
    ax.text(0.35, 7.06, "Source roles and record grain remain explicit through the dashboard.",
            fontsize=10, color=MUTED)

    # Main public listing and geographic context lane.
    ax.text(0.35, 6.61, "PUBLIC LISTING + GEOGRAPHIC CONTEXT", fontsize=9, weight="bold", color=BLUE)
    rounded_box(ax, (0.35, 5.45), 2.15, 0.87, "Kaggle CSV", "One listing dataset\n13,785 source rows", BLUE)
    rounded_box(ax, (3.2, 5.45), 2.15, 0.87, "PySpark public path", "Schema, review ledger,\nquality and summaries", BLUE, fill="#f2f8fc")
    rounded_box(ax, (6.05, 5.45), 2.25, 0.87, "Listing marts", "102 curated rows\nsummary + quality", BLUE)
    rounded_box(ax, (0.35, 4.1), 2.15, 0.87, "OSM extract", "Prepared Hanoi city\naggregate", TEAL)
    rounded_box(ax, (3.2, 4.1), 2.15, 0.87, "OSM JSON", "Context stays at\ncity grain", TEAL, fill="#f1f9f8")
    rounded_box(ax, (6.05, 4.1), 2.25, 0.87, "OSM city mart", "One Hanoi aggregate", TEAL)
    rounded_box(ax, (0.35, 2.75), 2.15, 0.87, "WorldPop raster", "2020 source; clipped\nand converted to cells", GOLD)
    rounded_box(ax, (3.2, 2.75), 2.15, 0.87, "Spark cell path", "408,151 valid\nraster cells", GOLD, fill="#fcf8ef")
    rounded_box(ax, (6.05, 2.75), 2.25, 0.87, "WorldPop mart", "Cells + one city\naggregate", GOLD)
    rounded_box(ax, (8.95, 4.03), 2.2, 1.48, "City integration", "OSM + WorldPop +\nKaggle summary\ncity_key=VN-HN", NAVY, fill="#f2f5f8", title_size=12, body_size=9)

    arrow(ax, (2.5, 5.88), (3.2, 5.88), BLUE)
    arrow(ax, (5.35, 5.88), (6.05, 5.88), BLUE)
    arrow(ax, (2.5, 4.53), (3.2, 4.53), TEAL)
    arrow(ax, (5.35, 4.53), (6.05, 4.53), TEAL)
    arrow(ax, (2.5, 3.18), (3.2, 3.18), GOLD)
    arrow(ax, (5.35, 3.18), (6.05, 3.18), GOLD)
    arrow(ax, (8.3, 5.88), (8.95, 5.05), BLUE, rad=-0.05)
    arrow(ax, (8.3, 4.53), (8.95, 4.75), TEAL)
    arrow(ax, (8.3, 3.18), (8.95, 4.42), GOLD, rad=-0.08)

    # Independent aggregate source lane; intentionally no arrow to the city join.
    ax.text(0.35, 2.24, "OPTIONAL, INDEPENDENT RENTAL AGGREGATES — NOT LISTING ROWS", fontsize=9, weight="bold", color=PURPLE)
    rounded_box(ax, (0.35, 0.92), 2.15, 0.87, "NEST public CSV", "Monthly asking-rent\naggregate cells", PURPLE)
    rounded_box(ax, (3.2, 0.92), 2.15, 0.87, "Separate PySpark path", "Validate grain, suppression\nand source provenance", PURPLE, fill="#f7f3fb")
    rounded_box(ax, (6.05, 0.92), 2.25, 0.87, "NEST marts", "City, district, type\nand bedroom cuts", PURPLE)
    rounded_box(ax, (8.95, 0.92), 2.2, 0.87, "Two captures", "45 shared; 7 changed\n38 unchanged; 0 added/removed", PURPLE, fill="#fbf9fd")
    arrow(ax, (2.5, 1.35), (3.2, 1.35), PURPLE)
    arrow(ax, (5.35, 1.35), (6.05, 1.35), PURPLE)
    arrow(ax, (8.3, 1.35), (8.95, 1.35), PURPLE)
    ax.plot([8.65, 8.65], [-0.85, 6.14], color=PURPLE, linewidth=1.2, linestyle=(0, (3, 3)), alpha=0.7)

    rounded_box(ax, (11.72, 3.55), 2.15, 1.5, "Streamlit dashboard",
                "Coverage and roles\nNEST aggregates + n\nKaggle monthly n=9\nOSM / WorldPop context", NAVY,
                fill="#f2f5f8", title_size=11.5, body_size=8.5)
    arrow(ax, (11.15, 4.75), (11.72, 4.45), NAVY)
    arrow(ax, (8.3, 5.88), (11.72, 4.9), BLUE, rad=-0.08)
    arrow(ax, (8.3, 4.53), (11.72, 4.5), TEAL)
    arrow(ax, (8.3, 3.18), (11.72, 4.1), GOLD, rad=0.05)
    arrow(ax, (11.15, 1.35), (11.72, 3.8), PURPLE, style="--", rad=-0.08)

    ax.text(0.35, -0.03, "SYNTHETIC FIXTURES — SEPARATE TEST-ONLY PATH", fontsize=8.5, weight="bold", color=MUTED)
    rounded_box(ax, (0.35, -0.8), 2.15, 0.65, "Fixture JSONL", "generated records", MUTED, fill="#f6f8fa", title_size=9, body_size=7.4)
    rounded_box(ax, (3.2, -0.8), 2.15, 0.65, "Synthetic PySpark", "dedupe + quality", MUTED, fill="#f6f8fa", title_size=9, body_size=7.4)
    rounded_box(ax, (6.05, -0.8), 2.25, 0.65, "Fixture marts", "not real listings", MUTED, fill="#f6f8fa", title_size=9, body_size=7.4)
    arrow(ax, (2.5, -0.475), (3.2, -0.475), MUTED)
    arrow(ax, (5.35, -0.475), (6.05, -0.475), MUTED)
    ax.plot([8.3, 11.45, 11.45], [-0.475, -0.475, 3.65], color=MUTED, linewidth=1.2, linestyle="--", zorder=1)
    arrow(ax, (11.45, 3.65), (11.72, 3.78), MUTED, style="--")
    fig.savefig(FIGURES / "architecture_diagram.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def nest_chart() -> None:
    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / latest["manifest_path"]).read_text(encoding="utf-8"))
    raw_path = ROOT / manifest["raw_csv_path"]
    if not raw_path.exists():
        raise FileNotFoundError(f"Registered local NEST CSV is missing: {raw_path}")
    with raw_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    types = [row for row in rows if row["cut"] == "type" and row["published"].lower() == "true"]
    types.sort(key=lambda row: float(row["median_vnd"]))
    labels = [row["property_type"] for row in types]
    medians = [float(row["median_vnd"]) / 1_000_000 for row in types]
    homes = [int(row["homes"]) for row in types]
    city = next(row for row in rows if row["cut"] == "city")
    profile = manifest["profile"]
    comparison = json.loads((ROOT / "data" / "public_pilot" / "snapshot_comparison" / "nest_living_latest.json").read_text(encoding="utf-8"))
    delta = comparison["comparison"]

    fig = plt.figure(figsize=(12.2, 6.6), dpi=180, facecolor="white")
    grid = fig.add_gridspec(2, 1, height_ratios=[1.05, 3.35], hspace=0.34)
    top = fig.add_subplot(grid[0])
    top.axis("off")
    top.text(0.01, 0.96, "NEST Living — monthly asking-rent aggregates", fontsize=17, weight="bold", color=NAVY, transform=top.transAxes)
    top.text(0.01, 0.67,
             f"City cell: median {float(city['median_vnd'])/1_000_000:.1f}M VND/month  •  n={int(city['homes']):,} homes  •  captured {manifest['source_captured_at_utc']}",
             fontsize=10, color=INK, transform=top.transAxes)
    top.text(0.01, 0.38,
             f"{profile['row_count']} aggregate cells  •  {profile['published_cell_counts']['true']} published  •  {profile['suppressed_cells']} suppressed below sample floor {profile['minimum_sample_floor_values'][0]}",
             fontsize=9, color=MUTED, transform=top.transAxes)
    top.text(0.01, 0.07,
             f"Two genuine captures ({delta['old_source_captured_at_utc']} → {delta['new_source_captured_at_utc']}): {delta['changed_cells']} of {delta['shared_cells']} cells changed; {delta['unchanged_shared_cells']} unchanged; {delta['added_cells']} added / {delta['removed_cells']} removed. Aggregate changes only—not rental-listing Velocity.",
             fontsize=8.2, color=MUTED, transform=top.transAxes)

    ax = fig.add_subplot(grid[1])
    bars = ax.barh(labels, medians, color=[BLUE, TEAL, GOLD, PURPLE, "#c16a52"][:len(labels)], height=0.62)
    ax.set_xlabel("Published median monthly asking rent (million VND)", color=INK, labelpad=9)
    ax.set_title("Published NEST property-type cells", loc="left", fontsize=12, weight="bold", color=NAVY, pad=12)
    ax.grid(axis="x", color="#dce3e8", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#aebbc5")
    ax.tick_params(axis="y", length=0, labelcolor=INK, labelsize=9)
    ax.tick_params(axis="x", labelcolor=MUTED, labelsize=8)
    ax.set_xlim(0, max(medians) * 1.26)
    for bar, median, n in zip(bars, medians, homes):
        ax.text(median + max(medians) * 0.025, bar.get_y() + bar.get_height() / 2,
                f"{median:.1f}M  ·  n={n}", va="center", fontsize=9, color=INK)
    fig.text(0.105, 0.025,
             "NEST's own inventory only; n is homes behind each aggregate. Cells below five homes suppress rent statistics. "
             "This figure is not directly comparable with Kaggle listed amounts.",
             fontsize=8.4, color=MUTED)
    fig.savefig(FIGURES / "nest_rent_aggregates.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    FIGURES.mkdir(parents=True, exist_ok=True)
    architecture_png()
    nest_chart()
    print(f"Wrote {FIGURES / 'architecture_diagram.png'}")
    print(f"Wrote {FIGURES / 'nest_rent_aggregates.png'}")
