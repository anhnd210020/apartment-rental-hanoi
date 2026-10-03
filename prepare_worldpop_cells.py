"""Convert the prepared Hanoi-clipped WorldPop raster to a compact Spark-readable CSV."""
import csv
import gzip
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parent
CONTEXT = ROOT / "data" / "public_pilot" / "context"
RASTER = CONTEXT / "worldpop_hanoi_2020.tif"
TABLES = CONTEXT / "tables"
OUTPUT = TABLES / "worldpop_hanoi_cells.csv.gz"
SCHEMA = TABLES / "worldpop_hanoi_cells.schema.json"
SOURCE_MANIFEST = ROOT / "data" / "raw" / "public_datasets" / "manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_cells(rebuild: bool = False) -> dict:
    if not RASTER.exists():
        raise FileNotFoundError(f"Prepared Hanoi raster not found: {RASTER}; run prepare_public_context.py first")
    if OUTPUT.exists() and SCHEMA.exists() and not rebuild:
        info = json.loads(SCHEMA.read_text(encoding="utf-8"))
        if info.get("input_raster_sha256") == sha256_file(RASTER):
            print(f"Using existing WorldPop cell table: {OUTPUT} ({info['rows']:,} rows)")
            return info

    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    raw_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    worldpop_source = next(item for item in raw_manifest["files"] if item["path"].endswith("vnm_ppp_2020.tif"))
    TABLES.mkdir(parents=True, exist_ok=True)
    written = 0
    with rasterio.open(RASTER) as raster:
        width, height = raster.width, raster.height
        transform = raster.transform
        raster_crs = raster.crs.to_string() if raster.crs else None
        raster_nodata = raster.nodata
        with gzip.open(OUTPUT, "wt", encoding="utf-8", newline="", compresslevel=6) as stream:
            writer = csv.writer(stream)
            writer.writerow(["cell_row", "cell_col", "population_count"])
            for _, window in raster.block_windows(1):
                values = raster.read(1, window=window, masked=False)
                mask = raster.read_masks(1, window=window) > 0
                valid = mask & np.isfinite(values) & (values >= 0)
                for local_row, local_col in np.argwhere(valid):
                    writer.writerow([
                        int(window.row_off + local_row),
                        int(window.col_off + local_col),
                        format(float(values[local_row, local_col]), ".9g"),
                    ])
                    written += 1
    elapsed = round(time.perf_counter() - started, 3)
    completed_at = datetime.now(timezone.utc)
    info = {
        "table": "worldpop_hanoi_cells",
        "row_grain": "one valid pixel in the existing Hanoi-clipped WorldPop raster",
        "rows": written,
        "fields": {
            "cell_row": "zero-based raster row index; stable within this source raster",
            "cell_col": "zero-based raster column index; stable within this source raster",
            "population_count": "WorldPop people-per-pixel count; valid mask and value >= 0",
        },
        "source_product": "WorldPop Vietnam population count, reference year 2020",
        "source_url": worldpop_source["url"],
        "source_license": worldpop_source.get("license"),
        "source_downloaded_at_utc": raw_manifest.get("downloaded_at_utc"),
        "source_file_bytes": worldpop_source["bytes"],
        "source_file_sha256": worldpop_source["sha256"],
        "input_raster": str(RASTER.relative_to(ROOT)),
        "input_raster_bytes": RASTER.stat().st_size,
        "input_raster_sha256": sha256_file(RASTER),
        "raster_shape_rows_cols": [height, width],
        "raster_crs": raster_crs,
        "raster_transform": list(transform)[:6],
        "raster_nodata": raster_nodata,
        "output_csv_gzip": str(OUTPUT.relative_to(ROOT)),
        "output_bytes": OUTPUT.stat().st_size,
        "output_sha256": sha256_file(OUTPUT),
        "conversion_started_at_utc": started_at.isoformat(),
        "conversion_completed_at_utc": completed_at.isoformat(),
        "conversion_seconds": elapsed,
    }
    SCHEMA.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return info


if __name__ == "__main__":
    prepare_cells()
