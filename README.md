# IT5427: Hanoi apartment rental data prototype

The project keeps its synthetic fixtures separate from an exploratory public-data prototype. The prototype uses one Kaggle-published rental-oriented listing dataset, OpenStreetMap context, and WorldPop context. It does **not** establish three independent rental-listing sources or represent the whole Hanoi market.

## Run on the existing Windows `dev` environment

Open PowerShell in this folder and configure the existing Java/Spark setup:

```powershell
$env:JAVA_HOME = 'D:\Apps\Temurin17\jdk-17.0.20.1+1'
$env:PATH = "$env:JAVA_HOME\bin;D:\Apps\hadoop-3.3.6\bin;D:\envs\dev\Scripts;$env:PATH"
$env:HADOOP_HOME = 'D:\Apps\hadoop-3.3.6'
$env:PYSPARK_PYTHON = 'D:\envs\dev\Scripts\python.exe'
$env:PYSPARK_DRIVER_PYTHON = 'D:\envs\dev\Scripts\python.exe'
```

Run the synthetic fixture path or the public-data path:

```powershell
python pipeline.py                         # synthetic fixtures only
python prepare_public_context.py           # reuses the existing Hanoi OSM/WorldPop clip
python prepare_worldpop_cells.py           # valid WorldPop cells -> gzip CSV for Spark
python pipeline.py --dataset public        # Spark listings + OSM summary + WorldPop cells
python compare_geofabrik_snapshots.py --old-manifest data/public_pilot/snapshot_comparison/manifests/vietnam-261001.json --new-manifest data/public_pilot/snapshot_comparison/manifests/vietnam-261002.json --output data/public_pilot/snapshot_comparison/vietnam-261001_to_261002.json
python -m streamlit run dashboard.py
```

`prepare_public_context.py --rebuild` explicitly repeats the geospatial scan and raster clip. It is not needed for the current prepared artifacts. Raw public source files and prepared Parquet outputs are kept under `data/` and are separate from synthetic fixtures.

## Sources, grain, and limits

- **Kaggle Vietnam House Rent Dataset**, by Van Viet Hieu Anh: [dataset page](https://www.kaggle.com/datasets/vanviethieuanh/vietnam-house-rent-dataset). The uploader declares CC0. Its repository says records were scraped from websites but does not identify the original websites. Original platform provenance and third-party rights remain unresolved; keep source rows local and do not redistribute them. The CSV fields are title, publication string, address, area, and listed amount. Amounts are described in million VND, but the time basis is unknown for most rows. Only nine rows with explicit monthly title evidence and matching structured amounts enter monthly summaries.
- **OpenStreetMap via Geofabrik Vietnam extract**: [Geofabrik source and snapshots](https://download.geofabrik.de/asia/vietnam.html). OSM data is under ODbL 1.0. Attribute “© OpenStreetMap contributors” and link [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright). The dashboard uses city-level context.
- **WorldPop Vietnam 2020 population counts**: [dataset record](https://hub.worldpop.org/geodata/summary?id=6449). The raster is CC BY 4.0; cite WorldPop / University of Southampton and DOI [10.5258/SOTON/WP00645](https://doi.org/10.5258/SOTON/WP00645).
- **TiniX Vietnam Real Estate Listings** is excluded from rent analysis because it has no validated rental-versus-sale label.

The public run screens 13,785 listing rows, including 3,284 Hanoi rows, and produces 102 positive-amount/area rows after the corrected title review. OSM and WorldPop are processed at their own grains: one prepared Hanoi OSM summary row and 408,151 valid WorldPop cells, then one city aggregate for each. Spark joins the two context aggregates and the listing summary by the explicit key `city_key=VN-HN`. No OSM or population values are attached to individual listing rows: the listings have no reliable coordinates or structured district/ward IDs.

The dated OSM comparisons use the downloaded 2026-09-30 Geofabrik PBF and official consecutive update sequences 4926 (2026-10-01) and 4927 (2026-10-02). The full newer PBFs were not downloaded; the official `.osc.gz` deltas and frozen `state.txt` manifests were used. Sequence 4927 was replayed twice with identical manifests and change counts. This is partial OSM batch-change evidence, not streaming or rental-listing Velocity. Kaggle remains one listing snapshot last updated in 2022, and WorldPop remains a 2020 reference-year product. See [the demo runbook](docs/demo_runbook.md) for startup commands and caveats.

The dashboard labels all mixed/unknown-period amounts as **listed amount** and **listed amount per m²**. Its separate monthly summary shows n=9 and a small-sample caveat. Full lineage, Parquet sizes, Spark times, snapshot counts, and limitations are in [`docs/public_data_implementation.md`](docs/public_data_implementation.md). The audit sample and price semantics are in [`docs/data_quality_and_analysis_review.md`](docs/data_quality_and_analysis_review.md).

## Synthetic fixture notice

Every record in `data/fixtures/` is synthetic test data. It is not a real rental listing and must not be presented as one. The default `python pipeline.py` path uses only these fixtures.
