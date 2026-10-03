# Public dataset feasibility study

**Checked:** 2026-10-02 (Asia/Bangkok)  
**Project:** *Multi-source Apartment Rental Data Integration and Analysis in Hanoi*  
**Scope:** Small feasibility study only. The Spark pipeline and dashboard were not changed, and no full listing dataset or Geofabrik extract was downloaded.

## Decision summary

This plan has **two published rental-oriented listing datasets plus one geographic context dataset**. It does not describe all three as rental websites or claim that either listing dataset represents multiple original platforms. Dataset publisher provenance is distinct from original listing-platform provenance.

| Candidate | Decision | Feasibility result |
|---|---|---|
| Kaggle, *Vietnam House Rent Dataset* (Van Viet Hieu Anh) | **CONDITIONAL** | CC0 is stated on the Kaggle page, but the publisher says the data was scraped from websites without identifying them. The Hanoi CSV has only five untyped fields. A 100-row preview yielded two clear apartment-rental title matches; a dependable full-file apartment filter is not established. |
| TiniX AI, *Vietnam Real Estate Listings* | **REJECT** for current rental analysis | The card says CC BY-NC 4.0 and exposes Hanoi and apartment categories, but has no transaction field or original platform provenance. The stratified text review did not verify a rental in the sample; ambiguous records are excluded. Reconsider only with explicit labels, source provenance, and rights evidence. |
| OpenStreetMap via Geofabrik Vietnam extract | **ACCEPT** for geographic context only | Public ODbL data, a documented Vietnam `.osm.pbf` extract, and daily snapshot/diff workflow are available. It supplies no rental listings and cannot count as a listing source. |

**G2 remains incomplete.** This study has not verified three qualifying rental listing sources or three adequate, independently sourced rental datasets. The existing Batdongsan pilot remains a separate manual pilot with one valid record; the synthetic fixtures remain synthetic.

## Method and what “independent source” means

The listing previews were inspected through publisher descriptions and small samples, without crawling listing sites. Kaggle metadata and a 100-row prefix of its Hanoi CSV were inspected; the 100 rows were streamed from the publisher's public repository and no source addresses were copied into this report. For TiniX, 500 rows were inspected through the Hugging Face dataset viewer API at five separated offsets (0, 100,000, 1,000,000, 2,000,000, and 3,000,000; 100 rows per offset). No Parquet shard was fetched. A Vietnamese keyword rule using only title/description text assigned `sale`, `rental`, `ambiguous`, or `no cue`; I manually reviewed a reference set of 20 rows, five sampled from each predicted class. Price magnitude was not used to assign transaction class. Rows whose offer type was unclear or whose text mixed sale and rental context were marked ambiguous and excluded from rental analysis.

An independent source here means a distinct dataset publication or a direct provider feed with documented creator, provenance, and reuse basis. A mirror, format conversion, copied Hugging Face repository, or repackaging of the same underlying records is not a new source. Kaggle and TiniX are distinct published datasets, but their original listing platforms are not established by the evidence reviewed. OSM is an independent geographic context source, not a rental-listing source.

## Kaggle: Vietnam House Rent Dataset

**Decision: CONDITIONAL.** The Kaggle page states the license as **CC0: Public Domain**, publisher as Van Viet Hieu Anh, and last updated **2022-08-13**. CC0 does not itself verify that the publisher owned rights in every third-party record; the publisher's repository says the dataset was scraped from websites and disclaims responsibility, but does not identify those websites. This provenance gap matters even though the dataset's Kaggle license field is permissive. The CC0 deed also explains that a CC0 mark does not affect privacy/publicity or other third-party rights.

The publisher's README describes 9,052 rows overall: `hcm.csv` 5,000; `dn.csv` 768; `hn.csv` 3,284. Total published file size is about **2.49 MB**; `hn.csv` is 599,720 bytes. The listing format is CSV (the README also lists corresponding JSON files). Its schema is exactly `title`, `published`, `address`, `acreage`, and `price`; `published` is documented as `dd/mm/yyyy`, acreage as square metres, and price as millions of VND with `-1` meaning negotiable. There is no structured property type, transaction type, district, or ward field.

