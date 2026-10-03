# Real-data quality and analysis review

**Audit date:** 2026-10-02. This review covers `pipeline.py`, `dashboard.py`, the title-review and price-period ledgers, and the generated public Spark outputs. It does not add a rental-listing source or make market-wide claims.

## 1. Rental and apartment labels

### Screening and ledger coverage

Spark screened every row in the 3,284-row Hanoi partition using title cues. The manual title-review ledger is not a complete annotation of that partition: it contains **303 apartment-cue candidates**, leaving **2,981 Hanoi rows without a manual ledger entry**. It is a candidate review ledger, not a row-by-row label set.

The original 105 predicted positives were selected using title evidence for an apartment or studio, an explicit rental phrase, and a whole-unit offer, with no room-level or conflicting sale cue. Price size was not used to infer transaction type. The original candidate-ledger counts were 105 include, 106 ambiguous, 91 room/shared-stay exclusions, and one apartment-sale exclusion.

### Manual audit sample

I drew simple random samples without replacement from the original classifier output, then reviewed the sampled titles manually. The audit rows, source row numbers, hashes, sample seeds, labels, and reasons are in `data/curation/kaggle_title_audit_sample.csv`; it contains no raw titles or addresses.

| Original prediction stratum | Population | Sample | Manual review result |
|---|---:|---:|---|
| Predicted positive (`include`) | 105 | 50, seed 5427 | 49 clear whole-apartment rentals; 1 ambiguous single/double-room offer |
| Predicted negative (all other Hanoi rows) | 3,179 | 100, seed 25427 | 2 clear missed whole-apartment rentals; 6 ambiguous candidates; 92 with no confirmed rental evidence |

Conservative audit precision is **49/50 = 98%**, counting the ambiguous positive as unsupported. The approximate 95% Wilson interval is **89.5–99.6%**. This is a small title-only estimate, not a gold-standard validation result.

The negative sample found two confirmed misses that the original title rules had predicted as negative; the revised ledger now includes them. Applying the sample miss rate (2/100) to 3,179 predicted negatives gives about **64 additional candidate rentals**; the approximate Wilson interval scaled to that population is **18–223**. Six other sampled negatives were ambiguous, so the point estimate is particularly uncertain. I do not report a population recall figure from this small title-only audit.

The ledger was corrected to **106 include, 105 ambiguous, 91 room/shared-stay exclusions, and 1 apartment-sale exclusion** (303 total). It now includes the two sampled false negatives and changes the ambiguous original positive to ambiguous. The positive and negative sample results describe the original classifier, before these corrections.

The rerun Spark output contains **102 likely rental rows with positive structured amount and area**, **4 likely rentals with unknown/nonpositive amount**, and **25 manual-review ambiguous rows**. Ambiguous and room-level records remain excluded from the numeric rental summaries.

## 2. Price semantics

The publisher describes structured `price` in million VND but does not provide a general time basis. The CSV has no separate price-text field, so I inspected the actual titles and compared any explicit period/amount evidence with the structured `price` value. Eleven of the 106 revised title-positive rows explicitly attach a numeric amount to a monthly period (`/tháng`, `/th`, or `.tháng`). No explicit weekly or daily price period was observed. Relative values such as “3 days ago” are publication dates, not price units.

Among those 11 monthly-title rows:

- 9 have a positive structured amount matching the explicit title amount; one matches the lower end of a title range. These are the only rows used for monthly statistics.
- 1 title amount does not match the structured field and is excluded from monthly statistics.
- 1 has `price=-1`/unknown and is excluded from all amount summaries.

The other 95 title-positive rows have no verified monthly period. Of the 102 numeric curated rows, **92 have unknown time basis, 9 have a verified monthly period and matching amount, and 1 has explicit monthly text but a mismatching amount**. The period-review ledger records source rows 823, 1066, 1697, 1740, 1919, 2479, 2532, 2541, 2693, 2831, and 3104; row 2541 is the amount mismatch and row 2693 has unknown structured price. Field-level decisions are in `data/curation/kaggle_price_period_review.csv`.

For all 102 numeric rows, the dashboard and reports use **listed amount** and **listed amount per m²**, and state that the period is unknown for most rows. Median listed amount is **3.5 million VND**, median area is **30 m²**, and median listed amount per m² is **120,000 VND/m²**. These values are not monthly-rent statistics.

The verified monthly subset has 9 rows: median amount **3.2 million VND/month**, median area **25 m²**, and median amount per area **133,333 VND/m²/month**. These small-sample results are preliminary.

## 3. Geographic integration

The listing fields are `title`, `published`, `address`, `acreage`, and `price`; there is no district code, ward code, or coordinate. Address is free text. As a bounded joinability check, I matched address text against a Hanoi district-name whitelist and required an explicit preceding `quận`, `huyện`, or `thị xã` marker:

- Of 106 title-positive rows, 52 had one unique, explicitly marked district; 9 had one district-like name without a marker; 1 had multiple district names; and 44 had no whitelist match.
- Of the 102 numeric rows, 52 had one unique marked district; 8 had one unqualified district-like name; and 42 had no match.

This is not a reliable complete join key. No listing-to-district join was performed and no district/ward value was assigned. OSM and WorldPop remain separate **Hanoi-wide city context** joined only to the single city-level listing aggregate; the dashboard does not present them as per-listing or neighborhood enrichment.

## 4. Volume, variety, and velocity

