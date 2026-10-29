"""Validate and ingest a manually downloaded NEST Hanoi aggregate CSV.

This program never contacts NEST. Download the CSV from the rent-index page's
public CSV link, then pass the local file and its retrieval time explicitly.
The input grain is an aggregate index cell, not an individual home/listing.
"""
import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession, functions as F, types as T


ROOT = Path(__file__).resolve().parent
SNAPSHOT_DIR = ROOT / "data" / "raw" / "nest_living" / "snapshots"
MART_DIR = ROOT / "data" / "public_pilot" / "mart" / "nest_rent_index"
EXPECTED_COLUMNS = (
    "cut", "district", "district_name", "bedroom_class", "property_type",
    "homes", "median_vnd", "p25_vnd", "p75_vnd", "published",
    "floor_at_capture", "captured_at",
)
METRIC_FIELDS = ("homes", "median_vnd", "p25_vnd", "p75_vnd", "published", "floor_at_capture")
SOURCE_PAGE_URL = "https://nestliving.vn/rent-index"
CSV_URL = "https://nestliving.vn/rent-index/rent-index.csv"
METHOD_URL = "https://nestliving.vn/rent-index"
TERMS_URL = "https://nestliving.vn/terms"
TERMS_STATUS = (
    "The public CSV is aggregate data. NEST's terms prohibit automated harvesting and copying listing content, "
    "but do not state an open license or explicit reuse grant for this CSV. Keep this as an optional local input; "
    "retain attribution and do not redistribute the raw CSV."
)


