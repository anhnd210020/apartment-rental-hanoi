# NEST Living Hanoi Rent Index — source note

**Assessment date:** 2026-10-29<br>
**Publisher:** NEST Living<br>
**Role:** independent publisher's aggregate rental source; not individual listing records

## Source and intended download

- Rent index and methodology: <https://nestliving.vn/rent-index>
- Public CSV link on that page: <https://nestliving.vn/rent-index/rent-index.csv>
- Terms read before download: <https://nestliving.vn/terms>
- Download method: one direct request to the CSV URL exposed by the page's **Download the data (CSV)** control; no listing pages were crawled and no harvesting automation was used.
- HTTP result: `200`, `text/csv; charset=utf-8`, 5,039 bytes.
- Retrieved at: **2026-10-29T08:27:06.485Z**.
- NEST source capture timestamp in the CSV: **2026-10-29T08:26:44.540Z**.
- Local optional snapshot: `data/raw/nest_living/snapshots/nest_hanoi_rent_index_20261029T082644540Z.csv`.
- SHA-256: `af233deb251762a2a4065704087b3844acf3cd76accb7fd5d91d1eb6b06b268e`.

## Methodology and terms assessment

NEST describes the index as monthly **asking rents** from homes in its own inventory, not a survey of Hanoi's whole rental market or agreed lease prices. It reports the median and interpolated 25th/75th percentiles in VND, rounded to the nearest 100,000; nightly-rate listings are excluded. Multiple separately let homes in one building count separately. The page says cells with fewer than five homes do not publish rent statistics, while the sample count remains visible. It also warns that its inventory mix shapes the figures and that thin district groups are indicative only.

The terms prohibit using automated tools to harvest the site and copying listing text, photos, or listings into another listing site or advertisement. The requested file was the page's intended aggregate CSV download; the project did not crawl or save listing records. The terms page does **not** state an open-data license or an explicit reuse grant for the CSV. Reuse rights therefore remain unclear. The CSV is treated as an **optional local input**, with attribution and the terms caveat retained; the raw CSV is excluded from Git and the submission ZIP. No individual NEST home/listing data is present in the file or pipeline.

## CSV profile

The exact source columns, in order, are:

`cut`, `district`, `district_name`, `bedroom_class`, `property_type`, `homes`, `median_vnd`, `p25_vnd`, `p75_vnd`, `published`, `floor_at_capture`, `captured_at`.

`cut` defines the aggregate grain: `city`, `district`, `district_bedroom`, or `type`. The file contains **45 aggregate cells**: 1 city, 10 district, 29 district-by-bedroom, and 5 property-type rows. The city cell reports 890 homes; the property-type counts sum to the same 890.

| Profile item | Observed |
|---|---:|
| Cells marked published | 28 |
| Small-sample cells marked unpublished | 17 |
| `median_vnd` suppressed as `too few homes` | 17 |
| `p25_vnd` suppressed as `too few homes` | 17 |
| `p75_vnd` suppressed as `too few homes` | 17 |
| Recorded sample floor | 5 homes |
| Missing/blank `homes`, `published`, `floor_at_capture`, `captured_at`, or rent-statistic source fields | 0 |

Blank dimension counts are structural for a cell's grain, not missing observations: `district` 6, `district_name` 6, `bedroom_class` 16, and `property_type` 40. The three suppressed statistic fields on each of 17 unpublished cells remain as their original text in the Spark output; their parsed numeric columns are null and `small_sample_suppressed` is true. This preserves suppression instead of converting it to zero or silently dropping it.

The city value is a monthly median across NEST's own homes, not a listing-level value. District keys remain in NEST's namespace. Kaggle addresses are free text and do not provide reliable district keys; its curated records are apartment candidates and have a different source period and coverage. The city/district/property-type NEST marts therefore stay separate from the existing Kaggle + OSM + WorldPop city mart. No median-of-medians or aggregate-to-listing join is performed.

## Local processing outputs

`ingest_nest_rent_index.py` validates a manually downloaded CSV with PySpark and writes dated Parquet marts beneath `data/public_pilot/mart/nest_rent_index/nest-20261029T082644540Z/`:

- `cells/`: 45 source-grain aggregate cells.
- `city/`: 1 Hanoi aggregate cell.
- `district/`: 10 district aggregate cells.
- `district_bedroom/`: 29 district-by-bedroom aggregate cells, including all 17 suppressed cells.
- `property_type/`: 5 property-type aggregate cells.
- `manifest.json`: source URL, source and retrieval timestamps, schema/profile, hash, terms assessment, and output grains.

`compare_nest_snapshots.py` compares only two registered CSVs with distinct source capture times. At this assessment there is **one genuine snapshot**, so the comparison status is `insufficient_snapshots`; no earlier snapshot is fabricated and no change count is reported. Any future comparison describes aggregate-cell changes only, not rental listing Velocity. The existing Geofabrik/OSM batch manifests and comparison outputs remain separate.

The source page, methodology, and terms were read on 2026-10-29: [NEST Hanoi Rent Index](https://nestliving.vn/rent-index) and [NEST Terms of Use](https://nestliving.vn/terms).
