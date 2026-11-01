"""Rebuild only the public-listing screening figure from local project data.

Run from any directory with: python docs/reproduce_data_quality_funnel.py
This script never runs Spark or writes to the report, slides, or original figure.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
FIGURE = ROOT / "docs" / "figures" / "data_quality_funnel_reproduced.png"
RAW = ROOT / "data" / "raw" / "public_datasets" / "kaggle_vietnam_house_rent"
LEDGER = ROOT / "data" / "curation" / "kaggle_hanoi_title_review.csv"
MANIFEST = ROOT / "data" / "public_pilot" / "mart" / "run_manifest.json"
QUALITY = ROOT / "data" / "public_pilot" / "mart" / "quality"
CURATED = ROOT / "data" / "public_pilot" / "curated" / "listings"


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def parquet_table(directory: Path):
    parts = sorted(directory.glob("part-*.parquet"))
    if not parts or not (directory / "_SUCCESS").exists():
        raise FileNotFoundError(f"Completed public pipeline output is missing: {directory}")
    return pq.read_table(parts)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def measured_counts() -> tuple[dict[str, int], Counter[str]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    listing_lineage = manifest["source_lineage"]["listings"]
    raw_counts = {}
    fingerprints = set()
    for item in listing_lineage["raw_files"]:
        path = ROOT / "data" / "raw" / "public_datasets" / item["path"]
        check(path.is_file(), f"Missing source CSV: {path}")
        check(path.stat().st_size == item["bytes"], f"Source CSV size changed since the public run: {path}")
        check(hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"],
              f"Source CSV changed since the public run: {path}")
        rows = csv_rows(path)
        raw_counts[path.name] = len(rows)
        if path.name == "hn.csv":
            for row in rows:
                fields = ["hn", *(row.get(key) or "" for key in
                                  ("title", "published", "address", "acreage", "price"))]
                fingerprints.add(hashlib.sha256("\x1f".join(fields).encode("utf-8")).hexdigest())

    ledger_rows = csv_rows(LEDGER)
    dispositions = Counter(row["review_status"] for row in ledger_rows)
    check(set(dispositions) <= {"include", "ambiguous", "exclude_room_offer", "exclude_sale"},
          f"Unexpected ledger disposition: {dispositions}")
    ledger_fingerprints = [row["source_fingerprint"] for row in ledger_rows]
    check(len(set(ledger_fingerprints)) == len(ledger_rows), "Duplicate fingerprint in review ledger")
    check(set(ledger_fingerprints) <= fingerprints, "Review ledger does not match the current Hanoi CSV")

    quality_parts = list(QUALITY.glob("part-*.parquet"))
    curated_parts = list(CURATED.glob("part-*.parquet"))
    check(bool(quality_parts and curated_parts), "Public pipeline outputs are missing")
    oldest_output = min(part.stat().st_mtime_ns for part in quality_parts + curated_parts)
    check(LEDGER.stat().st_mtime_ns <= oldest_output and
          all((RAW / name).stat().st_mtime_ns <= oldest_output for name in raw_counts),
          "An input is newer than the public pipeline outputs; rerun the public pipeline first")

    quality = parquet_table(QUALITY)
    q = dict(zip(quality["quality_reason"].to_pylist(), quality["records"].to_pylist()))
    curated = parquet_table(CURATED)
    check(all(amount is not None and amount > 0 and area is not None and area > 0
              for amount, area in zip(curated["listed_amount_vnd"].to_pylist(),
                                      curated["area_m2"].to_pylist())),
          "Curated Parquet contains a nonpositive or missing amount/area")
    total = sum(raw_counts.values())
    hanoi = raw_counts["hn.csv"]
    valid = curated.num_rows
    check(sum(q.values()) == total, "Quality dispositions do not sum to source rows")
    check(q.get("outside_hanoi_partition", 0) == total - hanoi,
          "Quality output disagrees with the Hanoi partition count")
    check(q.get("valid_exploratory_rental", 0) == valid,
          "Curated rows disagree with the quality output")
    check(dispositions["include"] == valid + q.get("included_price_unknown", 0) + q.get("invalid_area", 0),
          "Included ledger rows disagree with the public quality output")
    check(dispositions["exclude_room_offer"] == q.get("room_or_shared_stay_excluded", 0),
          "Room exclusions disagree with the public quality output")
    check(dispositions["exclude_sale"] == q.get("apartment_sale_excluded", 0),
          "Sale exclusions disagree with the public quality output")
    check(total == listing_lineage["input_rows_all_partitions"] and
          hanoi == listing_lineage["input_rows_hanoi_partition"] and
          valid == listing_lineage["curated_positive_amount_area_rows"],
          "Current counts disagree with the public run manifest")

    counts = {"all": total, "hanoi": hanoi, "ledger": len(ledger_rows),
              "likely": dispositions["include"], "valid": valid,
              "unknown": q.get("included_price_unknown", 0),
              "invalid_area": q.get("invalid_area", 0)}
    return counts, dispositions


def draw(counts: dict[str, int], dispositions: Counter[str]) -> None:
    navy, ink, muted = "#172a43", "#293d50", "#506276"
    fig = plt.figure(figsize=(14.56, 7.2), dpi=180, facecolor="white")
    grid = fig.add_gridspec(1, 2, left=0.175, right=0.95, top=0.82, bottom=0.17,
                            width_ratios=(1.35, 1), wspace=0.45)
    left, right = (fig.add_subplot(grid[0, i]) for i in range(2))
    fig.text(0.058, 0.955, "Measured public-listing screening counts",
             fontsize=20, weight="bold", color=navy, va="top")

    left_labels = ["All source listing rows", "Hanoi partition", "Manual ledger candidates",
                   "Title-reviewed likely rentals", "Positive amount + area curated"]
    left_values = [counts[key] for key in ("all", "hanoi", "ledger", "likely", "valid")]
    left_colors = ["#477dac", "#6497bd", "#7aabb3", "#e3aa4e", "#4aa07d"]
    left.barh(left_labels, left_values, color=left_colors, height=0.62)
    left.invert_yaxis()
    left.set_xscale("log")
    left.set_xlim(70, max(left_values) * 1.8)
    left.set_title("Screening funnel", loc="left", fontsize=16, weight="bold", pad=8)
    left.set_xlabel("Rows (log scale)", fontsize=11)
    left.grid(axis="x", which="both", alpha=0.17)
    left.tick_params(axis="y", labelsize=10.5)
    left.tick_params(axis="x", labelsize=10)
    for i, value in enumerate(left_values):
        left.text(value * 1.06, i, f"{value:,}", ha="left", va="center",
                  fontsize=11, weight="bold", color=ink)

    right_labels = ["Likely whole-apartment\nrental", "Ambiguous",
                    "Room/shared stay\nexcluded", "Apartment sale\nexcluded"]
    right_values = [dispositions[key] for key in
                    ("include", "ambiguous", "exclude_room_offer", "exclude_sale")]
    right_colors = ["#4aa07d", "#d8a648", "#829bb5", "#c4675a"]
    right.barh(right_labels, right_values, color=right_colors, height=0.62)
    right.invert_yaxis()
    right.set_xlim(0, max(right_values) * 1.18)
    right.set_title(f"Ledger dispositions (n={counts['ledger']:,})", loc="left",
                    fontsize=16, weight="bold", pad=8)
    right.set_xlabel("Ledger records", fontsize=11)
    right.grid(axis="x", alpha=0.17)
    right.tick_params(axis="y", labelsize=10.5)
    right.tick_params(axis="x", labelsize=10)
    for i, value in enumerate(right_values):
        right.text(value + max(right_values) * 0.02, i, f"{value:,}",
                   ha="left", va="center", fontsize=11, weight="bold", color=ink)

    fig.text(0.175, 0.035,
             "Stages narrow by city, ledger coverage, title review, then usable numeric fields.",
             fontsize=9.3, color=muted)
    numeric_excluded = counts["likely"] - counts["valid"]
    fig.text(0.685, 0.035,
             f"Of {counts['likely']:,} likely rentals, {numeric_excluded:,} have unknown/nonpositive amount;\n"
             f"{counts['valid']:,} enter numeric summaries.",
             fontsize=9.3, color=muted)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, facecolor="white")
    plt.close(fig)


def main() -> None:
    counts, dispositions = measured_counts()
    print(f"Source listing rows: {counts['all']:,}; Hanoi partition: {counts['hanoi']:,}")
    print(f"Manual ledger candidates: {counts['ledger']:,}; title-reviewed likely rentals: {counts['likely']:,}")
    print(f"Positive amount and area: {counts['valid']:,}; excluded from numeric summaries: "
          f"{counts['likely'] - counts['valid']:,}")
    print("Ledger dispositions: " + ", ".join(f"{key}={dispositions[key]:,}" for key in
          ("include", "ambiguous", "exclude_room_offer", "exclude_sale")))
    draw(counts, dispositions)
    print(f"Wrote: {FIGURE}")


if __name__ == "__main__":
    main()
