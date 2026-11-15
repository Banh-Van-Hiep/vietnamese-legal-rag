# AGENTS.md — Vietnamese Legal RAG Harness Router

Tài liệu này là điểm vào trung tâm (Single Entrypoint) theo nguyên lý **Progressive Disclosure** của Harness Engineering. Mọi lập trình viên và AI Coding Agent phải đọc file này trước khi sửa code.

---

## 1. Bản Đồ Kiến Trúc & Ranh Giới Phân Hệ (Module Boundaries)

Dự án được chia thành 3 phân hệ độc lập giao tiếp qua hợp đồng dữ liệu nghiêm ngặt:

| Phân hệ | Thư mục nguồn | Tài liệu thiết kế | Quản lý Task theo tuần | Chỉ dẫn cục bộ |
| :--- | :--- | :--- | :--- | :--- |
| **Team 1 (Data & Retrieval)** | `team1_data/` | `docs/team1_data/` | `team1_data/docs_1/` | `team1_data/AGENTS.md` |
| **Team 2 (RAG & LLM Engine)** | `team2_rag/` | `docs/team2_rag/` | `team2_rag/docs_2/` | `team2_rag/AGENTS.md` |
| **Team 3 (Fullstack & System)** | `team3_fullstack/` | `docs/team3_fullstack/` | `team3_fullstack/docs_3/` | `team3_fullstack/AGENTS.md` |
| **Contracts (SSOT Schemas)** | `contracts/v0.1/` | `docs/ARCHITECTURE.md` | - | Xem mục 2 & 3 bên dưới |

- **Quy tắc tài liệu bắt buộc:** Thư mục gốc `docs/` chỉ chứa `ARCHITECTURE.md` và `CODING_CONVENTIONS.md`. Mọi báo cáo thiết kế/benchmark của team nào phải đặt trong `docs/teamX_*/`, và kế hoạch công việc hàng tuần (`weekX/tasks.md`) phải đặt trong `teamX_*/docs_X/`.

---

## 2. Các Bất Biến Hệ Thống (System Invariants — CẤM VI PHẠM)

1. **Bất biến Trung thực Trích dẫn (No Citation Fabrication/Auto-fixing):**
   - Mọi câu trả lời có `status == "answered"` bắt buộc phải có marker trích dẫn hợp lệ dạng `[C1]`, `[C2]`... liên tục từ `C1` và khớp 1–1 với mảng `citations`.
   - Nếu LLM sinh nhãn trích dẫn sai hoặc nằm ngoài context, hệ thống phải từ chối (`insufficient_context`) hoặc ném lỗi `CITATION_INVALID` / `INVALID_LLM_OUTPUT`. Tuyệt đối không dùng regex/code để tự ý sửa, gọt hoặc đoán lại citation của LLM.
2. **Bất biến Chuỗi Timeout Phân Tầng (NFR-08):**
   - `T_AI_Deadline (45.0s) < T_Java_Backend_Timeout (50.0s) < T_Frontend_Timeout (60.0s)`.
   - Tầng Pipeline (`team2_rag/pipeline.py`) phải truyền ngân sách thời gian còn lại `remaining = deadline - time.monotonic()` xuống bước gọi LLM (`llm_timeout_seconds = max(0.1, remaining - 0.5)`). Nếu `remaining <= 1.0s` trước khi gọi LLM, phải ngắt sớm với `LLMTimeoutError` (`HTTP 504`, wire code `"LLM_TIMEOUT"`).
3. **Bất biến Khóa Đồng Thời (Concurrency Slot Lock):**
   - AI Service (`team2_rag/api/app.py`) sử dụng `slot = threading.Lock()` non-blocking, chỉ cho phép 1 suy luận LLM tại một thời điểm. Request thứ 2 gọi đồng thời khi `slot` đang bận phải lập tức nhận `HTTP 503` (`wire code: "LLM_UNAVAILABLE"`, `retryable: true`).
4. **Bất biến Độ Trễ Truy Vấn & Article Viewer (NFR-07 & NFR-09):**
   - **NFR-07:** Độ trễ End-to-End qua `RAGPipeline.query` đạt `p95 <= 45.0s`.
   - **NFR-09:** Endpoint tra cứu Điều luật `GET /internal/v1/documents/{document_id}/articles/{article_id}` phản hồi `<= 10.0s` (Java -> AI) và `<= 15.0s` (FE Viewer), trả đúng mã lỗi `404` (`DOCUMENT_NOT_FOUND`, `ARTICLE_NOT_FOUND`) và `400` (`INVALID_REQUEST`).
5. **Bất biến Tính Toàn Vẹn Thực Nghiệm (Benchmark Integrity):**
   - Mọi báo cáo benchmark JSON phải lưu mảng `raw_results` của từng câu hỏi thực tế. Các chỉ số tổng hợp (`request_outcomes`, `stage_latency`) phải được tính toán trực tiếp từ `raw_results`, tuyệt đối không ghi cứng (hardcode) hoặc dùng số liệu giả lập.

---

## 3. Cổng Kiểm Chứng Thực Thi (Executable Verification Gates)

Trước khi mở Pull Request vào nhánh `develop`, bắt buộc phải chạy cổng kiểm chứng tự động và đạt trạng thái **PASSED 100%**:

```powershell
# Chạy toàn bộ 4 cổng kiểm chứng (Hygiene + Contracts + Report Integrity + Unit Tests)
.venv\Scripts\python.exe scripts/harness_verify.py

# Chạy bộ test chuyên biệt của Team 2 (RAG & LLM)
.venv\Scripts\python.exe -m pytest team2_rag/tests -q

# Chạy bộ test tích hợp & hợp đồng ở thư mục gốc
.venv\Scripts\python.exe -m pytest tests -q
```
