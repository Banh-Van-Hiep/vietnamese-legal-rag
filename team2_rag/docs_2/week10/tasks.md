# Kế Hoạch Triển Khai Kỹ Thuật (Spec-Driven) — Tuần 10
## Phân Hệ: RAG & LLM (Team 2)

Số liệu và hiện trạng đối chiếu từ nhánh `feature/team2-rag` tại commit `d1b32c3266` / `bfa89a9` và báo cáo Benchmark Tuần 9 (08/11/2026).

---

## 1. Thông Tin Chung & Mục Tiêu
- **Giai đoạn:** Tuần 10 (Tuần 7 cũ + 3), ứng với **VLRA Sprint 7** trên Jira, từ 09/11 đến 16/11/2026.
- **Hạn:** cả hai ticket `VLRA-73` và `VLRA-74` đến hạn 16/11/2026.
- **Mục tiêu đặc tả:**
  - **Ổn định response & mã lỗi AI Service (`VLRA-73`):** Khóa chặt bảng ánh xạ lỗi nội bộ Python $\rightarrow$ Java wire code (`api/handlers.py`, `articles.py`); xử lý các ca lỗi định dạng JSON/Citation còn sót ở Tuần 9 (`gold_003`, `gold_008`, `gold_022`, `gold_030`); đồng bộ `runtime.py` (không nạp `BGEScorer` khi `RAG_RERANK=false`, bổ sung cổng cấu hình `RAG_VERIFY_CLAIMS`).
  - **Đặc tả Markdown & Hướng dẫn tích hợp UI (`VLRA-73`):** Định nghĩa quy chuẩn sinh Markdown trong `answer` (danh sách, bảng biểu, vị trí marker `[C1]`, `[C2]`), mở rộng `api/mock_app.py` với các fixture tất định và bàn giao `docs/team2_rag/ui-integration-guide.md` cho Team 3.
  - **Đặc tả & Đo lường NFR-07, NFR-08, NFR-09 (`VLRA-74`):**
    - **NFR-07:** Độ trễ truy vấn End-to-End qua `RAGPipeline.query` / `POST /internal/v1/query` đạt `p95 <= 45.0s`.
    - **NFR-08:** Chuỗi timeout phân tầng bất biến: AI deadline `45.0s` $\rightarrow$ Backend Java chờ AI `50.0s` $\rightarrow$ Frontend timeout `60.0s`.
    - **NFR-09:** Phối hợp Team 1 & Team 3 nghiệm thu luồng mở Điều luật từ citation (`GET /internal/v1/documents/{document_id}/articles/{article_id}`): Viewer Java $\rightarrow$ AI `<= 10.0s`, FE `<= 15.0s`, kiểm tra cả lỗi nguồn và hiển thị bảng biểu/chú thích sửa đổi.

### Hiện trạng trên code (trước khi làm Tuần 10; trạng thái cập nhật ở mục 8)
- `api/app.py` đặt `timeout_seconds=45` qua `asyncio.wait_for(asyncio.shield(work), timeout=timeout_seconds)` và dùng `slot = threading.Lock()` (non-blocking) chỉ cho phép 1 inference tại một thời điểm. Khi `slot` đang bận, request mới nhận ngay HTTP 503 (`LLM_UNAVAILABLE`, `retryable=True`).
- `pipeline.py` kiểm tra `deadline = start_time + self.pipeline_timeout` (`45.0s`) giữa các bước, nhưng bước `generate_answer_detailed` vẫn dùng `settings.timeout_seconds` cố định (`30.0s`) chứ chưa co giãn theo thời gian còn lại `remaining = deadline - time.monotonic()`.
- `runtime.py` (dòng 96–100) luôn khởi tạo `BGEScorer(truncate=truncate)` và chạy warm-up ngay cả khi `RAG_RERANK=false`. Đồng thời `build_runtime()` chưa truyền `verifier` vào `RAGPipeline`.
- `api/mock_app.py` mới chỉ hỗ trợ 2 kịch bản `answered` (1 câu đơn giản) và `insufficient_context`, chưa có kịch bản Markdown phức tạp (danh sách + bảng biểu + đa trích dẫn `[C1]`, `[C2]`) và kịch bản giả lập lỗi để Team 3 chạy bộ test E2E các trạng thái UI đạt 100%.

