"""Spark pipelines for synthetic fixtures, the legacy pilot, and public data."""
import argparse
import hashlib
import json
import re
import unicodedata
import time
from datetime import datetime, timezone
from functools import reduce
from pathlib import Path

from pyspark.sql import SparkSession, functions as F, types as T

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "data" / "fixtures"
PUBLIC_RAW = ROOT / "data" / "raw" / "public_datasets" / "kaggle_vietnam_house_rent"
PUBLIC_OUT = ROOT / "data" / "public_pilot"
WORLDPOP_CELLS = PUBLIC_OUT / "context" / "tables" / "worldpop_hanoi_cells.csv.gz"
PILOT_RAW = ROOT / "data" / "raw" / "batdongsan" / "g1_20261002" / "listings.jsonl"


def adapter_batdongsan(spark, pilot=False):
    if pilot:
        raw = spark.read.json(str(PILOT_RAW))
        return raw.select(F.lit("batdongsan").alias("source"), F.col("metadata.source_listing_id").cast("string").alias("source_listing_id"), F.col("metadata.source_url").alias("source_url"), F.col("listing.title").alias("title"), F.coalesce(F.col("listing.characteristics.price_text"), F.col("listing.overview.price")).cast("string").alias("price_raw"), F.col("listing.overview.area").cast("string").alias("area_raw"), F.col("listing.overview.bedrooms").cast("string").alias("bedrooms_raw"), F.col("listing.location.district").alias("district_raw"), F.col("listing.overview.property_type").alias("property_subtype_raw"), F.col("metadata.collected_at").alias("collected_at_raw"), F.col("listing.status").alias("listing_status"))
    raw = spark.read.json(str(FIXTURES / "batdongsan.jsonl"))
    return raw.select(F.lit("batdongsan").alias("source"), F.col("listing_id").cast("string").alias("source_listing_id"), F.col("url").alias("source_url"), F.col("title"), F.col("price").cast("string").alias("price_raw"), F.col("area").cast("string").alias("area_raw"), F.col("bedrooms").cast("string").alias("bedrooms_raw"), F.col("district").alias("district_raw"), F.col("property_type").alias("property_subtype_raw"), F.col("collected_at").alias("collected_at_raw"), F.lit("active").alias("listing_status"))


def adapter_nhatot(spark):
    raw = spark.read.json(str(FIXTURES / "nhatot.jsonl"))
    return raw.select(F.lit("nhatot").alias("source"), F.col("id").cast("string").alias("source_listing_id"), F.col("permalink").alias("source_url"), F.col("subject").alias("title"), F.col("rent_price").cast("string").alias("price_raw"), F.col("square_meters").cast("string").alias("area_raw"), F.col("rooms").cast("string").alias("bedrooms_raw"), F.col("location.district").alias("district_raw"), F.col("category").alias("property_subtype_raw"), F.col("observed_at").alias("collected_at_raw"), F.lit("active").alias("listing_status"))


def adapter_homedy(spark):
    raw = spark.read.json(str(FIXTURES / "homedy.jsonl"))
    return raw.select(F.lit("homedy").alias("source"), F.col("code").cast("string").alias("source_listing_id"), F.col("listing_url").alias("source_url"), F.col("headline").alias("title"), F.col("price_text").cast("string").alias("price_raw"), F.col("size_text").cast("string").alias("area_raw"), F.col("attributes.bedrooms").cast("string").alias("bedrooms_raw"), F.col("address.district").alias("district_raw"), F.col("category_name").alias("property_subtype_raw"), F.col("capture_time").alias("collected_at_raw"), F.lit("active").alias("listing_status"))


