# Kịch bản demo trực tiếp 5 phút

**Đã kiểm tra:** 2026-10-29. Số liệu public tham chiếu manifest `public-20261029T083945Z`; NEST tham chiếu hai capture `nest-20261029T082644540Z` và `nest-20261029T091525078Z` cùng comparison đã lưu. Khởi động dashboard trước phần trình bày; không cần chạy lại Spark trong năm phút demo.

## Khởi động từ thư mục dự án

Mở PowerShell và chạy:

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

Mở `http://127.0.0.1:8501/?view=public`. Chuyển sang **Synthetic fixtures** hoặc mở `http://127.0.0.1:8501/?view=synthetic` để xem fixture path. Kiểm tra HTTP local bằng:

```powershell
(Invoke-WebRequest -Uri 'http://127.0.0.1:8501/?view=public' -UseBasicParsing -TimeoutSec 10).StatusCode
```

## Dẫn chương trình

### 0:00–0:35 — Phạm vi nguồn

**Nói:** “Dự án có một dataset listing hướng tới cho thuê từ Kaggle, một nguồn độc lập của NEST cung cấp thống kê tiền thuê tổng hợp, và OSM/WorldPop làm dữ liệu bối cảnh. NEST không chứa các bản ghi listing. Tôi không tuyên bố ba nền tảng listing độc lập hay số liệu đại diện toàn thị trường.”

### 0:35–1:10 — Run và sàng lọc

**Nêu:** manifest `public-20261029T083945Z`: 13.785 dòng Kaggle, 3.284 dòng Hà Nội, ledger thủ công bao phủ 303 ứng viên cue căn hộ, 106 tiêu đề có khả năng là thuê căn hộ nguyên căn và 102 dòng có khoản tiền cùng diện tích dương. Spark xử lý 408.151 ô WorldPop và tạo một dòng integrated city.

**Nói:** “Đây là sàng lọc cùng rà soát tiêu đề, không phải xác minh 102 giao dịch thuê.”

### 1:10–2:05 — Kaggle amounts

Chỉ vào dashboard listing summary và phần tháng: 102 khoản tiền/diện tích dương; median listed amount 3.500.000 VND; median diện tích 30 m²; median amount per m² 120.000 VND/m²; chỉ 9 bản ghi có kỳ tháng xác minh.

**Nói:** “Kỳ hạn chưa biết với 92/102 khoản tiền. Tập tháng n=9 có median 3.200.000 VND/tháng, nhưng đây là mẫu nhỏ, cũ và thăm dò, không phải mức thuê hiện tại của thị trường.”

### 2:05–3:10 — NEST aggregate và độ phủ nguồn

Mở source coverage và NEST section. Nêu 45 aggregate cells: 1 city, 10 district, 29 district-bedroom, 5 property type; 28 công bố và 17 cell bị suppress. City cell mới nhất có n=894 homes, median 19,1 triệu VND/tháng, p25 12,7M và p75 30,5M tại source capture `2026-10-29T09:15:25.078Z`. Hai capture cách nhau 48 phút 40,538 giây; 7/45 aggregate cells đổi, 38 giữ nguyên, không thêm/bớt. Đây là thay đổi aggregate của NEST, không phải rental-listing Velocity. Property-type chart gắn median với sample size từng cell.

**Nói:** “Đây là asking rents từ inventory của NEST, không phải toàn thị trường và không phải từng listing. NEST có population và time basis khác Kaggle nên tôi không so sánh trực tiếp hai bộ số. Terms không nêu open license hoặc quyền reuse CSV rõ; đây là optional local aggregate input, có attribution và caveat.”

Nêu thêm: “Chỉ có một capture thật. Dashboard không tạo changed-cell counts cho đến khi có lần tải CSV thứ hai; OSM batch evidence được trình bày riêng.”

### 3:10–4:00 — Bối cảnh địa lý

Chỉ vào OSM/WorldPop. Hai nguồn context được nối với Kaggle summary ở city grain qua `city_key=VN-HN`. Listing không có tọa độ hay district/ward IDs đáng tin cậy để enrichment từng dòng hoặc khu phố. WorldPop là raster tham chiếu năm 2020.

### 4:00–4:35 — Nhánh synthetic

Chuyển sang **Synthetic fixtures**.

**Nói:** “Đây là dữ liệu fixture tổng hợp để kiểm tra pipeline: 7 raw, 7 active, 5 valid và 4 unique listings. Không dòng nào là tin thuê thực.”

### 4:35–5:00 — Giới hạn và kết luận

**Nói:** “Pipeline chạy cục bộ, nối OSM/WorldPop ở cấp thành phố và giữ NEST aggregates riêng. Kaggle upstream rights còn chưa rõ; NEST terms cũng không đưa ra reuse grant rõ cho CSV. OSM có thay đổi batch và NEST hiện có một aggregate capture; chưa có bằng chứng rental-listing Velocity hay streaming.”

## Lệnh làm mới trước demo

Public manifest ghi 109,395 giây Spark và 119,968 giây elapsed trong một lần chạy local. Lệnh ingest NEST chỉ đọc CSV đã tải thủ công, không kết nối site:

```powershell
& $py pipeline.py
& $py prepare_public_context.py
& $py prepare_worldpop_cells.py
& $py pipeline.py --dataset public
& $py ingest_nest_rent_index.py --input 'data\raw\nest_living\snapshots\nest_hanoi_rent_index_20261029T091525078Z.csv' --retrieved-at-utc '2026-10-29T09:18:31.870Z'
& $py compare_nest_snapshots.py
```

NEST CSV phải được tải thủ công qua link CSV công khai. Chỉ báo cáo comparison sau khi có hai capture thật khác nhau; không giả lập snapshot cũ.
