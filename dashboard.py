"""Presentation dashboard for the public pilot and separate synthetic fixtures."""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent


@st.cache_data
def load_csv(kind):
    files = sorted((ROOT / "data" / "mart" / kind).glob("part-*.csv"))
    return pd.read_csv(files[0]) if files else None


@st.cache_data
def load_parquet(kind):
    folder = ROOT / "data" / "public_pilot" / "mart" / kind
    return pd.read_parquet(folder) if folder.exists() else None


@st.cache_data
def load_public_run_manifest():
    path = ROOT / "data" / "public_pilot" / "mart" / "run_manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@st.cache_data
def load_nest_snapshot():
    latest_path = ROOT / "data" / "public_pilot" / "mart" / "nest_rent_index" / "latest.json"
    if not latest_path.exists():
        return None
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / latest["manifest_path"]).read_text(encoding="utf-8"))
    tables = {name: pd.read_parquet(ROOT / path) if (ROOT / path).exists() else None
              for name, path in manifest["outputs"].items()}
    comparison_path = ROOT / "data" / "public_pilot" / "snapshot_comparison" / "nest_living_latest.json"
    comparison = json.loads(comparison_path.read_text(encoding="utf-8")) if comparison_path.exists() else None
    return {"manifest": manifest, "tables": tables, "comparison": comparison}


def integer(value):
    return f"{value:,.0f}".replace(",", " ")


def million(value, digits=1):
    return f"{value / 1_000_000:,.{digits}f}".replace(",", " ") if pd.notna(value) else "N/A"


def section(number, title, description):
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kicker">{number} / PUBLIC DATA</div>', unsafe_allow_html=True)
    st.markdown(f"## {title}")
    st.markdown(f'<p class="section-description">{description}</p>', unsafe_allow_html=True)


def metric(place, label, value, note=""):
    place.metric(label, value)
    if note:
        place.caption(note)


def detail_table(frame, columns):
    st.dataframe(frame[columns], width="stretch", hide_index=True)


