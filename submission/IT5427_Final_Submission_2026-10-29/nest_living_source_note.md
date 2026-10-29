# NEST Living Hanoi Rent Index — source note

**Assessment date:** 2026-10-29<br>
**Publisher:** NEST Living<br>
**Role:** independent publisher's aggregate rental source; not individual listing records

## Source and intended download

- Rent index and methodology: <https://nestliving.vn/rent-index>
- Intended public CSV link: <https://nestliving.vn/rent-index/rent-index.csv>
- Terms read before both downloads: <https://nestliving.vn/terms>
- Method: two individual direct requests to the page's **Download the data (CSV)** link. No listing pages were crawled and no harvesting automation was used.
- Both responses were HTTP 200 with `text/csv; charset=utf-8`; each file is 5,039 bytes and has the same 12-column schema.

| Snapshot | Source `captured_at` (UTC) | Retrieved (UTC) | SHA-256 | Local optional CSV |
|---|---|---|---|---|
| `nest-20261029T082644540Z` | `2026-10-29T08:26:44.540Z` | `2026-10-29T08:27:06.485Z` | `af233deb251762a2a4065704087b3844acf3cd76accb7fd5d91d1eb6b06b268e` | `data/raw/nest_living/snapshots/nest_hanoi_rent_index_20261029T082644540Z.csv` |
| `nest-20261029T091525078Z` | `2026-10-29T09:15:25.078Z` | `2026-10-29T09:18:31.870Z` | `3574de70a9787d99a65ae68b412f10df55d80b195c0a5088c4923601049a638a` | `data/raw/nest_living/snapshots/nest_hanoi_rent_index_20261029T091525078Z.csv` |

The source captures are **48 minutes 40.538 seconds apart**. The latest snapshot ID is `nest-20261029T091525078Z`; its Spark marts are under `data/public_pilot/mart/nest_rent_index/nest-20261029T091525078Z/`.

## Methodology and terms assessment

NEST describes the index as monthly **asking rents** from homes in its own inventory, not a survey of all Hanoi homes or agreed lease prices. It reports medians and interpolated 25th/75th percentiles in VND, rounded to the nearest 100,000; nightly-rate listings are excluded. Separate homes in one building count separately. The methodology says cells below five homes suppress rent statistics while retaining the sample count. NEST also warns that its inventory mix shapes the figures and thin district groups are indicative only.

The terms prohibit automated harvesting and copying listing text, photos, or listings into another listing site or advertisement. They state no open-data license or explicit reuse grant for the CSV. These files are therefore treated as **optional local aggregate inputs**, with attribution and the terms caveat retained. The raw CSVs and derived local Parquet marts remain outside Git and the submission ZIP. No individual NEST home or listing data is present in either file.

## CSV profile

The exact source columns, in order, are:

`cut`, `district`, `district_name`, `bedroom_class`, `property_type`, `homes`, `median_vnd`, `p25_vnd`, `p75_vnd`, `published`, `floor_at_capture`, `captured_at`.

Each capture contains **45 aggregate cells**: 1 city, 10 district, 29 district-by-bedroom, and 5 property-type rows. Both profiles have 28 published cells and 17 suppressed small-sample cells. Each suppressed cell retains its count and the original `too few homes` marker for median and quartiles; parsed numeric statistics are null and `small_sample_suppressed` is true. The recorded minimum sample floor is 5.

| Profile item | Observed in each capture |
|---|---:|
| Aggregate cells | 45 |
| Published / suppressed cells | 28 / 17 |
| Empty required values (`homes`, `published`, floor, capture timestamp, rent statistics) | 0 |
| Structural blank dimensions: `district`, `district_name`, `bedroom_class`, `property_type` | 6, 6, 16, 40 |
| Missing city, district, property-type, or sample-size fields needed for the reported grains | 0 |

The latest city aggregate has **894 NEST homes**, median monthly asking rent **19,100,000 VND**, p25 **12,700,000 VND**, and p75 **30,500,000 VND** at source capture `2026-10-29T09:15:25.078Z`. This represents NEST's own inventory, not the Hanoi-wide market.

## Snapshot comparison

`compare_nest_snapshots.py` compared the two registered CSV captures using aggregate-cell keys (`cut`, source district, bedroom class, property type) and source metrics. The verified result is **45 shared cells, 7 changed, 38 unchanged, 0 added, and 0 removed**. Field counts across the seven changed cells were: `homes` 7, `median_vnd` 3, `p25_vnd` 2, `p75_vnd` 2, `published` 0, and `floor_at_capture` 0. There were 14 field-level changes because some cells changed in more than one field.

The city cell changed from 890 to 894 homes and p25 from 12,900,000 to 12,700,000 VND; its median stayed 19,100,000 and p75 stayed 30,500,000. These are changes in NEST's published aggregates between two captures. They do **not** show individual listing changes or rental-listing Velocity. The dated OSM batch comparison remains separate.

The machine-readable result is `data/public_pilot/snapshot_comparison/nest_living_latest.json`. Snapshot manifests beside the ignored CSVs record the exact URL, retrieval time, schema, profile, hash, terms assessment, and output grains.

## Processing and integration limits

`ingest_nest_rent_index.py` validates a manually downloaded CSV with PySpark and writes capture-specific Parquet marts for cells, city, district, district-bedroom, and property type. The latest capture has 45 cells: 1 city, 10 district, 29 district-bedroom (including all suppressed cells), and 5 property-type rows.

The city identifier `VN-HN` is syntactically compatible with the project city key, but the all-home NEST aggregate, Kaggle apartment-candidate subset, source dates, and rent populations do not match closely enough for a statistical join. District aggregates are not joined to Kaggle's free-text addresses. No aggregate is joined to individual listings and medians are not averaged.

The source page, methodology, and terms were read on 2026-10-29: [NEST Hanoi Rent Index](https://nestliving.vn/rent-index) and [NEST Terms of Use](https://nestliving.vn/terms).