def normalize_fixture(df):
    price = F.lower(F.trim(F.col("price_raw")))
    numeric_vnd = price.rlike(r"^[0-9]+$")
    range_price = price.rlike(r"[0-9]+(?:[.,][0-9]+)?\s*[-–]\s*[0-9]+")
    monthly = price.rlike(r"tháng|/th")
    unit_million = price.rlike(r"triệu|\btr\b")
    unit_thousand = price.rlike(r"nghìn|ngàn|\bng\b")
    amount_text = F.regexp_extract(price, r"([0-9]+(?:[.,][0-9]+)?)", 1)
    amount = F.regexp_replace(amount_text, ",", ".").cast("double")
    price_value = F.when(range_price, F.lit(None).cast("double")).when(numeric_vnd, price.cast("double")).when(monthly & unit_million, amount * 1_000_000.0).when(monthly & unit_thousand, amount * 1_000.0)
    area_raw = F.lower(F.col("area_raw"))
    area_range = area_raw.rlike(r"[0-9]+(?:[.,][0-9]+)?\s*[-–]\s*[0-9]+")
    area = F.regexp_replace(F.regexp_extract(area_raw, r"([0-9]+(?:[.,][0-9]+)?)", 1), ",", ".").cast("double")
    subtype = F.when(F.lower(F.col("property_subtype_raw")).rlike(r"mini|dịch vụ"), "mini_service").when(F.lower(F.col("property_subtype_raw")).rlike(r"chung cư|căn hộ"), "apartment").otherwise("unknown")
    df = df.withColumn("price_vnd_month", price_value).withColumn("area_m2", F.when(area_range, F.lit(None).cast("double")).otherwise(area)).withColumn("bedrooms", F.regexp_extract(F.col("bedrooms_raw"), r"([0-9]+)", 1).cast("int")).withColumn("property_subtype", subtype).withColumn("district_normalized", F.trim(F.col("district_raw"))).withColumn("collected_at", F.to_timestamp("collected_at_raw", "yyyy-MM-dd'T'HH:mm:ssXXX"))
    return df.withColumn("quality_reason", F.when(F.lower(F.col("listing_status")) != "active", "expired_listing").when(F.col("source_listing_id").isNull(), "missing_id").when(F.lower(F.col("title")).rlike(r"quỹ căn|giỏ hàng|danh sách căn"), "multi_unit_listing").when(F.col("property_subtype") == "unknown", "unknown_type").when(F.col("price_vnd_month").isNull() | (F.col("price_vnd_month") <= 0), "invalid_price").when(F.col("area_m2").isNull() | (F.col("area_m2") <= 0), "invalid_area").when(F.col("district_normalized").isNull(), "missing_district").otherwise("valid"))


def ascii_vietnamese(value):
    value = unicodedata.normalize("NFD", value or "")
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn").replace("đ", "d").replace("Đ", "d").lower()


def rental_fingerprint(city, title, published, address, acreage, price):
    fields = [city or "", title or "", published or "", address or "", acreage or "", price or ""]
    return hashlib.sha256("\x1f".join(fields).encode("utf-8")).hexdigest()


fingerprint_udf = F.udf(rental_fingerprint, T.StringType())
normalize_text_udf = F.udf(ascii_vietnamese, T.StringType())


def parquet_payload_bytes(path):
    return sum(file.stat().st_size for file in path.rglob("part-*.parquet")) if path.exists() else 0


