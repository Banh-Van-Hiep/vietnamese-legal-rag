# Biên bản kiểm chứng nhiệm vụ Team 3 — Tuần 6

**Ngày kiểm tra:**29/10/2026 (Asia/Saigon), thay kết quả tổng hợp28/10.
**Nguồn:** [ARCHITECTURE](../../../docs/ARCHITECTURE.md),
[CODING_CONVENTIONS](../../../docs/CODING_CONVENTIONS.md), [tasks](tasks.md).
**Source:** `26c4649478956fd588a7f2d165cccbb33ac2f541`; **develop đã fetch:** `eea5604251afd4d8605fed510d6bf4de31d629bb`.
Code Team3/Team2 HTTP/runtime/contracts liên quan không khác develop; không merge
worktree. Thay đổi tuần5 là dữ liệu và hồ sơ, không đổi implementation được kiểm tra.
[Hồ sơ chi tiết](vlra-t3-07-10-integration/spec.md),
[validation](vlra-t3-07-10-integration/validation.md).

## 1. Kết luận

**Tuần6 chưa đủ điều kiện nghiệm thu G3 dữ liệu thật.** Phần adapter/mapping,
persistence/history và UI đã đạt kiểm chứng độc lập với mock. Hai phụ thuộc thật còn
thiếu: runtime chưa có đường dẫn index hợp lệ và app Team2 chưa có route đọc Điều luật.
Không có lỗi test mới ở code Team3 trong các suite đã chạy; không tự chốt toàn bộ
07/08 bằng kết quả mock. Không sửa app Team1/2, schema, corpus hoặc cấu hình shared.

## 2. Expected / Actual theo task

| Task | Expected / DoD | Actual29/10 | Kết luận |
| --- | --- | --- | --- |
| VLRA-T3-07 | Java gọi FastAPI thật thành công; trace/timeouts/error mapping/không giữ DB tx | HttpAiClient7/7 và StreamHTTP12/12; source connect2s/wait≤50s, transaction kết thúc trước HTTP. Factory thật query503; qua Java meta→error SERVICE_UNAVAILABLE, lưu failed và replay503. | Adapter/xử lý lỗi đạt; còn chờ pipeline thật để nghiệm thu toàn task |
| VLRA-T3-08 | Citation/article map đủ trường, giữ ID/URL, proxy article đúng snapshot | Validator43/43 và HTTP tests/FE adapters đạt; Viewer E03/E06 mock đạt. Factory thật không có route article; upstream404 NOT_FOUND → Java502 UPSTREAM_CONTRACT_ERROR. | Mapping đạt; proxy dữ liệu thật còn chờ endpoint Team2 |
| VLRA-T3-09 | State/citations nhất quán PostgreSQL; history chỉ5 cặp answered/completed≤20000 code point | PostgreSQL16/16 và H2 16/16; chronological/whole pairs/rollback/terminal/replay đạt; E2E tiếp nối/reload đạt. Factory thật lỗi vẫn lưu completed/failed đúng. | Đủ điều kiện chốt kỹ thuật persistence/history |
| VLRA-T3-10 | URL từ meta, khóa pending, delta, render an toàn, insufficient không citation rỗng | FE72/72/build; E2E10/10 và0 exception. Parser unit kiểm UTF8/frame/error/timeout/abort; output HTML là text. | Đủ điều kiện chốt kỹ thuật UI trong phạm vi đã kiểm; không chứng minh chất lượng live |

Không bắt buộc thêm class/libraries trùng ví dụ: JDK HttpClient, DTO/controller và
ChatStore đã thực hiện trách nhiệm. Không phát sinh thay đổi công nghệ/API.

## 3. Readiness thật và trách nhiệm bàn giao

| Kiểm tra app factory thật | Kết quả |
| --- | --- |
| GET /internal/v1/health |200 up |
| GET /internal/v1/ready |503 LLM_UNAVAILABLE |
| POST /internal/v1/query |503 LLM_UNAVAILABLE, không có answer giả |
| Runtime config |RAG_BM25_INDEX/RAG_DENSE_INDEX chưa cấu hình; startup ConfigError |
| OpenAPI |Chỉ health/ready/query; thiếu endpoint article |
| GET article với ID snapshot thật |404 NOT_FOUND |
| Java gọi query factory thật |SSE200 meta→error SERVICE_UNAVAILABLE; DB user completed/assistant failed; replay503 |
| Java proxy article factory thật |502 UPSTREAM_CONTRACT_ERROR, không thay phiên bản hoặc tạo nguyên văn |

Mã LLM_UNAVAILABLE không đủ để kết luận thiếu/sai API key: startup dừng ở cấu hình
index trước khi kiểm model/provider. Probe bật offline guard, không tải model/index.
Cần Team1 bàn giao index/snapshot tương thích; Team2 cấu hình runtime và phục vụ
article theo hợp đồng. Đây là khoảng thiếu bàn giao, không phải xung đột yêu cầu.
Không tự triển khai bên họ. Golden đã chuyển Team2 kiểm chứng, không lẫn vào audit này.

## 4. Kiểm thử và evidence

- Maven Wrapper package: **94/94**,0 fail/error/skip;5 suite liên quan, bao gồm16 ca
  PostgreSQL thật và16 H2. Không cộng các nhóm con vào tổng94.
- Frontend: **72/72**, tsc/Vite build PASS.
- Browser E2E: **10/10**,0 uncaught exception, React→Java→PostgreSQL→FastAPI HTTP mock.
- Factory probe và Java gọi factory thật đã chạy riêng; kết quả503/404 là bằng chứng
  blocker G3, không ghi thành ca trả lời thành công hoặc fallback mock.

Lệnh/setup tại [quickstart](vlra-t3-07-10-integration/quickstart.md).
DB test legal_rag_week6_20261029 ở127.0.0.1:55442; Java18043/FE15173/Python18044,
factory probe18049/CDP19242. Python venv riêng, JDK25, Node24.21, PostgreSQL18.
Không thay .env, không in credential/danh tính. Không đo mobile/latency/token-stream
provider hoặc chờ55s manual lần này; không lấy kết quả cũ gán PASS mới.

Evidence ignored: backend/target/week6-acceptance-20261029/ có summary.json,
backend-package.log, frontend-unit.json/log, frontend-build.log, e2e/results.json,
ảnh browser và logs, live-readiness.json, live-through-java.json/stream.txt,
live-runtime.log, preservation.json, process-cleanup.json.
Đã dừng đúng tiến trình/cluster test audit mở;6 cổng đã đóng, không đụng dịch vụ thật.

## 5. Điều kiện khép tuần6

1. Team1/2 bàn giao index BM25/Dense cùng phiên bản/chunk IDs, article snapshot và
   cấu hình runtime/model/provider dùng được; ready200.
2. Team2 bổ sung endpoint article đúng6 field và mã404 DOCUMENT_NOT_FOUND/
   ARTICLE_NOT_FOUND; không dùng NOT_FOUND cho lookup cần phân biệt này.
3. Team3 chạy lại query thật qua Java/UI→Answer+Citation, click Viewer đúng document/
   article/version, kiểm nối tiếp/history và lỗi liên quan. Sau đó mới nghiệm thu G3.

W6-06 trong [tasks kiểm chứng](vlra-t3-07-10-integration/tasks.md) còn mở.
Không tự sửa Jira, xác nhận nhóm đã duyệt gate, hoặc báo tuần6 hoàn tất khi thiếu
luồng thật. Phần độc lập09/10 có thể chốt kỹ thuật theo bằng chứng trên.
