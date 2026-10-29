# Câu hỏi bảo vệ dự kiến và câu trả lời

Các câu trả lời dưới đây bám theo code, public manifest `public-20261029T083945Z`, NEST snapshots `nest-20261029T082644540Z` và `nest-20261029T091525078Z`, cùng các báo cáo QA hiện có. Những con số chỉ mô tả prototype cục bộ và mẫu hiện tại.

## Nguồn dữ liệu và phạm vi

### 1. NEST có phải listing source thứ hai, và nguồn nào tích hợp được?

Trong nhánh public có một dataset listing hướng tới cho thuê từ Kaggle, một nguồn độc lập của NEST chứa aggregate asking-rent statistics, và hai nguồn geographic context là OpenStreetMap và WorldPop. NEST không chứa listing records, không được nối với từng listing hay với Kaggle city summary, và không biến dự án thành ba nền tảng listing. Tôi nêu rõ các vai trò này để giảng viên đánh giá cách hiểu “multi-source” của môn học.

### 2. Tuyên bố CC0 của Kaggle có giải quyết đầy đủ quyền sử dụng không?

Không. Hồ sơ dự án ghi uploader khai báo CC0. Tuyên bố đó không xác định các website gốc hoặc chứng minh uploader có quyền cấp phép nội dung upstream. Raw rows vì thế được giữ cục bộ và không phân phối lại; quyền và provenance gốc vẫn là giới hạn chưa giải quyết.

### 3. Bằng chứng nào có về cách thu thập và website gốc của dữ liệu Kaggle?
README cấp repository của publisher nói các dataset được scrape từ websites. README riêng của house-rent mô tả dữ liệu là các bài đăng cho thuê nhưng không nêu website nguồn hay quy trình cụ thể. Vì vậy có thể nói publisher tự khai báo đã scraping; nền tảng gốc, chi tiết thu thập và quyền upstream vẫn chưa được xác minh.

### 4. Vì sao dùng dữ liệu niêm yết cũ?

Kaggle ghi cập nhật cuối ngày 2022-08-13. Trong 102 dòng curated, 100 ngày đăng parse được, từ 2016-01-14 đến 2022-07-26. Dataset được dùng để kiểm chứng quy trình tích hợp và làm sạch, không để mô tả giá hiện tại. Dashboard và báo cáo gọi kết quả là thăm dò, không phải market-wide estimate.

### 5. TiniX có phải nguồn thuê thứ hai không?

Không trong phân tích này. Card có schema bất động sản phong phú nhưng không có nhãn thuê/bán được xác nhận. Trong preview đã kiểm tra, 160/500 dòng ở Hà Nội và 41 có loại căn hộ có cấu trúc; không có Hanoi-apartment rental nào được xác minh. Tôi không suy transaction type từ độ lớn giá hoặc từ khóa mô tả và không nạp TiniX vào pipeline. NEST là aggregate rental source độc lập, nhưng cũng không phải nguồn listing thứ hai.

### 6. Tại sao Batdongsan pilot không được tính là nguồn thứ hai?

Audit G1 ghi nhận pilot thủ công ba bản ghi, trong đó một dòng qua các kiểm tra hiện có. Nó không phải dataset đủ lớn hoặc feed được cấp quyền cho pipeline hiện tại; quyết định G1 chỉ cho phép mẫu thủ công tối giản. Pilot cũng không nằm trong public run manifest.

## Tốc độ dữ liệu và tích hợp

### 7. Đã đáp ứng Velocity chưa?

Chưa có bằng chứng rental-listing Velocity. OSM có batch evidence riêng: Geofabrik sequences 4925, 4926 và 4927 được ghi ngày 2026-09-30 đến 2026-10-02; seq. 4927 có 14.572 create / 5.901 modify / 2.284 delete. Hai NEST aggregate CSV captures ngày 2026-10-29 cách nhau 48 phút 40,538 giây; comparison ghi 7/45 aggregate cells thay đổi, 38 giữ nguyên, không thêm/bớt. Đây là thay đổi ở chỉ số tổng hợp của NEST, không phải thay đổi listing records. Không có listing feed hoặc snapshot listing lặp lại, nên không tuyên bố streaming hay rental-listing Velocity.