st.set_page_config(page_title="IT5427 - Hanoi rental data", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
.stApp {background:#f7f9fc; color:#17324d}
.block-container {max-width:1200px; padding-top:1.6rem; padding-bottom:3rem}
h1,h2,h3,p {color:#17324d}
h2 {font-size:1.45rem!important; letter-spacing:-.02em; margin-bottom:.2rem!important}
h3 {font-size:1.08rem!important}
[data-testid="stMetric"] {background:white; border:1px solid #dce6ef; border-radius:12px; padding:15px 17px; min-height:108px; box-shadow:0 2px 8px rgba(18,53,81,.04)}
[data-testid="stMetricLabel"] {color:#52677b; font-size:.86rem; line-height:1.3}
[data-testid="stMetricValue"] {color:#17324d; font-size:1.75rem; line-height:1.2}
[data-testid="stAlert"],[data-testid="stExpander"] {border-radius:10px}
[data-testid="stExpander"] {background:white; border:1px solid #dce6ef}
.hero {background:linear-gradient(110deg,#173b5e,#246a79); border-radius:18px; padding:25px 32px; color:white; margin-bottom:1rem}
.hero .eyebrow {color:#b7e6e4; font-size:.77rem; font-weight:700; letter-spacing:.14em}
.hero h1 {color:white; font-size:2.1rem; line-height:1.15; margin:.35rem 0}
.hero p {color:#e1edf3; margin:0; max-width:840px}
.kicker {font-size:.74rem; font-weight:750; letter-spacing:.13em; color:#147d75; margin-top:1rem}
.section-description {color:#52677b; margin:0 0 1rem; line-height:1.45}
.note {background:#edf5f8; border-left:4px solid #147d75; padding:12px 16px; border-radius:7px; color:#27445d; margin:.7rem 0 1rem; line-height:1.45}
.divider {height:1px; background:#dce6ef; margin:1.5rem 0 .2rem}
@media(max-width:750px){.hero{padding:20px}.hero h1{font-size:1.6rem}[data-testid="stMetricValue"]{font-size:1.4rem}}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">IT5427 · HANOI RENTAL DATA PROTOTYPE</div><h1>Hanoi rental data</h1><p>Explore the data integration workflow and the limits of each source. Results support an academic demonstration and do not represent the whole market.</p></div>', unsafe_allow_html=True)
view_options = ["Public-data prototype", "Synthetic fixtures"]
if "dashboard_view" in st.session_state and st.session_state["dashboard_view"] not in view_options:
    del st.session_state["dashboard_view"]
mode = st.radio("View", view_options,
                index=1 if st.query_params.get("view", "public") == "synthetic" else 0,
                horizontal=True, key="dashboard_view")

if mode == "Synthetic fixtures":
    st.warning("SYNTHETIC DATA - Generated fixtures test the pipeline only. They do not represent real Hanoi rental listings or market conditions.")
    summary, quality = load_csv("summary"), load_csv("quality")
    if summary is None or quality is None:
        st.info("Run python pipeline.py to generate the synthetic fixture outputs.")
        st.stop()
    st.markdown("## Pipeline checks with synthetic fixtures")
    st.caption("Filters change the view of saved synthetic outputs only.")
    f1, f2 = st.columns(2)
    sources = sorted(summary["source"].unique().tolist())
    subtypes = sorted(summary["property_subtype"].unique().tolist())
    chosen = f1.multiselect("Fixture source", sources, default=sources)
    subtype = f2.selectbox("Synthetic property type", subtypes,
                          format_func=lambda value: {"apartment": "Apartment", "mini_service": "Mini / serviced apartment", "unknown": "Unknown"}.get(value, value))
    view = summary[summary["source"].isin(chosen) & (summary["property_subtype"] == subtype)]
    st.metric("Valid fixtures after deduplication", integer(view["sample_size"].sum()))
    if not view.empty:
        fig = px.bar(view, x="district_normalized", y="median_price_vnd_month", color="source",
                     hover_data=["sample_size"], barmode="group", color_discrete_sequence=["#2563a6", "#147d75", "#e39b51"],
                     labels={"district_normalized":"District (synthetic)", "median_price_vnd_month":"Median synthetic asking rent (VND/month)", "source":"Fixture source", "sample_size":"Fixture records"})
        fig.update_layout(template="plotly_white", height=350, margin=dict(l=20,r=15,t=20,b=20))
        st.plotly_chart(fig, width="stretch")
    with st.expander("Fixture quality details"):
        display_quality = quality.replace({"quality_reason": {
            "valid": "Valid", "expired_listing": "Expired listing", "missing_id": "Missing ID",
            "multi_unit_listing": "Multiple units in one listing", "unknown_type": "Unknown property type",
            "invalid_price": "Invalid price", "invalid_area": "Invalid area", "missing_district": "Missing district",
        }}).rename(columns={"source": "Source", "quality_reason": "Quality status", "records": "Records"})
        detail_table(display_quality, list(display_quality.columns))
    st.caption("All prices and place names in this view illustrate pipeline behavior only.")
    st.stop()

summary, quality = load_parquet("summary"), load_parquet("quality")
context_table = load_parquet("city_context")
run_manifest, nest_snapshot = load_public_run_manifest(), load_nest_snapshot()
if summary is None or quality is None or context_table is None:
    st.info("Public outputs are missing. Follow the README input checklist, then run prepare_public_context.py, prepare_worldpop_cells.py, and pipeline.py --dataset public.")
    st.stop()
row, context = summary.iloc[0], context_table.iloc[0]
st.info("SCOPE - Kaggle is one rental-oriented listing dataset. NEST is an independent aggregate source; OSM and WorldPop provide geographic context. NEST stays separate from listing records, and its rents are not directly comparable with Kaggle listed amounts.")

section("01", "Kaggle - Screening and listed amounts", "From the Hanoi partition to 102 records with usable amounts and areas.")
q1,q2,q3,q4 = st.columns(4)
total = int(quality["records"].sum())
outside = int(quality.loc[quality["quality_reason"]=="outside_hanoi_partition", "records"].sum())
metric(q1,"Kaggle source rows",integer(total),"Three input CSV files")
metric(q2,"Hanoi partition rows",integer(total-outside),"Hanoi partition")
metric(q3,"Manually reviewed titles","303","Candidates with apartment cues")
metric(q4,"Usable amount + area",integer(row["valid_listings"]),"Exploratory records; no confirmed transactions")
st.markdown('<div class="note"><strong>How to read this:</strong> Title review identified 106 likely whole-apartment rentals; 4 lack a usable positive amount. Of the remaining 102 listed amounts, 92 have an unknown time basis. These amounts must not be described as monthly rents.</div>', unsafe_allow_html=True)
k1,k2,k3 = st.columns(3)
metric(k1,"Median listed amount",f"{million(row['median_listed_amount_vnd'],2)} million VND","Time basis is mostly unknown")
metric(k2,"Median area",f"{integer(row['median_area_m2'])} m²")
metric(k3,"Median listed amount / m²",f"{integer(row['median_listed_amount_per_m2_vnd'])} VND","Per m²; time basis is mostly unknown")
with st.expander("Kaggle quality classification details"):
    labels = {"outside_hanoi_partition":"Outside the Hanoi partition", "rental_cue_non_apartment":"Rental cue without an apartment cue", "valid_exploratory_rental":"Included in exploratory summaries", "apartment_transaction_ambiguous":"Apartment cue with unclear transaction type", "room_or_shared_stay_excluded":"Room / shared stay excluded", "no_apartment_or_transaction_cue":"No apartment or transaction cue", "manual_review_ambiguous":"Ambiguous after manual review", "apartment_sale_excluded":"Apartment sale excluded", "sale_cue_non_apartment":"Sale cue without an apartment cue", "included_price_unknown":"Likely rental with unusable amount"}
    q = quality.assign(**{"Classification":quality["quality_reason"].map(labels),"Rows":quality["records"]})
    detail_table(q.sort_values("Rows",ascending=False),["Classification","Rows"])
    st.caption("The manual ledger covers only 303 candidates with apartment cues. Other classifications do not establish confirmed transactions.")

section("02", "Kaggle - Verified monthly subset", "A small historical subset, kept separate from NEST statistics.")
monthly_count = int(row["verified_monthly_listing_count"])
m1,m2,m3 = st.columns(3)
metric(m1,"Titles stating a monthly amount",integer(row["monthly_period_title_count"]))
metric(m2,"Matching structured amounts",integer(monthly_count),"Records used for monthly statistics")
metric(m3,"Median verified monthly amount",f"{million(row['median_verified_monthly_rent_vnd'],2)} million","VND/month · n=9")
st.warning(f"Only {monthly_count} records have a verified monthly basis; {int(row['monthly_title_amount_mismatch_count'])} title amount does not match the structured amount, and {int(row['monthly_title_unknown_price_count'])} has an unknown amount. Median per area: {integer(row['median_verified_monthly_rent_per_m2_vnd'])} VND/m²/month. This very small historical sample does not estimate the market and is not directly comparable with NEST.")

section("03", "Hanoi context - OSM and WorldPop", "Two geographic sources are aggregated and joined at one city key: VN-HN.")
g1,g2,g3,g4 = st.columns(4)
metric(g1,"WorldPop population estimate",integer(context["worldpop_population_sum_estimate"]),"Reference raster: 2020")
metric(g2,"Valid raster cells",integer(context["worldpop_valid_cell_count"]))
metric(g3,"OSM highway-tagged ways",integer(context["osm_road_ways"]),"Ways are not unique roads")
metric(g4,"Public transport stop features",integer(context["osm_public_transport_stops"]))
integrated = load_parquet("integrated_city")
st.markdown(f'<div class="note"><strong>Integration grain:</strong> OSM + WorldPop form one Hanoi context row; the integrated table has {len(integrated) if integrated is not None else 0} row at city_key=VN-HN. Listing records lack reliable coordinates or district/ward IDs for enrichment at individual listing or neighborhood level.</div>', unsafe_allow_html=True)
with st.expander("More geographic context metrics and limitations"):
    geo = pd.DataFrame([("Approximate tagged-way length",f"{integer(context['osm_road_length_km_approx'])} km"),("Education features",integer(context["osm_education_features"])),("Health features",integer(context["osm_health_features"])),("Other amenity features",integer(context["osm_other_amenities"])),("OSM source data timestamp",context["osm_snapshot_data_timestamp_utc"])],columns=["Metric","Value"])
    detail_table(geo,["Metric","Value"])
    st.caption("Length includes paths and service ways and can include overlapping segments. OSM counts tagged features rather than deduplicated institutions. WorldPop is a modelled estimate, not observed population at individual addresses.")

section("04", "NEST Living - Separate aggregate statistics", "Monthly asking rents from NEST's own inventory. Each row is an aggregate cell rather than an individual listing.")
if not nest_snapshot:
    st.info("No NEST CSV has been ingested. This optional local input is registered with ingest_nest_rent_index.py using the CSV path and its actual retrieval timestamp.")
else:
    manifest, tables = nest_snapshot["manifest"], nest_snapshot["tables"]
    st.caption(f"Source: NEST Living - Capture {manifest['source_captured_at_utc']} - CSV retrieved {manifest['retrieved_at_utc']} - Describes the publisher's own inventory only.")
    city_rows, property_rows = tables.get("city"), tables.get("property_type")
    if city_rows is not None and len(city_rows):
        city = city_rows.iloc[0]
        st.markdown("### City cell - All property types")
        n1,n2,n3 = st.columns(3)
        metric(n1,"NEST city median",f"{million(city['median_vnd'])} million","VND/month - All property types")
        metric(n2,"Homes in the city cell",integer(city["homes"]),"Home count rather than cell count")
        metric(n3,"Middle 50% range",f"{million(city['p25_vnd'])} - {million(city['p75_vnd'])} million","VND/month - p25 to p75")
    if property_rows is not None and len(property_rows):
        st.markdown("### Property types - Separate cells")
        chart = property_rows.loc[property_rows["published"] == True].copy()
        if not chart.empty:
            chart["median_million"] = chart["median_vnd"] / 1_000_000
            chart["Property type"] = chart["property_type"].replace({"Whole house":"Whole house","Serviced apartment":"Serviced apartment","Villa":"Villa","Studio":"Studio","Apartment":"Apartment"})
            chart = chart.sort_values("median_million")
            chart["Label"] = chart.apply(lambda r:f"{million(r['median_vnd'])} million · n={integer(r['homes'])}",axis=1)
            fig = px.bar(chart,x="median_million",y="Property type",orientation="h",text="Label",custom_data=["homes","p25_vnd","p75_vnd"],color_discrete_sequence=["#147d75"],labels={"median_million":"Median asking rent (million VND/month)","Property type":""})
            fig.update_traces(textposition="outside",cliponaxis=False,hovertemplate="%{y}<br>Median: %{x:.1f} million VND/month<br>Homes: %{customdata[0]}<br>p25: %{customdata[1]:,.0f} VND<br>p75: %{customdata[2]:,.0f} VND<extra></extra>")
            fig.update_layout(template="plotly_white",height=340,font=dict(color="#17324d",size=13),margin=dict(l=18,r=125,t=14,b=40),showlegend=False,xaxis=dict(range=[0,chart["median_million"].max()*1.3],gridcolor="#e8eef4",zeroline=False),yaxis=dict(categoryorder="array",categoryarray=chart["Property type"].tolist(),autorange="reversed"),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,width="stretch")
        apartment = property_rows.loc[property_rows["property_type"]=="Apartment"]
        if not apartment.empty:
            apt = apartment.iloc[0]
            st.caption(f"Separate Apartment cell: n={integer(apt['homes'])} homes, median {million(apt['median_vnd'])} million VND/month. The city cell above covers multiple property types. These two cells have different populations and medians.")
        st.caption("Only published NEST cells are plotted. Cells with fewer than 5 homes suppress medians and quartiles; types with fewer than 12 homes are especially thin. Publication does not imply high precision.")
        with st.expander("Details of the 5 property-type cells"):
            p = property_rows.rename(columns={"property_type":"Property type","homes":"Homes","median_vnd":"Median (VND/month)","p25_vnd":"p25 (VND)","p75_vnd":"p75 (VND)","published":"Published"})
            detail_table(p,["Property type","Homes","Median (VND/month)","p25 (VND)","p75 (VND)","Published"])
    profile = manifest["profile"]
    st.markdown(f'<div class="note"><strong>NEST coverage:</strong> {profile["row_count"]} aggregate cells per capture: {profile["city_aggregate_rows"]} city, {profile["district_aggregate_rows"]} district, {profile["property_type_aggregate_rows"]} property type, and {profile["cut_counts"]["district_bedroom"]} district × bedroom. {profile["suppressed_cells"]} cells suppress statistics because of small samples.</div>',unsafe_allow_html=True)
    comp = nest_snapshot["comparison"]
    if comp and comp["status"] == "compared":
        counts = comp["comparison"]
        st.markdown("### Two NEST captures - Changes at cell level")
        c1,c2,c3 = st.columns(3)
        metric(c1,"Shared cells",integer(counts["shared_cells"]))
        metric(c2,"Changed cells",integer(counts["changed_cells"]))
        metric(c3,"Unchanged cells",integer(counts["unchanged_shared_cells"]))
        st.caption(f"{counts['old_source_captured_at_utc']} → {counts['new_source_captured_at_utc']}; added {counts['added_cells']}, removed {counts['removed_cells']} cells. These are aggregate-cell changes, not individual listing changes or rental-listing Velocity.")
    elif comp and comp["status"] == "insufficient_snapshots":
        st.caption(f"Only {comp['available_snapshots']} genuine capture(s) are available; changed-cell counts cannot be inferred yet. This does not establish rental-listing Velocity.")
    with st.expander("NEST district and bedroom details"):
        if tables.get("district") is not None:
            st.markdown("**NEST district aggregate cells**")
            d = tables["district"].rename(columns={"district_name":"District","homes":"Homes","median_vnd":"Median (VND/month)","published":"Published"})
            detail_table(d,["District","Homes","Median (VND/month)","Published"])
        if tables.get("district_bedroom") is not None:
            st.markdown("**District × bedroom cells, including suppressed statistics**")
            d = tables["district_bedroom"].rename(columns={"district_name":"District","bedroom_class":"Bedrooms","homes":"Homes","median_vnd":"Median (VND/month)","published":"Published"})
            detail_table(d,["District","Bedrooms","Homes","Median (VND/month)","Published"])
        st.caption("NEST district keys use a separate namespace. Kaggle district text is not reliable enough to join the two sources.")
    st.caption("NEST is an optional local CSV input. Its terms state no open license or explicit CSV reuse grant; retain attribution and this caveat with the outputs.")

section("05", "Spark - Processing and provenance", "Listing records, raster cells, and aggregate cells retain their distinct observation grains.")
if run_manifest:
    outputs, times = run_manifest["outputs"], run_manifest["processing_seconds_by_stage"]
    s1,s2,s3 = st.columns(3)
    metric(s1,"Curated listing records",integer(outputs["curated_listing_records"]["rows"]),"Kaggle records")
    metric(s2,"WorldPop raster cells",integer(outputs["worldpop_valid_cells"]["rows"]),"Parquet output")
    metric(s3,"Spark processing time",f"{times['total_spark_seconds']:.1f} seconds","One local run; not a benchmark")
    st.caption(f"Integration at VN-HN: {outputs['integrated_city']['rows']} row, {integer(outputs['integrated_city']['parquet_data_bytes'])} Parquet bytes. NEST runs as a separate job and is excluded from the timing above.")
    with st.expander("Lineage and processing size details"):
        listing = run_manifest["source_lineage"]["listings"]
        osm = run_manifest["source_lineage"]["osm"]
        worldpop = run_manifest["source_lineage"]["worldpop"]
        lineage = pd.DataFrame([
            {"Source":"Kaggle listing","Spark input":f"{integer(listing['input_rows_all_partitions'])} listing rows","Output":f"{integer(outputs['curated_listing_records']['rows'])} listing rows","Parquet (byte)":outputs["curated_listing_records"]["parquet_data_bytes"],"Spark (seconds)":times["listings_spark_seconds"]},
            {"Source":"OSM / Geofabrik","Spark input":"1 city JSON aggregate","Output":f"{outputs['osm_city_context']['rows']} city row","Parquet (byte)":outputs["osm_city_context"]["parquet_data_bytes"],"Spark (seconds)":times["osm_context_spark_seconds"]},
            {"Source":"WorldPop","Spark input":f"{integer(outputs['worldpop_valid_cells']['rows'])} raster cells","Output":f"{integer(outputs['worldpop_valid_cells']['rows'])} raster cells","Parquet (byte)":outputs["worldpop_valid_cells"]["parquet_data_bytes"],"Spark (seconds)":times["worldpop_cells_and_aggregate_spark_seconds"]}])
        detail_table(lineage,list(lineage.columns))
        st.caption(f"Source sizes: Kaggle {integer(sum(item['bytes'] for item in listing['raw_files']))} bytes; OSM PBF {integer(osm['source_file_bytes'])} bytes; WorldPop GeoTIFF {integer(worldpop['source_file_bytes'])} bytes. The manifest records hashes, timestamps, and each output size.")
with st.expander("Sources, attribution, and reuse limitations"):
    st.markdown("""- **Kaggle:** Van Viet Hieu Anh, [Vietnam House Rent Dataset](https://www.kaggle.com/datasets/vanviethieuanh/vietnam-house-rent-dataset). The uploader declares CC0 but does not identify the original listing websites; upstream rights remain unverified. Keep source CSVs local and do not redistribute them.
- **NEST Living:** [Hanoi Rent Index](https://nestliving.vn/rent-index) and [terms](https://nestliving.vn/terms). Optional aggregate CSV; no stated open license or explicit reuse grant.
- **OSM / Geofabrik:** [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL. Geographic context rather than listing data.
- **WorldPop:** [Vietnam Population Counts 2020](https://hub.worldpop.org/geodata/summary?id=6449), CC BY 4.0; WorldPop / University of Southampton, DOI [10.5258/SOTON/WP00645](https://doi.org/10.5258/SOTON/WP00645).

TiniX is excluded because it lacks a validated rental-versus-sale label. Results support academic exploration only.""")

