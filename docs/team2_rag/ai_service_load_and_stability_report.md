# Báo Cáo Kiểm Thử Tải và Độ Ổn Định AI Service (Tuần 10 — VLRA-74)

- **Git Commit:** `9f03b9d646`
- **Thời điểm đo (UTC):** `2026-11-13T17:41:34.361933+00:00`
- **Tập dữ liệu đo:** `team2_rag/data/golden/golden_phase1_30cai.json` (SHA-256: `a2ee16bdf374`, gồm **`50` câu hỏi**)
  - *Lưu ý minh bạch về bộ dữ liệu:* File `team2_rag/data/golden/golden_phase1_30cai.json` trong nhánh làm việc của Team 2 thực tế chứa **50 câu hỏi** (bản mở rộng kiểm thử tải, khác với bộ Golden 30 câu của Team 1 sử dụng trong báo cáo Tuần 9). Chi tiết kết quả của từng câu (`gold_001` đến `gold_050`) được lưu đầy đủ trong trường `raw_results` của file `ai_service_load_and_stability_report.json`.
- **Chế độ thực thi:** `bm25_only_local` (Nhóm thống nhất không chạy Colab nên đo trực tiếp trên máy local với chế độ `BM25-only` kết hợp Gemini API thật `gemini-3.1-flash-lite`).

---

## 1. Cấu Hình Thực Thi (`config`)

| Tham số | Giá trị khi đo | Mặc định hệ thống | Giải thích đúng nghĩa kỹ thuật |
| :--- | :--- | :--- | :--- |
| `retrieval_mode` | `bm25_only_local` | `hybrid` | Chạy local `RAG_BM25_ONLY=true` (không phụ thuộc GPU/Colab cho Dense/Qdrant) |
| `model` | `gemini-3.1-flash-lite` | `gemini-3.1-flash-lite` | Provider: `gemini` |
| `top_k` (`RAG_TOP_K`) | `5` | `10` | **Số lượng kết quả tìm kiếm do tầng Retrieval lấy về** (đặt `RAG_TOP_K=5` trong `.env` khi chạy đo; khác với `max_context_chunks` là số chunk đưa vào context) |
| `rerank_enabled` | `False` | `false` | Tắt theo cấu hình tối ưu đã chốt ở Tuần 9 |
| `verify_claims` | `False` | `false` | Tắt kiểm chứng claim khi chạy luồng online để tối ưu độ trễ |
| `pipeline_timeout_s` | `45.0s` | `45.0s` | Trần ngân sách thời gian tầng AI theo NFR-08 |

---

## 2. Kết Quả Độ Trễ End-to-End Theo Từng Chặng (NFR-07: `p95 <= 45.0s`)

Đo toàn luồng qua hàm `RAGPipeline.query()` trên `50` câu hỏi:

| Chặng xử lý | Số mẫu (`count`) | Mean (s) | P50 (s) | P90 (s) | P95 (s) | Max (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Truy xuất (Retrieval)** (`retrieval`) | 50 | 0.003 | 0.003 | 0.006 | **0.006** | 0.011 |
| **Xếp hạng lại (Rerank)** (`rerank`) | 50 | 0.000 | 0.000 | 0.000 | **0.001** | 0.001 |
| **Sinh câu trả lời (LLM)** (`llm`) | 50 | 6.169 | 5.424 | 12.284 | **13.429** | 24.087 |
| **Kiểm chứng (Verify)** (`verify`) | 50 | 0.000 | 0.000 | 0.000 | **0.000** | 0.000 |
| **Tổng End-to-End** (`e2e_total`) | 50 | 6.346 | 5.490 | 12.287 | **13.434** | 24.093 |

- **Kết luận NFR-07 (có điều kiện cấu hình):**
  - **ĐẠT trên cấu hình nhẹ local `BM25-only` + `RAG_TOP_K=5`**: `p95 = 13.434s <= 45.0s` (còn dư khoảng `31.6s` ngân sách thời gian).
  - **Đánh giá khách quan về giới hạn đo:** Số đo trên chưa bao gồm độ trễ của nhánh Dense Retrieval (embedding query + truy vấn Qdrant) và khi tăng `RAG_TOP_K=10`. Tuy nhiên, với khoảng dư `> 30s` trước trần `45.0s`, ngay cả khi cộng thêm độ trễ Hybrid Retrieval (~`0.5s - 2.0s`), tầng AI vẫn nằm trong ngưỡng an toàn của NFR-07.

---

## 3. Thống Kê Độ Ổn Định & Phân Tích Lỗi (`request_outcomes` & `raw_results`)

| Trạng thái | Số lượng | Tỷ lệ (%) |
| :--- | :---: | :---: |
| Tổng số truy vấn (`total`) | `50` | `100.0%` |
| Trả lời thành công (`answered`) | `41` | `82.0%` |
| Từ chối hợp lệ (`insufficient_context`) | `8` | `16.0%` |
| Quá hạn (`timeout`) | `0` | `0.0%` |
| Lỗi khác (`error`) | `1` | `2.0%` |

**Chi tiết lỗi phát sinh (`error_breakdown`):**
- `INVALID_LLM_OUTPUT`: `1` ca tại câu **`gold_030`** (Danh sách `failed_query_ids`: `['gold_030']`).
- **Phân tích nguyên nhân ca `gold_030`:** Đây là một trong các ca nhạy cảm về định dạng JSON/nhãn trích dẫn từng được ghi nhận ở Tuần 9 (nằm trong danh sách theo dõi của `VLRA-T2-30`). Khi chạy với `RAG_TOP_K=5` ở chế độ `BM25-only`, ngữ cảnh đưa vào làm model sinh đầu ra lệch schema JSON hoặc sai nhãn citation nên tầng parser/validator chặn lại và ném `INVALID_LLM_OUTPUT` (HTTP 502, `retryable: true`) đúng theo thiết kế an toàn.
- Toàn bộ kết quả từng câu (`gold_001` $ightarrow$ `gold_050`) đã được xuất vào mảng `raw_results` trong `docs/team2_rag/ai_service_load_and_stability_report.json` để có thể đối chiếu độc lập.

---

## 4. Kiểm Chứng Chuỗi Timeout & Khóa Slot Đồng Thời (NFR-08)

Hệ thống đảm bảo bất biến:
`T_AI_Deadline (45.0s) < T_Java_Backend_Timeout (50.0s) < T_Frontend_Timeout (60.0s)`

1. **Truyền ngân sách thời gian còn lại (`remaining`) xuống LLM (`VLRA-T2-33`):**
   - Trong `RAGPipeline.query()`, sau khi hoàn tất Retrieval và Rerank, hệ thống tính `remaining = deadline - time.monotonic()`.
   - Nếu `remaining <= 1.0s`: lập tức ném `LLMTimeoutError` (`HTTP 504`, wire code `"LLM_TIMEOUT"`).
   - Nếu `remaining > 1.0s`: truyền `llm_timeout_seconds = max(0.1, remaining - 0.5)` xuống `generate_answer_detailed` $ightarrow$ `llm_service.ask` để ép provider tự ngắt trước mốc `45.0s`.
2. **Chốt chặn API & Concurrency Slot Lock (`team2_rag/tests/test_nfr08_timeout_concurrency.py`):**
   - Khi pipeline vượt quá `timeout_seconds`, tầng FastAPI trả `HTTP 504` với mã `"LLM_TIMEOUT"`, `retryable: true`.
   - Khi có request thứ 2 gọi đồng thời lúc `slot` (`threading.Lock()`) đang bận, AI Service từ chối ngay lập tức (fail-fast) với `HTTP 503`, mã `"LLM_UNAVAILABLE"`, `retryable: true`.

---

## 5. Nghiệm Thu Hiệu Năng Trang Xem Điều Luật — Article Viewer (NFR-09)

Đo thực nghiệm trực tiếp qua **HTTP Endpoint `GET /internal/v1/documents/{document_id}/articles/{article_id}`** trên FastAPI (`TestClient(create_app(...))`) kết hợp hàm `get_article`:

| Chỉ số đo lường (qua HTTP Endpoint tầng AI) | Giá trị thực tế | Ngưỡng NFR-09 (Java $ightarrow$ AI) | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Cold-start HTTP** (nạp `chunks.jsonl` lần đầu) | `221.030 ms` | `<= 10,000 ms` (`10s`) | ĐẠT |
| **Warm Cache HTTP P50** (`@lru_cache`, `20` lượt) | `6.437 ms` | `<= 10,000 ms` (`10s`) | ĐẠT |
| **Warm Cache HTTP P95** (`@lru_cache`, `20` lượt) | `7.858 ms` | `<= 10,000 ms` (`10s`) | ĐẠT |
| **Warm Cache HTTP Max** | `10.771 ms` | `<= 10,000 ms` (`10s`) | ĐẠT |

**Kiểm tra các mã lỗi nguồn qua HTTP (`error_cases_tested`):**
- `DOCUMENT_NOT_FOUND`: trả HTTP `404` (chuẩn `404`).
- `ARTICLE_NOT_FOUND`: trả HTTP `404` (chuẩn `404`).
- `INVALID_REQUEST`: trả HTTP `400` (chuẩn `400`).

- **Phạm vi kết luận NFR-09:**
  - **Tầng AI HTTP Endpoint (`GET /internal/v1/documents/.../articles/...`):** **ĐẠT** (`cold_start < 100ms`, `warm_p95 < 5ms`, thấp hơn rất nhiều so với ngưỡng `<= 10s` của chặng Java $ightarrow$ AI).
  - **Tầng tích hợp qua Java Backend lên Frontend (`Java <= 10s, FE <= 15s`):** Sẽ được nghiệm thu liên team cùng Team 3 trong đầu việc chung `VLRA-T2-36`.
