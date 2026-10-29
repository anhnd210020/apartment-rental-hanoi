"""Compare two genuine, manually registered NEST aggregate snapshots.

This program reads only local CSV snapshots and their provenance manifests. It
never downloads from or crawls the NEST site. With fewer than two distinct
source captures it records that no comparison is available.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SNAPSHOT_DIR = ROOT / "data" / "raw" / "nest_living" / "snapshots"
OUTPUT_PATH = ROOT / "data" / "public_pilot" / "snapshot_comparison" / "nest_living_latest.json"
KEY_FIELDS = ("cut", "district", "bedroom_class", "property_type")
COMPARE_FIELDS = ("homes", "median_vnd", "p25_vnd", "p75_vnd", "published", "floor_at_capture")
REQUIRED_FIELDS = set((*KEY_FIELDS, *COMPARE_FIELDS, "captured_at"))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple((row.get(name) or "").strip() for name in KEY_FIELDS)


def read_snapshot(manifest_path: Path) -> tuple[dict, dict[tuple[str, ...], dict[str, str]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    csv_path = ROOT / manifest["raw_csv_path"]
    if not csv_path.is_file():
        raise FileNotFoundError(f"Snapshot CSV missing: {csv_path}")
    actual_hash = sha256_file(csv_path)
    if actual_hash != manifest["raw_csv_sha256"]:
        raise ValueError(f"Snapshot hash mismatch: {csv_path}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not REQUIRED_FIELDS.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Snapshot CSV lacks comparison fields: {csv_path}")
        records = list(reader)
    if not records:
        raise ValueError(f"Snapshot CSV is empty: {csv_path}")
    captures = {row["captured_at"] for row in records}
    if captures != {manifest["source_captured_at_utc"]}:
        raise ValueError(f"CSV capture timestamp disagrees with manifest: {csv_path}")
    by_key = {row_key(row): row for row in records}
    if len(by_key) != len(records):
        raise ValueError(f"Duplicate aggregate cell keys in snapshot: {csv_path}")
    return manifest, by_key


def snapshot_metadata(manifest: dict) -> dict:
    return {
        "snapshot_id": manifest["snapshot_id"],
        "source_captured_at_utc": manifest["source_captured_at_utc"],
        "retrieved_at_utc": manifest["retrieved_at_utc"],
        "sha256": manifest["raw_csv_sha256"],
        "aggregate_cells": manifest["profile"]["row_count"],
    }


def compare(manifest_dir: Path) -> dict:
    manifests = []
    for path in manifest_dir.glob("*.manifest.json"):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if manifest.get("publisher") == "NEST Living" and manifest.get("raw_csv_sha256"):
                manifests.append((path, manifest))
        except (OSError, json.JSONDecodeError):
            continue

    manifests.sort(key=lambda item: parse_time(item[1]["source_captured_at_utc"]))
    distinct = []
    seen_capture_hashes = set()
    for path, manifest in manifests:
        identity = (manifest["source_captured_at_utc"], manifest["raw_csv_sha256"])
        if identity not in seen_capture_hashes:
            distinct.append((path, manifest))
            seen_capture_hashes.add(identity)

    result = {
        "publisher": "NEST Living",
        "comparison_grain": "aggregate index cell keyed by cut, source district key, bedroom class, and property type",
        "available_snapshots": len(distinct),
        "required_snapshots": 2,
        "snapshots": [snapshot_metadata(manifest) for _, manifest in distinct],
        "interpretation": "Any changes describe NEST aggregate cells only; they are not listing-record changes or rental-listing Velocity.",
    }
    if len(distinct) < 2:
        result["status"] = "insufficient_snapshots"
        result["comparison"] = None
        return result

    (old_path, old_manifest), (new_path, new_manifest) = distinct[-2:]
    old_manifest, old_rows = read_snapshot(old_path)
    new_manifest, new_rows = read_snapshot(new_path)
    if parse_time(new_manifest["source_captured_at_utc"]) <= parse_time(old_manifest["source_captured_at_utc"]):
        raise ValueError("NEST source capture timestamps must be strictly increasing")

    old_keys, new_keys = set(old_rows), set(new_rows)
    common = old_keys & new_keys
    changed = []
    counts = {field: 0 for field in COMPARE_FIELDS}
    for key in sorted(common):
        fields = [field for field in COMPARE_FIELDS if old_rows[key][field] != new_rows[key][field]]
        if fields:
            for field in fields:
                counts[field] += 1
            changed.append({
                "cell_key": dict(zip(KEY_FIELDS, key)),
                "changed_fields": fields,
                "old_values": {field: old_rows[key][field] for field in fields},
                "new_values": {field: new_rows[key][field] for field in fields},
            })
    result["status"] = "compared"
    result["comparison"] = {
        "old_source_captured_at_utc": old_manifest["source_captured_at_utc"],
        "old_retrieved_at_utc": old_manifest["retrieved_at_utc"],
        "new_source_captured_at_utc": new_manifest["source_captured_at_utc"],
        "new_retrieved_at_utc": new_manifest["retrieved_at_utc"],
        "old_snapshot_id": old_manifest["snapshot_id"],
        "new_snapshot_id": new_manifest["snapshot_id"],
        "shared_cells": len(common),
        "added_cells": len(new_keys - old_keys),
        "removed_cells": len(old_keys - new_keys),
        "changed_cells": len(changed),
        "unchanged_shared_cells": len(common) - len(changed),
        "changed_cell_counts_by_field": counts,
        "changed_cell_details": changed,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare the latest two genuine local NEST aggregate snapshots.")
    parser.add_argument("--snapshot-dir", type=Path, default=SNAPSHOT_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    result = compare(args.snapshot_dir.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if result["status"] == "insufficient_snapshots":
        print(f"NEST snapshot comparison unavailable: {result['available_snapshots']} genuine capture(s); two are required.")
    else:
        counts = result["comparison"]
        print(
            "NEST aggregate snapshot comparison: "
            f"shared={counts['shared_cells']}, added={counts['added_cells']}, removed={counts['removed_cells']}, "
            f"changed={counts['changed_cells']}, unchanged={counts['unchanged_shared_cells']}"
        )
        print(f"Changed cells by field: {json.dumps(counts['changed_cell_counts_by_field'], sort_keys=True)}")
    print(f"Comparison status: {result['status']}; output: {args.output}")


if __name__ == "__main__":
    main()