### 8. Có nối OSM hoặc WorldPop vào từng listing hay từng khu phố không?

Không. Kaggle có địa chỉ văn bản tự do nhưng không có tọa độ hay district/ward ID tin cậy. Một kiểm tra văn bản tìm được 52/106 title-positive rows có một quận ghi rõ duy nhất, nhưng đó không phải khóa hành chính đủ tin cậy cho phép nối toàn bộ tập. OSM và WorldPop được ghép với listing summary ở cấp thành phố qua `city_key=VN-HN`; không có context field nào gắn vào listing rows.

### 9. WorldPop thể hiện điều gì trong dashboard?

Đây là raster population count tham chiếu năm 2020. Spark đọc 408.151 ô hợp lệ sau khi clip Hà Nội rồi tính tổng ước lượng khoảng 8.440.532,41 người. Đây là sản phẩm mô hình theo ô raster, không phải đếm dân số tại listing hay địa chỉ cụ thể.

### 10. Tại sao đưa OSM vào nếu không có spatial join đến listing?

OSM vẫn là một nguồn context riêng, được tiền xử lý thành thống kê thành phố như đường, transit, giáo dục, y tế và amenities. Mục tiêu tích hợp là minh bạch về nhiều định dạng và grain có thể nối được. Khi không có tọa độ listing đáng tin cậy, dừng ở cấp thành phố là quyết định đúng về dữ liệu; không gán quan hệ neighborhood giả.

## Spark, chất lượng và phân tích

### 11. Vì sao dùng Spark cho 13.785 listing rows? Đây có phải big-data scale không?

Không phải bằng chứng về quy mô sản xuất. Spark được dùng để thể hiện các bước đọc nhiều file, schema alignment, cleaning/quality disposition, aggregate, city-key join và ghi Parquet trong pipeline tái lập được. Nhánh public chạy PySpark 3.5.9 ở `local[2]`; lần chạy ngày 2026-10-29 xử lý 13.785 Kaggle rows và 408.151 WorldPop cells, mất 109,395 giây theo Spark và 119,968 giây elapsed theo manifest. NEST có job Spark riêng; đây không phải so sánh hiệu năng với pandas hoặc cluster.

### 12. “102 curated” có nghĩa là 102 tin thuê đã xác minh không?

Không. Đó là các dòng tiêu đề được rà soát là có khả năng thuê căn hộ, đồng thời có price và area dương. Ledger có 106 title-positive rows; bốn dòng có khoản tiền không dùng được và bị loại khỏi summary số. Ngay cả 102 dòng còn lại cũng là các bản ghi thăm dò, không phải giao dịch thuê đã xác minh.

### 13. Precision 98% có nói classifier chính xác 98% trên toàn bộ dataset không?

Không. Đó là precision bảo thủ ước tính trên mẫu ngẫu nhiên 50/105 predicted positives: 49 tiêu đề rõ là căn hộ thuê, một dòng mơ hồ được tính không đúng. Mẫu âm 100/3.179 có hai trường hợp bỏ sót xác nhận và sáu trường hợp mơ hồ. Vì cỡ mẫu nhỏ và nhãn dựa trên tiêu đề, tôi không báo accuracy toàn tập hoặc recall dân số.

### 14. Tại sao không coi toàn bộ `price` là tiền thuê tháng?

Dataset mô tả `price` theo triệu VND nhưng không có time basis chung. QA kiểm tra tiêu đề: 11/106 title-positive rows nêu khoản tiền theo tháng; chín khớp trường cấu trúc, một không khớp và một có `price=-1`/không biết. Trong 102 dòng số học, 92 có kỳ hạn chưa biết. Vì vậy chỉ chín dòng được dùng cho summary tháng; phần còn lại là “listed amount”.

### 15. Kết quả nào được dashboard hiển thị?

Kaggle hiển thị median listed amount 3.500.000 VND, median area 30 m² và median listed amount per m² 120.000 VND/m²; time basis của 92/102 khoản chưa biết. Tập Kaggle có kỳ tháng xác minh là n=9, median 3.200.000 VND/tháng. NEST city cell mới nhất có median asking rent 19.100.000 VND/tháng trên 894 NEST homes tại capture `2026-10-29T09:15:25.078Z`; p25 là 12.700.000 và p75 là 30.500.000 VND. Mỗi capture có 45 cell, trong đó 17 cell suppress rent statistics. Comparison giữa hai captures tìm thấy 7 cell thay đổi; đây là aggregate-cell changes, không phải listing Velocity. Hai nguồn có record universe và định nghĩa khác nhau, nên không so sánh trực tiếp hoặc gộp median.