def parse_timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def snapshot_slug(value: datetime) -> str:
    return value.strftime("%Y%m%dT%H%M%S") + f"{value.microsecond // 1000:03d}Z"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def profile_csv(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = tuple(reader.fieldnames or ())
        if columns != EXPECTED_COLUMNS:
            raise ValueError(f"Unexpected NEST CSV schema: {columns!r}")
        rows = list(reader)

    if not rows:
        raise ValueError("NEST CSV contains no aggregate cells")
    if any(None in row for row in rows):
        raise ValueError("NEST CSV has rows with more values than the declared schema")

    captured_values = sorted({row["captured_at"].strip() for row in rows})
    if len(captured_values) != 1:
        raise ValueError(f"Expected one source capture timestamp, found {captured_values!r}")
    captured_at = parse_timestamp(captured_values[0], "captured_at")

    cut_counts: dict[str, int] = {}
    for row in rows:
        cut_counts[row["cut"]] = cut_counts.get(row["cut"], 0) + 1
    empty_counts = {
        column: sum(not (row[column] or "").strip() for row in rows)
        for column in EXPECTED_COLUMNS
    }
    published_counts: dict[str, int] = {}
    for row in rows:
        value = row["published"].strip().lower()
        if value not in {"true", "false"}:
            raise ValueError(f"Invalid published value: {row['published']!r}")
        published_counts[value] = published_counts.get(value, 0) + 1

    suppressed = [row for row in rows if row["published"].strip().lower() == "false"]
    suppressed_fields = {
        field: sum(row[field].strip().lower() == "too few homes" for row in suppressed)
        for field in ("median_vnd", "p25_vnd", "p75_vnd")
    }
    if any(count != len(suppressed) for count in suppressed_fields.values()):
        raise ValueError("Suppressed cells do not consistently mark all three rent statistics")

    for row in rows:
        try:
            homes = int(row["homes"])
            floor = int(row["floor_at_capture"])
        except ValueError as exc:
            raise ValueError("homes and floor_at_capture must be integers") from exc
        if homes < 0 or floor < 1:
            raise ValueError("homes must be non-negative and floor_at_capture must be positive")
        is_published = row["published"].strip().lower() == "true"
        values = [row[field].strip() for field in ("median_vnd", "p25_vnd", "p75_vnd")]
        if is_published:
            if not all(value.isdigit() for value in values):
                raise ValueError("Published cells must have numeric median and quartiles")
            p25, median, p75 = map(int, (values[1], values[0], values[2]))
            if not p25 <= median <= p75:
                raise ValueError("NEST quartiles must satisfy p25 <= median <= p75")
            if homes < floor:
                raise ValueError("A published cell is below its recorded sample floor")
        else:
            if homes >= floor or any(value.lower() != "too few homes" for value in values):
                raise ValueError("Unpublished cells must preserve below-floor counts and suppression markers")

    return {
        "columns": list(columns),
        "row_count": len(rows),
        "cut_counts": cut_counts,
        "empty_field_counts": empty_counts,
        "published_cell_counts": published_counts,
        "suppressed_cells": len(suppressed),
        "suppressed_statistic_value_counts": suppressed_fields,
        "minimum_sample_floor_values": sorted({int(row["floor_at_capture"]) for row in rows}),
        "source_captured_at": utc_iso(captured_at),
        "city_aggregate_rows": sum(row["cut"] == "city" for row in rows),
        "district_aggregate_rows": sum(row["cut"] == "district" for row in rows),
        "district_bedroom_aggregate_rows": sum(row["cut"] == "district_bedroom" for row in rows),
        "property_type_aggregate_rows": sum(row["cut"] == "type" for row in rows),
        "dimension_blank_counts_are_structural": True,
    }


def register_snapshot(input_path: Path, profile: dict, retrieved_at: datetime) -> tuple[Path, str]:
    capture = parse_timestamp(profile["source_captured_at"], "source_captured_at")
    slug = snapshot_slug(capture)
    target = SNAPSHOT_DIR / f"nest_hanoi_rent_index_{slug}.csv"
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    file_hash = sha256_file(input_path)

    if input_path.resolve() != target.resolve():
        if target.exists():
            if sha256_file(target) != file_hash:
                raise FileExistsError(f"A different CSV already uses this source capture time: {target}")
        else:
            shutil.copy2(input_path, target)

    return target, file_hash


def require_no_validation_errors(df, profile: dict) -> int:
    total = df.count()
    expected = profile["row_count"]
    if total != expected:
        raise ValueError(f"Spark row count {total} disagrees with CSV profile {expected}")

    duplicate_keys = df.groupBy("cell_key").count().filter(F.col("count") > 1).count()
    if duplicate_keys:
        raise ValueError(f"Found {duplicate_keys} duplicate aggregate cell keys")

    bad = df.filter(
        F.col("cut").isNull()
        | ~F.col("cut").isin("city", "district", "district_bedroom", "type")
        | F.col("homes").isNull()
        | F.col("floor_at_capture").isNull()
        | F.col("published").isNull()
        | F.col("captured_at_timestamp").isNull()
        | F.col("city_key").isNull()
        | (F.col("published") & (F.col("median_vnd").isNull() | F.col("p25_vnd").isNull() | F.col("p75_vnd").isNull()))
        | (~F.col("published") & (F.col("median_vnd_raw") != "too few homes"))
    ).count()
    if bad:
        raise ValueError(f"Spark validation found {bad} invalid aggregate rows")

    city_rows = df.filter(F.col("cut") == "city").count()
    if city_rows != 1:
        raise ValueError(f"Expected exactly one Hanoi city aggregate row, found {city_rows}")

    suppression_rows = df.filter(~F.col("published")).count()
    if suppression_rows != profile["suppressed_cells"]:
        raise ValueError("Spark suppression count disagrees with the CSV profile")
    return total


def ingest(input_path: Path, retrieved_at_text: str) -> dict:
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    retrieved_at = parse_timestamp(retrieved_at_text, "retrieved_at_utc")
    profile = profile_csv(input_path)
    snapshot_path, file_hash = register_snapshot(input_path, profile, retrieved_at)
    capture = parse_timestamp(profile["source_captured_at"], "source_captured_at")
    snapshot_id = f"nest-{snapshot_slug(capture)}"
    raw_file_schema = T.StructType([T.StructField(name, T.StringType(), True) for name in EXPECTED_COLUMNS])

    spark = (
        SparkSession.builder.master("local[2]")
        .appName("IT5427-NEST-Hanoi-Rent-Aggregate")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    try:
        source = (
            spark.read.schema(raw_file_schema)
            .option("header", True)
            .option("encoding", "UTF-8")
            .option("mode", "FAILFAST")
            .csv(str(snapshot_path))
        )
        blank_to_null = lambda name: F.when(F.trim(F.col(name)) == "", F.lit(None).cast("string")).otherwise(F.col(name))
        normalized = source.select(
            *[blank_to_null(name).alias(name) for name in ("district", "district_name", "bedroom_class", "property_type")],
            F.col("cut").alias("cut"),
            F.col("homes").cast("long").alias("homes"),
            F.col("median_vnd").alias("median_vnd_raw"),
            F.col("p25_vnd").alias("p25_vnd_raw"),
            F.col("p75_vnd").alias("p75_vnd_raw"),
            F.lower(F.trim(F.col("published"))).cast("boolean").alias("published"),
            F.col("floor_at_capture").cast("integer").alias("floor_at_capture"),
            F.col("captured_at").alias("source_captured_at_utc"),
            F.to_timestamp("captured_at", "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").alias("captured_at_timestamp"),
        )
        key_parts = ["cut", "district", "bedroom_class", "property_type"]
        normalized = normalized.withColumn(
            "cell_key",
            F.concat_ws("|", *[F.coalesce(F.col(name), F.lit("")) for name in key_parts]),
        ).withColumn("median_vnd", F.col("median_vnd_raw").cast("long")) \
         .withColumn("p25_vnd", F.col("p25_vnd_raw").cast("long")) \
         .withColumn("p75_vnd", F.col("p75_vnd_raw").cast("long")) \
         .withColumn("city_key", F.lit("VN-HN")) \
         .withColumn("city_name", F.lit("Hà Nội")) \
         .withColumn("source_publisher", F.lit("NEST Living")) \
         .withColumn("source_grain", F.lit("one aggregate index cell; not a home/listing row")) \
         .withColumn("source_url", F.lit(SOURCE_PAGE_URL)) \
         .withColumn("source_csv_url", F.lit(CSV_URL)) \
         .withColumn("source_snapshot_id", F.lit(snapshot_id)) \
         .withColumn("source_file_name", F.lit(snapshot_path.name)) \
         .withColumn("source_file_sha256", F.lit(file_hash)) \
         .withColumn("source_retrieved_at_utc", F.lit(utc_iso(retrieved_at))) \
         .withColumn("small_sample_suppressed", ~F.col("published")) \
         .withColumn("small_sample_floor", F.col("floor_at_capture"))

        total = require_no_validation_errors(normalized, profile)
        snapshot_output = MART_DIR / snapshot_id
        outputs = {
            "cells": snapshot_output / "cells",
            "city": snapshot_output / "city",
            "district": snapshot_output / "district",
            "district_bedroom": snapshot_output / "district_bedroom",
            "property_type": snapshot_output / "property_type",
        }
        normalized.write.mode("overwrite").parquet(str(outputs["cells"]))
        normalized.filter(F.col("cut") == "city").write.mode("overwrite").parquet(str(outputs["city"]))
        normalized.filter(F.col("cut") == "district").write.mode("overwrite").parquet(str(outputs["district"]))
        normalized.filter(F.col("cut") == "district_bedroom").write.mode("overwrite").parquet(str(outputs["district_bedroom"]))
        normalized.filter(F.col("cut") == "type").write.mode("overwrite").parquet(str(outputs["property_type"]))

        output_counts = {
            "cells": total,
            "city": profile["city_aggregate_rows"],
            "district": profile["district_aggregate_rows"],
            "district_bedroom": profile["district_bedroom_aggregate_rows"],
            "property_type": profile["property_type_aggregate_rows"],
        }
        relative_outputs = {name: str(path.relative_to(ROOT)) for name, path in outputs.items()}
    finally:
        spark.stop()

    manifest = {
        "snapshot_id": snapshot_id,
        "publisher": "NEST Living",
        "role": "independent rental-agency aggregate source; not listing-level data",
        "city_key": "VN-HN",
        "source_page_url": SOURCE_PAGE_URL,
        "intended_public_csv_download_url": CSV_URL,
        "methodology_url": METHOD_URL,
        "terms_url": TERMS_URL,
        "source_captured_at_utc": profile["source_captured_at"],
        "retrieved_at_utc": utc_iso(retrieved_at),
        "raw_csv_path": str(snapshot_path.relative_to(ROOT)),
        "raw_csv_bytes": snapshot_path.stat().st_size,
        "raw_csv_sha256": file_hash,
        "schema": profile["columns"],
        "profile": profile,
        "license_and_terms_assessment": TERMS_STATUS,
        "reuse_status": "optional local input; no open license or redistribution right assumed",
        "outputs": relative_outputs,
        "output_rows_by_grain": output_counts,
        "integration_policy": (
            "Keep city and district aggregate marts separate from Kaggle listings and the existing city-context mart. "
            "The city key identifies Hanoi, but the NEST all-home aggregate, Kaggle apartment-candidate subset, "
            "source snapshot dates, and rent populations do not match closely enough for a statistical join. "
            "District aggregates are not joined to free-text Kaggle addresses."
        ),
        "interpretation": "Monthly asking-rent aggregates for NEST's own inventory; not the Hanoi market and not individual listings.",
    }

    raw_manifest_path = snapshot_path.with_suffix(".manifest.json")
    raw_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    snapshot_output.mkdir(parents=True, exist_ok=True)
    (snapshot_output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = {"snapshot_id": snapshot_id, "manifest_path": str((snapshot_output / "manifest.json").relative_to(ROOT))}
    MART_DIR.mkdir(parents=True, exist_ok=True)
    (MART_DIR / "latest.json").write_text(json.dumps(latest, indent=2), encoding="utf-8")

    print(
        "NEST aggregate: "
        f"cells={profile['row_count']}, city={output_counts['city']}, district={output_counts['district']}, "
        f"district_bedroom={output_counts['district_bedroom']}, property_type={output_counts['property_type']}, "
        f"published={profile['published_cell_counts'].get('true', 0)}, suppressed={profile['suppressed_cells']}"
    )
    print(f"Source captured at: {profile['source_captured_at']}; retrieved at: {manifest['retrieved_at_utc']}")
    print(f"SHA-256: {file_hash}")
    print(f"Raw snapshot (local, ignored): {snapshot_path}")
    print(f"Spark marts: {snapshot_output}")
    print(f"Manifest: {snapshot_output / 'manifest.json'}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and ingest a manually downloaded NEST Hanoi aggregate CSV.")
    parser.add_argument("--input", required=True, type=Path, help="Local CSV downloaded through NEST's public CSV link")
    parser.add_argument("--retrieved-at-utc", required=True, help="ISO-8601 UTC time when the CSV download completed")
    args = parser.parse_args()
    ingest(args.input.resolve(), args.retrieved_at_utc)


if __name__ == "__main__":
    main()