---

## 2. Phân Rã Công Việc

Mã `VLRA-T2-NN` nối tiếp Tuần 9 (kết thúc ở `VLRA-T2-29`). Hai ticket Jira thuộc Sprint 7, hạn 16/11/2026, mỗi ticket 2 story points.

| Jira | Tên ticket | Epic | Mã nội bộ |
| :--- | :--- | :--- | :--- |
| **VLRA-73** | Ổn định response, mã lỗi AI Service và test hiển thị Markdown | `[EPIC 3] Core RAG & LLM Engine` | `VLRA-T2-30` đến `VLRA-T2-32` (Người 1) |
| **VLRA-74** | Đo lường hiệu năng End-to-End và cấu hình timeout (NFR-07, NFR-08) | `[EPIC 5] System Evaluation & Benchmark` | `VLRA-T2-33` đến `VLRA-T2-35` (Người 2) và `VLRA-T2-36` (Chung) |

### 2.1. Người 1: Ổn Định AI Service, Đặc Tả Markdown & UI Integration Guide (`VLRA-73`)

| Mã | Công việc | Tiêu chí hoàn thành (DoD) |
| :--- | :--- | :--- |
| **VLRA-T2-30** | Sửa `runtime.py`: chỉ nạp `BGEScorer` khi `RAG_RERANK=true`; thêm biến môi trường `RAG_VERIFY_CLAIMS` để nối `verify_response` và `include_claims` vào `RAGPipeline`. Rà soát và giảm lỗi format/citation của LLM từ 4 ca lỗi Tuần 9 (`gold_003`, `gold_008`, `gold_022`, `gold_030`) mà không vi phạm quy tắc không tự vá citation. | `build_runtime()` không import/khởi tạo `BGEScorer` khi `RAG_RERANK=false`. Test `test_runtime_config.py` kiểm chứng cả 2 nhánh `RAG_VERIFY_CLAIMS`. Tỷ lệ lỗi format/citation trên 30 câu Golden giảm xuống $\le 1$ ca. |
| **VLRA-T2-31** | Chuẩn hóa quy tắc Markdown trong `answer` (danh sách, bảng biểu, liên kết `[C1]`, `[C2]`). Nâng cấp `api/mock_app.py` bổ sung kịch bản `answered_markdown` và kịch bản lỗi định sẵn theo đặc tả ở mục 4.3. Viết unit test kiểm tra `validate_generated_response` với nội dung Markdown phức tạp. | `RAGResponse` và `validate_generated_response` pass 100% với các mẫu Markdown có bảng `|...|`, danh sách lồng nhau và nhiều marker `[C1]`, `[C2]`. `mock_app.py` trả đúng fixture cho Team 3 test E2E. |
| **VLRA-T2-32** | Viết tài liệu bàn giao `docs/team2_rag/ui-integration-guide.md` đặc tả đầy đủ: hợp đồng API, bảng mã lỗi wire code & cờ `retryable`, quy tắc regex parse `[Ck]` gắn sự kiện mở Document Viewer, và luồng xử lý nút "Dừng nhận stream" / retry. | Tài liệu khớp 100% với `api/handlers.py`, `errors.py`, `articles.py`. Team 3 xác nhận dùng được để hoàn thiện Chat Panel và Document Viewer. |

### 2.2. Người 2: Cưỡng Chế Deadline NFR-08, Đo End-to-End NFR-07 & Nghiệm Thu NFR-09 (`VLRA-74`)

