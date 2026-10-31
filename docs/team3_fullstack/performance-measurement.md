# Đo độ trễ và timing Backend

Đối chiếu implementation ngày31/10/2026. Căn cứ [ARCHITECTURE](../ARCHITECTURE.md) §3/§8;
API public theo [đặc tả SSE](public-api-specification.md). Đây là thiết kế chức năng
dùng chung, không phải biên bản nghiệm thu hoặc phê duyệt benchmark.

## 1. Ranh giới phép đo

Runner [measure_latency.py](../../team3_fullstack/tools/measure_latency.py) dùng Locust
để chạy số lượt hữu hạn. Đồng hồ đơn điệu đo từ gửi request đến terminal SSE complete/error;
tra cứu Điều được đo đến khi nhận/kiểm JSON body đầy đủ. Native HTTP metric của Locust
với stream chỉ đo đến headers nên không được cộng vào số lượt hoặc phân vị terminal.
Warm-up có lượt/UUID riêng và nằm ngoài phân vị chính. Không retry ngầm.

Article API timing không bao gồm render/focus/DOM. AI Service timing là HTTP chờ xử lý
và validation response, không suy thành thời gian retrieval/rerank/model riêng. Các chỉ
tiêu chất lượng pháp lý và nghiệm thu toàn hệ thống cần bằng chứng khác.

## 2. Trace và timing opt-in

Trong profile rag, `CHAT_LATENCY_ENABLED=true` bật dòng log `CHAT_LATENCY {JSON}`.
Mặc định false. Dùng biến môi trường của tiến trình hoặc Spring property; script
`backend/run-local.ps1` legacy chỉ hỗ trợ mock, không dùng để nạp cấu hình rag này.

[ApiRequestFilter](../../team3_fullstack/backend/src/main/java/com/legalai/backend/common/web/ApiRequestFilter.java)
tự cấp X-Request-ID cho mỗi public request. Runner lấy trace từ response header và
ghép với clientRequestId của lượt hỏi. Không đòi gateway echo trace client gửi vào.
Backend vẫn gọi AI qua AiClient và chuyển trace theo interface nội bộ hiện hành.

[TurnTimings](../../team3_fullstack/backend/src/main/java/com/legalai/backend/chat/stream/TurnTimings.java)
và [StreamService](../../team3_fullstack/backend/src/main/java/com/legalai/backend/chat/stream/StreamService.java)
ghi các pha bằng System.nanoTime:

| Pha | Ranh giới |
| --- | --- |
| backend_init | store.accept, gồm tiếp nhận/persistence của lượt |
| ai_service | AiClient.query và validation response |
| db_persist | Ghi complete hoặc fail; cộng các lần ghi liên quan |
| stream_finish | Gửi meta/delta/terminal và finish; cộng các đoạn gửi, không đếm chờ AI |
| total_ms | Từ trước accept đến sau finish; phần chênh gồm queue/scheduling/overhead |

JSON gồm kind, trace_id, client_request_id, outcome, upstream_origin, phases_ms,
total_ms, transport_connected. Outcome phân biệt completed/failed/replayed/discarded;
pha chưa chạy là null, không là0. Dòng CHAT_LATENCY không chứa question/answer/citation/credential.
Origin bỏ path/query/userinfo; telemetry lỗi không thay đổi kết quả nghiệp vụ.
Transport flag là trạng thái kết nối tại thời điểm finish, không chứng minh browser render.
Các dòng log khác vẫn theo cấu hình ứng dụng; helper chỉ xuất field whitelist của timing,
không đưa nguyên file stdout vào report hoặc repository.

## 3. Dataset, chế độ và báo cáo

Helper [latency_report.py](../../team3_fullstack/tools/latency_report.py) đọc UTF-8/NFC,
kiểm ID/câu hỏi và reuse validator/schema public. Mỗi request gửi body UTF-8 thật,
clientRequestId UUIDv4 mới; trace chỉ được xác định sau khi nhận header Backend.

- mock: fixture để kiểm công cụ; status MOCK_ONLY dù thời gian dưới ngưỡng.
- exploratory: số đo thăm dò, không thay Dev benchmark.
- live: cần Dev90 và split report từ bộ150 khớp hash/count/trạng thái; RAG ready và
  không đánh dấu mock; timing đủ, đúng trace/UUID/origin. Split report không tự xác nhận
  review pháp lý của dữ liệu.

Report JSON format_version1 giữ raw sample/outcome/error_code, warm-up, số lỗi,
phân vị nearest-rank p50/p90/p95/p99 theo giây và timing pha gốc theo ms.
Phân vị chính chỉ dùng mẫu thành công; lỗi vẫn trong mẫu số/tổng và được giữ riêng.
Không có mẫu thì phân vị null. Không log raw error body hoặc đường dẫn cá nhân.
Source hashes/head là checkout của runner, không tự chứng minh revision server/model
đã triển khai; môi trường/snapshot server cần được ghi trong bằng chứng bàn giao.

Ngưỡng API: p95 chat≤45s, article≤1s. `latency_api_pass` chỉ có thể true ở chế độ live
đủ điều kiện, không request/lookup lỗi và đạt hai ngưỡng. `viewer_ui_verified=false`
vì runner này không đo render UI. Replay/timing thiếu hoặc trùng không được coi là
pipeline mới. Output tạo độc quyền, không ghi đè hoặc sửa dataset nguồn.

## 4. Interface vận hành

CLI yêu cầu mode/dataset/output; hỗ trợ base-url, users1–5, warmup, timeout toàn lượt,
timing-log, split-report và rag-url. Chỉ nhận URL origin HTTP/HTTPS không credentials,
query hoặc fragment. Mỗi request có deadline toàn lượt kể cả stream chỉ heartbeat.
Nhập module helper không monkey patch. Entry point patch networking/queue của gevent,
giữ native thread locks và tắt auto-patch lần hai của Locust; LocalRunner dùng greenlet.

Exit0 là công cụ chạy đúng trong mode đã chọn; exit1 là lỗi request/timing/ngưỡng
(timing bắt buộc khi đã chỉ định log hoặc ở live); exit2 là thiếu điều kiện/cấu hình/output.
Exit0 với mock không là nghiệm thu live. Dependency riêng tại
[requirements-performance.txt](../../team3_fullstack/requirements-performance.txt).
