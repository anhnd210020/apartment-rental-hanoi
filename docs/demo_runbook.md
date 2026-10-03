# IT5427 five-minute demo runbook

**Checked:** 2026-10-03. The commands below use the existing Windows `dev` Conda environment, Java 17, and local prepared public inputs. Run them in PowerShell from the project folder.

## Start-up

```powershell
Set-Location 'D:\Research\IT5427\apartment-rental-hanoi'
$env:JAVA_HOME = 'D:\Apps\Temurin17\jdk-17.0.20.1+1'
$env:HADOOP_HOME = 'D:\Apps\hadoop-3.3.6'
$env:PATH = "$env:JAVA_HOME\bin;$env:HADOOP_HOME\bin;D:\envs\dev\Scripts;$env:PATH"
$env:PYSPARK_PYTHON = 'D:\envs\dev\Scripts\python.exe'
$env:PYSPARK_DRIVER_PYTHON = 'D:\envs\dev\Scripts\python.exe'
```

Run either data path; their inputs and outputs are kept separate:

```powershell
python pipeline.py
```

Expected synthetic result: `raw rows=7, active rows=7, valid rows=5, unique listings=4`. These are synthetic test fixtures only.

For the public-data prototype, the preparation commands reuse existing clips and cell tables unless those inputs are missing or changed. Do not pass `--rebuild` for the ordinary demo.

```powershell
python prepare_public_context.py
python prepare_worldpop_cells.py
python pipeline.py --dataset public
```

Expected public result: 13,785 source rows, 3,284 Hanoi rows, 102 curated positive-amount/area listing records, 408,151 valid WorldPop cells, and one integrated city row. Spark typically takes about one minute on this machine.

Start the dashboard:

```powershell
python -m streamlit run dashboard.py
```

Open `http://localhost:8501`, then select **Public-data prototype** to show the real public-data outputs. Select **Synthetic fixtures** for the test-only example.

## Five-minute sequence

| Time | Demo action | What to say or show |
|---|---|---|
| 0:00–0:30 | Introduce the scope | This prototype uses one Kaggle-published rental-oriented listing dataset plus OSM and WorldPop geographic context. It does not contain three rental-listing sources. Kaggle's uploader declares CC0, but the original listing platforms and third-party rights are unresolved. |
| 0:30–1:00 | Run `python pipeline.py` | Point out the synthetic-only label and expected 7 raw / 5 valid / 4 unique rows. The synthetic records are not rental-market observations. |
| 1:00–2:30 | Run the three public commands above | Show 13,785 input rows, 3,284 Hanoi rows, and 102 exploratory curated rows. The run uses the local Kaggle, Geofabrik, and WorldPop files; it does not crawl listing sites. |
| 2:30–4:00 | Open the dashboard and switch to **Public-data prototype** | Show “listed amount” because the time basis is unknown for most prices. The separate monthly subset has **9 verified records**; it is a small historical sample, not a market estimate. OSM and WorldPop values are **Hanoi city-level context**, joined by `city_key=VN-HN`; none are attached to individual listings or neighborhoods. |
| 4:00–5:00 | Show the latest OSM batch comparison, if time permits | Run the comparison command below. The Oct 1 → Oct 2 Geofabrik diff has 14,572 creates, 5,901 modifies, and 2,284 deletes. This is partial OSM batch-change evidence only. It is not streaming or rental-listing Velocity. |

Latest comparison command (uses the stored, hash-verified official diff and does not download a full extract):

```powershell
python compare_geofabrik_snapshots.py --old-manifest data/public_pilot/snapshot_comparison/manifests/vietnam-261001.json --new-manifest data/public_pilot/snapshot_comparison/manifests/vietnam-261002.json --output data/public_pilot/snapshot_comparison/vietnam-261001_to_261002.json
```

## Expected dashboard caveats

- **One listing dataset:** Kaggle is the only rental-oriented listing input. OSM and WorldPop supply geographic context, not rental listings. The original platforms behind the Kaggle rows are unidentified.
- **Monthly prices:** only 9 rows have a title-stated monthly amount that matches the structured amount. Other values are listed amounts with unknown time basis; do not call them monthly rents.
- **Geography:** listings have no reliable coordinates or district/ward IDs. Context is aggregated for the city and cannot support neighborhood or per-listing comparisons.
- **Velocity:** the available dated changes are Geofabrik OSM batches. Kaggle is one 2022-published listing snapshot and WorldPop is a 2020 reference-year product. There is no rental feed or repeated rental snapshot, so rental-listing Velocity remains open.
- **Interpretation:** records are preliminary and exploratory. Do not make market-wide claims or describe synthetic fixtures as real listings.

## Optional dashboard smoke check

```powershell
python -c "from streamlit.testing.v1 import AppTest; a=AppTest.from_file('dashboard.py').run(timeout=30); assert not a.exception, a.exception; a.radio[0].set_value('Public-data prototype').run(timeout=30); assert not a.exception, a.exception; assert any('n=9' in x.label for x in a.metric)"
```