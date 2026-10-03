# Stage G2 candidate source validation

**Checked:** 2026-10-02 (Asia/Bangkok)  
**Scope:** Reviewed the current project contract in `README.md`, `docs/source_audit.md`, and `pipeline.py`; checked publisher metadata/cards and small previews for the two downloadable datasets; used only the existing three-record Batdongsan pilot. No full dataset was downloaded, no website was crawled, and no contact details were collected.

## Project requirements and decision meaning

The project needs real Hanoi apartment **rental** records. A row only qualifies if location, apartment type, and rental status are supported by explicit fields or sufficiently documented source-level curation. A large dataset or a suggestive title is not enough. A price amount, even if it looks like a monthly rent, cannot establish transaction type.

- **ACCEPT** means the rights, provenance, and required record distinctions are verified for this project.
- **CONDITIONAL** means some requirements are supported, but a named evidence gap must be closed before ingestion/use as a qualifying source.
- **REJECT** means the source currently lacks a safe reuse basis or cannot support the project's target records.

A **distinct ingestion source** here means an independently published corpus/provider with documented provenance and a reuse basis. A mirror, alternate file format, or repackaging of the same corpus is not another source. A publisher name alone does not prove the underlying listing platform, nor that two corpora do not overlap. I count separately documented Kaggle and TiniX releases as separate candidate inputs at the corpus/publisher level, but do not claim distinct underlying website platforms or non-overlap where their documentation does not say so. The Kaggle author's GitHub files are a mirror of the same Kaggle corpus, not another source.

## Candidate decisions

| Candidate | Decision | Can target rows be isolated from verified fields/records? | Reuse basis |
|---|---|---|---|
| Vietnam House Rent Dataset (vanviethieuanh) | **CONDITIONAL** | Hanoi is isolated by the `hn.csv` file, and the publisher describes the corpus as house-rental posts. However, the file has no property-type field, ID, or listing URL. Apartment-only Hanoi rental count cannot be verified from the schema or small sample. | Kaggle metadata states **CC0: Public Domain**. No attribution condition is stated by the CC0 declaration; cite the creator and dataset as good academic practice. |
| TiniX Vietnam Real Estate Listings | **CONDITIONAL** | Hanoi and apartment category are represented by explicit fields (`province_name`, `property_type_name`), and the card reports 1,140,542 total Hanoi listings. The schema has no transaction/listing-type field. Sale and rental records are mixed, so rental rows cannot be separated reliably from the verified structured fields. | Dataset card declares **CC BY-NC 4.0**: attribute TiniX AI and the dataset, link the license, indicate changes, and limit reuse to noncommercial purposes under that license. |
| Existing Batdongsan.com.vn manual pilot | **CONDITIONAL** | The raw sample has source IDs, URLs, visible status, and structured overview fields. Of three manually inspected records, only one passed the current pipeline's active/valid checks. It is too small to establish an adequate source of Hanoi apartment rentals. | G1 assessed the site agreement's reasonable internal-copy language as supporting only a tiny, minimised manual internal pilot. This is not an open-data license or permission for automated/bulk collection or expansion. Follow the restrictions in `docs/source_audit.md`. |

## 1. Vietnam House Rent Dataset | Kaggle

**Publisher/platform provenance.** Kaggle lists creator **Van Viet Hieu Anh** and links to the same creator's [GitHub `house-rent` directory](https://github.com/vanviethieuanh/dataset/tree/main/house-rent). The linked README calls it a collection of house-rent posts in Vietnam, with separate city files. It does not identify the original listing website/platform, so this report does not attribute the posts to one. The GitHub data are the publisher-linked mirror of the Kaggle dataset, not a separate source.

**License and attribution.** Kaggle's dataset metadata reports **CC0: Public Domain**. No attribution is required by the stated CC0 license. For traceability, record the creator, dataset title, Kaggle URL, and access date if the dataset is later ingested. The linked GitHub README does not add a separate license statement; rely on the Kaggle release's stated CC0 basis and preserve that provenance.

**Date, format, schema, and size.** Kaggle reports last updated **2022-08-13** (version 1). The publisher states the posts have a `published` field formatted `dd/mm/yyyy`, but does not give a complete collection-date range. Files are CSV and JSON variants in the publisher's repository; this review inspected only a streamed beginning of the Hanoi CSV, not a full file. Kaggle's file metadata lists `hn.csv` at **599,720 bytes** and 3,284 records, `dn.csv` at 140,446 bytes / 768 records, and `hcm.csv` at 1,751,373 bytes / 5,000 records (about **2.49 MB** total for the three CSVs).

