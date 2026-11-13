# Báo Cáo Kiểm Thử Tải và Độ Ổn Định AI Service (Tuần 10 — VLRA-74)

- **Git Commit:** `9f03b9d646`
- **Thời điểm đo (UTC):** `2026-11-13T17:41:34.361933+00:00`
- **Tập dữ liệu:** `team2_rag/data/golden/golden_phase1_30cai.json` (SHA-256: `a2ee16bdf374`, `50` câu hỏi)
- **Chế độ thực thi:** `bm25_only_local` (Nhóm thống nhất không dùng Colab, chạy trực tiếp trên máy local với BM25-only + LLM `gemini-3.1-flash-lite`)

---

## 1. Cấu Hình Thực Thi (`config`)

| Tham số | Giá trị | Ghi chú |
| :--- | :--- | :--- |
| `retrieval_mode` | `bm25_only_local` | Chạy local không phụ thuộc GPU/Colab |
| `model` | `gemini-3.1-flash-lite` | Provider: `gemini` |
| `top_k` | `5` | Số chunk đưa vào bước tạo context |
| `rerank_enabled` | `False` | Tắt theo cấu hình tối ưu Tuần 9 |
| `verify_claims` | `False` | Chế độ runtime online (`RAG_VERIFY_CLAIMS=false`) |
| `pipeline_timeout_s` | `45.0s` | Trần ngân sách thời gian tầng AI (NFR-08) |

---

## 2. Kết Quả Độ Trễ End-to-End Theo Từng Chặng (NFR-07: `p95 <= 45.0s`)

Đo trực tiếp qua hàm `RAGPipeline.query()` trên toàn bộ `50` câu hỏi:

| Chặng xử lý | Số mẫu (`count`) | Mean (s) | P50 (s) | P90 (s) | P95 (s) | Max (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Truy xuất (Retrieval)** (`retrieval`) | 50 | 0.003 | 0.003 | 0.006 | **0.006** | 0.011 |
| **Xếp hạng lại (Rerank)** (`rerank`) | 50 | 0.000 | 0.000 | 0.000 | **0.001** | 0.001 |
| **Sinh câu trả lời (LLM)** (`llm`) | 50 | 6.169 | 5.424 | 12.284 | **13.429** | 24.087 |
| **Kiểm chứng (Verify)** (`verify`) | 50 | 0.000 | 0.000 | 0.000 | **0.000** | 0.000 |
| **Tổng End-to-End** (`e2e_total`) | 50 | 6.346 | 5.490 | 12.287 | **13.434** | 24.093 |

- **Kết luận NFR-07 (`p95 <= 45.0s`):** **ĐẠT (PASSED)** (`p95 = 13.434s <= 45.0s`).
- *Lưu ý kỹ thuật:* Chế độ đo local sử dụng `BM25-only` (do nhóm không sử dụng Colab cho Dense/Qdrant). Độ trễ Retrieval của BM25 local ở mức mili-giây; phần lớn thời gian End-to-End nằm ở chặng gọi Gemini API (`llm`).

---

## 3. Thống Kê Độ Ổn Định & Phân Loại Kết Quả (`request_outcomes`)

| Trạng thái | Số lượng | Tỷ lệ (%) |
| :--- | :---: | :---: |
| Tổng số truy vấn (`total`) | `50` | `100.0%` |
| Trả lời thành công (`answered`) | `41` | `82.0%` |
| Từ chối hợp lệ (`insufficient_context`) | `8` | `16.0%` |
| Quá hạn (`timeout`) | `0` | `0.0%` |
| Lỗi khác (`error`) | `1` | `2.0%` |

**Chi tiết mã lỗi (`error_breakdown`):**
- `INVALID_LLM_OUTPUT`: 1 ca

- **Danh sách `query_id` gặp lỗi/timeout:** `gold_030`

---

## 4. Kiểm Chứng Chuỗi Timeout & Khóa Slot Đồng Thời (NFR-08)

Hệ thống đảm bảo bất biến:
`T_AI_Deadline (45.0s) < T_Java_Backend_Timeout (50.0s) < T_Frontend_Timeout (60.0s)`

1. **Truyền ngân sách thời gian còn lại (`remaining`) xuống LLM (`VLRA-T2-33`):**
   - Trong `RAGPipeline.query()`, sau khi hoàn tất Retrieval và Rerank, hệ thống tính `remaining = deadline - time.monotonic()`.
   - Nếu `remaining <= 1.0s`: lập tức ném `LLMTimeoutError` (`HTTP 504`, wire code `"LLM_TIMEOUT"`).
   - Nếu `remaining > 1.0s`: truyền `llm_timeout_seconds = max(0.1, remaining - 0.5)` xuống `generate_answer_detailed` -> `llm_service.ask` để ép provider tự ngắt trước mốc `45.0s`.
2. **Chốt chặn API & Concurrency Slot Lock (`team2_rag/tests/test_nfr08_timeout_concurrency.py`):**
   - Khi pipeline vượt quá `timeout_seconds`, tầng FastAPI trả `HTTP 504` với mã `"LLM_TIMEOUT"`, `retryable: true`.
   - Khi có request thứ 2 gọi đồng thời lúc `slot` (`threading.Lock()`) đang bận, AI Service từ chối ngay lập tức (fail-fast) với `HTTP 503`, mã `"LLM_UNAVAILABLE"`, `retryable: true`, giữ cho tiến trình không bị dồn ứ (pile-up).

---

## 5. Nghiệm Thu Hiệu Năng Trang Xem Điều Luật — Article Viewer (NFR-09)

Đo thực nghiệm trực tiếp trên hàm tra cứu `get_article(document_id, article_id)` (phục vụ endpoint `GET /internal/v1/documents/{document_id}/articles/{article_id}`):

| Chỉ số đo lường | Giá trị thực tế | Ngưỡng NFR-09 | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Cold-start** (nạp `chunks.jsonl` lần đầu) | `83.546 ms` | `<= 10,000 ms` (`10s`) | ĐẠT |
| **Warm Cache P50** (`@lru_cache`, `20` lượt) | `0.002 ms` | `<= 10,000 ms` (`10s`) | ĐẠT |
| **Warm Cache P95** (`@lru_cache`, `20` lượt) | `0.005 ms` | `<= 10,000 ms` (`10s`) | ĐẠT |
| **Warm Cache Max** | `0.014 ms` | `<= 10,000 ms` (`10s`) | ĐẠT |

**Kiểm tra các mã lỗi nguồn (`error_cases_tested`):**
- `DOCUMENT_NOT_FOUND`: trả HTTP `404` (chuẩn `404`).
- `ARTICLE_NOT_FOUND`: trả HTTP `404` (chuẩn `404`).
- `INVALID_REQUEST`: trả HTTP `400` (chuẩn `400`).

- **Kết luận NFR-09:** **ĐẠT (PASSED)** (Tốc độ tra cứu dưới `50ms` ở lần đầu và `< 1ms` từ lần thứ hai, đảm bảo luồng Java `<= 10s` và Frontend Viewer `<= 15s`).