| Mã | Công việc | Tiêu chí hoàn thành (DoD) |
| :--- | :--- | :--- |
| **VLRA-T2-33** | Truyền ngân sách thời gian còn lại (`remaining`) từ `RAGPipeline.query` xuống `generate_answer_detailed` $\rightarrow$ `LLMService.ask` theo đúng chữ ký ở mục 4.1. Viết test kiểm chứng chuỗi timeout NFR-08 (`45s` AI / `50s` Java / `60s` FE) và hành vi giữ/nhả khóa `slot` khi request timeout hoặc bị ngắt. | Khi tổng thời gian các bước vượt `pipeline_timeout` (`45.0s`), bước gọi LLM bị giới hạn đúng bằng `remaining` và trả HTTP 504 `LLM_TIMEOUT`. Test timeout và concurrency trong `test_internal_query_api.py` & `test_pipeline_integration.py` pass 100%. |
| **VLRA-T2-34** | Cập nhật runner benchmark để đo độ trễ **End-to-End** qua `RAGPipeline.query` (thay vì gọi rời từng bước như Tuần 9) theo schema `LoadAndStabilityReport` ở mục 4.2. Đo trên tập 30 câu Golden, xuất đủ `p50`, `p90`, `p95`, `max` cho toàn luồng và từng chặng, báo cáo cả lỗi và timeout. | Có báo cáo JSON + Markdown lưu commit SHA, cấu hình và kết quả đo thật. `e2e_latency_p95_s <= 45.0` đạt chuẩn NFR-07. Không ẩn các ca `error` hay `timeout` khỏi báo cáo. |
| **VLRA-T2-35** | Phối hợp Team 1 & Team 3 nghiệm thu NFR-09 trên `GET /internal/v1/documents/{document_id}/articles/{article_id}` (đo cold-start & warm-cache, kiểm tra bảng biểu/chú thích sửa đổi trong Điều luật P0 và các mã lỗi 400/404). Xuất báo cáo tổng hợp `docs/team2_rag/ai_service_load_and_stability_report.md`. | Độ trễ AI Service cho Article Viewer đạt `p95 <= 1.0s` (warm) và `<= 5.0s` (cold), thỏa mãn NFR-09 (Java $\rightarrow$ AI $\le 10\text{s}$, FE $\le 15\text{s}$). Báo cáo đầy đủ số liệu ổn định và tải. |

### 2.3. Việc Chung

| Mã | Công việc | Tiêu chí hoàn thành (DoD) |
| :--- | :--- | :--- |
| **VLRA-T2-36** | Phối hợp Team 1 và Team 3 chạy nghiệm thu tích hợp E2E toàn hệ thống (Chat Panel, Document Viewer, ngắt stream, retry lỗi mạng) và chốt lại Dev Set nếu Team 1 hoàn tất review (`VLRA-T2-29`). | Bộ test E2E các trạng thái UI của Team 3 đạt 100% khi ghép với AI Service v2. |

---

## 3. Đặc Tả Thiết Kế & Các Bất Biến Hệ Thống (System Invariants)

### 3.1. Bất Biến Về Ngân Sách Thời Gian & Timeout Phân Tầng (NFR-07, NFR-08, NFR-09)
Hệ thống phải thỏa mãn các bất biến thời gian sau trên mọi request:

1. **Bất biến chuỗi Timeout truy vấn (NFR-08):**
   $$T_{\text{AI Deadline}} (45.0\text{s}) < T_{\text{Java Backend Timeout}} (50.0\text{s}) < T_{\text{Frontend Timeout}} (60.0\text{s})$$
   - Tại tầng FastAPI (`api/app.py`): `asyncio.wait_for(asyncio.shield(work), timeout=45.0)` là chốt chặn cứng ngoài cùng. Nếu quá 45.0s, trả HTTP `504` với wire code `"LLM_TIMEOUT"`, header `X-Request-ID` giữ nguyên, và khóa `slot` vẫn được giữ cho đến khi thread nền thực sự thoát để chống dồn ứ (pile-up).
   - Tại tầng Pipeline (`pipeline.py`):
     $$\text{remaining\_before\_llm} = \text{deadline} - \text{time.monotonic}()$$
     Nếu $\text{remaining\_before\_llm} \le 1.0\text{s} \implies$ ném `LLMTimeoutError` ngay lập tức mà không gọi LLM. Ngược lại, truyền `timeout_override = min(settings.timeout_seconds, remaining_before_llm - 0.5)` xuống lần gọi provider.

