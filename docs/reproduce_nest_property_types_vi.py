"""Plot the NEST property-type chart in English from one local capture only.

Requires pandas, pyarrow and matplotlib. Does not download data or run Spark.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = "2026-10-29T09:15:25.078Z"
SNAPSHOT_ID = "nest-20261029T091525078Z"
MANIFEST = (ROOT / "data" / "public_pilot" / "mart" / "nest_rent_index"
            / SNAPSHOT_ID / "manifest.json")
OUTPUT = ROOT / "docs" / "figures" / "nest_property_types_vi_20261029T091525078Z.png"
VI_LABELS = {
    "Villa": "Villa",
    "Whole house": "Whole house",
    "Serviced apartment": "Serviced apartment",
    "Apartment": "Apartment",
    "Studio": "Studio",
}


def project_path(relative: str) -> Path:
    return ROOT / relative.replace("\\", "/")


def load_capture() -> tuple[pd.DataFrame, pd.Series]:
    if not MANIFEST.is_file():
        raise FileNotFoundError(f"Missing capture-specific provenance manifest: {MANIFEST}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["snapshot_id"] != SNAPSHOT_ID or manifest["source_captured_at_utc"] != CAPTURE:
        raise ValueError("Manifest identifies a different NEST capture")
    raw_manifest = project_path(manifest["raw_csv_path"]).with_suffix(".manifest.json")
    if not raw_manifest.is_file():
        raise FileNotFoundError(f"Missing raw snapshot provenance manifest: {raw_manifest}")
    raw_provenance = json.loads(raw_manifest.read_text(encoding="utf-8"))
    if (raw_provenance["snapshot_id"], raw_provenance["raw_csv_sha256"]) != (
        SNAPSHOT_ID, manifest["raw_csv_sha256"]
    ):
        raise ValueError("Raw and Parquet provenance manifests disagree")

    csv_path = project_path(manifest["raw_csv_path"])
    if not csv_path.is_file():
        raise FileNotFoundError(f"Required historical NEST snapshot is missing: {csv_path}")
    if (csv_path.stat().st_size != manifest["raw_csv_bytes"] or
            hashlib.sha256(csv_path.read_bytes()).hexdigest() != manifest["raw_csv_sha256"]):
        raise ValueError("Historical CSV differs from its provenance manifest")

    all_cells = pd.read_csv(csv_path, encoding="utf-8-sig")
    if len(all_cells) != manifest["profile"]["row_count"]:
        raise ValueError("CSV row count differs from the capture profile")
    if all_cells["captured_at"].nunique() != 1 or all_cells["captured_at"].iloc[0] != CAPTURE:
        raise ValueError("CSV contains a different or mixed source capture")
    published = all_cells["published"].astype(str).str.lower().eq("true")
    types = all_cells.loc[all_cells["cut"].eq("type") & published,
                          ["property_type", "homes", "median_vnd", "captured_at"]].copy()
    types["homes"] = pd.to_numeric(types["homes"], errors="raise").astype(int)
    types["median_vnd"] = pd.to_numeric(types["median_vnd"], errors="raise")
    if (types.empty or types["property_type"].isna().any() or
            types["property_type"].duplicated().any() or
            (types[["homes", "median_vnd"]] <= 0).any().any()):
        raise ValueError("Published property-type cells are missing or invalid")
    if len(types) != manifest["output_rows_by_grain"]["property_type"]:
        raise ValueError("CSV property-type count differs from the capture manifest")

    mart_path = project_path(manifest["outputs"]["property_type"])
    if not mart_path.is_dir():
        raise FileNotFoundError(f"Capture-specific property-type mart is missing: {mart_path}")
    mart = pd.read_parquet(mart_path)
    if (len(mart) != len(types) or not mart["published"].all() or
            not mart["source_captured_at_utc"].eq(CAPTURE).all() or
            not mart["source_snapshot_id"].eq(SNAPSHOT_ID).all() or
            not mart["source_file_sha256"].eq(manifest["raw_csv_sha256"]).all()):
        raise ValueError("Property-type Parquet mart does not match this capture")
    fields = ["property_type", "homes", "median_vnd"]
    csv_values = types[fields].sort_values("property_type").reset_index(drop=True)
    mart_values = mart[fields].sort_values("property_type").reset_index(drop=True)
    pd.testing.assert_frame_equal(csv_values, mart_values, check_dtype=False)

    city = all_cells.loc[all_cells["cut"].eq("city")]
    if len(city) != 1 or not bool(published.loc[city.index[0]]):
        raise ValueError("Expected one published all-property city cell")
    return types.sort_values("median_vnd", ascending=False), city.iloc[0]


def draw(types: pd.DataFrame) -> None:
    labels = [VI_LABELS.get(name, name) for name in types["property_type"]]
    values = types["median_vnd"] / 1_000_000
    colors = ["#3779a6", "#29857f", "#c7903b", "#7859a6", "#c16b53"]
    fig, ax = plt.subplots(figsize=(12.8, 6.6), dpi=220, facecolor="white")
    fig.subplots_adjust(left=0.22, right=0.94, top=0.78, bottom=0.22)
    bars = ax.barh(labels, values, color=colors[:len(types)], height=0.62)
    ax.invert_yaxis()
    ax.set_xlim(0, values.max() * 1.25)
    ax.set_xlabel("Median asking rent (million VND/month)", fontsize=12,
                  color="#243244", labelpad=10)
    ax.grid(axis="x", color="#dce3e8", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#aebbc5")
    ax.tick_params(axis="y", length=0, labelsize=11, colors="#243244")
    ax.tick_params(axis="x", labelsize=10, colors="#596b7d")
    for bar, value, homes in zip(bars, values, types["homes"]):
        ax.text(value + values.max() * 0.025, bar.get_y() + bar.get_height() / 2,
                f"{value:.1f} million  -  n={homes:,}", va="center", fontsize=11,
                color="#243244", weight="bold")

    fig.text(0.07, 0.94, "NEST Living - Median monthly asking rent by property type",
             fontsize=19, weight="bold", color="#17324d", va="top")
    fig.text(0.07, 0.875, "Published aggregate cells by property type",
             fontsize=11, color="#596b7d")
    fig.text(0.22, 0.10, f"Source capture: {CAPTURE} (UTC).  Source: NEST Living Hanoi Rent Index.",
             fontsize=9.5, color="#596b7d")
    fig.text(0.22, 0.065,
             "Asking rents from NEST's own inventory only; not representative of the whole Hanoi market.",
             fontsize=9.5, color="#596b7d")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=220, facecolor="white")
    plt.close(fig)


def main() -> None:
    types, city = load_capture()
    print(f"Source capture: {CAPTURE}")
    for row in types.itertuples(index=False):
        print(f"{row.property_type}: {row.median_vnd / 1_000_000:.1f} million VND/month; n={row.homes}")
    print(f"Separate all-property city cell: {int(city['median_vnd']) / 1_000_000:.1f} "
          f"million VND/month; n={int(city['homes'])}")
    draw(types)
    print(f"Wrote: {OUTPUT}")


if __name__ == "__main__":
    main()
