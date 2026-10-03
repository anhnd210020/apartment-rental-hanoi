# Authorized data access request plan

**Prepared:** 2026-10-02 (Asia/Bangkok)  
**Purpose:** Obtain three independently sourced, authorized, de-identified, listing-level samples for “Multi-source Apartment Rental Data Integration and Analysis in Hanoi.” This is a request plan only. No messages were sent or scheduled, and no data access was attempted.

## Ranked provider plan

Statuses describe the next request action, not permission to use data. **CONTACT** means ask for a scoped, permissioned sample; **BACKUP** means pursue if a primary request fails or as a provenance clarification; **DO NOT USE** means do not ingest under current evidence.

| Rank | Provider | Exact request | Current evidence | Main risks / acceptance gate | Status |
|---:|---|---|---|---|---|
| 1 | **Nest Living** | 20–50 de-identified Hanoi apartment rental rows from the agency’s own inventory; ask for written non-commercial research permission, field definitions, and authorized weekly snapshots if available. | Its [Hanoi Rent Index](https://nestliving.vn/rent-index) describes one agency’s own book, reports 279 apartments with monthly rent, and offers only aggregate CSV cells. Its [terms](https://nestliving.vn/terms) say home facts come from owners/managers and prohibit automated harvesting and copying listing content for another listing site/advertisement. | Do not copy public listing pages or treat the aggregate CSV as raw data. Require explicit row-level research permission and authority to share owner/manager supplied fields. It is the clearest new provider lead, but underlying properties may also appear elsewhere. | **CONTACT** |
| 2 | **Batdongsan.com.vn operator** | Request 20–50 de-identified Hanoi apartment rental rows or an operator-supplied research feed, with written permission for analysis and report/demo aggregates; ask about an authorized repeated snapshot cadence. | G1 has three manually inspected records and one valid pipeline row, with source ID, status, property type, location, price, area and rooms. The [access agreement](https://trogiup.batdongsan.com.vn/docs/dieu-khoan-thoa-thuan) supported only a tiny internal manual pilot; it did not establish bulk/automated rights. An official research contact appears in Batdongsan [research reports](https://research.batdongsan.com.vn/images/report/analytical/3-tam-ly-nguoi-tieu-dung-bds-cuoi-nam-2024.pdf); the G1 [help center](https://trogiup.batdongsan.com.vn/) is another official route. | Existing pilot is too small. Seek direct operator authorization; do not expand collection or build a crawler on the current terms assessment. Require confirmation of first-party origin and whether syndicated copies are included. | **CONTACT** |
| 3 | **Nhà Tốt / Chợ Tốt** | Request an authorized research export/API or 20–50 de-identified Hanoi apartment rental rows, with a written reuse grant and source-level transaction/type definitions. | G1 found public pages with category, location, price and area, but did not verify research reuse permission or a documented data API. Chợ Tốt has an official [business/partnership page](https://chuongtrinh.nhatot.com/gioi-thieu-nen-tang-nhatot) with a partnership contact route. It is separately operated from Nest and Batdongsan. | Its G1 terms restrict reproduction/use, so written approval is required. Ask whether the export is drawn from Nhà Tốt itself, not another provider’s feed. | **CONTACT** |
| 4 | **Homedy** | If a primary request fails, request a permissioned, de-identified 20–50-row Hanoi apartment rental sample or documented feed and written research rights. | G1 found pages with title, price, area and location, but no established license/API. Homedy publishes an official [contact page](https://homedy.com/lien-he) and [operating rules](https://homedy.com/quy-che-hoat-dong). It is a distinct marketplace operator. | Its rules reserve content rights and do not clearly permit this research use. No copying or automation; require an explicit grant and confirmation of first-party provenance. | **BACKUP** |
| 5 | **Publisher of Kaggle’s Vietnam House Rent Dataset** | Ask for original source/platform and data-rights documentation; a 20–50-row author-verified Hanoi sample with explicit apartment category, rental status and counts; permission/attribution terms. | Kaggle declares CC0 and partitions a Hanoi file, but its schema has only title, date, address, area and price. The author’s [GitHub repository](https://github.com/vanviethieuanh/dataset) says its datasets were scraped from websites and disclaims responsibility. Public routes are [repository issues](https://github.com/vanviethieuanh/dataset/issues) and the Kaggle dataset discussion page. | CC0 on a re-publication does not establish rights in underlying scraped content. Apartment type is not structured and the preview did not verify an apartment-only count. Do not ingest unless authority, provenance and required sample are documented. | **BACKUP** |
| 6 | **TiniX AI / Hugging Face publisher** | Ask for a validated Hanoi apartment rental subset of 20–50 rows; explicit rental-versus-sale label definition; original platforms, collection/provenance and deduplication method; coursework permission terms; and snapshot availability. | The [dataset card](https://huggingface.co/datasets/tinixai/vietnam-real-estates) has Hanoi and apartment fields and declares CC BY-NC 4.0, but no structured transaction field. The organization profile lists TiniX’s website; the dataset’s [public discussion channel](https://huggingface.co/datasets/tinixai/vietnam-real-estates/discussions) is a publisher route. | Do not infer rental status from price or text. Require an explicit label and original provenance; confirm the license covers storage, transformation, report and demo. Do not download the multi-gigabyte corpus for this request. | **BACKUP** |

The first three requests target separate providers: an agency inventory and two separately operated listing platforms. They are plausible independent inputs, not verified sources yet. Count them as independent only if each provider confirms its own source provenance and that its export is not merely repackaged from another listed provider. Cross-posted properties may still occur; retain provider-specific pseudonymous IDs and document known overlap. Kaggle and TiniX are separate published corpora but do not qualify as independent listing-platform sources until original provenance is documented. Mirrors and alternate formats never count as additional sources.

## Request package

### Minimum pilot

Request **20–50 rows per provider** for authorization and parser validation. Ask for a normal mix of Hanoi apartment rentals, including normal missing optional values. A larger export may follow only after written permission and pilot acceptance. A 20–50-row pilot validates access, labels and schema; it is not representative market coverage.

### Fields to request

- Provider-issued **pseudonymous listing ID** stable across authorized snapshots.
- District and ward; no exact personal address or unit number.
- Property type in the provider’s category, with its definition and the apartment value.
- Explicit transaction/listing type confirming **rental**, not inferred from amount or free text.
- Rent amount, currency and unit/period (for example VND/month); preserve ranges/negotiable values as such.
- Area and unit; bedroom/bathroom count if available.
- Published date, last-updated date, provider collection/export timestamp and timezone.
- Listing status (active, expired, removed, etc.).
- Provider/source name, original source/platform provenance, dataset/version or feed name, and permission/license basis.

Do **not** request names, phone numbers, exact personal addresses, account IDs, photos, or other contact details. Keep absent optional fields null; do not infer them from text or prices.

### Source acceptance checklist

A provider passes only when all items have evidence in the project source register:

1. **Independent provenance:** provider identifies who supplied/created the rows and original platform/source; no mirror or repackaged copy; no unsupported multi-platform claim.
2. **Hanoi:** explicit Hanoi location with usable district/ward values in the sample.
3. **Apartment:** explicit property-type field/category and documented mapping.
4. **Rental status:** explicit rental transaction field or provider-validated rental-only export; sale status distinguishable.
5. **Row-level structure:** one listing per row, stable pseudonymous ID, field definitions, units, status and date context.
6. **Reuse permission:** written permission or clear license covers non-commercial coursework, local storage, PySpark transformation, derived aggregates in the final report/classroom demo, attribution and agreed retention.
7. **Disclosure boundary:** provider specifies whether raw rows may be shown or redistributed. Default: raw data will not be published unless explicitly permitted.
8. **Pilot review:** inspect 20–50 rows, record missing/irregular fields, verify counts by Hanoi/type/rental/status, and confirm no direct identifiers/contact details.
9. **Snapshot rights:** for Velocity, permission covers repeated snapshots and provider defines their timestamp/cadence.

A request is not permission until approved. Retain the approval, license/version, approval date, sample manifest and retention/deletion date with the data. Restrict raw access and keep real rows separate from synthetic fixtures.

### Freshness and Velocity plan

Ask whether the provider can supply a dated snapshot and, if allowed, repeated exports. Propose **one provider-supplied snapshot per week for at least four weeks** (six to eight weeks is preferable), with stable pseudonymous IDs and provider snapshot/as-of time. Never collect more often than authorized.

For each batch, retain a snapshot ID, provider, export/collection timestamp with timezone, provider as-of time, source version, row count and permission reference. Compare authorized snapshots by stable pseudonymous ID to count new, updated and no-longer-active rows per interval. A small pilot only demonstrates that repeated authorized snapshots can be processed, not market-wide velocity. For a one-time file, report its as-of/received date and do not claim a measured Velocity result. Do not call the process real-time or streaming unless the provider supplies a documented real-time/streaming service.

## Fallback if fewer than three providers approve

Keep the registered topic **“Multi-source Apartment Rental Data Integration and Analysis in Hanoi”** unchanged. Use only the number of authorized, accepted real sources available; label one- or two-source results as limited and do not count synthetic fixtures or mirrors as real sources. Keep the synthetic MVP as a labeled pipeline/dashboard demo, separate from research findings. Report the gap and access outcomes; do not fill it with unauthorized collection or a different property segment.

Changing the number/type of sources, replacing apartments with houses/short-stay rentals, widening beyond Hanoi, or dropping the real multi-source requirement changes the registered scope. Obtain instructor approval before such a change. If fewer than three qualify, present the limitation and request a scope decision rather than describing G2 as complete.

## Draft 1: Vietnamese request to Nest Living

**Tiêu đề:** Xin phép sử dụng mẫu dữ liệu căn hộ cho thuê Hà Nội phục vụ bài tập học thuật

Kính gửi Nest Living,

Em đang thực hiện bài tập học thuật phi thương mại về tích hợp và phân tích dữ liệu căn hộ cho thuê tại Hà Nội. Em xin phép Nest Living cung cấp mẫu nhỏ gồm 20–50 dòng dữ liệu căn hộ đang/đã đăng cho thuê, đã ẩn danh và không có tên, số điện thoại, địa chỉ căn hộ cụ thể hoặc thông tin liên hệ. Nếu được phép, em cũng xin hỏi liệu có thể nhận snapshot dữ liệu định kỳ hằng tuần trong 4–6 tuần để kiểm tra mức độ thay đổi theo thời gian hay không.

Các trường mong muốn gồm mã tin giả danh ổn định, quận/phường, loại bất động sản, trạng thái thuê, giá thuê kèm đơn vị/kỳ thuê, diện tích, số phòng ngủ/phòng tắm nếu có, ngày đăng/cập nhật và thời điểm xuất dữ liệu. Em dự định xử lý dữ liệu bằng PySpark trong phạm vi bài tập, và chỉ trình bày kết quả tổng hợp trong báo cáo cuối kỳ và phần trình bày trên lớp.

Xin Nest Living cho biết bằng văn bản phạm vi quyền sử dụng phi thương mại, yêu cầu ghi nguồn/ghi công, thời hạn lưu trữ và cách xóa dữ liệu sau thời hạn đó. Xin xác nhận liệu dữ liệu thô có được phép hiển thị hoặc phân phối lại hay không. Mặc định em sẽ không công bố dữ liệu thô nếu chưa được cho phép rõ ràng.

Nếu Nest Living không thể cấp quyền hoặc cung cấp mẫu dữ liệu, em hoàn toàn hiểu và sẽ không thu thập từ trang web.

Em xin cảm ơn,  
[Tên sinh viên]  
[Trường/lớp hoặc mã môn học]

## Draft 2: Vietnamese request to a dataset publisher or agency

**Tiêu đề:** Xin xác nhận nguồn gốc và quyền sử dụng mẫu dữ liệu thuê căn hộ Hà Nội

Kính gửi [Tên đơn vị/người xuất bản],

Em đang thực hiện bài tập học thuật phi thương mại về tích hợp dữ liệu căn hộ cho thuê tại Hà Nội. Em xin hỏi đơn vị có thể cung cấp hoặc cho phép sử dụng mẫu nhỏ 20–50 dòng listing đã ẩn danh để kiểm tra dữ liệu và xây dựng quy trình PySpark hay không.

Để tránh phân loại sai, em mong mẫu có trường xác nhận Hà Nội, loại căn hộ và trạng thái giao dịch là cho thuê; đồng thời xin tài liệu giải thích định nghĩa các nhãn này, nguồn gốc/nền tảng ban đầu, thời gian thu thập và quyền mà đơn vị có thể cấp cho dữ liệu. Với Kaggle, em đặc biệt cần xác nhận website nguồn và quy tắc nhận diện căn hộ Hà Nội. Với TiniX, em cần nhãn phân biệt thuê/bán, định nghĩa nhãn, nền tảng nguồn và điều kiện giấy phép áp dụng cho mẫu.

Các trường đề nghị gồm mã tin giả danh ổn định, quận/phường, loại bất động sản, trạng thái thuê, giá và đơn vị/kỳ thuê, diện tích, số phòng ngủ/phòng tắm nếu có, ngày đăng/cập nhật/thu thập, tên nguồn và xuất xứ dữ liệu. Em không cần tên, số điện thoại, địa chỉ cá nhân chính xác, ảnh hoặc thông tin liên hệ.

Dữ liệu chỉ được dùng cho bài tập phi thương mại, xử lý bằng PySpark và trình bày kết quả tổng hợp trong báo cáo cuối kỳ/phần trình bày trên lớp. Xin cho biết yêu cầu ghi nguồn, thời hạn lưu trữ/xóa, và liệu dữ liệu thô có được phép hiển thị hoặc phân phối lại hay không. Em sẽ không công bố dữ liệu thô nếu chưa được cho phép rõ ràng. Nếu được cấp quyền, em cũng muốn hỏi về snapshot lặp lại theo tuần; em sẽ không tự động thu thập từ website.

Trân trọng,  
[Tên sinh viên]  
[Trường/lớp hoặc mã môn học]

## Draft 3: Optional English request

**Subject:** Request for permission to use a small de-identified Hanoi apartment rental sample

Dear [Provider/Publisher],

I am completing non-commercial academic coursework on integrating apartment rental data in Hanoi. Would you consider providing or authorizing a small pilot sample of 20–50 de-identified listing rows for local PySpark processing?

To validate the records, I need explicit Hanoi location, apartment type, and rental status, definitions of those labels, and documentation of original source/platform and collection period. Requested fields are a stable pseudonymous listing ID, district/ward, property type, rental status, rent amount and period, area, bedroom/bathroom counts if available, published/updated/collected timestamps, listing status, provider name and source provenance. I do not need names, phone numbers, exact personal addresses, photos or contact details.

The data would be used only for non-commercial coursework. I would transform them with PySpark and present aggregate results in the final report and classroom demo. Please specify attribution requirements, permitted uses, retention/deletion limits, and whether raw rows may be shown or redistributed. Raw data will not be published unless you explicitly authorize it. If permitted, please also let me know whether dated weekly snapshots could be supplied for four to six weeks; I will not scrape or automatically collect data from your website.

Thank you,  
[Student name]  
[Course / institution]
