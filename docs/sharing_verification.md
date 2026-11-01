# Biên bản chuẩn bị chia sẻ - 01/11/2026

## Phạm vi thay đổi

Giao diện `dashboard.py` và nhãn của `docs/reproduce_nest_property_types_vi.py` dùng tiếng Anh. Các tiêu đề trong `docs/generate_project_figures.py` dùng dấu ASCII `-`. Tên file `_vi.py` được giữ để không phá đường dẫn cũ. Nhãn hiển thị tách khỏi schema/enum lưu trữ; không sửa phép tính, lọc, dedup, fingerprint, snapshot key hoặc dữ liệu nguồn.

README tiếng Việt có hướng dẫn CMD, dependency và checklist đầu vào thật. Thêm pyarrow vào requirements để việc đọc Parquet được khai báo rõ. Hai bản ledger chia sẻ chỉ chiếu đúng các trường mà Spark tiêu thụ, giữ nguyên giá trị hiện có:

- `reproducibility/curation/kaggle_hanoi_title_review.csv`: 303 dòng, `source_fingerprint`, `review_status`, `review_reason`.
- `reproducibility/curation/kaggle_price_period_review.csv`: 11 dòng, `source_fingerprint`, `explicit_price_period`, `monthly_amount_status`.

Đã đối chiếu toàn bộ các trường này với ledger cục bộ. Không thêm tiêu đề, địa chỉ, liên hệ, khoản tiền nguồn, số dòng nguồn hoặc nhãn mới. `reproducibility/public_inputs.manifest.json` là bản provenance lịch sử, ghi thời điểm tải gốc của nhóm; không mô tả một lần tải mới.

## Môi trường thực tế

| Thành phần | Phiên bản đã dùng |
|---|---|
| Python | 3.12.1 64-bit, `D:\envs\dev\Scripts\python.exe` |
| Java | Temurin OpenJDK 17.0.20.1+1 |
| PySpark | 3.5.9 |
| pandas / Streamlit / Plotly | 2.3.3 / 1.64.0 / 6.9.0 |
| pyarrow | 24.0.0 |
| osmium / rasterio / shapely | 4.3.1 / 1.5.2 / 2.1.2 |
| matplotlib | 3.10.9, dùng riêng cho kiểm tra hình |

`pip check` không tìm thấy dependency bị hỏng. Môi trường chung có cảnh báo một distribution `~uggingface-hub` không hợp lệ; không sửa thành phần ngoài project. Không tạo môi trường Python mới hoặc thử cài toàn bộ từ Internet trong lần này.

### Native Hadoop Windows

Máy hiện tại dùng hai binary ở `D:\Apps\hadoop-3.3.6\bin`. Không có README nguồn, build log hoặc Zone.Identifier chỉ ra nguồn tải. Tên thư mục không đủ xác minh phiên bản/build hoặc nhà cung cấp. Hash chỉ nhận diện đúng bản đã kiểm tra, **không** chứng minh độ tin cậy/provenance:

| File | Byte | SHA-256 |
|---|---:|---|
| `winutils.exe` | 119296 | `496a591eb1e67df2a620f710d529ba6ddfe1c19149e6647cc4e320bb0efd8553` |
| `hadoop.dll` | 78848 | `d7ab36a68518748cef142be2da5069b4c763c2cd764c1d2e6ac48c7200405be3` |

Không đưa binary vào Git và không đề xuất nguồn tải không rõ ràng. Máy Windows mới cần bản native tương thích được xác minh/build có nguồn gốc; README ghi riêng cấu hình cục bộ và cấu hình di động. Linux/WSL chưa được kiểm tra.

## Kiểm tra đã thực hiện