- **Listing rows processed by Spark:** 13,785 across `hn.csv`, `hcm.csv`, and `dn.csv`; 3,284 Hanoi rows; 303 apartment-cue ledger candidates; 106 revised title-positive candidates; 102 positive-amount-and-area curated rows. The 4 unknown-amount candidates are quality-counted separately.
- **OSM context preprocessing (not listing volume):** 201,686 tagged `highway` ways, about 34,342.71 km of clipped tagged-way length, 5,048 transport-stop features, 2,404 education features, 666 health features, and 5,828 other amenity features. Highway length includes paths/service ways, can contain overlapping ways, and is not an official road total. Amenity features are not deduplicated institutions.
- **WorldPop context preprocessing (not listing volume):** 408,151 valid 2020 raster cells within the Hanoi clip, with a modelled count sum of about 8,440,532.
- **Variety:** listing CSV, OSM PBF, WorldPop GeoTIFF, and Spark Parquet outputs have different schemas and granularities.
- **Observed dates:** accepted listing publication values that parse as calendar dates range from 2016-01-14 to 2022-07-26. Kaggle reports last update 2022-08-13; Geofabrik snapshot date is 2026-09-30; WorldPop reference year is 2020. One static snapshot is not streaming and is insufficient evidence of rental-listing velocity.

A one-day official Geofabrik comparison has now been run: the downloaded 2026-09-30 PBF (sequence 4925, data time 2026-09-30T20:22:42Z) and official sequence 4926 update (target time 2026-10-01T20:22:06Z). It recorded 9,555 created, 6,385 modified, and 1,969 removed Vietnam OSM objects. This documents one OSM source change only; the next full PBF was not downloaded and the city context was not recomputed. Rental-listing Velocity remains open.

## Checks run

Using the existing `dev` environment, Java 17, and Hadoop path, I ran:

```powershell
$env:JAVA_HOME = 'D:\Apps\Temurin17\jdk-17.0.20.1+1'
$env:PATH = "$env:JAVA_HOME\bin;D:\Apps\hadoop-3.3.6\bin;D:\envs\dev\Scripts;$env:PATH"
$env:HADOOP_HOME = 'D:\Apps\hadoop-3.3.6'
$env:PYSPARK_PYTHON = 'D:\envs\dev\Scripts\python.exe'
$env:PYSPARK_DRIVER_PYTHON = 'D:\envs\dev\Scripts\python.exe'
& 'D:\envs\dev\Scripts\python.exe' -m py_compile pipeline.py dashboard.py prepare_public_context.py download_public_data.py
& 'D:\envs\dev\Scripts\python.exe' pipeline.py
& 'D:\envs\dev\Scripts\python.exe' pipeline.py --dataset public
```

Results:

- Compilation passed.
- Synthetic fixtures: `raw rows=7, active rows=7, valid rows=5, unique listings=4`.
- Public Spark: `raw_rows=13785, hanoi_rows=3284, curated_valid_rentals=102`. Quality counts: 10,501 outside-Hanoi rows; 2,213 rental-cue non-apartment; 749 no apartment/transaction cue; 91 room/shared-stay exclusions; 80 apartment-transaction ambiguous; 25 manual-review ambiguous; 19 non-apartment sale cues; 1 apartment sale; 4 included unknown-price rows; 102 valid exploratory rows.
- Generated Parquet summary: median listed amount 3,500,000 VND; median area 30 m²; median listed amount per m² 120,000 VND/m²; 9 verified monthly rows; median verified monthly amount 3,200,000 VND; median verified monthly amount per m² 133,333.33 VND/m²/month. Eleven titles state a monthly period, with one mismatch and one unknown structured amount.

I also ran the dashboard's `streamlit.testing.v1.AppTest` in both modes. It completed without exceptions; synthetic mode loaded fixture summaries and public mode showed 102 rows, listed-amount metrics, the 9-row verified-monthly subset, and separate city context. The already-running Streamlit server returned **HTTP 200** at `http://127.0.0.1:8501` and remains running.

The AppTest script was run from PowerShell as an inline Python script using `AppTest.from_file('dashboard.py').run()`, then `app.radio[0].set_value('Public-data prototype').run()`, with `assert not app.exception` after each render. The HTTP check was `Invoke-WebRequest -Uri 'http://127.0.0.1:8501' -UseBasicParsing -TimeoutSec 10`.

G2 remains incomplete: this project still has one published rental-oriented listing dataset, with unresolved upstream provenance and third-party rights.




## Follow-up: Spark context tables and output lineage

The later public run is recorded in `data/public_pilot/mart/run_manifest.json` (run ID `public-20261002T143608Z`). Spark processed the prepared 1-row Hanoi OSM JSON summary and the 408,151-row valid WorldPop cell table, then joined OSM and WorldPop city aggregates and the listing summary using `city_key=VN-HN`. The city context and integrated outputs each contain one row; no context columns were added to individual listings.

WorldPop was converted from the existing clipped raster to a 3,120,702-byte gzip CSV with row/column indexes and population counts, then written to 3,410,996-byte Parquet. The curated listing Parquet has 102 rows / 13,883 bytes; OSM city-context Parquet has 1 row / 7,034 bytes; the joined city context has 1 row / 8,595 bytes; the integrated city summary has 1 row / 12,864 bytes. Spark stage times were 37.568 s for listings, 0.702 s for OSM summary processing, 2.678 s for WorldPop cell/aggregate processing, and 16.419 s for city-key integration (58.353 s total). Sizes count Parquet part payloads only.

The newer Geofabrik full extract listed at 329,574,705 bytes was not downloaded; the 668,745-byte official consecutive update was. The comparison found 29 context-tagged node operations within the fixed Hanoi boundary (1 created, 27 modified, 1 removed). Way geometry was not spatially resolved, so this is not a full Hanoi context delta. Listing and WorldPop snapshots remain static.