In the 100-row Hanoi preview, 99 `published` values parsed, spanning **2015-11-16 through 2022-07-14**. A title-only cue screen found 68 rows with a rent/lease word and four with an apartment-like term (`căn hộ`, `chung cư`, `apartment`, `studio`, or `condo`); two titles had both kinds of cue. Manual title inspection confirmed two clear apartment-rental candidates in this 100-row sample (a mini-apartment rental and an apartment rental). The other two apartment-like titles did not state a clear rental offer in the title. The sample also contains many room/boarding-house ads. These are preview counts, not estimates for all 3,284 rows.

**Verified filtering count:** 2 Hanoi apartment-rental candidates in the 100 inspected rows; the number in the full 3,284-row Hanoi file remains unknown. This is too little evidence to call a reliable full-file apartment filter. The `address` field can contain detailed addresses, so any later use should immediately reduce it to district/ward where possible and discard exact address text; do not geocode it.

The Kaggle page's stated CC0 and the publisher's scrape disclosure are recorded at [Kaggle's dataset page](https://www.kaggle.com/datasets/vanviethieuanh/vietnam-house-rent-dataset), the [publisher's field and sample README](https://github.com/vanviethieuanh/dataset/blob/main/house-rent/README.md), the [publisher's repository provenance note](https://github.com/vanviethieuanh/dataset/blob/main/README.md), and the [CC0 deed](https://creativecommons.org/publicdomain/zero/1.0/).

## TiniX Vietnam Real Estate Listings

**Decision: REJECT for current rental analysis.** The Hugging Face card names TiniX AI as the dataset publisher, states **CC BY-NC 4.0**, gives a collection/published-date range of **2025-06-01 to 2026-03-31**, and lists 3,500,744 records in 10 Parquet shards (about **1.67 GB**). The Hugging Face repository snapshot metadata was last modified **2026-04-14**. The card's full-dataset distribution table claims **1,140,542 Hanoi records**. These are publisher-stated corpus figures, not counts independently recomputed from the full shards.

The 19 fields include `name`, `description`, `property_type_name`, `province_name`, `district_name`, `ward_name`, `street_name`, `project_name`, `price`, `area`, floor/frontage/depth/road-width values, bedroom/bathroom counts, directions, and `published_at`. In the preview, province and apartment type are directly identifiable from fields. There is no explicit rent/sale or listing-status column. The publisher says phone numbers are redacted. No original listing websites/platforms are named in the card, so TiniX is treated as the publisher of a distinct dataset publication, not as evidence of a distinct original listing platform or a multi-platform source.

### Text-classification pilot and manual reference sample

The tested keyword rule looked for Vietnamese sale cues (`bán`, `cần bán`, `giá bán`, `chuyển nhượng`) and rental cues (`cho thuê`, `cần thuê`, `giá thuê`, `thuê căn hộ`, `thuê phòng`) in title/description. A match in descriptive text alone was not treated as conclusive where the listing appeared to offer the property for sale while mentioning current tenants, rental yield, or suitability for letting. This exposed the main failure mode: “cho thuê” can describe income from a property being sold, not the transaction being advertised.

| Predicted class | Manual reference n | Manually clear sale | Manually clear rental | Manually ambiguous |
|---|---:|---:|---:|---:|
| Rental | 5 | 1 | 0 | 4 |
| Sale | 5 | 5 | 0 | 0 |
| Ambiguous (both cue families) | 5 | 5 | 0 | 0 |
| No cue | 5 | 0 | 0 | 5 |
| **Total** | **20** | **11** | **0** | **9** |

This reference set was manually selected across predicted classes from the 500-row preview; it is deliberately stratified and is not prevalence-representative. On the one non-ambiguous row predicted rental, **rental precision was 0/1 = 0%**. Four of the five predicted-rental rows were manually ambiguous and excluded. **Rental recall is not estimable** because the 20-row reference contains no manually confirmed rental positives; reporting a numeric recall would be misleading. Nine of 20 rows were manually ambiguous. The 500-row preview's heuristic classes were 396 sale, 14 rental, 29 ambiguous, and 61 no-cue; these are candidate counts, not accuracy estimates.

Within those same 500 preview rows, 160 had `province_name = Hà Nội`; 41 of those had the structured apartment category `Căn hộ chung cư`. The text rule labeled those 41 as 38 sale, 2 ambiguous, 1 no-cue, and **0 rental**. Therefore **zero Hanoi apartment rentals were verified in this preview sample**. All ambiguous rows are excluded from rental analysis. This does not prove that the full 1.14M Hanoi subset contains no rentals; it means the available evidence cannot establish them or support safe full-corpus rental filtering.


The manually adjudicated preview sample is recorded below by the viewer’s zero-based row offset within the five sampled blocks. These are audit references only, not source listing IDs (the schema has no listing ID). Text is paraphrased so the report does not reproduce listing descriptions or contact data.

| Preview offset | Predicted | Manual label | Adjudication note |
|---:|---|---|---|
| 3,000,042 | Rental | Ambiguous | Listing text combines a monthly letting offer and negotiable sale wording. |
| 100,033 | Rental | Ambiguous | Text describes suitability for letting but does not resolve the advertised transaction. |
| 100,004 | Rental | Sale | Description explicitly says the apartment is being transferred/resold. |
| 80 | Rental | Ambiguous | Current commercial tenancy and negotiable wording do not resolve the advertised transaction. |
| 3,000,008 | Rental | Ambiguous | Mentions rental income and office letting suitability, without a clear transaction label. |
| 89 | Ambiguous | Sale | Title explicitly advertises an apartment for sale; letting is only a possible use. |
| 100,030 | Ambiguous | Sale | Description explicitly gives a sale offer; letting is mentioned as a possible use. |
| 49 | Ambiguous | Sale | Description explicitly says the apartment is for sale and separately mentions rental yield. |
| 100,095 | Ambiguous | Sale | Description explicitly gives a sale asking offer and separately says rooms are rented. |
| 77 | Ambiguous | Sale | Description explicitly advertises sale; nearby rental housing is contextual text. |
| 3,000,068 | No cue | Ambiguous | No explicit sale or rental offer found in the reviewed text. |
| 2,000,043 | No cue | Ambiguous | Property details and a unit price appear, but no clear transaction statement. |
| 1,000,030 | No cue | Ambiguous | Property details and asking-price text alone do not establish sale/rent class. |
| 100,009 | No cue | Ambiguous | Property description has no explicit transaction status. |
| 100,097 | No cue | Ambiguous | Property description has no explicit transaction status. |
| 3,000,058 | Sale | Sale | Title and description state a project is opening sales. |
| 100,096 | Sale | Sale | Title and description explicitly advertise houses for sale. |
| 3,000,031 | Sale | Sale | Description explicitly describes sale/resale of the unit. |
| 22 | Sale | Sale | Title explicitly says transfer/resale. |
| 2 | Sale | Sale | Title and description explicitly advertise a villa for sale. |
The card's license permits attributed, non-commercial sharing/adaptation under CC BY-NC 4.0 and requires credit, a license link, and indication of changes. That stated license is not proof that the publisher can sublicense underlying listing text. For any course use, cite TiniX AI and the dataset title, link the dataset and license, record modifications, and do not redistribute raw rows unless rights are clarified. See the [TiniX dataset card and schema](https://huggingface.co/datasets/tinixai/vietnam-real-estates), the [CC BY-NC 4.0 deed](https://creativecommons.org/licenses/by-nc/4.0/), and [Hugging Face repository metadata](https://huggingface.co/api/datasets/tinixai/vietnam-real-estates).

The detailed text includes location and property context, sometimes with street/project names, but no coordinates are shown in the 19-field schema. Use only district/ward or coarser areas for analysis. Do not attempt to infer transaction type from `price`, including price magnitude.

## OpenStreetMap via Geofabrik Vietnam

**Decision: ACCEPT for geographic context only.** OpenStreetMap data is under the **Open Data Commons Open Database License 1.0 (ODbL)**. The attribution page requires credit to OpenStreetMap and its contributors and a clear statement/link that the data is available under ODbL. Adapted data distributed onward may carry share-alike obligations; the intended form of any derived database should be checked against the full ODbL terms. A suitable map/report credit is “© OpenStreetMap contributors” linked to `https://www.openstreetmap.org/copyright`, with the ODbL named.

Geofabrik's Vietnam page offers `vietnam-latest.osm.pbf`, a country extract suitable for Osmium and related tools. On the check date it was 314 MB, last modified about a day earlier, and contained OSM data through **2026-09-30 20:22:42 UTC**. The page also offers larger selected shapefile/GeoPackage exports and an updates directory with `.osc.gz` daily changes. Geofabrik states that public extracts omit contributor usernames, user IDs, and changeset IDs. The appropriate small-project workflow is to record the chosen PBF filename, URL, retrieval time, reported data timestamp, and checksum; use Osmium to extract/clip Hanoi features from the Vietnam PBF; retain ODbL attribution; and, only if repeated snapshots are actually retrieved, apply compatible diffs or compare dated full extracts. No extract was downloaded during this study.

Useful contextual tags include:

- **Roads:** `highway=*` (for example primary/secondary/residential), optionally `surface=*` and `lit=*` where mapped.
- **Public transport:** `highway=bus_stop`, `public_transport=platform` / `stop_position`, `railway=station`, `station=subway`, and route relations where available.
- **Education:** `amenity=school`, `amenity=university`, `amenity=college`, `amenity=kindergarten`.
- **Health:** `amenity=hospital`, `amenity=clinic`, `amenity=doctors`, `amenity=pharmacy`.
- **Other amenities:** `amenity=marketplace`, `shop=supermarket`, `leisure=park`, `amenity=library`, and mapped public facilities.

OSM completeness varies by place and feature; a missing mapped school or stop is not proof that the real-world feature is absent. Join rental records using district/ward polygons or generalized area centroids and produce district/ward counts or broad accessibility measures. Do not retain or geocode exact personal addresses. If a provider supplies only ward/district labels, use those labels to aggregate OSM points/polygons to the same administrative unit. This yields contextual variables such as amenity counts per ward, road density per ward, or approximate distance from an area centroid—not a precise property-to-amenity location.

Official references: [OSM copyright and license](https://www.openstreetmap.org/copyright), [Geofabrik Vietnam download page](https://download.geofabrik.de/asia/vietnam.html), [Geofabrik download/extract workflow](https://www.geofabrik.de/de/data/download.html), and [Geofabrik technical details for extracts and diffs](https://osm-internal.download.geofabrik.de/technical.html).

## 3V assessment

| V | Evidence from this feasibility check | What can and cannot be concluded |
|---|---|---|
| **Volume** | Kaggle publishes 9,052 rows total, including 3,284 Hanoi rows; 100 Hanoi rows inspected, 2 clear apartment-rental title matches. TiniX publishes 3,500,744 rows (1.67 GB), including 1,140,542 Hanoi rows per its card; 500 rows inspected, with 160 Hanoi rows and 41 structured apartments, but 0 verified Hanoi apartment rentals. Geofabrik's current Vietnam PBF is 314 MB of context features, not listings. | The visible published sizes demonstrate substantial *candidate* volume for TiniX and modest volume for Kaggle. Verified rental counts after filtering the complete files are unknown; no full listing file was loaded. The only sample survivors are 2 Kaggle title-confirmed candidates and 0 TiniX rows in the inspected samples. Neither is sufficient proof of a qualifying full dataset. |
| **Variety** | Kaggle: 5-column CSV (publisher also offers JSON), with text title/address and untyped price/area. TiniX: 19-column Parquet with structured location, property category, numeric property attributes, text, and published date. OSM: tagged geospatial PBF; Geofabrik also lists derived SHP/GPKG formats. | The published formats and structures differ, allowing a file-format integration exercise. TiniX has richer structured geography/type, but its missing transaction label blocks verified rental integration. OSM adds geographic context, not rental listings. |
| **Velocity** | Kaggle's dataset snapshot was last updated 2022-08-13; the 100-row date sample spans 2015-11-16 to 2022-07-14. TiniX lists publication coverage 2025-06-01 to 2026-03-31 and repository metadata last modified 2026-04-14. The Geofabrik snapshot reports data through 2026-09-30 20:22:42 UTC and the country page provides daily diff files. | These are static date ranges and snapshot/update metadata. They do not establish a streaming feed or real-time listing velocity. A future repeated-snapshot study must log actual retrieval timestamps and provider snapshot IDs, compare only records observed in the saved snapshots, and describe cadence as the observed interval. No ingestion events are claimed here. |

## Next concrete action

Request author-verified Hanoi apartment rental labels and documented original provenance/rights from both listing dataset publishers. For Kaggle, ask the author to confirm whether `hn.csv` was lawfully released under CC0 and provide a row-level apartment criterion or an author-verified subset. For TiniX, ask for a small Hanoi apartment rental sample with an explicit transaction label definition, source-platform provenance, and confirmation of rights to license the underlying records under CC BY-NC 4.0. Keep both corpora out of the rental pipeline until those checks pass; use OSM only as contextual geography after recording and attributing a dated extract. If providers cannot verify these points, retain the registered topic and synthetic MVP, and seek instructor approval before narrowing or otherwise changing the project scope. **G2 is not complete.**


