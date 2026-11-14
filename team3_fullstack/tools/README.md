# Công cụ kiểm chứng Team 3

## Đánh giá Retrieval qua Backend/API

`evaluate_retrieval_api.py` gửi cùng bộ câu hỏi qua Backend Java cho từng dịch vụ
RAG đã được cấu hình sẵn. Công cụ thu câu trả lời, citation, trace ID, lỗi và
bảng latency; không thay cấu hình retrieval bên trong dịch vụ RAG.

### Chuẩn bị

- Python 3.12 và dependency trong [requirements-performance.txt](../requirements-performance.txt).
- URL RAG local hoặc remote đã cấu hình sẵn, hỗ trợ `/internal/v1/ready`, query và article API theo contract.
- Backend đang chạy cho mỗi URL RAG, hoặc JAR backend/JDK 25 và PostgreSQL để công cụ khởi động Backend tạm.

Từ gốc repository, cài dependency vào môi trường riêng nếu chưa có:

```powershell
python -m venv .venv-performance
& ./.venv-performance/Scripts/python.exe -m pip install -r team3_fullstack/requirements-performance.txt
```

Sao chép [matrix mẫu](examples/retrieval-api-matrix.example.json) và
[bộ câu hỏi mẫu](examples/retrieval-api-queries.example.json) ra thư mục làm việc.
**URL trong ví dụ chỉ minh họa, không phải dịch vụ đã triển khai.** Thay bằng URL
đang sẵn sàng. Không đưa credential vào URL, manifest hoặc file cấu hình đính kèm.
Khi chuyển matrix sang vị trí khác, sửa lại `config_path` cho đúng vị trí mới.

Manifest có `format_version: 1`, tên `selected` và các `targets`:

| Trường | Ý nghĩa |
| --- | --- |
| `name` | Tên cấu hình duy nhất, chữ ASCII/số/gạch nối/gạch dưới |
| `rag_url` | Origin của dịch vụ RAG đã cấu hình sẵn, không kèm path/query/credential |
| `backend_url` | Tùy chọn: Backend có sẵn, đã được bên vận hành nối tới `rag_url` này |
| `config_path` | Tùy chọn: JSON cấu hình kỹ thuật; đường dẫn tính từ manifest; lưu hash và trường được phép |

Không có `backend_url`: công cụ khởi động một Java Backend riêng cho target,
đặt `SPRING_PROFILES_ACTIVE=rag` và `RAG_BASE_URL`, kiểm tra health rồi dừng đúng
process đã tạo. URL RAG bên ngoài luôn do bên vận hành quản lý.

### Chạy

Nếu dùng Backend tạm, build bằng Maven Wrapper trước; đặt `JAVA_HOME` trỏ JDK 25:

```powershell
Push-Location team3_fullstack/backend
./mvnw.cmd package
Pop-Location
```

Đặt `SPRING_DATASOURCE_URL`, `SPRING_DATASOURCE_USERNAME` và
`SPRING_DATASOURCE_PASSWORD` trong môi trường process bằng cấu hình database kiểm
thử của bạn. Công cụ không đọc credential từ manifest hoặc tự tạo database.

```powershell
& ./.venv-performance/Scripts/python.exe -X utf8 team3_fullstack/tools/evaluate_retrieval_api.py `
  --matrix path/to/matrix.json --dataset path/to/queries.json `
  --output-dir team3_fullstack/backend/target/retrieval-api-run-001 `
  --mode api --users 1 --warmup 1 --timeout-seconds 60 `
  --backend-jar team3_fullstack/backend/target/backend-0.0.1-SNAPSHOT.jar
```

Nếu mọi target có `backend_url`, bỏ `--backend-jar`; không cần Java/PostgreSQL
trên máy chạy công cụ. Có thể chỉ chạy một cấu hình bằng `--configuration NAME`
hoặc cấu hình đã chọn bằng `--selected-only`.

Dataset là JSON array có `id`, `question`, UTF-8/NFC; ID không trùng, câu hỏi tối
đa 2.000 code point. Không dùng Test Set (`split: "test"`) cho lượt đánh giá này.
Mỗi query/config dùng UUID mới và hội thoại mới; đây là phép đo truy vấn độc lập.