2. **Bất biến độ trễ End-to-End (NFR-07):**
   $$\text{Percentile}_{95}\left(T_{\text{E2E}}\right) \le 45.0\text{s}$$
   Trong đó $T_{\text{E2E}} = T_{\text{validate\_input}} + T_{\text{retrieval}} + T_{\text{rerank}} + T_{\text{context}} + T_{\text{llm}} + T_{\text{verify}}$ được đo trên tập các truy vấn hoàn tất qua `RAGPipeline.query`. Các ca `timeout` hoặc `error` phải được ghi nhận riêng vào `timeout_count` và `error_count` kèm thời gian thực tế trước khi lỗi.

3. **Bất biến độ trễ Document Viewer (NFR-09):**
   $$T_{\text{AI Article Lookup}} \le T_{\text{Java}\rightarrow\text{AI}} (\le 10.0\text{s}) < T_{\text{FE Viewer}} (\le 15.0\text{s})$$

### 3.2. Đặc Tả Biến Môi Trường Bổ Sung / Cập Nhật Tại `runtime.py`

| Biến môi trường | Kiểu | Mặc định | Đặc tả hành vi (Behavior Spec) |
| :--- | :---: | :---: | :--- |
| `RAG_RERANK` | `bool` | `"false"` | Khi `"false"`, `build_runtime()` đặt `scorer=None`, `rerank_enabled=False` và **tuyệt đối không** khởi tạo `BGEScorer` hay tải model BGE vào RAM. Khi `"true"`, khởi tạo và warm-up `BGEScorer(truncate=...)`. |
| `RAG_VERIFY_CLAIMS` | `bool` | `"false"` | Khi `"true"`, `build_runtime()` khởi tạo `LLMService(..., include_claims=True)` và truyền `verifier=verify_response` vào `RAGPipeline`. Khi `"false"`, tắt sinh `claims` để giảm độ trễ và lượng output token trên luồng online. |
| `RAG_RETRIEVAL_TIMEOUT` | `float` | `"10"` | Giới hạn thời gian tìm kiếm Hybrid (giây), nằm trong khoảng `(0, 30]`. |
| `RAG_RERANK_TIMEOUT_SECONDS` | `float` | `"4"` | Giới hạn thời gian rerank (giây); quá hạn và `RAG_STRICT_RERANK=false` thì fallback về thứ hạng Hybrid RRF và ghi log `reranker_degraded_fallback reason=RerankTimeout degraded=true`. |

### 3.3. Đặc Tả Cú Pháp Markdown & Marker Trích Dẫn Trong `answer` (`VLRA-73`)
Mọi chuỗi `answer` khi `status == "answered"` phải tuân thủ đồng thời JSON Schema `contracts/v0.1/rag_response.schema.json` và các quy tắc định dạng Markdown sau:
1. **Cú pháp Marker bất biến:**
   - Chỉ khớp biểu thức chính quy `\[C([1-9][0-9]*)\]`.
   - Không có khoảng trắng bên trong ngoặc vuông (cấm `[ C1]`, `[C1 ]`), không có số 0 đứng đầu (cấm `[C0]`, `[C01]`), không có ngoặc vuông mở mà không đóng.
   - Thứ tự xuất hiện đầu tiên của các marker trong toàn bộ văn bản Markdown (kể cả trong danh sách hoặc ô của bảng biểu) phải liên tục là `C1, C2, ..., Cn` và khớp 1–1 với mảng `citations`.
2. **Tương thích với bộ Render Markdown của Frontend:**
   - **Danh sách (Lists):** Sử dụng `- ` cho danh sách không thứ tự hoặc `1. `, `2. ` cho danh sách có thứ tự; trước khối danh sách phải có dòng trống hoặc xuống dòng `\n`. Marker `[Ck]` đặt ở cuối mục danh sách, trước dấu chấm câu kết thúc (ví dụ: `- Công ty cổ phần có tối thiểu 03 cổ đông [C1].`).
   - **Bảng biểu (Tables):** Sử dụng chuẩn GFM (GitHub Flavored Markdown) gồm dòng tiêu đề `| Cột 1 | Cột 2 |`, dòng phân cách `| :--- | :--- |` và các dòng dữ liệu. Marker `[Ck]` đặt bên trong ô dữ liệu, tuyệt đối không chứa ký tự `|` hay xuống dòng `\n` bên trong marker.
   - **Cấm bọc link Markdown quanh marker:** LLM và backend không sinh `[C1](https://...)`; việc biến `[C1]` thành phần tử tương tác (chip/button mở Document Viewer) do Frontend thực hiện dựa trên mảng `citations`.

