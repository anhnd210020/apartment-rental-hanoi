"""Local dashboard for synthetic fixtures or the explicitly labelled public pilot."""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent


@st.cache_data
def load_csv(kind: str):
    files = list((ROOT / "data" / "mart" / kind).glob("part-*.csv"))
    return pd.read_csv(files[0]) if files else None


def load_parquet(kind: str):
    folder = ROOT / "data" / "public_pilot" / "mart" / kind
    return pd.read_parquet(folder) if folder.exists() else None


def load_public_run_manifest():
    path = ROOT / "data" / "public_pilot" / "mart" / "run_manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def load_nest_snapshot():
    latest_path = ROOT / "data" / "public_pilot" / "mart" / "nest_rent_index" / "latest.json"
    if not latest_path.exists():
        return None
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    manifest_path = ROOT / latest["manifest_path"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_paths = {name: ROOT / path for name, path in manifest["outputs"].items()}
    tables = {
        name: pd.read_parquet(path) if path.exists() else None
        for name, path in output_paths.items()
    }
    comparison_path = ROOT / "data" / "public_pilot" / "snapshot_comparison" / "nest_living_latest.json"
    comparison = json.loads(comparison_path.read_text(encoding="utf-8")) if comparison_path.exists() else None
    return {"manifest": manifest, "tables": tables, "comparison": comparison}


st.set_page_config(page_title="Hanoi Rental Integration MVP", layout="wide")
st.title("Hanoi apartment rental data prototype")
view_options = ["Synthetic fixtures", "Public-data prototype"]
requested_view = st.query_params.get("view", "")
default_view = 1 if requested_view == "public" else 0
mode = st.radio("View", view_options, index=default_view, horizontal=True, key="dashboard_view")

if mode == "Synthetic fixtures":
    st.warning("Synthetic test records only. They do not represent real Hanoi rental listings or market conditions.")
    summary, quality = load_csv("summary"), load_csv("quality")
    if summary is None or quality is None:
        st.info("Run `python pipeline.py` to create the synthetic fixture outputs.")
        st.stop()
    sources = sorted(summary["source"].unique().tolist())
    chosen = st.multiselect("Fixture sources", sources, default=sources)
    subtypes = sorted(summary["property_subtype"].unique().tolist())
    subtype = st.selectbox("Property segment", subtypes)
    view = summary[summary["source"].isin(chosen) & (summary["property_subtype"] == subtype)]
    st.metric("Valid fixture rows after deduplication", int(view["sample_size"].sum()))
    st.caption("Fixture price summaries are for pipeline demonstration only.")
    if not view.empty:
        fig = px.bar(view, x="district_normalized", y="median_price_vnd_month", color="source", hover_data=["sample_size"], barmode="group", labels={"district_normalized": "District (fixture)", "median_price_vnd_month": "Median fixture asking price (VND/month)"})
        st.plotly_chart(fig, width="stretch")
    st.subheader("Fixture quality counts")
    st.dataframe(quality, width="stretch")
else:
    st.warning("Exploratory public-data prototype. This uses one published rental-oriented listing dataset plus two geographic context datasets. It is not three independent rental-listing sources and does not represent the Hanoi market.")
    summary, quality = load_parquet("summary"), load_parquet("quality")
    city_context = load_parquet("city_context")
    run_manifest = load_public_run_manifest()
    nest_snapshot = load_nest_snapshot()
    if summary is None or quality is None or city_context is None:
        st.info("Run `python prepare_public_context.py`, `python prepare_worldpop_cells.py`, then `python pipeline.py --dataset public` first.")
        st.stop()
    row = summary.iloc[0]
    context = city_context.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Curated likely rental listings", int(row["valid_listings"]))
    c2.metric("Median listed amount (period mostly unknown)", f"{row['median_listed_amount_vnd'] / 1_000_000:.2f} million VND" if pd.notna(row["median_listed_amount_vnd"]) else "n/a")
    c3.metric("Median listed area", f"{row['median_area_m2']:.0f} m\u00b2" if pd.notna(row["median_area_m2"]) else "n/a")
    c4.metric("Median listed amount per m\u00b2", f"{row['median_listed_amount_per_m2_vnd']:,.0f} VND/m\u00b2" if pd.notna(row["median_listed_amount_per_m2_vnd"]) else "n/a")
    st.caption("The uploader gives amounts in million VND but no time basis for most rows. These are preliminary listed amounts, not transaction prices or market-wide estimates.")

    st.subheader("Kaggle monthly subset — separate small sample")
    st.warning("This Kaggle-only subset has n=9 verified monthly records. Treat it as a small, historical sample. It is not directly comparable with NEST's all-home aggregate, and the other 102 Kaggle listed amounts have mostly unknown time bases.")
    m1, m2, m3 = st.columns(3)
    monthly_count = int(row["verified_monthly_listing_count"])
    monthly_title_count = int(row["monthly_period_title_count"])
    monthly_unknown_price_count = int(row["monthly_title_unknown_price_count"])
    monthly_mismatch_count = int(row["monthly_title_amount_mismatch_count"])
    m1.metric("Titles with explicit monthly amount", int(row["monthly_period_title_count"]))
    m2.metric(f"Verified monthly records used (n={monthly_count})", monthly_count)
    m3.metric(f"Median verified monthly listed amount (n={monthly_count})", f"{row['median_verified_monthly_rent_vnd'] / 1_000_000:.2f} million VND/month" if pd.notna(row["median_verified_monthly_rent_vnd"]) else "n/a")
    monthly_rate = row["median_verified_monthly_rent_per_m2_vnd"]
    st.caption(f"Exploratory only: {monthly_count} of {monthly_title_count} titles stating a monthly amount match the structured field. {monthly_mismatch_count} mismatch and {monthly_unknown_price_count} unknown-price title are excluded. Median verified monthly listed amount per m\u00b2: {monthly_rate:,.0f} VND/m\u00b2/month. This small historical sample is not a market estimate." if pd.notna(monthly_rate) else "No verified monthly amount is available.")

    st.subheader("Listing title screening and quality counts")
    st.dataframe(quality.sort_values("records", ascending=False), width="stretch", hide_index=True)
    st.caption("The 3,284-row Hanoi partition was screened. The manual ledger covers only 303 apartment-cue candidates. The revised ledger marks 106 titles as likely whole-apartment rentals; 4 have unknown/nonpositive amounts, and 102 enter listed-amount summaries. Other uncertain labels and room-level offers remain excluded or flagged.")

    st.subheader("Hanoi-wide geographic context (city grain)")
    a, b, c, d = st.columns(4)
    a.metric("WorldPop population estimate (2020)", f"{context['worldpop_population_sum_estimate']:,.0f}")
    b.metric("OSM tagged highway ways", f"{context['osm_road_ways']:,.0f}")
    c.metric("OSM public transport stops", f"{context['osm_public_transport_stops']:,.0f}")
    d.metric("Approx. clipped tagged-way length", f"{context['osm_road_length_km_approx']:,.0f} km")
    st.write({"Education features": int(context["osm_education_features"]), "Health features": int(context["osm_health_features"]), "Other amenities": int(context["osm_other_amenities"]), "WorldPop valid cells": int(context["worldpop_valid_cell_count"])})
    integrated = load_parquet("integrated_city")
    integrated_rows = len(integrated) if integrated is not None else 0
    st.caption(f"Grain and join: OSM and WorldPop are city aggregates joined by city_key=VN-HN; the integrated city table has {integrated_rows} row. WorldPop cells were processed separately at one row per valid raster cell ({int(context['worldpop_valid_cell_count']):,} rows). Listing records have no reliable coordinates or district/ward IDs, so context is not attached to listings or described as neighborhood-level. OSM source data time: {context['osm_snapshot_data_timestamp_utc']}; WorldPop reference year: {int(context['worldpop_reference_year'])}.")
    st.caption("OSM highway length includes paths and service ways and may contain overlapping mapped segments. OSM counts are tagged features, not deduplicated institutions.")

    st.subheader("Source coverage and roles")
    nest_coverage = "Not registered — optional local aggregate input"
    if nest_snapshot:
        nest_manifest = nest_snapshot["manifest"]
        nest_profile = nest_manifest["profile"]
        nest_coverage = (
            f"{nest_profile['row_count']} aggregate cells; "
            f"{nest_profile['city_aggregate_rows']} city row; "
            f"{nest_profile['district_aggregate_rows']} district rows; "
            f"{nest_profile['property_type_aggregate_rows']} property-type rows; "
            f"snapshot {nest_profile['source_captured_at']}"
        )
    source_coverage = pd.DataFrame([
        {"Source": "Kaggle Vietnam House Rent Dataset", "Role": "One rental-oriented listing dataset", "Coverage evidence": "13,785 source rows; 3,284 Hanoi rows; 102 curated amount/area rows; 9 verified monthly rows", "Time basis": "Publisher last updated 2022-08-13; most listed amount periods unknown"},
        {"Source": "NEST Living Hanoi Rent Index", "Role": "Independent publisher's aggregate rental source; not listing rows", "Coverage evidence": nest_coverage, "Time basis": "Monthly asking-rent aggregates at the CSV capture time"},
        {"Source": "Geofabrik / OpenStreetMap", "Role": "Geographic context", "Coverage evidence": "One prepared Hanoi city aggregate", "Time basis": "OSM source data through 2026-09-30"},
        {"Source": "WorldPop", "Role": "Population context", "Coverage evidence": "408,151 valid Hanoi raster cells", "Time basis": "2020 reference year"},
    ])
    st.dataframe(source_coverage, width="stretch", hide_index=True)
    st.caption("Kaggle is one rental-oriented listing dataset. NEST is a separately published aggregate rental source. OSM and WorldPop are geographic context, not rental sources. NEST's all-home index has a different record universe from Kaggle's apartment-candidate sample; no NEST-to-Kaggle statistical join is made.")

    st.subheader("NEST Living — optional aggregate rental input")
    if not nest_snapshot:
        st.info("No NEST CSV has been ingested. The public, manually downloaded CSV remains optional because the terms page does not state an open reuse license. To register a local snapshot, use `ingest_nest_rent_index.py` with its CSV path and exact retrieval time.")
    else:
        nest_manifest = nest_snapshot["manifest"]
        nest_tables = nest_snapshot["tables"]
        city_rows = nest_tables.get("city")
        property_rows = nest_tables.get("property_type")
        district_rows = nest_tables.get("district")
        district_bedroom_rows = nest_tables.get("district_bedroom")
        capture_at = nest_manifest["source_captured_at_utc"]
        retrieved_at = nest_manifest["retrieved_at_utc"]
        st.info("NEST publishes monthly asking-rent aggregates from its own inventory, not the whole Hanoi market. These rows are aggregate cells, not homes/listings. The CSV is optional local input; NEST's terms do not state an open license for reuse, so source attribution and the terms caveat travel with every output.")
        if city_rows is not None and len(city_rows):
            city = city_rows.iloc[0]
            n1, n2, n3, n4 = st.columns(4)
            n1.metric("NEST city median asking rent", f"{city['median_vnd'] / 1_000_000:.1f}M VND/month" if pd.notna(city["median_vnd"]) else "suppressed")
            n2.metric("NEST middle half", f"{city['p25_vnd'] / 1_000_000:.1f}M–{city['p75_vnd'] / 1_000_000:.1f}M VND/month" if pd.notna(city["p25_vnd"]) and pd.notna(city["p75_vnd"]) else "suppressed")
            n3.metric("Homes behind NEST city cell", f"{int(city['homes']):,}")
            n4.metric("Source capture time (UTC)", capture_at)
        st.caption(f"CSV retrieved {retrieved_at}. NEST's methodology suppresses small cells below the recorded floor; this snapshot contains {nest_manifest['profile']['suppressed_cells']} suppressed cells. The city row covers NEST-listed homes only, with district/property mix concentrated in NEST's own inventory.")

        if property_rows is not None and len(property_rows):
            property_view = property_rows.copy()
            property_view = property_view[property_view["published"] == True].copy()
            st.markdown("**NEST monthly asking-rent median by property type**")
            if not property_view.empty:
                fig = px.bar(
                    property_view,
                    x="property_type",
                    y="median_vnd",
                    hover_data={"homes": True, "p25_vnd": ":,.0f", "p75_vnd": ":,.0f", "source_captured_at_utc": True},
                    labels={"property_type": "NEST property type", "median_vnd": "Median monthly asking rent (VND)"},
                )
                st.plotly_chart(fig, width="stretch")
            st.dataframe(
                property_rows[["property_type", "homes", "median_vnd", "p25_vnd", "p75_vnd", "published", "small_sample_floor"]],
                width="stretch", hide_index=True,
            )
            st.caption("Bars show only cells NEST marked published. Hover for sample size and middle-half values. Categories with fewer than 12 homes are especially thin; a publishable median is not automatically precise.")

        if district_rows is not None and len(district_rows):
            st.markdown("**NEST district totals — a separate aggregate mart**")
            st.dataframe(
                district_rows[["district_name", "homes", "median_vnd", "p25_vnd", "p75_vnd", "published"]],
                width="stretch", hide_index=True,
            )
        if district_bedroom_rows is not None and len(district_bedroom_rows):
            with st.expander("NEST district by bedroom class, including suppressed cells"):
                st.dataframe(
                    district_bedroom_rows[["district_name", "bedroom_class", "homes", "median_vnd", "p25_vnd", "p75_vnd", "published", "small_sample_suppressed"]],
                    width="stretch", hide_index=True,
                )
        if nest_snapshot["comparison"]:
            comp = nest_snapshot["comparison"]
            if comp["status"] == "insufficient_snapshots":
                st.caption(f"NEST aggregate snapshot comparison: {comp['available_snapshots']} genuine snapshot recorded; a second distinct source capture is required. No earlier snapshot or change count is inferred. This is separate from the dated OSM batch evidence and is not rental-listing Velocity.")
            elif comp["status"] == "compared":
                counts = comp["comparison"]
                st.caption(
                    f"NEST aggregate-only comparison: {counts['old_source_captured_at_utc']} → {counts['new_source_captured_at_utc']}; "
                    f"{counts['changed_cells']} changed of {counts['shared_cells']} shared cells, "
                    f"{counts['added_cells']} added, {counts['removed_cells']} removed. "
                    "These are aggregate-cell changes, not listing changes or rental-listing Velocity."
                )
        st.caption("NEST district keys remain in NEST's own namespace. Kaggle district text is not a reliable administrative join key, so no district aggregates are attached to Kaggle listings.")

    if run_manifest:
        listing_raw_bytes = sum(item["bytes"] for item in run_manifest["source_lineage"]["listings"]["raw_files"])
        listing_input_rows = int(run_manifest["source_lineage"]["listings"]["input_rows_all_partitions"])
        osm = run_manifest["source_lineage"]["osm"]
        worldpop = run_manifest["source_lineage"]["worldpop"]
        outputs = run_manifest["outputs"]
        times = run_manifest["processing_seconds_by_stage"]
        lineage_view = pd.DataFrame([
            {"Source": "Kaggle listings", "Original source bytes": listing_raw_bytes, "Spark input grain / rows / bytes": f"listing records / {listing_input_rows:,} / {listing_raw_bytes:,}", "Spark output grain / rows": f"curated listing records / {outputs['curated_listing_records']['rows']}", "Parquet bytes": outputs["curated_listing_records"]["parquet_data_bytes"], "Spark seconds": times["listings_spark_seconds"]},
            {"Source": "Geofabrik / OSM", "Original source bytes": osm["source_file_bytes"], "Spark input grain / rows / bytes": f"prepared city JSON / 1 / {osm['prepared_aggregate_input']['bytes']:,}", "Spark output grain / rows": f"Hanoi city aggregate / {outputs['osm_city_context']['rows']}", "Parquet bytes": outputs["osm_city_context"]["parquet_data_bytes"], "Spark seconds": times["osm_context_spark_seconds"]},
            {"Source": "WorldPop", "Original source bytes": worldpop["source_file_bytes"], "Spark input grain / rows / bytes": f"valid raster cells / {outputs['worldpop_valid_cells']['rows']:,} / {worldpop['spark_input_table']['bytes']:,}", "Spark output grain / rows": f"raster cells / {outputs['worldpop_valid_cells']['rows']:,}", "Parquet bytes": outputs["worldpop_valid_cells"]["parquet_data_bytes"], "Spark seconds": times["worldpop_cells_and_aggregate_spark_seconds"]},
        ])
        st.subheader("Spark processing and source grain")
        st.dataframe(lineage_view, width="stretch", hide_index=True)
        st.caption(f"City-key integration: {outputs['integrated_city']['rows']} output row, {outputs['integrated_city']['parquet_data_bytes']:,} Parquet bytes. Total Spark run time: {times['total_spark_seconds']:.2f} seconds. See the source lineage manifest for dates, hashes, and all output sizes.")

    st.subheader("Sources, attribution, and reuse notes")
    st.markdown("""- **Rental-oriented rows:** Van Viet Hieu Anh, [Vietnam House Rent Dataset](https://www.kaggle.com/datasets/vanviethieuanh/vietnam-house-rent-dataset). The uploader declares CC0. Its repository says records were scraped from websites but does not name the original websites; original platform provenance and third-party rights remain unverified. Source CSV rows and addresses are not shown here.
- **Geographic context:** [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL. Geofabrik Vietnam extract.
- **Population context:** [WorldPop Vietnam 2020](https://hub.worldpop.org/geodata/summary?id=6449), CC BY 4.0. Recommended citation: WorldPop (www.worldpop.org) / University of Southampton; DOI [10.5258/SOTON/WP00645](https://doi.org/10.5258/SOTON/WP00645).

The Kaggle publisher's CC0 declaration does not resolve rights in its unidentified upstream material. Use listing results for coursework exploration only, keep raw source files local, and do not redistribute them. TiniX is excluded because its dataset does not provide a validated rental-versus-sale label.""")