def run_public(spark):
    run_started_at = datetime.now(timezone.utc)
    run_started = time.perf_counter()
    run_id = run_started_at.strftime("public-%Y%m%dT%H%M%SZ")
    raw_manifest_path = ROOT / "data" / "raw" / "public_datasets" / "manifest.json"
    raw_manifest = json.loads(raw_manifest_path.read_text(encoding="utf-8"))
    raw_files = {item["path"].replace("\\", "/"): item for item in raw_manifest["files"]}
    context_file = PUBLIC_OUT / "context" / "hanoi_context.json"
    context_metadata = json.loads(context_file.read_text(encoding="utf-8"))
    cells_path = WORLDPOP_CELLS
    cells_schema_path = PUBLIC_OUT / "context" / "tables" / "worldpop_hanoi_cells.schema.json"
    if not cells_path.exists() or not cells_schema_path.exists():
        raise FileNotFoundError("WorldPop Spark table is missing; run prepare_worldpop_cells.py first")
    cells_schema_info = json.loads(cells_schema_path.read_text(encoding="utf-8"))

    # Source 1: listing records, kept at one row per reviewed source record.
    listing_started = time.perf_counter()
    parts = []
    for city_file in ("hn.csv", "hcm.csv", "dn.csv"):
        frame = spark.read.option("header", True).option("encoding", "UTF-8").csv(str(PUBLIC_RAW / city_file))
        parts.append(frame.withColumn("source_city_file", F.lit(city_file)).withColumn("source", F.lit("Kaggle: Vietnam House Rent Dataset")))
    raw = reduce(lambda left, right: left.unionByName(right), parts)
    raw = raw.withColumn("source_fingerprint", fingerprint_udf(F.regexp_extract("source_city_file", r"^(.*)\.csv$", 1), "title", "published", "address", "acreage", "price"))
    review_path = ROOT / "data" / "curation" / "kaggle_hanoi_title_review.csv"
    review = spark.read.option("header", True).csv(str(review_path))
    checked = raw.join(review.select("source_fingerprint", "review_status", "review_reason"), "source_fingerprint", "left")
    period_path = ROOT / "data" / "curation" / "kaggle_price_period_review.csv"
    periods = spark.read.option("header", True).csv(str(period_path))
    checked = checked.join(periods.select("source_fingerprint", "explicit_price_period", "monthly_amount_status"), "source_fingerprint", "left")
    checked = checked.withColumn("explicit_price_period", F.coalesce(F.col("explicit_price_period"), F.lit("unknown")))
    checked = checked.withColumn("monthly_amount_status", F.coalesce(F.col("monthly_amount_status"), F.lit("not_explicit_or_not_reviewed")))
    checked = checked.withColumn("normalized_title", normalize_text_udf(F.col("title")))
    apartment = F.col("normalized_title").rlike(r"\bcan ho\b|chung cu|\bapartment\b|\bcondo\b|\bstudio\b")
    rent_cue = F.col("normalized_title").rlike(r"cho thue|can thue|gia thue|thue phong|thue can ho|thue chung cu|\brent\b|\blease\b")
    sale_cue = F.col("normalized_title").rlike(r"can ban|gia ban|ban gap|\bban (can ho|chung cu|nha|dat|phong)|chuyen nhuong|sang nhuong|nhuong lai|\bmo ban\b")
    checked = checked.withColumn("is_apartment_cue", apartment).withColumn("has_rent_cue", rent_cue).withColumn("has_sale_cue", sale_cue)
    reason = (F.when(F.col("source_city_file") != "hn.csv", "outside_hanoi_partition")
        .when(~apartment & rent_cue, "rental_cue_non_apartment")
        .when(~apartment & sale_cue, "sale_cue_non_apartment")
        .when(~apartment & ~rent_cue & ~sale_cue, "no_apartment_or_transaction_cue")
        .when(apartment & sale_cue & ~rent_cue, "apartment_sale_excluded")
        .when(apartment & ~rent_cue & ~sale_cue, "apartment_transaction_ambiguous")
        .when(apartment & rent_cue & sale_cue, "conflicting_transaction_cues")
        .when(F.col("review_status") == "exclude_room_offer", "room_or_shared_stay_excluded")
        .when(F.col("review_status") == "ambiguous", "manual_review_ambiguous")
        .when(F.col("review_status") != "include", "unreviewed_apartment_rental_cue")
        .when(F.col("price").cast("double") <= 0, "included_price_unknown")
        .when(F.col("acreage").cast("double") <= 0, "invalid_area")
        .otherwise("valid_exploratory_rental"))
    checked = checked.withColumn("quality_reason", reason)
    price_vnd = F.col("price").cast("double") * F.lit(1_000_000.0)
    date_value = F.to_date(F.col("published"), "dd/MM/yyyy")
    curated = checked.filter(F.col("quality_reason") == "valid_exploratory_rental").select(
        F.lit("H\u00e0 N\u1ed9i").alias("city"), F.lit("VN-HN").alias("city_key"),
        F.lit("Kaggle uploader dataset").alias("listing_source"), "source_fingerprint",
        F.col("price").cast("double").alias("listed_amount_million_vnd"), price_vnd.alias("listed_amount_vnd"),
        F.col("acreage").cast("double").alias("area_m2"), F.col("published").alias("published_raw"), date_value.alias("published_date"),
        "explicit_price_period", "monthly_amount_status",
        F.when((F.col("explicit_price_period") == "monthly") & (F.col("monthly_amount_status") == "verified_match"), price_vnd).alias("verified_monthly_rent_vnd"),
        F.lit("apartment").alias("property_type"), F.lit("rental title cue + manual title review").alias("classification_basis"))
    quality = checked.groupBy("quality_reason").agg(F.count("*").alias("records"))
    raw_rows = checked.count()
    hanoi_rows = checked.filter(F.col("source_city_file") == "hn.csv").count()
    valid_count = curated.count()
    curated_path = PUBLIC_OUT / "curated" / "listings"
    quality_path = PUBLIC_OUT / "mart" / "quality"
    summary_path = PUBLIC_OUT / "mart" / "summary"
    curated.write.mode("overwrite").parquet(str(curated_path))
    quality.write.mode("overwrite").parquet(str(quality_path))
    listing_summary = curated.agg(
        F.count("*").alias("valid_listings"),
        F.expr("percentile_approx(listed_amount_vnd, 0.5)").alias("median_listed_amount_vnd"),
        F.expr("percentile_approx(area_m2, 0.5)").alias("median_area_m2"),
        F.expr("percentile_approx(listed_amount_vnd / area_m2, 0.5)").alias("median_listed_amount_per_m2_vnd"),
        F.sum(F.when(F.col("published_date").isNotNull(), 1).otherwise(0)).alias("parsed_published_dates"),
        F.sum(F.when(F.col("verified_monthly_rent_vnd").isNotNull(), 1).otherwise(0)).alias("verified_monthly_listing_count"),
        F.expr("percentile_approx(verified_monthly_rent_vnd, 0.5)").alias("median_verified_monthly_rent_vnd"),
        F.expr("percentile_approx(verified_monthly_rent_vnd / area_m2, 0.5)").alias("median_verified_monthly_rent_per_m2_vnd"),
        F.sum(F.when((F.col("explicit_price_period") == "monthly") & (F.col("monthly_amount_status") == "mismatch"), 1).otherwise(0)).alias("monthly_title_amount_mismatch_count"),
    ).withColumn("city_key", F.lit("VN-HN")).withColumn("city", F.lit("H\u00e0 N\u1ed9i"))
    period_summary = checked.agg(
        F.sum(F.when(F.col("explicit_price_period") == "monthly", 1).otherwise(0)).alias("monthly_period_title_count"),
        F.sum(F.when((F.col("explicit_price_period") == "monthly") & (F.col("monthly_amount_status") == "unknown_price"), 1).otherwise(0)).alias("monthly_title_unknown_price_count"),
    )
    listing_summary = listing_summary.crossJoin(period_summary).withColumn("table_grain", F.lit("one aggregate row for the Hanoi listing dataset snapshot"))
    listing_summary.write.mode("overwrite").parquet(str(summary_path))
    listing_seconds = round(time.perf_counter() - listing_started, 3)

    # Source 2: Spark reads the existing OSM preparation JSON and normalizes its Hanoi-wide aggregate.
    osm_started = time.perf_counter()
    osm_input = spark.read.option("multiLine", True).json(str(context_file))
    osm_city = osm_input.select(
        F.lit("VN-HN").alias("city_key"), F.col("city").cast("string").alias("city"),
        F.col("osm_file_date").cast("string").alias("osm_snapshot_date"),
        F.col("osm_snapshot_data_timestamp_utc").cast("string").alias("osm_snapshot_data_timestamp_utc"),
        F.col("osm_replication_sequence_number").cast("long").alias("osm_replication_sequence_number"),
        F.col("osm_extract_file").cast("string").alias("osm_extract_file"),
        F.col("osm_source_url").cast("string").alias("osm_source_url"),
        F.col("osm_source_file_bytes").cast("long").alias("osm_source_file_bytes"),
        F.col("osm_source_sha256").cast("string").alias("osm_source_sha256"),
        F.col("context_record_written_at_utc").cast("string").alias("context_prepared_at_utc"),
        F.col("osm_counts.road_ways").cast("long").alias("osm_road_ways"),
        F.col("osm_counts.public_transport_stops").cast("long").alias("osm_public_transport_stops"),
        F.col("osm_counts.education_features").cast("long").alias("osm_education_features"),
        F.col("osm_counts.health_features").cast("long").alias("osm_health_features"),
        F.col("osm_counts.other_amenities").cast("long").alias("osm_other_amenities"),
        F.col("osm_counts.road_length_km_approx").cast("double").alias("osm_road_length_km_approx"),
        F.col("boundary_osm_relation_id").cast("long").alias("boundary_osm_relation_id"),
        F.lit("one Hanoi city aggregate; no listing-level geometry").alias("table_grain"))
    osm_count = osm_city.count()
    osm_output_path = PUBLIC_OUT / "mart" / "osm_city_context"
    osm_city.write.mode("overwrite").parquet(str(osm_output_path))
    osm_seconds = round(time.perf_counter() - osm_started, 3)

    # Source 3: Spark reads one row per valid WorldPop pixel and aggregates at Hanoi city grain.
    worldpop_started = time.perf_counter()
    cells_schema = T.StructType([
        T.StructField("cell_row", T.IntegerType(), False),
        T.StructField("cell_col", T.IntegerType(), False),
        T.StructField("population_count", T.DoubleType(), False),
    ])
    cells = (spark.read.schema(cells_schema).option("header", True).option("mode", "FAILFAST").csv(str(cells_path))
        .filter(F.col("population_count").isNotNull() & (F.col("population_count") >= 0))
        .withColumn("city_key", F.lit("VN-HN"))
        .withColumn("worldpop_reference_year", F.lit(int(context_metadata["worldpop"]["year"])))
        .select("city_key", "worldpop_reference_year", "cell_row", "cell_col", "population_count"))
    cells = cells.cache()
    cell_rows = cells.count()
    cells_output_path = PUBLIC_OUT / "context" / "tables" / "worldpop_hanoi_cells_parquet"
    cells.write.mode("overwrite").parquet(str(cells_output_path))
    worldpop_city = cells.groupBy("city_key", "worldpop_reference_year").agg(
        F.count("*").alias("worldpop_valid_cell_count"),
        F.sum("population_count").alias("worldpop_population_sum_estimate"))
    worldpop_city = worldpop_city.withColumn("city", F.lit("H\u00e0 N\u1ed9i")).withColumn("table_grain", F.lit("one city aggregate from valid WorldPop raster cells"))
    worldpop_city_path = PUBLIC_OUT / "mart" / "worldpop_city_context"
    worldpop_city.write.mode("overwrite").parquet(str(worldpop_city_path))
    worldpop_seconds = round(time.perf_counter() - worldpop_started, 3)

    # Integrate context only at the explicit city key; no per-listing spatial match is attempted.
    integration_started = time.perf_counter()
    city_context = osm_city.join(worldpop_city.drop("city", "table_grain"), on="city_key", how="inner").withColumn(
        "context_grain", F.lit("Hanoi city aggregate; independent from listing-record grain"))
    city_context_path = PUBLIC_OUT / "mart" / "city_context"
    city_context.write.mode("overwrite").parquet(str(city_context_path))
    integrated_city = listing_summary.join(city_context.drop("city", "table_grain"), on="city_key", how="inner").withColumn(
        "integrated_grain", F.lit("one city-key integration row; context is not copied onto listing records"))
    integrated_path = PUBLIC_OUT / "mart" / "integrated_city"
    integrated_city.write.mode("overwrite").parquet(str(integrated_path))
    integrated_rows = integrated_city.count()
    integration_seconds = round(time.perf_counter() - integration_started, 3)
    cells.unpersist()

    # Verify the Spark-derived WorldPop totals against the prepared-context metadata.
    spark_worldpop = worldpop_city.first()
    context_worldpop = context_metadata["worldpop"]
    if int(spark_worldpop["worldpop_valid_cell_count"]) != int(context_worldpop["valid_pixel_count"]):
        raise ValueError("WorldPop Spark valid-cell count disagrees with prepared raster metadata")
    if abs(float(spark_worldpop["worldpop_population_sum_estimate"]) - float(context_worldpop["population_sum_estimate"])) > 0.05:
        raise ValueError("WorldPop Spark population sum disagrees with prepared raster metadata")
    if integrated_rows != 1:
        raise ValueError(f"Expected one Hanoi city integration row, found {integrated_rows}")

    raw_file_names = [f"kaggle_vietnam_house_rent/{name}" for name in ("hn.csv", "hcm.csv", "dn.csv")]
    listing_files = [raw_files[name] for name in raw_file_names]
    worldpop_raw = next(item for item in raw_manifest["files"] if item["path"].endswith("vnm_ppp_2020.tif"))
    stage_times = {
        "listings_spark_seconds": listing_seconds,
        "osm_context_spark_seconds": osm_seconds,
        "worldpop_cells_and_aggregate_spark_seconds": worldpop_seconds,
        "city_key_integration_spark_seconds": integration_seconds,
        "total_spark_seconds": round(time.perf_counter() - run_started, 3),
    }
    products = {
        "curated_listing_records": {"path": str(curated_path.relative_to(ROOT)), "grain": "one curated listing record", "rows": valid_count, "parquet_data_bytes": parquet_payload_bytes(curated_path)},
        "listing_summary": {"path": str(summary_path.relative_to(ROOT)), "grain": "one Hanoi listing snapshot aggregate", "rows": 1, "parquet_data_bytes": parquet_payload_bytes(summary_path)},
        "listing_quality": {"path": str(quality_path.relative_to(ROOT)), "grain": "one row per quality disposition", "rows": quality.count(), "parquet_data_bytes": parquet_payload_bytes(quality_path)},
        "osm_city_context": {"path": str(osm_output_path.relative_to(ROOT)), "grain": "one Hanoi city aggregate", "rows": osm_count, "parquet_data_bytes": parquet_payload_bytes(osm_output_path)},
        "worldpop_valid_cells": {"path": str(cells_output_path.relative_to(ROOT)), "grain": "one valid raster cell", "rows": cell_rows, "parquet_data_bytes": parquet_payload_bytes(cells_output_path)},
        "worldpop_city_context": {"path": str(worldpop_city_path.relative_to(ROOT)), "grain": "one Hanoi city aggregate", "rows": 1, "parquet_data_bytes": parquet_payload_bytes(worldpop_city_path)},
        "city_context_join": {"path": str(city_context_path.relative_to(ROOT)), "grain": "one Hanoi city aggregate joined by city_key=VN-HN", "rows": city_context.count(), "parquet_data_bytes": parquet_payload_bytes(city_context_path)},
        "integrated_city": {"path": str(integrated_path.relative_to(ROOT)), "grain": "one listing-summary and context row joined by city_key=VN-HN", "rows": integrated_rows, "parquet_data_bytes": parquet_payload_bytes(integrated_path)},
    }
    lineage = {
        "listings": {
            "publisher_dataset": "Vietnam House Rent Dataset (Kaggle uploader: Van Viet Hieu Anh)",
            "grain": "source listing record; curated subset is title-reviewed likely Hanoi apartment rentals",
            "raw_files": listing_files,
            "input_rows_all_partitions": raw_rows,
            "input_rows_hanoi_partition": hanoi_rows,
            "title_positive_after_audit": 106,
            "curated_positive_amount_area_rows": valid_count,
            "source_last_updated": "2022-08-13",
        },
        "osm": {
            "publisher": "Geofabrik Vietnam OpenStreetMap extract",
            "source_snapshot_date": context_metadata["osm_file_date"],
            "source_snapshot_data_timestamp_utc": context_metadata["osm_snapshot_data_timestamp_utc"],
            "replication_sequence": context_metadata["osm_replication_sequence_number"],
            "source_downloaded_at_utc": context_metadata["osm_source_downloaded_at_utc"],
            "source_url": context_metadata["osm_source_url"],
            "source_file_bytes": context_metadata["osm_source_file_bytes"],
            "source_sha256": context_metadata["osm_source_sha256"],
            "prepared_aggregate_input": {"path": str(context_file.relative_to(ROOT)), "bytes": context_file.stat().st_size, "osm_feature_counts": context_metadata["osm_counts"]},
            "grain": "Hanoi city aggregate; tagged OSM counts and approximate road length",
            "license": "ODbL 1.0; \u00a9 OpenStreetMap contributors",
        },
        "worldpop": {
            "publisher": "WorldPop / University of Southampton",
            "source_reference_year": int(context_metadata["worldpop"]["year"]),
            "source_downloaded_at_utc": context_metadata["worldpop_source_downloaded_at_utc"],
            "source_url": worldpop_raw["url"],
            "source_file_bytes": worldpop_raw["bytes"],
            "source_sha256": worldpop_raw["sha256"],
            "prepared_raster": {"path": str((PUBLIC_OUT / "context" / "worldpop_hanoi_2020.tif").relative_to(ROOT)), "bytes": context_metadata["worldpop_clipped_raster_bytes"], "valid_cells": context_metadata["worldpop"]["valid_pixel_count"]},
            "spark_input_table": {"path": str(cells_path.relative_to(ROOT)), "bytes": cells_path.stat().st_size, "sha256": cells_schema_info["output_sha256"], "rows": cell_rows, "fields": list(cells_schema_info["fields"])},
            "grain": "one valid 100 m-class raster cell; aggregate output is one Hanoi city row",
            "license": "CC BY 4.0; WorldPop / University of Southampton; DOI 10.5258/SOTON/WP00645",
        },
    }
    run_manifest = {
        "run_id": run_id,
        "started_at_utc": run_started_at.isoformat(),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "spark_version": spark.version,
        "city_join_key": "VN-HN",
        "spatial_join_policy": "Context is aggregated at city grain. No OSM or WorldPop fields are attached to individual listing records because reliable listing coordinates/district/ward IDs are unavailable.",
        "source_lineage": lineage,
        "processing_seconds_by_stage": stage_times,
        "outputs": products,
        "attribution": {"osm": "\u00a9 OpenStreetMap contributors, ODbL 1.0", "worldpop": "WorldPop / University of Southampton, CC BY 4.0, DOI 10.5258/SOTON/WP00645"},
    }
    manifest_path = PUBLIC_OUT / "mart" / "run_manifest.json"
    manifest_path.write_text(json.dumps(run_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    quality_rows = quality.orderBy("quality_reason").collect()
    print(f"public: raw_rows={raw_rows}, hanoi_rows={hanoi_rows}, curated_valid_rentals={valid_count}, worldpop_valid_cells={cell_rows}, integrated_city_rows={integrated_rows}")
    print("Public pilot quality counts:")
    for row in quality_rows:
        print(f"  {row['quality_reason']}: {row['records']}")
    print("Spark stage seconds: " + json.dumps(stage_times, sort_keys=True))
    print("Parquet payload bytes: " + json.dumps({name: item["parquet_data_bytes"] for name, item in products.items()}, sort_keys=True))
    print(f"Run lineage manifest: {manifest_path}")
    print(f"Output: {PUBLIC_OUT}")

def main():
    parser = argparse.ArgumentParser(description="Run synthetic fixtures, legacy pilot, or public-data prototype.")
    parser.add_argument("--dataset", choices=("synthetic", "bds-pilot", "public"), default="synthetic")
    args = parser.parse_args()
    spark = (SparkSession.builder.master("local[2]").appName("IT5427-Hanoi-Rental-MVP").config("spark.driver.host", "127.0.0.1").config("spark.driver.bindAddress", "127.0.0.1").config("spark.sql.session.timeZone", "UTC").config("spark.sql.shuffle.partitions", "2").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    try:
        if args.dataset == "public":
            run_public(spark)
            return
        if args.dataset == "bds-pilot":
            adapters = [adapter_batdongsan(spark, pilot=True)]
            output = ROOT / "data" / "real_pilot"
        else:
            adapters = [adapter_batdongsan(spark), adapter_nhatot(spark), adapter_homedy(spark)]
            output = ROOT / "data"
        checked = normalize_fixture(reduce(lambda a, b: a.unionByName(b, allowMissingColumns=True), adapters))
        quality = checked.groupBy("source", "quality_reason").agg(F.count("*").alias("records"))
        valid = checked.filter(F.col("quality_reason") == "valid")
        curated = valid.dropDuplicates(["source", "source_listing_id"]).withColumn("price_per_m2", F.round(F.col("price_vnd_month") / F.col("area_m2"), 0))
        summary = curated.groupBy("source", "property_subtype", "district_normalized").agg(F.count("*").alias("sample_size"), F.expr("percentile_approx(price_vnd_month, 0.5)").alias("median_price_vnd_month"), F.expr("percentile_approx(price_per_m2, 0.5)").alias("median_price_per_m2"))
        curated.write.mode("overwrite").parquet(str(output / "curated" / "listings"))
        summary.coalesce(1).write.mode("overwrite").option("header", "true").csv(str(output / "mart" / "summary"))
        quality.coalesce(1).write.mode("overwrite").option("header", "true").csv(str(output / "mart" / "quality"))
        print(f"{args.dataset}: raw rows={checked.count()}, active rows={checked.filter(F.lower(F.col('listing_status')) == 'active').count()}, valid rows={valid.count()}, unique listings={curated.count()}")
        print(f"Output: {output / 'curated' / 'listings'}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
