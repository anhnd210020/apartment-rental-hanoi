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


st.set_page_config(page_title="Hanoi Rental Integration MVP", layout="wide")
st.title("Hanoi apartment rental data prototype")
mode = st.radio("View", ["Synthetic fixtures", "Public-data prototype"], horizontal=True)

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

    st.subheader("Explicit monthly-price subset")
    m1, m2, m3 = st.columns(3)
    m1.metric("Titles with explicit monthly amount", int(row["monthly_period_title_count"]))
    m2.metric(f"Verified monthly records used (n={int(row['verified_monthly_listing_count'])})", int(row["verified_monthly_listing_count"]))
    m3.metric(f"Median verified monthly listed amount (n={int(row['verified_monthly_listing_count'])})", f"{row['median_verified_monthly_rent_vnd'] / 1_000_000:.2f} million VND/month" if pd.notna(row["median_verified_monthly_rent_vnd"]) else "n/a")
    monthly_rate = row["median_verified_monthly_rent_per_m2_vnd"]
    st.caption(f"Exploratory only: n=9 titles state a monthly amount and match the structured field. One mismatch and one unknown-price title are excluded. Median verified monthly listed amount per m\u00b2: {monthly_rate:,.0f} VND/m\u00b2/month. This small historical sample is not a market estimate." if pd.notna(monthly_rate) else "No verified monthly amount is available.")

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

    if run_manifest:
        listing_raw_bytes = sum(item["bytes"] for item in run_manifest["source_lineage"]["listings"]["raw_files"])
        osm = run_manifest["source_lineage"]["osm"]
        worldpop = run_manifest["source_lineage"]["worldpop"]
        outputs = run_manifest["outputs"]
        times = run_manifest["processing_seconds_by_stage"]
        lineage_view = pd.DataFrame([
            {"Source": "Kaggle listings", "Original source bytes": listing_raw_bytes, "Spark input grain / rows / bytes": f"listing records / 13,785 / {listing_raw_bytes:,}", "Spark output grain / rows": f"curated listing records / {outputs['curated_listing_records']['rows']}", "Parquet bytes": outputs["curated_listing_records"]["parquet_data_bytes"], "Spark seconds": times["listings_spark_seconds"]},
            {"Source": "Geofabrik / OSM", "Original source bytes": osm["source_file_bytes"], "Spark input grain / rows / bytes": f"prepared city JSON / 1 / {osm['prepared_aggregate_input']['bytes']:,}", "Spark output grain / rows": f"Hanoi city aggregate / {outputs['osm_city_context']['rows']}", "Parquet bytes": outputs["osm_city_context"]["parquet_data_bytes"], "Spark seconds": times["osm_context_spark_seconds"]},
            {"Source": "WorldPop", "Original source bytes": worldpop["source_file_bytes"], "Spark input grain / rows / bytes": f"valid raster cells / {outputs['worldpop_valid_cells']['rows']:,} / {worldpop['spark_input_table']['bytes']:,}", "Spark output grain / rows": f"raster cells / {outputs['worldpop_valid_cells']['rows']:,}", "Parquet bytes": outputs["worldpop_valid_cells"]["parquet_data_bytes"], "Spark seconds": times["worldpop_cells_and_aggregate_spark_seconds"]},
        ])
        st.subheader("Spark processing and source grain")
        st.dataframe(lineage_view, width="stretch", hide_index=True)
        st.caption(f"City-key integration: {outputs['integrated_city']['rows']} output row, {outputs['integrated_city']['parquet_data_bytes']:,} Parquet bytes. Total Spark run time: {times['total_spark_seconds']:.2f} seconds. See the source lineage manifest for dates, hashes, and all output sizes.")

    st.subheader("Sources, attribution, and reuse notes")
    st.markdown("""- **Rental-oriented rows:** Van Viet Hieu Anh, [Vietnam House Rent Dataset](https://www.kaggle.com/datasets/vanviethieuanh/vietnam-house-rent-dataset). The uploader declares CC0. Its repository says records were scraped from websites but does not name the original websites; original platform provenance and third-party rights remain unverified. Source CSV rows and addresses are not shown here.
- **Geographic context:** ? [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL. Geofabrik Vietnam extract.
- **Population context:** [WorldPop Vietnam 2020](https://hub.worldpop.org/geodata/summary?id=6449), CC BY 4.0. Recommended citation: WorldPop (www.worldpop.org) / University of Southampton; DOI [10.5258/SOTON/WP00645](https://doi.org/10.5258/SOTON/WP00645).

The Kaggle publisher's CC0 declaration does not resolve rights in its unidentified upstream material. Use listing results for coursework exploration only, keep raw source files local, and do not redistribute them. TiniX is excluded because its dataset does not provide a validated rental-versus-sale label.""")