The documented schema is only:

- `title` (post title)
- `published` (publication date)
- `address` (detailed address)
- `acreage` (area in m2)
- `price` (price in million VND; `-1` means negotiable)

There is no structured property category, transaction type, stable listing ID, or source URL. The publisher identifies `hn.csv` as Hanoi, which is a usable city partition. Its rental-only corpus description is positive source-level evidence of rent status, but the source website and row-level transaction label are not documented.

**Small-sample observations.** I streamed the first **100 CSV data rows** from the publisher-linked Hanoi file and stopped without saving them. All 100 had a publication date; the schema fields for address, acreage, and price were populated in the first 12 inspected rows. A simple title-cue check found apartment terms in 69/100 titles, rental terms in 66/100, and both in 41/100. These counts are only a preview diagnostic, not a classifier or a verified count of apartment rentals. The publisher's example record is explicitly a room-rental post, which confirms that the corpus can include non-apartment housing. The preview does not establish how many Hanoi apartment records exist or whether apartment mentions can be distinguished consistently from rooms, houses, and serviced units.

**Limitations and decision.** The stated corpus scope supports treating rows as rental posts at a dataset level, but the apartment-only subset remains unverified because type is free text, and records lack IDs/URLs for deduplication or provenance checks. Keep this **CONDITIONAL**. Before accepting, request an author-confirmed apartment labeling rule or a labeled sample with counts for Hanoi apartment rentals; otherwise manually review and document a sufficiently sized permitted subset before ingestion. Do not treat GitHub and Kaggle copies as separate sources.

