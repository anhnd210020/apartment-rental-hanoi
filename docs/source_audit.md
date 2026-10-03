# Stage G1 — source audit and pilot

**Checked:** 2026-10-02 (Asia/Bangkok)  
**Scope:** public pages, current terms pages, and each first-party `robots.txt`; no account sign-in, private endpoint, CAPTCHA, or access-control bypass. `robots.txt` is treated as a crawler directive, not a license or grant of reuse rights.

## Existing project contract

The default `python pipeline.py` path reads only the synthetic fixtures in `data/fixtures/`. Its shared Spark columns include source ID/URL, title, raw price/area/bedrooms, raw district/type, collection time, normalized price/area/bedrooms/district/type, and `quality_reason`. The prior fixture outputs and Streamlit dashboard remain synthetic. The fixture identifiers and `example.invalid` links are placeholders, not website identifiers.

The small permitted Batdongsan pilot is isolated at `data/raw/batdongsan/g1_20261002/listings.jsonl`. Each line retains the observed visible field groups (`listing.location`, `listing.overview`, and `listing.characteristics`) plus source URL/ID, collection timestamp, run ID, and method. It intentionally omits contact names, phone numbers, photos, and full descriptions. It is a manual, minimised transcription of visible page fields, not an underlying site API response or full page capture.

## Decisions

| Source | Terms and robots findings | Visible fields and feasibility | Decision |
|---|---|---|---|
| **Batdongsan.com.vn** | [Access agreement](https://trogiup.batdongsan.com.vn/docs/dieu-khoan-thoa-thuan) says reasonable digital copies for internal use are allowed, while prohibiting interference and disproportionate traffic; it also protects site and user content. [Site rules](https://trogiup.batdongsan.com.vn/docs/ix-quyen-va-trach-nhiem-cua-ban-quan-tri-batdongsancomvn) reserve site-content rights. [robots.txt](https://batdongsan.com.vn/robots.txt), checked directly, returned 200; `User-agent: *` allows `/`, with several internal routes disallowed. Selected named agents have a 10-second crawl delay; there is no general delay rule. | Public listing pages opened without login. Visible fields include listing code, title, asking-price label, area, bedrooms, bathrooms, ward/district/city, property type/features, and posting date. The page can expose personal contact details, which were not retained. | **Use only a tiny manual internal pilot.** The terms’ reasonable-copy/internal-use clause supports the three-record minimised pilot below. It does not clearly grant automated harvesting, so no crawler or bulk collection is authorised. Obtain written permission or a documented feed/API before automation or expanding the sample. |
| **Nhà Tốt (nhatot.com)** | [Terms of use](https://trogiup.chotot.com/nguoi-ban/dieu-khoan-su-dung-cua-nhatot-com/) prohibit excessive load/interference, restrict reproduction and use of site products to personal use, and require written permission for copying/distribution in specified contexts. [robots.txt](https://www.nhatot.com/robots.txt), checked directly after the bare host redirected to `www`, returned 200. It generally allows `/`, but disallows user/chat routes and numerous query parameters, including `price=`, `rooms=`, `subject=`, and `body=`. | A public listing page is human-readable and shows title, price, area, category, location, description/amenities, and posting context. Public contact/publisher information can also appear. No documented public data API or licensed export was verified. | **Replace pending written permission or documented API.** A general robots allowance does not grant copying rights; no sample was collected. A site-provided research export or owner-authorised, manually supplied sample is a practical alternative. |
| **Homedy.com** | [Operating rules](https://homedy.com/quy-che-hoat-dong) say access/use is for personal purposes and reserve content rights, prohibiting unlawful copying and dissemination. [robots.txt](https://homedy.com/robots.txt), checked directly, returned 200; `User-agent: *` allows `/`, with `/amp`, `-bg`, and `/js/` disallowed; it blocks some named crawlers. No explicit permission for research copying or automated collection was found. | First-party category pages display listing title, asking price, area, location, and description/amenities; bedroom count may appear in title/body. Direct page parsing or a documented API was not established in this audit. Contact/publisher details may also appear. | **Replace pending written permission or documented API.** Public visibility and robots allowance are not reuse permission. No sample was collected. Use an owner-authorised, manually supplied sample or licensed open dataset instead. |

## Batdongsan pilot record observations

The pilot contains three manually inspected public listing pages, checked on 2026-10-02. The sample is preliminary and not representative. No crawler was used.

| Source ID | Listing condition | Visible values / irregularity | Pipeline treatment |
|---|---|---|---|
| `46355243` | Active | Overview shows 12 triệu/tháng, 45 m², 1 bedroom, 1 bathroom. A separate visible detail says 45.6 m². | Kept the structured overview area (`45 m²`) for this pilot mapping; retained the conflicting detail separately. Flag the 0.6 m² discrepancy for manual review before scaling. |
| `46357913` | Active | Overview shows 10 triệu/tháng and 45 m². Bedroom and bathroom overview values are absent, although the title/detail says “1 ngủ”; the detail gives a 10–12 triệu/month range. | Do not infer a point price from the overview or title. The observed range is passed as `price_raw` and excluded as `invalid_price`. Bedroom remains missing in the structured overview. |
| `46118872` | Expired | Overview price says “Thỏa thuận”; visible description says from 11 triệu/month. Page explicitly says the listing has expired. | Excluded as `expired_listing` before price aggregation; recorded the conflicting price text without treating it as a current asking price. |

The source pages expose listing codes and dates, but the pipeline uses collection time as `collected_at`; the original posted date remains in raw. No record was missing a source ID, URL, collection time, or run ID. No personal contact detail was copied into the pilot file.

## Pilot run and counts

Command: `python pipeline.py --dataset bds-pilot`  
Output: `data/real_pilot/` (separate from synthetic `data/curated/` and `data/mart/`).

- Raw pilot records: **3**
- Active listings after status screening: **2**
- Rows passing the current price/area/type/location checks: **1**
- Unique curated listings after source-ID deduplication: **1**
- Excluded: **1 expired listing**, **1 range-price listing** (`invalid_price`)

These are preliminary checks on three manually selected listings only. They do not support market-trend or representative-market claims. The visible area mismatch and missing room fields should be reviewed on a larger authorised sample before the mapping is expanded.

## Next compliant input

For Nhà Tốt and Homedy, request a written research-use licence or documented public API/export from the operator. Otherwise, use a licensed open dataset or collect a few records directly from owners who authorise storage and analysis. Keep any supplied real records under `data/raw/`, separate from the clearly synthetic fixtures, and retain the source URL, source ID when available, collection time, run ID, and permission basis.