### 16. Hệ thống xử lý trùng lặp và entity resolution như thế nào?

Nhánh synthetic gọi `dropDuplicates(["source", "source_listing_id"])`. Ở Kaggle public không có ID ổn định; SHA-256 fingerprint chỉ dùng để khớp các ledger review/price-period, không dùng để deduplicate. Không có matching liên nền tảng hay cross-platform entity resolution.

### 17. Các đầu ra và thời gian Spark được đo thế nào?

Manifest `public-20261029T083945Z` ghi 13.785 Kaggle inputs, 102 curated rows, 408.151 WorldPop cells, và một dòng integrated city output; `total_spark_seconds` là 109,395, manifest elapsed là 119,968 giây. NEST có manifest riêng với 45 cells và các mart city/district/type/bedroom. Đây là một lần chạy local, nên không ngoại suy sang production.

### 18. Vì sao không có ML hoặc Kafka/Hadoop cluster?

Mục tiêu của phiên bản này là Big Data Integration and Processing: nạp nhiều schema/format, làm sạch, quản lý chất lượng, nối đúng grain và tạo đầu ra phân tích. Nhãn title hiện có và cỡ mẫu review nhỏ không tạo tập huấn luyện đã xác nhận; do đó ML nằm ngoài phạm vi. Cluster hoặc streaming cũng không cần để minh họa pipeline local đã triển khai. Không có claim về real-time processing.

### 19. Dự án có thể kết luận mức thuê hoặc tác động tiện ích của toàn Hà Nội không?

Không. Có một dataset listing cũ với nhãn dựa một phần vào title review; chỉ chín dòng Kaggle có time basis tháng xác minh. NEST là aggregate từ inventory riêng của publisher; hai captures gần nhau ghi nhận thay đổi một số cell, nhưng không đại diện toàn thị trường hoặc đo listing Velocity. Không có spatial join listing-to-neighborhood. Chúng tôi chỉ trình bày mô tả thăm dò, không đưa ra market-wide rents, xu hướng hiện tại hay tác động nhân quả của tiện ích.

### 20. Những giấy phép nào cần ghi công?

Theo hồ sơ hiện tại, OpenStreetMap cần ghi “© OpenStreetMap contributors” và tuân thủ ODbL 1.0 khi phân phối dữ liệu phái sinh phù hợp; WorldPop cần attribution WorldPop / University of Southampton theo CC BY 4.0 cùng DOI. Kaggle uploader khai báo CC0 nhưng provenance website và quyền upstream còn chưa xác minh; raw data không được phân phối lại. NEST terms cấm automated harvesting và sao chép nội dung listing nhưng không nêu open license hay grant tái sử dụng CSV rõ ràng. Vì vậy CSV chỉ là optional local aggregate input, có attribution/terms caveat; không crawl listings, và không đưa raw CSV vào Git/ZIP.

### 21. Snapshot NEST nào đã so sánh được?

Hai capture CSV thật được tải riêng qua link công khai. Capture thứ nhất: source `2026-10-29T08:26:44.540Z`, retrieval `2026-10-29T08:27:06.485Z`; capture thứ hai: source `2026-10-29T09:15:25.078Z`, retrieval `2026-10-29T09:18:31.870Z`. `compare_nest_snapshots.py` xác nhận 45 shared cells, 7 changed, 38 unchanged, 0 added, 0 removed. `homes` đổi ở 7 cells, median ở 3, p25 ở 2, p75 ở 2; publication flag và sample floor không đổi. City cell tăng từ 890 lên 894 homes; median giữ 19.100.000 VND, p25 giảm từ 12.900.000 xuống 12.700.000, p75 giữ 30.500.000. Đây là thay đổi trong thống kê aggregate của NEST, không phải thay đổi listing records hay rental-listing Velocity. Các tệp, hashes và đánh giá terms nằm trong `docs/nest_living_source_note.md`.