- Biên dịch 15 module Python ở gốc và `docs/` bằng `py_compile`.
- Chạy `python pipeline.py` bằng môi trường `dev`: **7 raw, 7 active, 5 valid, 4 unique**.
- Streamlit AppTest ở cả synthetic và public với output cục bộ hiện có; đối chiếu toàn bộ giá trị số KPI trước/sau dịch, không thay đổi.
- Kiểm điều hướng qua lại bằng **Public-data prototype** / **Synthetic fixtures**, query `view=synthetic`, enum bộ lọc `apartment` / `mini_service`, bộ lọc nguồn rỗng và session state dùng nhãn tiếng Việt cũ.
- Kiểm các caveat: 92 khoản chưa rõ kỳ giá, chỉ 9 dòng xác minh tháng, city/Apartment NEST khác quần thể, so sánh ô aggregate, tích hợp cấp thành phố. Không có U+2013/U+2014 trong text UI được render bởi AppTest.
- HTTP 200 cho cả `?view=synthetic` và `?view=public` trên server local cổng kiểm tra 8517. HTTP chỉ xác nhận server trả trang; AppTest kiểm nội dung/chạy ứng dụng.
- Chạy helper hình NEST với output chuyển tới thư mục tạm: hash raw, manifest, Parquet và số liệu capture 29/10 khớp; quan sát ảnh tiếng Anh, tiêu đề/nhãn không bị cắt. Không ghi đè ảnh/báo cáo/slide có sẵn.
- Kiểm CLI `--help` thật của pipeline, prepare context, ingest NEST, compare NEST và compare Geofabrik; đối chiếu tên script, option và link file trong README.
- Kiểm hash 89 tệp output/context public trước/sau thay đổi: giữ nguyên.

Kênh browser automation báo `The browser access host is unavailable`; truy cập native Chrome được chọn cũng bị chặn do cửa sổ minimized và API không cung cấp thao tác restore tương ứng. Vì vậy **chưa kiểm tra trực quan toàn trang dashboard** để kết luận về wrapping/clipping ở từng kích thước màn hình. Ảnh helper NEST đã được xem; AppTest/HTTP không thay thế kiểm tra bố cục toàn trang.

## Cây sạch và kiểm tra upload

Kiểm tra synthetic và dashboard synthetic trên bản checkout riêng chỉ chứa cây file được đưa vào commit, không có raw, ledger làm việc, marts cũ, `.venv` hoặc dependency native trong project. Chỉ tái dùng dependency Python/Java/Hadoop đã cài ở ngoài repository. Kết quả synthetic phải là 7/7/5/4; public view trên clone sạch phải hiện thông báo thiếu input/output, không tự tạo dữ liệu.

Đã rà file được track, metadata đề xuất, đường dẫn trong Git history, nội dung ZIP/Office và kích thước file. Không tìm thấy pattern credential/token/private key hoặc raw/env trong archive được kiểm tra. Báo cáo học phần đã track có tên/mã học viên của nhóm; giữ tài liệu cho phạm vi repository private phục vụ nhóm, không thêm thông tin liên hệ. Quét pattern không phải công cụ chứng minh tuyệt đối rằng tài liệu không chứa bí mật.

Các báo cáo, slide, hình và ZIP nộp bài đã track được giữ như tài liệu lịch sử, đều dưới giới hạn 100 MiB/file. Những chỉnh sửa báo cáo/slide và thay đổi không liên quan có sẵn ở working tree được giữ ngoài commit công việc chia sẻ; riêng dashboard hiện có là nền tảng cho bản dịch này. Không reset, discard, sửa lịch sử hay force-push.

## Không chạy lại

Không chạy lại `pipeline.py --dataset public`, quét/clip địa lý, ingest NEST hoặc refresh dữ liệu live: thay đổi ngôn ngữ không cần tái tính các kết quả đó. Đã đọc output public hiện có của run **`public-20261030T131827Z`** (119,777 giây Spark tổng), khác run 29/10 được trích trong báo cáo lịch sử. Không coi thời gian đọc dashboard là một lần xử lý public mới. Không dựng lại báo cáo, slide hoặc archive lịch sử; không thử môi trường Windows mới thiếu native dependency.
