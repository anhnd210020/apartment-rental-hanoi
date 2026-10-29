# Public-data prototype: implementation and results

**Latest verified run:** 2026-10-29, Kaggle/OSM/WorldPop manifest plus separate NEST snapshot `nest-20261029T082644540Z`. This remains a local exploratory prototype. Kaggle is one rental-oriented listing dataset; NEST is an independent publisher's aggregate rental source, not listing rows; OSM and WorldPop are geographic context. The project does not claim three independent rental-listing platforms, make market-wide claims, or provide streaming/real-time data.

## Source decisions, provenance, and terms

| Input | Decision and grain | Source evidence and limits |
|---|---|---|
| [Vietnam House Rent Dataset](https://www.kaggle.com/datasets/vanviethieuanh/vietnam-house-rent-dataset), Van Viet Hieu Anh | **CONDITIONAL**, listing-record grain | The Kaggle uploader declares CC0; the publisher repository-level README says datasets are scraped from websites; the house-rent-specific README describes posts but identifies no original websites. Upstream platform provenance and third-party rights remain unresolved. Keep source rows local and do not redistribute them. Three CSVs total 2,491,539 bytes (Da Nang 768 rows, HCMC 9,733, Hanoi 3,284; total 13,785). Fields: `title`, `published`, `address`, `acreage`, `price`. Kaggle last updated 2022-08-13. |
| [NEST Living Hanoi Rent Index](https://nestliving.vn/rent-index), NEST Living | **OPTIONAL**, aggregate-cell grain; separate PySpark path and separate city/district/type marts | Downloaded once through the page's intended public CSV link at `https://nestliving.vn/rent-index/rent-index.csv`; 5,039 bytes, SHA-256 `af233deb251762a2a4065704087b3844acf3cd76accb7fd5d91d1eb6b06b268e`. Capture `2026-10-29T08:26:44.540Z`; retrieved `2026-10-29T08:27:06.485Z`. Profile: 45 cells (1 city, 10 district, 29 district-by-bedroom, 5 property type), 28 published and 17 suppressed. CSV fields are documented in `docs/nest_living_source_note.md`. NEST's [methodology](https://nestliving.vn/rent-index) describes its own asking-rent inventory, not all Hanoi. Its [terms](https://nestliving.vn/terms) prohibit automated harvesting/copying listing content but state no open license or explicit reuse grant for the CSV. Preserve attribution and the terms caveat; no raw CSV in Git or ZIP; reuse rights remain unclear. |
| [Geofabrik Vietnam OSM extract](https://download.geofabrik.de/asia/vietnam.html), OpenStreetMap contributors | **ACCEPT** for Hanoi city context | Pinned PBF: `vietnam-260930.osm.pbf`, 329,495,536 bytes. Its PBF header says OSM data through **2026-09-30T20:22:42Z**, replication sequence 4925. Data is ODbL 1.0; attribute “© OpenStreetMap contributors” and link [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright). |
| [WorldPop Vietnam population counts](https://hub.worldpop.org/geodata/summary?id=6449), 2020 | **ACCEPT** for population context | Original GeoTIFF: 196,897,622 bytes, reference year 2020, people per pixel. CC BY 4.0; attribute WorldPop / University of Southampton and cite [DOI 10.5258/SOTON/WP00645](https://doi.org/10.5258/SOTON/WP00645). |
| [TiniX Vietnam Real Estate Listings](https://huggingface.co/datasets/tinixai/vietnam-real-estates) | **REJECT** for rental-price analysis | Not used because rental-versus-sale status is not validated. |

The project has one rental-oriented listing dataset (Kaggle), one independent aggregate rental source (NEST), and two geographic context datasets (OSM and WorldPop). NEST is not a listing-record platform feed. It is not joined to the 102 Kaggle listing amounts: their coverage, property mix, and time bases do not match, and Kaggle's 102 listed amounts are mostly period-unknown. District NEST cells remain in their own mart because Kaggle addresses do not provide a reliable district key. OSM and WorldPop are context, not rental sources.

## Prepared artifacts inspected

The existing prepared outputs were reused; the expensive OSM scan and WorldPop spatial clip were not repeated.

| Artifact | Actual format/schema and size | Grain / current records |
|---|---|---|
| `context/hanoi_context.json` | 1,910-byte UTF-8 JSON with city, relation ID, OSM source snapshot metadata, tagged OSM counts, WorldPop summary and attribution | One Hanoi aggregate prepared from the 2026-09-30 PBF |
| `context/hanoi_boundary.geojson` | GeoJSON, 148,356 bytes | Hanoi administrative relation 3807033 |
| `context/worldpop_hanoi_2020.tif` | GeoTIFF, 1,559,619 bytes; 987 × 878, one float32 band, EPSG:4326, nodata -99999 | 408,151 valid cells |
| `context/tables/worldpop_hanoi_cells.csv.gz` | Gzip CSV, 3,120,702 bytes; `cell_row`, `cell_col`, `population_count` | 408,151 valid raster cells |

The WorldPop CSV contains only cells with a valid raster mask, finite value, and value ≥ 0. Row and column are zero-based indexes in the clipped raster; population is the people-per-pixel count. The table schema and lineage are recorded in `context/tables/worldpop_hanoi_cells.schema.json`. The earlier conversion from the clipped raster took **1.459 seconds**. In the 2026-10-26 verification, existing context and cell-table files were reused; the two preparation commands together took **2.677 seconds** wall time. Spark re-aggregates the cells and verifies the row count and population total against the prepared metadata. Population sum is **8,440,532.41**; the preparation code now sums float32 source values as float64 to avoid the previous 0.41 accumulation discrepancy.

## Spark processing and integration grain

PySpark 3.5.9 reads the three Kaggle CSVs, prepared OSM JSON, and WorldPop gzip CSV for the existing public path. A separate run of `ingest_nest_rent_index.py` reads one manually downloaded NEST CSV without contacting NEST. Its manifest records the source URL, capture/retrieval times, SHA-256, schema, profile, terms caveat and output paths. Parquet byte counts below sum `part-*.parquet` payloads and exclude Spark success markers and filesystem CRC sidecars.

| Source / output | Original source bytes | Spark input grain and rows | Output grain and rows | Parquet bytes | Spark processing time |
|---|---:|---|---|---:|---:|
| Kaggle CSV listing input → curated listings | 2,491,539 | Listing record / 13,785 rows; Hanoi partition 3,284 | Curated likely rental listing record / 102 | 13,883 | 73.635 s |
| OSM PBF → prepared JSON → OSM context table | 329,495,536 PBF; 1,910-byte prepared JSON | One pre-aggregated Hanoi JSON row; the PBF was processed earlier by the preparation script | Hanoi city aggregate / 1 | 7,034 | 1.545 s |
| WorldPop TIFF → clipped raster → cell CSV → cell Parquet | 196,897,622 TIFF; 1,559,619-byte clip; 3,120,702-byte CSV.gz | Valid raster cell / 408,151 | Raster cell / 408,151 | 3,410,996 | 6.391 s |
| WorldPop city aggregate | Same WorldPop lineage | Aggregated in Spark from the 408,151 cell rows | Hanoi city aggregate / 1 | 2,240 | Included above |
| OSM + WorldPop city-context join | OSM/WorldPop inputs above | `city_key=VN-HN` on both one-row city aggregates | Hanoi city context / 1 | 8,595 | 26.073 s for city integration stage |
| Listing summary + city context | Listing aggregate plus city context | Explicit key `city_key=VN-HN` | Integrated city summary / 1 | 12,864 | Included in city integration stage |
| Listing summary / quality table | Listing rows above | Spark aggregate / 1; quality reason / 10 | One listing summary row; 10 quality rows | 4,871 / 1,085 | Included in listing stage |
| NEST aggregate cells → separate marts | One manual CSV / 45 cells / 5,039 bytes | `cut` grain; 45 aggregate cells, no home/listing rows | Cells / 45; city / 1; district / 10; district-by-bedroom / 29; property type / 5 | See snapshot manifest | Separate PySpark job; no join to listing or context marts |

For public manifest `public-20261029T083945Z`, total measured Spark time was **109.395 seconds** and elapsed time between manifest timestamps was **119.968 seconds**. Four stage timers in the table sum to 107.644 seconds; the total is the separately recorded overall timer. The NEST Spark job is separate and not included in these timings. Spark did not read 329 MB of OSM objects as individual rows: it read the existing one-row city JSON summary and flattened its fields. OSM preprocessing had already counted 201,686 tagged highway ways, about 34,342.71 km of clipped highway-tag length, 5,048 transport-stop features, 2,404 education features, 666 health features, and 5,828 other amenity features. Those are preparation counts, not Spark input-row counts. Highway length includes paths/service ways and can include overlapping mapped segments; OSM amenity features are not deduplicated institutions.

WorldPop's Spark cell output includes `city_key`, `worldpop_reference_year`, `cell_row`, `cell_col`, and `population_count`; Spark also writes a one-row city aggregate. The one-row context table joins OSM and WorldPop using `city_key=VN-HN`. The one-row `integrated_city` output adds Kaggle listing-snapshot summary metrics to that city context. Curated listing records remain separate and contain no OSM or population fields. There is no reliable listing coordinate, district, or ward identifier, so no per-listing or neighborhood join is performed.

The NEST path preserves the source `cut`, district key/name, bedroom class, property type, sample count, raw suppression strings, numeric rent statistics where published, source capture time, retrieval time, and file SHA-256. It writes separate `cells`, `city`, `district`, `district_bedroom`, and `property_type` Parquet outputs under the dated snapshot directory. Although the source covers Hanoi and includes a city row, its all-home inventory and capture do not match Kaggle's apartment-candidate summary; it therefore stays outside `integrated_city`. No median-of-medians or aggregate-to-listing join is performed. All 17 unpublished cells and their 51 suppressed statistic values remain traceable.

## Rental labels and amount semantics

Spark screened all **3,284 Hanoi rows** and used a manual ledger for **303 apartment-cue candidates**, not for the whole Hanoi partition. The corrected ledger has 106 title-supported likely whole-apartment rentals, 105 ambiguous rows, 91 room/shared-stay exclusions, and one apartment-sale exclusion. A random title audit estimated positive precision at 49/50 (98%) for the original predicted-positive set; it is a small title-only audit and must not be presented as whole-dataset accuracy. A separate random sample of 100 predicted negatives found two confirmed missed candidates and six ambiguous titles. Do not claim population recall.

The curated amount table contains **102 positive-amount-and-area rows**; four likely rental titles have unknown/nonpositive amount and remain excluded from numeric summaries. Amounts are in million VND, but period is unknown for most records. Dashboard/report metrics therefore read **listed amount** and **listed amount per m²**. The medians for 102 rows are 3.5 million VND and 120,000 VND/m² (time basis unknown for 92 rows). Only **9** records have an explicit monthly title amount matching the structured amount; the dashboard shows their separate monthly statistics with n=9 and an exploratory small-sample caveat. One title/field mismatch and one unknown-price title are excluded. Full audit design and price evidence are in `docs/data_quality_and_analysis_review.md`.

## Dated OSM batch comparison

Geofabrik's [official Vietnam page](https://download.geofabrik.de/asia/vietnam.html) listed a newer `vietnam-261001.osm.pbf` at 329,574,705 bytes, with source data through **2026-10-01T20:22:06Z** and server `Last-Modified` time 2026-10-02T12:04:51Z. The pinned base PBF is sequence 4925; the next official state is sequence 4926. [Geofabrik documents `.osc.gz` files as extract-to-extract updates](https://download.geofabrik.de/technical.html). Because the full newer PBF would require another roughly 330 MB transfer, it was not downloaded. Instead, the actual 668,745-byte public update `vietnam-updates/000/004/926.osc.gz` and its `state.txt` were downloaded. The target state timestamp and sequence were checked against the official state file; both dated source manifests include file sizes and SHA-256 hashes.

The repeatable command is `python compare_geofabrik_snapshots.py`; it verifies the manifests and input hashes, confirms consecutive sequence numbers, parses the OSM change file, and writes `data/public_pilot/snapshot_comparison/vietnam-260930_to_261001.json`.

| OSM update operation in the Vietnam extract | Count |
|---|---:|
| Added (`create`) objects | 9,555 |
| Changed (`modify`) objects | 6,385 |
| Removed (`delete`) objects | 1,969 |
| Total unique object operations | 17,909 |

The update included 7,828 created / 4,191 modified / 1,713 deleted nodes; 1,613 / 1,992 / 253 ways; and 114 / 202 / 3 relations. Tagged road/transit/education/health/amenity memberships are also recorded in the comparison JSON and are Vietnam-wide. A fixed-boundary check found 29 added/modified/removed context-tagged **node** operations inside the Hanoi boundary (1 create, 27 modify, 1 delete). Changed way geometry is not spatially resolved by this diff-only comparison, so these are not complete Hanoi OSM context deltas. The current 201,686-way Hanoi aggregate still comes from the 2026-09-30 snapshot; it was not recomputed from the next-day update.

The comparison establishes that OSM changed between these two source states. It is a dated batch comparison, not streaming or rental-listing Velocity. Kaggle remains one listing snapshot last updated 2022-08-13. WorldPop remains the 2020 reference-year raster. Rental-listing Velocity remains open.

### Follow-up OSM batch and replay check (2026-10-02)

Geofabrik's [official Vietnam page](https://download.geofabrik.de/asia/vietnam.html) listed `vietnam-261002.osm.pbf` (329,688,139 bytes; official file modification 2026-10-02 22:40 UTC), with state timestamp **2026-10-02T20:21:34Z**, sequence **4927**. The full PBF was not downloaded. The official consecutive `000/004/927.osc.gz` update was 746,517 bytes (SHA-256 `462e96762688581a5a953c8f9466480c050e1aa72c963965922da9008fecc2cd`); the frozen target state and source manifest are under `data/public_pilot/snapshot_comparison/manifests/`.

Compared with sequence 4926, the update contains **14,572 creates, 5,901 modifies, and 2,284 deletes** (22,757 unique operations, no duplicates). The fixed-boundary point-in-polygon check found changed context-tagged nodes in Hanoi: 1 create, 62 modifies, and 6 deletes. As before, these counts do not resolve changed way geometry and are not a complete Hanoi context delta. The prepared OSM city aggregate remains based on the 2026-09-30 PBF.

The same command was replayed twice from the same dated manifests. Baseline, target manifest, boundary metadata, limits, and all change counts matched; only the generated timestamp and runtime differed (0.549 s and 0.511 s). This verifies repeatable batch processing for sequence 4927, not a streaming system or rental-listing velocity. The full replay result is `data/public_pilot/snapshot_comparison/vietnam-261001_to_261002.json`.

## NEST aggregate snapshot mechanism

`ingest_nest_rent_index.py` reads only a local CSV downloaded manually through the public link; its CLI requires the file path and exact retrieval time. It registers the capture under `data/raw/nest_living/snapshots/`, records a manifest beside the ignored raw file, and creates capture-specific Parquet marts. At this assessment there is one genuine capture: source time `2026-10-29T08:26:44.540Z`, retrieval time `2026-10-29T08:27:06.485Z`, 45 cells, 28 published, and 17 suppressed. `compare_nest_snapshots.py` writes `data/public_pilot/snapshot_comparison/nest_living_latest.json`; with one capture its status is `insufficient_snapshots` and no change counts are reported. The script requires two distinct source capture times before comparing cell keys; then it reports changed, added, removed, and unchanged cell counts, changed fields, and both capture/retrieval times. This measures NEST aggregate-cell changes only, not individual listings or rental-listing Velocity. It remains separate from the existing Geofabrik/OSM batch comparison.

## 3V evidence

- **Volume:** Spark read 13,785 Kaggle rows and curated 102 numeric Hanoi candidates. A separate NEST job read 45 aggregate cells (1 city, 10 district, 29 district-by-bedroom and 5 property-type cells); 17 small-sample cells remain with their rent statistics suppressed. OSM and WorldPop context counts are not listing volume.
- **Variety:** Kaggle listing CSV, NEST aggregate CSV, OSM PBF/JSON and change XML, WorldPop GeoTIFF/gzip CSV, and Spark Parquet marts use different formats and grains.
- **Velocity:** two consecutive official OSM daily batch changes are verified across 2026-09-30, 2026-10-01, and 2026-10-02 states, and the second diff replayed reproducibly. This is dated OSM batch evidence. NEST has one genuine aggregate snapshot; a second is needed before a NEST aggregate-cell comparison. Neither source establishes rental-listing Velocity. There is no rental feed or repeated listing snapshot.

## Commands and checks

From the project folder, using the configured existing `dev` environment and Java 17:

```powershell
& 'D:\envs\dev\Scripts\python.exe' prepare_public_context.py
& 'D:\envs\dev\Scripts\python.exe' prepare_worldpop_cells.py
& 'D:\envs\dev\Scripts\python.exe' compare_geofabrik_snapshots.py --old-manifest data/public_pilot/snapshot_comparison/manifests/vietnam-261001.json --new-manifest data/public_pilot/snapshot_comparison/manifests/vietnam-261002.json --output data/public_pilot/snapshot_comparison/vietnam-261001_to_261002.json
& 'D:\envs\dev\Scripts\python.exe' -m py_compile pipeline.py dashboard.py ingest_nest_rent_index.py compare_nest_snapshots.py prepare_public_context.py prepare_worldpop_cells.py compare_geofabrik_snapshots.py docs/generate_project_figures.py docs/export_final_report.py docs/build_final_presentation.py
& 'D:\envs\dev\Scripts\python.exe' pipeline.py
& 'D:\envs\dev\Scripts\python.exe' pipeline.py --dataset public
& 'D:\envs\dev\Scripts\python.exe' ingest_nest_rent_index.py --input data/raw/nest_living/snapshots/nest_hanoi_rent_index_20261029T082644540Z.csv --retrieved-at-utc 2026-10-29T08:27:06.485Z
& 'D:\envs\dev\Scripts\python.exe' compare_nest_snapshots.py
```

On 2026-10-29, public manifest `public-20261029T083945Z` reports 13,785 Kaggle rows, 3,284 Hanoi, 102 curated, 408,151 WorldPop cells, and one Kaggle + OSM + WorldPop city row (109.395 Spark seconds; 119.968 seconds between manifest timestamps). The synthetic rerun reports 7 raw, 7 active, 5 valid, and 4 unique fixture records. The separate NEST path reports 45 aggregate cells, 28 published, and 17 suppressed; with one genuine capture the comparison is unavailable. Dashboard AppTest covers both synthetic and public modes; the public mode labels NEST aggregate rows separately and gives the Kaggle n=9 monthly subset a prominent small-sample warning. A local Streamlit HTTP check returned status 200.

## Remaining gaps

1. Kaggle's unidentified original listing websites and third-party rights remain unresolved; do not redistribute raw rows. NEST is a separate publisher's aggregate source, not a second row-level listing feed; overlap with Kaggle's unidentified upstream records cannot be checked.
2. NEST's terms do not state an open license or explicit reuse grant for the CSV. Keep it optional/local with attribution and the terms caveat; do not include the raw CSV in Git or the ZIP.
3. Listing geography supports only city-level integration; district, ward, per-listing, and neighborhood enrichment remain unavailable.
4. The Oct 1 and Oct 2 OSM full PBFs were not downloaded; official consecutive change files were used. The dated comparison does not refresh the Hanoi city aggregate, which remains based on Sep 30, and way geometry in the diffs is not spatially resolved.
5. Only one genuine NEST aggregate CSV capture is registered, so no NEST cell-change comparison is yet possible. No repeated listing snapshots or feed are available. Rental-listing Velocity remains open; OSM batch evidence remains separate.