### Đọc kết quả

Thư mục output phải chưa tồn tại. Công cụ tạo `report.json`, `comparison.md` và
log Backend tạm. Mã thoát: `0` thu đủ kết quả; `1` có lỗi chạy; `2` đầu vào không
hợp lệ hoặc output đã tồn tại. Không ghi đè báo cáo trước đó.

- Cấu hình chạy lần lượt, cùng thứ tự câu hỏi, users, timeout và số warm-up.
  Mặc định một user để so sánh; không chạy benchmark khác đồng thời.
- Đo từ lúc gửi API đến terminal SSE hợp lệ. Đây là latency qua Backend, gồm
  RAG/DB/transport; không phải latency riêng của Retrieval hoặc thời gian render UI.
- p50/p95 dùng nearest rank trên mẫu thành công, đơn vị JSON là giây; bảng là ms.
  Warm-up, lỗi và lượt chưa chạy được ghi riêng; không có mẫu thành công thì phân vị `null`.
- Lưu đầy đủ complete response/citation và đối chiếu theo query ID. Mọi citation
  được kiểm schema; chỉ citation đầu được gọi Article API. Kết quả khác nhau
  không tự chứng minh cấu hình nào có chất lượng pháp lý cao hơn.
- Hash cấu hình và URL do người chạy khai báo, không chứng minh server thật sự
  nạp đúng index/model. `COLLECTED` chỉ xác nhận thu đủ dữ liệu; không phải kết luận
  nghiệm thu hoặc xác nhận model thật. Cần kèm cấu hình runtime từ bên bàn giao.

`--mode mock` chỉ nhận dịch vụ có header `X-RAG-Mode: mock`; `--mode api` từ chối
dịch vụ có header này. Không có header mock cũng chưa chứng minh suy luận model thật.

### Kiểm chứng công cụ

```powershell
& ./.venv-performance/Scripts/python.exe -X utf8 -m unittest discover -s team3_fullstack/tests -v
```

Harness [run_retrieval_api_integration.py](../tests/run_retrieval_api_integration.py)
dùng Java/PostgreSQL thật và các RAG HTTP fixture có gắn nhãn; cần thêm môi trường
Python đã cài dependency API Team 2 để chạy fixture. Truyền `--output-dir` mới,
`--runner-python` (Python có Locust), `--backend-jar` và `--java`. Database kiểm thử
phải đang chạy và được cấu hình qua các biến môi trường trên. Harness tự dừng các
fixture/Backend nó tạo, không khởi động hoặc dừng database.

Để kiểm phần Team3 mà không nạp model, chạy harness trên với dịch vụ FastAPI fixture
(Python cần dependency `.[api]`) và runner đã có Locust/jsonschema. Harness kiểm hai
target, selected-only, answer/citation/Article, lỗi503/502/504 và bảo toàn output.
Fixture dùng chính adapter FastAPI Team2 và luôn gắn `X-RAG-Mode: mock`; không dùng
latency fixture làm số đo Retrieval thật. Code cleanup có fallback dừng Java trực tiếp
nếu lệnh dừng cây tiến trình Windows không khởi chạy được; log luôn được đóng.

## Công cụ khác

