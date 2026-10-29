# IT5427 five-minute demo runbook

**Verified:** 2026-10-29. The walkthrough uses public manifest `public-20261029T083945Z`, NEST snapshot `nest-20261029T082644540Z`, and the existing Windows `dev` Python, Java 17, Hadoop and Spark setup. Start the dashboard before the five-minute presentation; rerunning Spark is optional preparation, not part of the timed walkthrough.

## Start the dashboard from this project folder

Run in PowerShell:

```powershell
$project = 'D:\Dai Hoc\Master\2026A\IT5427\Project\apartment-rental-hanoi'
Set-Location $project
$py = 'D:\envs\dev\Scripts\python.exe'
$env:JAVA_HOME = 'D:\Apps\Temurin17\jdk-17.0.20.1+1'
$env:HADOOP_HOME = 'D:\Apps\hadoop-3.3.6'
$env:PATH = "$env:JAVA_HOME\bin;$env:HADOOP_HOME\bin;D:\envs\dev\Scripts;$env:PATH"
$env:PYSPARK_PYTHON = $py
$env:PYSPARK_DRIVER_PYTHON = $py
& $py -m streamlit run dashboard.py --server.port 8501
```

Open `http://127.0.0.1:8501/?view=public`. Switch to **Synthetic fixtures** for the clearly labeled test-only path, or open `http://127.0.0.1:8501/?view=synthetic` directly. The app was checked in both modes with Streamlit AppTest and the local server returned HTTP 200.

## Latest verified run to describe

- Manifest: **`public-20261029T083945Z`**.
- Public input: 13,785 source listing rows; 3,284 Hanoi rows; 303 manually reviewed apartment-cue candidates; 106 likely whole-apartment rental titles; 102 with usable positive amount and area.
- Context: 408,151 valid WorldPop cells; one OSM Hanoi aggregate; one integrated Hanoi city row.
- Timing: public pipeline Spark total 109.395 seconds; elapsed time between manifest timestamps 119.968 seconds. This is one local run, not a benchmark.
- NEST: 45 aggregate cells (1 city, 10 district, 29 district-bedroom, 5 property-type); 28 published and 17 suppressed. The city cell reports n=890 homes and median 19.1M VND/month at capture `2026-10-29T08:26:44.540Z`. Only one genuine capture exists, so there are no change counts.
- Synthetic command output: 7 raw, 7 active, 5 valid, 4 unique records. These are generated fixtures, not real listings.

Kaggle remains one rental-oriented listing dataset. NEST is a separately published aggregate rental source from NEST's own inventory. OSM and WorldPop are geographic context. Do not compare NEST medians directly with Kaggle's 102 listed amounts; those have mostly unknown time bases. The NEST CSV remains an optional local input because the terms page does not state an open reuse license or explicit reuse grant.

To verify an HTTP response before the demo:

```powershell
(Invoke-WebRequest -Uri 'http://127.0.0.1:8501/?view=public' -UseBasicParsing -TimeoutSec 10).StatusCode
```

A `200` confirms the local Streamlit page responds.

## Five-minute sequence

| Time | Show | Say |
|---|---|---|
| 0:00–0:35 | Project title and dashboard warning | The project has one rental-oriented listing dataset, one independent aggregate rental source, and two geographic context sources. NEST provides aggregate cells, not listing records; this is not three listing platforms or a market estimate. |
| 0:35–1:10 | Manifest ID and measured counts above | The latest local run screened 13,785 rows, including 3,284 Hanoi rows. Manual title review covered 303 apartment-cue candidates; 102 records with usable amount and area enter listed-amount summaries. |
| 1:10–2:10 | Public dashboard: Kaggle amounts and monthly subset | The median listed amount is 3.50 million VND, but the time basis is unknown for 92 of 102 rows. Monthly statistics use only 9 verified records; this small historical sample is exploratory. |
| 2:10–3:10 | Source coverage and NEST aggregate section | NEST has 45 aggregate cells, 17 suppressed cells, and one city cell with n=890. It describes NEST's own homes; do not compare it directly with the Kaggle figures. A second genuine capture is needed for aggregate change counts. |
| 3:10–4:00 | Public dashboard city-context section | OSM and WorldPop are joined with the Kaggle listing summary at Hanoi city level using `city_key=VN-HN`; no context is attached to individual listings or neighborhoods. NEST remains in separate marts. |
| 4:00–4:35 | Switch to **Synthetic fixtures** | This path demonstrates the pipeline on generated records only. It reports 7 raw, 7 active, 5 valid, and 4 unique records; these are not real Hanoi observations. |
| 4:35–5:00 | Return to public view and summarize limits | The Kaggle publisher’s upstream listing provenance and rights remain unresolved. OSM batches do not establish rental-listing Velocity; there is no rental streaming feed or repeat listing snapshot. |

## Optional pipeline rerun before the presentation

The latest public Spark run took 119.968 seconds elapsed on this machine. Run the NEST ingest only when a manually downloaded local CSV is available; the command itself never downloads from NEST:

```powershell
& $py pipeline.py
& $py prepare_public_context.py
& $py prepare_worldpop_cells.py
& $py pipeline.py --dataset public
& $py ingest_nest_rent_index.py --input 'data\raw\nest_living\snapshots\nest_hanoi_rent_index_20261029T082644540Z.csv' --retrieved-at-utc '2026-10-29T08:27:06.485Z'
& $py compare_nest_snapshots.py
```

The preparation commands reuse existing clipped OSM/WorldPop files by default. Do not pass `--rebuild` for the ordinary demo. Raw public source files and the private curation ledger remain in the local working project and are not part of the shareable submission folder.