Evidence: [Kaggle dataset page](https://www.kaggle.com/datasets/vanviethieuanh/vietnam-house-rent-dataset) | [Kaggle metadata](https://www.kaggle.com/api/v1/datasets/view/vanviethieuanh/vietnam-house-rent-dataset) | [Kaggle file list](https://www.kaggle.com/api/v1/datasets/list/vanviethieuanh/vietnam-house-rent-dataset) | [publisher's README](https://github.com/vanviethieuanh/dataset/blob/main/house-rent/README.md) | [Hanoi CSV](https://github.com/vanviethieuanh/dataset/blob/main/house-rent/csv/hn.csv).

## 2. TiniX Vietnam Real Estate Listings | Hugging Face

**Publisher/platform provenance.** The Hugging Face dataset card identifies **TiniX AI** as curator/publisher. It reports records collected and processed by TiniX AI from June 2025 through March 2026, but the inspected card does not name the original listing platforms or provide per-record platform/source IDs or URLs. Therefore, treat TiniX as a separately published corpus input, but do not claim that it covers multiple websites or that it is disjoint from the Batdongsan pilot or Kaggle corpus.

**License and attribution.** The card declares **CC BY-NC 4.0**. For permitted noncommercial use, attribute **TiniX AI**, cite *TiniX Vietnam Real Estate Listings (2025-2026)* and the dataset URL, link the [CC BY-NC 4.0 license](https://creativecommons.org/licenses/by-nc/4.0/), and note any changes. This is not permission for commercial use.

**Date, format, schema, and size.** The card covers **2025-06-01 to 2026-03-31** and reports **3,500,744 records**, **10 Parquet shards**, about **1.67 GB** total. Hugging Face repository metadata shows the card/data repository last modified **2026-04-14**. The schema has 19 columns: `name`, `description`, `property_type_name`, `province_name`, `district_name`, `ward_name`, `street_name`, `project_name`, `price`, `area`, `floor_count`, `frontage_width`, `house_depth`, `road_width`, `bedroom_count`, `bathroom_count`, `house_direction`, `balcony_direction`, and `published_at`. The card says descriptions have HTML stripped and phone numbers redacted. It claims 1,140,542 Hanoi records across all property/transaction types; that is not a count of Hanoi apartment rentals.

**Small-sample observations.** I inspected the Hugging Face dataset viewer's small displayed preview and the full published schema, without downloading Parquet. The preview contains sale records, including apartment-category records (`property_type_name = apartment category`) whose title/description explicitly says `sale` and whose `price` is a sale price. The card describes the corpus as including for-sale and rental but does not define or expose a transaction-type field. `price` is a numeric VND value without a documented rent-period/transaction discriminator. The listed schema contains no `listing_type`, `transaction_type`, or equivalent structured field. The viewer preview confirms that sale listings are present; it does not provide a verified rental subset count.

**Limitations and decision.** Do not infer rent/sale from price magnitude, `name`, or `description` keywords alone. The explicit Hanoi and apartment fields are useful, but the critical rental-versus-sale filter is missing. Keep this **CONDITIONAL** until TiniX supplies a documented transaction field/label or a publisher-validated rental-only sample and filtering method with counts. Do not download the 1.67 GB dataset before that gap is closed. If accepted later, retain the required attribution and noncommercial restriction.

Evidence: [Hugging Face dataset card and viewer](https://huggingface.co/datasets/tinixai/vietnam-real-estates) | [repository metadata and file manifest](https://huggingface.co/api/datasets/tinixai/vietnam-real-estates) | [TiniX AI publisher page](https://tinix.ai/) | [CC BY-NC 4.0 deed](https://creativecommons.org/licenses/by-nc/4.0/).

## 3. Existing Batdongsan.com.vn pilot

**Provenance and rights.** `docs/source_audit.md` documents the official terms, robots review, the manual collection method, and the three source IDs/URLs. The source is the Batdongsan.com.vn site itself; the pilot was manually transcribed from visible listing fields and kept in `data/raw/batdongsan/g1_20261002/listings.jsonl`. The terms assessment permits only a tiny internal manual pilot on the evidence reviewed. Robots rules are not a license. No crawler or automated expansion is approved by this finding.

**Format and observed schema.** Raw JSON Lines, three records, each retaining groups `listing.location`, `listing.overview`, and `listing.characteristics`, plus metadata (`source_url`, source ID, collection timestamp, run ID, and method). The source pages were checked/collected **2026-10-02**. The records expose Hanoi location, title, status, observed price/area/room/property type, and source IDs; they also show missing overview room fields, a 45 vs 45.6 m' discrepancy, a price range, and one expired listing.

**Usability and decision.** The prior pilot pipeline run produced 3 raw, 2 active, 1 valid, and 1 unique listing. This is a real, source-distinct observation but not enough volume for an adequately sized Hanoi apartment-rental source, and the terms basis does not support bulk collection. Keep this **CONDITIONAL** as a tiny manual validation input only. To qualify a larger input, obtain written permission or a documented feed/API/export from the operator; alternatively use separately owner-authorized records with a retained permission basis.

Evidence: [G1 source audit](source_audit.md) | [official access agreement](https://trogiup.batdongsan.com.vn/docs/dieu-khoan-thoa-thuan) | [official robots.txt](https://batdongsan.com.vn/robots.txt).

## Does current evidence support three usable sources'

**No. G2 is not complete.** The evidence supports three candidate corpora/providers at a broad publisher/platform level, but none is currently verified as a sufficiently sized, reusable source of Hanoi apartment rental rows:

1. **Kaggle:** clear CC0 basis and documented Hanoi file; rental scope is publisher-stated, but apartment-only records cannot be counted/reliably isolated from its text-only schema using the inspected sample.
2. **TiniX:** clear noncommercial reuse basis and structured Hanoi/apartment fields; mixed sale/rent records lack a transaction field, so rental records cannot be selected reliably.
3. **Batdongsan pilot:** source identity and a narrow manual internal-use basis are documented, but only one of three rows passed and that pilot does not authorize expansion.

The Kaggle GitHub mirror is not another source. The original listing platforms for Kaggle and TiniX are not named, so no claim is made that either corpus represents multiple platforms or is non-overlapping with another candidate. No real dataset was ingested into the project, and no project code was changed.

## Safest next action

First ask the **Kaggle publisher** for an author-confirmed apartment-only labeling rule or a small labeled Hanoi sample with counts, and ask **TiniX AI** for the source-platform provenance plus an explicit transaction-type field or publisher-validated rental subset. In parallel, seek a written research-use export/feed from Batdongsan. If those are unavailable, the safest new source to investigate is a small, manually supplied sample from Hanoi landlords/agents who explicitly authorize storage and research reuse, with records de-identified and permission retained. Do not promote any candidate to ACCEPT until its actual rows, rights, provenance, type, city, and rental status are all verified.
