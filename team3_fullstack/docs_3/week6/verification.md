# Biên bản kiểm chứng nhiệm vụ Team 3 — Tuần 6

**Ngày kiểm tra:** 28/10/2026 (Asia/Saigon).
**Căn cứ hiện hành:** [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) (đặc tả chính),
[CODING_CONVENTIONS.md](../../../docs/CODING_CONVENTIONS.md) (quy chuẩn/DoD),
[tasks.md](tasks.md) (phân rã nhiệm vụ tuần). Jira phục vụ theo dõi công việc.
**Source kiểm tra:** `62c3556bab16e106e2e6ff29b0280a96fb738146` cùng thay đổi tài liệu chưa commit; không sửa code nghiệp vụ/test hoặc dataset để làm kết quả đạt.
**Môi trường:** Windows, JDK25/Spring Boot4.1.1, Maven Wrapper3.9.16, Node24.21,
Python3.12 trong venv kiểm thử riêng, PostgreSQL18 database riêng, Edge headless profile riêng.
**Phạm vi kết luận:** kiểm chứng kỹ thuật; chưa thay phê duyệt nhóm/gate hoặc trạng thái Jira.

**Đối chiếu nguồn ngày 28/10:** ARCHITECTURE §3/§6/§7/§8.1 và CODING_CONVENTIONS §2/§3.3/§4.2/§7 cho HTTP, mapping, persistence, lỗi, timeout và nghiệm thu. G3 là mốc kế hoạch tuần6; test mock chưa chứng minh dữ liệu thật.
Kết luận dựa trên baseline/quy chuẩn/task hiện hành, không loại tiêu chí chỉ vì Jira cũ
chưa ghi. Lượt cập nhật nguồn này không chạy lại build/test hoặc thay số liệu đã đo.

## 1. Kết luận

**Cơ chế tích hợp HTTP, mapping, persistence và UI được kiểm chứng với mock; chưa chốt G3/real data.**
Team2 **đã có app HTTP thật** (`team2_rag.api:create_app`), không còn kết luận “chưa có endpoint”.
App mặc định chạy health 200 nhưng ready/query 503 trong môi trường kiểm tra do thiếu cấu hình index.

## 2. Đối chiếu từng task

| Task | Expected / DoD | Actual và căn cứ | Kết luận |
| --- | --- | --- | --- |
| VLRA-T3-07 | Gọi FastAPI, trace, timeout≤2/50s, map502/503/504, không giữ DB tx khi chờ | `HttpAiClientTests`7/7, StreamApiTests12/12, E2E 10/10; header trace và query/history được kiểm. `StreamService` kết thúc store.accept trước khi worker gọi AI; JDK HttpClient connect2s/wait≤50s. HTTP app live ready 503, chưa gọi pipeline thật thành công. | Đạt adapter/mock, chưa đạt live |
| VLRA-T3-08 | Citation/Article map đủ trường, giữ IDs/URL và unit test đạt | `StreamDtos.PublicCitation.from`/`Complete.from`, `PublicDocumentController`/`DocumentService` đảm nhiệm mapping (không có class tên AiContractMapper). Tests kiểm9 field citation,6 field article, nullable và sai phiên bản; FE adapters cũng kiểm shape/IDs. | Đạt chức năng mapping |
| VLRA-T3-09 | Pending→completed/failed atomic, history chỉ5 cặp answered/completed |16 ca PostgreSQL và16 ca H2 đạt: atomic citation/snapshot, failed/insufficient không vào history, chronological/max5 cặp/20000 code point, terminal không ghi đè, lock/rollback. E2E lưu4 tin nhắn khi hỏi tiếp, reload không gọi lại AI. | Đạt persistence/history |
| VLRA-T3-10 | Bind URL từ meta, disable pending, render an toàn, thiếu căn cứ riêng | FE 72/72 và E2E 10/10; parser UTF8/frame split, errors/timeout/abort; format giữ HTML như text, Viewer xác minh IDs. E07 không có citation khi thiếu căn cứ; UI360/768 và mạng3G kiểm chức năng đạt. | Đạt kỹ thuật UI/mock |

Không coi khác tên class hoặc JDK HttpClient thay RestClient/WebClient là thay wire contract.
Nếu nhóm yêu cầu bắt buộc tên/libraries trong phần thiết kế thì cần thống nhất riêng;
lượt này không refactor implementation chỉ để khớp ví dụ.

## 3. Readiness live và giới hạn

Chạy app factory mặc định, không inject fake pipeline, không gọi provider ngoài:

```powershell
python -m uvicorn team2_rag.api:create_app --factory --host 127.0.0.1 --port 18049
```

- `GET /internal/v1/health`: **200**, status up.
- `GET /internal/v1/ready`: **503**, LLM_UNAVAILABLE.
- `POST /internal/v1/query` với question/history hợp lệ: **503**, LLM_UNAVAILABLE, không answer giả.
- Log startup ghi `ConfigError`; kiểm tra chỉ tên key/trạng thái không lộ secret:
  `RAG_BM25_INDEX` và `RAG_DENSE_INDEX` **chưa cấu hình** trong process/root dotenv được runtime đọc.
- Chưa xác minh index/snapshot/article store/model/provider cho live; không tự tạo hoặc tải
  model/index lớn, sửa pipeline Team1/2 hoặc sử dụng mock để nhận nghiệm thu real data.

## 4. Kiểm thử, evidence và việc tiếp tục

Maven package 125/125 và FE 72/72 + build đạt; G2 E2E 10/10 đạt. Lệnh/setup ở
[tuần5 §3](../week5/verification.md#3-lệnh-chạy-lại).
Evidence ignored: `backend/target/week-acceptance-20261028/{live-readiness.json,live-startup-error.log,inventory.json,backend-package.log}`,
`e2e/results.json` và surefire reports. Không có lỗi test được che bằng đổi schema/dataset.

Cần Team1/2 bàn giao index tương thích phiên bản, article snapshot và cấu hình runtime/model/provider;
sau đó kiểm ready 200 và query thật → Java → UI. Chỉ khi có bằng chứng dữ liệu thật mới chốt phần G3.