Kiểm UI/pool/render dùng [run_week8_acceptance.py](../tests/run_week8_acceptance.py),
với các chế độ `profile`, `ui`, `full`. Chi tiết phương pháp/giới hạn tại
[performance-measurement.md](../../docs/team3_fullstack/performance-measurement.md#5-kiểm-pool-và-render-độc-lập-với-model).
Frontend dev có thể bật `VITE_DEBUG_LATENCY=true` để xem thời gian request→complete;
production luôn ẩn nhãn này. Đây không phải phép đo riêng Retrieval/model.

### Viewer corpus và chuẩn bị G4

`team3_fullstack/tests/run_team3_acceptance.py` chạy Java, Vite, browser kiểm thử và
Article service trên các cổng riêng; database kiểm thử được cung cấp qua
`SPRING_DATASOURCE_URL/USERNAME/PASSWORD`. Dùng Python đã cài dependency API hiện có.

```powershell
python team3_fullstack/tests/run_team3_acceptance.py --mode corpus `
  --output-dir team3_fullstack/backend/target/viewer-corpus-001 `
  --backend-jar team3_fullstack/backend/target/backend-0.0.1-SNAPSHOT.jar `
  --java path/to/jdk-25/bin/java.exe --node path/to/node.exe --browser path/to/msedge.exe
```

`corpus` kiểm Article thật, không gọi model. `mock-demo` kiểm ba kịch bản P0/citation,
insufficient và replay bằng fixture gắn nhãn; không phải nghiệm thu G4 live.
`live-demo` dùng dịch vụ local hoặc remote sẵn sàng qua `--rag-url`, kèm `--questions` trỏ JSON có hai
chuỗi `answered` và `insufficient_context`; từ chối service gắn nhãn mock hoặc chưa ready.
Không đổi hay khởi động lại dịch vụ ngoài do người chạy cung cấp.
Truyền thêm `--ffmpeg <binary>` để lưu video `g4-demo.mp4`; ảnh và JSON kết quả
vẫn được ghi khi một kịch bản thất bại. Video kiểm chứng kỹ thuật không thay phê duyệt G4.

Output gồm raw timing20 lượt, kết quả từng ca, ảnh Viewer/mobile/G4 và log; thư mục
phải chưa tồn tại. Tự dừng các process do harness tạo. Đo route→DOM của SPA sau khi app
sẵn sàng; font ngoài được cô lập trong probe, không sửa font ứng dụng hoặc đo full-page.
Kết quả kỹ thuật không tự xác nhận chất lượng pháp lý hoặc phê duyệt G4 của nhóm.

### Chạy RAG thật trên cùng máy

Không cần một URL được cấp riêng: FastAPI của Team2 có thể chạy tại localhost8001.
`local_rag.py` chỉ điều phối API build/load hiện có của Team1 và factory Team2;
không chứa thuật toán tìm kiếm, prompt hoặc LLM riêng.

```powershell
# Python cần các dependency retrieval/dense/reranker/api của project.
python team3_fullstack/tools/local_rag.py prepare `
  --output-dir .local/team3/live-rag/runtime-001 --allow-model-download
python team3_fullstack/tools/local_rag.py check --runtime-dir .local/team3/live-rag/runtime-001
python team3_fullstack/tools/local_rag.py serve --runtime-dir .local/team3/live-rag/runtime-001
```

`prepare` mặc định offline; chỉ tải model khi có `--allow-model-download`. Model/cache,
BM25/Dense và Qdrant embedded lưu local. Batch embedding mặc định1 để hạn chế bộ nhớ;
có thể đặt `--embedding-batch-size`. Output phải mới; không ghi đè index có sẵn.
Nguồn cấu hình là `team1_data/retrieval/retrieval_v2.json`: model/revision, top_k20,
Hybrid weights0.5/1.0. `serve` đặt các RAG_* tương ứng và bật strict reranker; chỉ dùng
cache đã có. Corpus hoặc cấu hình đổi sau build sẽ bị từ chối trước khi nạp model.
`check` xác nhận artifact, không thay readiness `/internal/v1/ready` hay query thật.

Gemini/provider vẫn do root `.env` hiện có và Team2 quản lý; công cụ không sao chép key
vào runtime.json. Chạy Java với profile `rag`, `RAG_BASE_URL=http://localhost:8001`
và PostgreSQL riêng. Frontend vẫn chỉ gọi Java, không gọi thẳng dịch vụ Python.

- `measure_latency.py`: benchmark T3-15, timing bốn pha và các guard riêng.
- `split_golden_dataset.py`: chia và đóng băng bộ dữ liệu đã bàn giao.

Dùng `--help` để xem tham số từng công cụ. Hồ sơ thực hiện và kiểm chứng lưu local
theo [quy trình Team 3](../docs_3/README.md).
