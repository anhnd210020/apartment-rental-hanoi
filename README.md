# IT5427: Hanoi apartment rental data prototype

This project keeps its synthetic fixtures separate from an exploratory public-data prototype. The public path uses **one rental-oriented listing dataset** from Kaggle, an optional independent NEST Living aggregate rent index, and two geographic context datasets: OpenStreetMap (OSM) and WorldPop. NEST provides aggregate cells, not individual listing records. OSM and WorldPop remain integrated with the Kaggle listing summary at Hanoi city grain; the separate NEST city/district/type marts are not joined to Kaggle because their populations and time bases do not match. The project does not claim three independent rental-listing platforms, streaming, or market-wide estimates.

## Run locally on the existing Windows environment

Open PowerShell and use the current project location and existing `dev` Python/Java/Spark installation:

```powershell
$project = 'D:\Dai Hoc\Master\2026A\IT5427\Project\apartment-rental-hanoi'
Set-Location $project
$py = 'D:\envs\dev\Scripts\python.exe'
$env:JAVA_HOME = 'D:\Apps\Temurin17\jdk-17.0.20.1+1'
$env:HADOOP_HOME = 'D:\Apps\hadoop-3.3.6'
$env:PATH = "$env:JAVA_HOME\bin;$env:HADOOP_HOME\bin;D:\envs\dev\Scripts;$env:PATH"
$env:PYSPARK_PYTHON = $py
$env:PYSPARK_DRIVER_PYTHON = $py
```

Run the synthetic fixture pipeline, or prepare and run the public-data pipeline:

```powershell
& $py pipeline.py                         # synthetic fixtures only
& $py prepare_public_context.py            # reuses existing OSM/raster preparation
& $py prepare_worldpop_cells.py            # reuses or creates valid-cell CSV.gz
& $py pipeline.py --dataset public         # public Spark pipeline
& $py ingest_nest_rent_index.py --input 'data\raw\nest_living\snapshots\nest_hanoi_rent_index_20261029T091525078Z.csv' --retrieved-at-utc '2026-10-29T09:18:31.870Z'
& $py compare_nest_snapshots.py             # compares only the two genuine aggregate CSV captures
& $py -m streamlit run dashboard.py --server.port 8501
```

Future NEST snapshots must be downloaded manually through the public CSV link on the [rent-index page](https://nestliving.vn/rent-index). The ingestion command never contacts NEST; provide the exact local path and retrieval time. See [the NEST source note](docs/nest_living_source_note.md) for schema, counts, provenance, SHA-256, methodology, and the unresolved reuse terms.

Open `http://127.0.0.1:8501/?view=public` for the public-data prototype or `http://127.0.0.1:8501/?view=synthetic` for synthetic fixtures. The dashboard clearly labels the synthetic view. The public view labels amounts as listed amounts because the time basis is unknown for most rows.

## Latest verified local run — 2026-10-29

Public manifest **`public-20261029T083945Z`** records 13,785 Kaggle rows, including 3,284 Hanoi rows; 102 title-reviewed likely apartment-rental records with positive amount and area; 408,151 valid WorldPop cells; and one Kaggle + OSM + WorldPop city row. The Kaggle/OSM/WorldPop command took 109.395 Spark seconds and 119.968 seconds between manifest timestamps. The separately ingested latest NEST snapshot **`nest-20261029T091525078Z`** records 45 aggregate cells: 1 city, 10 district, 29 district-by-bedroom, and 5 property-type cells; 28 published and 17 suppressed. NEST's latest city cell reports 894 homes, median monthly asking rent 19.1 million VND, p25 12.7 million VND and p75 30.5 million VND at source capture `2026-10-29T09:15:25.078Z`. Two genuine captures share 45 cells: 7 changed, 38 unchanged, 0 added, and 0 removed. This describes changes in NEST aggregates only, not individual listings or rental-listing Velocity; NEST's own inventory is not the Hanoi market. Timings are single local runs, not performance benchmarks.

## Scope and data limits

- Kaggle remains the only rental-oriented listing dataset; its uploader declares CC0, but original platforms and third-party rights remain unresolved. NEST adds an independent publisher's aggregate rental source, not a second listing dataset. NEST's terms do not state an open license or explicit reuse grant for the CSV; it is an optional local input with attribution, and its raw file is excluded from the submission ZIP.
- Most listed amounts have unknown time basis; only the verified monthly subset is used for monthly statistics.
- Listing rows have no reliable coordinates or structured district/ward IDs. Geographic context is integrated only at Hanoi city level.
- OSM updates provide dated batch-change evidence only. NEST has two genuine aggregate CSV captures and a 7-cell comparison; neither source establishes rental-listing Velocity or streaming.
- `data/fixtures/` contains synthetic records, never real rental observations.

For the verified five-minute walkthrough, see [the demo runbook](docs/demo_runbook.md) and [the Vietnamese live demo script](docs/live_demo_script.md). Details and figures are in [the final report](docs/final_report.md).