---

## 4. Giao Tiếp Giữa Các Module & Hợp Đồng Dữ Liệu (Contracts & Signatures)

### 4.1. Chữ Ký Hàm Truyền Ngân Sách Thời Gian Còn Lại (`VLRA-T2-33`)

Cập nhật chữ ký tại `team2_rag/llm/base.py`, `team2_rag/llm/service.py` và `team2_rag/answer.py` (giữ tương thích ngược 100% với toàn bộ test cũ nhờ tham số keyword tùy chọn `timeout_seconds: Optional[float] = None`):

```python
# 1. team2_rag/llm/service.py
class LLMService:
    def generate(
        self,
        request: LLMInput,
        *,
        request_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None,  # Nếu truyền vào, giới hạn thời gian gọi provider <= timeout_seconds
    ) -> LLMResult: ...

    def ask(
        self,
        question: str,
        context: Union[str, Mapping],
        history: Optional[Iterable[Union[HistoryTurn, Mapping]]] = None,
        *,
        request_id: Optional[str] = None,
        original_question: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> LLMResult: ...

# 2. team2_rag/answer.py
def answer_from_rerank_detailed(
    rerank_output: Mapping,
    llm_service: LLMService,
    history: Optional[Iterable[Union[HistoryTurn, Mapping]]] = None,
    *,
    max_chunks: int = DEFAULT_MAX_CONTEXT_CHUNKS,
    max_context_chars: Optional[int] = DEFAULT_MAX_CONTEXT_CHARS,
    token_budget: Optional[TokenBudget] = None,
    request_id: Optional[str] = None,
    llm_timeout_seconds: Optional[float] = None,  # Truyền từ RAGPipeline.query: min(30.0, remaining - 0.5)
) -> GeneratedAnswer: ...

---

## Cập Nhật Trạng Thái Thực Thi (Cập nhật ngày 14/11/2026)

| Mã công việc | Người phụ trách | Trạng thái | Ghi chú kết quả |
| :--- | :--- | :---: | :--- |
| `VLRA-T2-30` | Người 1 (VLRA-73) | **DONE (Đã xong)** | Đã tối ưu `runtime.py`, thêm `RAG_VERIFY_CLAIMS`, rà soát prompt (kết luận không cần sửa) và merge PR #62 vào `develop`. |
| `VLRA-T2-31` | Người 1 (VLRA-73) | **DONE (Đã xong)** | Đã bổ sung kịch bản `answered_markdown` và các kịch bản lỗi vào `mock_app.py` kèm unit test. |
| `VLRA-T2-32` | Người 1 (VLRA-73) | **DONE (Đã xong)** | Đã bàn giao `docs/team2_rag/ui-integration-guide.md` cho Team 3. |
| `VLRA-T2-33` | Người 2 (VLRA-74) | **DONE (Đã xong)** | Đã truyền `remaining` timeout xuống LLM (`pipeline.py`, `answer.py`, `llm/service.py`) và có unit test `test_nfr08_timeout_concurrency.py`. |
| `VLRA-T2-34` | Người 2 (VLRA-74) | **DONE (Đã xong)** | Đã xây dựng `scripts/benchmark_e2e_nfr07.py` và chạy đo E2E thực nghiệm (`raw_results` đầy đủ trong JSON). |
| `VLRA-T2-35` | Người 2 (VLRA-74) | **DONE (Đã xong)** | Đã đo NFR-09 qua HTTP endpoint (`TestClient`) và xuất báo cáo `ai_service_load_and_stability_report.md` + `.json`. |
| `VLRA-T2-36` | Chung cả Team 2 | **IN_PROGRESS** | Phối hợp nghiệm thu tích hợp E2E với Team 1 và Team 3 sau khi merge PR vào `develop`. |
