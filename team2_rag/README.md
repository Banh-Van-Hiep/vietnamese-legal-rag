# team2_rag — Context → LLM → Answer + chunk_id

## Week 4 integration draft

Pipeline/HTTP entry points, real-run setup, tests and pending VLRA-39/47 handoff:
[week4-integration.md](../docs/team2_rag/week4-integration.md).
The new API is `team2_rag.api.create_app`; `service.query()` below remains the older mock.

```python
from team2_rag.llm import create_llm_service
from team2_rag.answer import answer_from_rerank, cited_chunk_ids

svc = create_llm_service()                      # LLM_PROVIDER / LLM_MODEL / *_API_KEY
resp = answer_from_rerank(reranker_output, svc)  # {"status", "answer", "citations"} = rag_response.schema.json
cited_chunk_ids(resp)                            # ["bll2019_v1_d113_k1", ...] (chunk_id nguồn thật sự được trích dẫn)

# hoặc để hàm tự đọc cấu hình (LLM thật + token budget + giới hạn chunk), và đổi lỗi LLM thành ErrorResponse:
from team2_rag.answer import generate_answer, to_error_response
try:
    resp = generate_answer(reranker_output, history)
except Exception as exc:
    body = to_error_response(exc)               # {"error": {"code", "message", "retryable"}} hoặc None (input sai -> 400/500 do tầng API)
```

Toàn bộ phần VLRA-29 nằm trong `answer.py`, `llm/tokens.py`, `prompts/context.py`. Các file dùng chung `service.py` (mock `query()` cho Team 3),
`__init__.py`, `__main__.py` **giữ nguyên như `main`** để không xung đột. `service.py` (gốc) và `llm/service.py` (`LLMService`) là hai module khác nhau.
Chạy Python từ thư mục chứa `team2_rag/`, không chạy từ bên trong `team2_rag/` (`types.py` sẽ che module `types` của thư viện chuẩn).

Luồng: `reranker_output → prompts.context.build_context → LLMService.ask → kiểm tra citation → RAGResponse`.

## Input: output của Reranker (Người 1)
Đúng contract `contracts/v0.1/retrieval_output.schema.json` của Team 1: `{"question", "results": [...]}`, mỗi candidate **12 trường**
`chunk_id, document_id, article_id, content, document_title, article, clause, point, source_url, score, rank, retrieval_method`,
đã xếp theo thứ tự rerank. Reranker có thể thêm key khác (ví dụ `rerank_score`), Context Builder bỏ qua.
Schema nháp cũ trong `docs/team2_rag/schemas/rerank_output.schema.json` (`document`, `source`, `retrieval_score`…) **không được hỗ trợ**.
Candidate vi phạm contract (thiếu trường, ID không ASCII, `source_url` không HTTPS…) → `ContextBuildError`; không tự sửa.

## Hành vi
- Tối đa `LLM_MAX_CONTEXT_CHUNKS` (5) chunk; chunk không vừa budget bị bỏ qua, xét chunk kế.
- **Budget token (đúng spec `context-builder.md`):** truyền `token_budget=TokenBudget(counter, context_window_tokens)` hoặc `token_budget_from_settings(settings)`.
  Budget = `min(3000, window − token(system+question+history) − output_reserve(1500) − margin(256))`, đếm bằng tokenizer của đúng model, rồi đếm lại cả prompt đã render.
  Cấu hình: `LLM_CONTEXT_WINDOW_TOKENS` (bắt buộc), `LLM_MAX_CONTEXT_TOKENS`, `LLM_SAFETY_MARGIN_TOKENS`. Hiện có counter cho `openai` (cần `pip install tiktoken`);
  Gemini/Qwen chưa có counter chính xác: `token_budget_from_settings` dùng `ConservativeByteCounter` (chặn trên theo byte UTF-8, luôn đếm dư, có log cảnh báo `token_counter_fallback`)
  nên prompt không vượt cửa sổ nhưng context nguồn bị cắt sớm (~2-3 byte/ký tự tiếng Việt; cần window đủ lớn); truyền `TokenCounter` chính xác của provider để dùng hết cửa sổ.
  Prompt cố định vượt giới hạn → `ContextBudgetError`; `LLM_CONTEXT_WINDOW_TOKENS` ≤ `LLM_MAX_OUTPUT_TOKENS + LLM_SAFETY_MARGIN_TOKENS` bị từ chối ngay khi khởi động.
- Không truyền `token_budget` → budget **ký tự xấp xỉ** (`LLM_MAX_CONTEXT_CHARS`=9000), **chưa đáp ứng spec token**, chỉ dùng dev/test (có log cảnh báo).
- Không có chunk dùng được → `insufficient_context`, không gọi LLM.
- Citation phải khớp nhãn + toàn bộ metadata của chunk đã gửi LLM; sai → `CitationInvalidError` (`CITATION_INVALID`). Citation được đánh lại `C1..Cn`
  theo lần xuất hiện đầu tiên trong answer (marker đổi theo). JSON/form sai → `LLMBadOutputError` (`INVALID_LLM_OUTPUT`); lỗi provider giữ nguyên `LLMError`.
- Response không có field `chunk_ids` riêng vì `rag_response.schema.json` có `additionalProperties:false`; dùng `cited_chunk_ids()`.

## Local LLM via Ollama (free, `qwen2.5:3b`)
Provider `ollama` talks to Ollama's OpenAI-compatible API (`http://localhost:11434/v1`). No API key, nothing leaves the machine.
Existing providers (`openai`, `gemini`, `qwen`), the pipeline, token budget, citation validation, API schemas and `X-Request-ID` are unchanged.

Settings (environment or `.env`; template: [`.env.ollama.example`](.env.ollama.example), never commit a real `.env`):

| Variable | Value for Ollama |
|---|---|
| `LLM_PROVIDER` | `ollama` |
| `LLM_MODEL` | `qwen2.5:3b` (exact name from `ollama list`) |
| `OLLAMA_BASE_URL` | default `http://localhost:11434/v1` |
| `LLM_CONTEXT_WINDOW_TOKENS` | **required**; must equal the context length the Ollama *server* uses (e.g. `8192`) |
| `LLM_TIMEOUT_SECONDS` | default 30; for Ollama up to 600 (other providers stay capped at 30). Use ~120 for cold start / CPU |
| `LLM_TEMPERATURE` | default `0` |

**Windows PowerShell setup (once)**
```powershell
winget install Ollama.Ollama                 # or download from https://ollama.com/download
setx OLLAMA_CONTEXT_LENGTH 8192              # server-side context; the /v1 API cannot set num_ctx per request
# Quit Ollama from the system tray, then start it again from the Start menu (so it reads the new variable)
ollama pull qwen2.5:3b
ollama ps                                    # while a model is loaded: recent versions show its CONTEXT, confirm 8192
```

**Run (from the directory that contains `team2_rag/`)**
```powershell
pip install -r team2_rag/requirements-dev.txt
Copy-Item team2_rag\.env.ollama.example .env   # or append these lines to your existing .env
python -m team2_rag.smoke_ollama             # REAL call: sample sources -> qwen2.5:3b -> citation validation
python -m team2_rag.run_query "Your question"   # full Hybrid/BGE pipeline (needs Team 1 indexes, see RAG_BM25_INDEX / RAG_DENSE_INDEX)
python -m uvicorn team2_rag.api:create_app --factory --host 127.0.0.1 --port 8001
```
`smoke_ollama` exits 0 only if the model answered and the answer passed the production checks; exit 2 = setup problem
(server down, model not pulled, bad config), exit 1 = the model/LLM layer failed (message shows the error class).

Behaviour notes
- Request uses JSON mode (`response_format: json_object`) and `max_tokens`; `max_completion_tokens` is OpenAI-only and not sent. Checked against docs.ollama.com/openai.
- Ollama truncates over-long prompts silently, and `/v1` ignores `num_ctx`. If `OLLAMA_CONTEXT_LENGTH` is smaller than `LLM_CONTEXT_WINDOW_TOKENS`, citations/JSON break; keep them equal.
- Token counting for Ollama uses the existing conservative byte counter (always over-counts, so context is cut early; roughly 1000-1500 Vietnamese characters per 3000 "tokens"). Raise `LLM_MAX_CONTEXT_TOKENS` (default 3000) only together with the window; not tuned against a real model yet.
- Failures map to the existing codes: server down/connection dropped -> `SERVICE_UNAVAILABLE` (503); timeout -> `UPSTREAM_TIMEOUT` (504); model not pulled -> `SERVICE_UNAVAILABLE` (log text says `ollama pull ...`); non-JSON/wrong-shape reply -> `UPSTREAM_INVALID_RESPONSE` (502). No retries.
- `create_app` has its own 45 s request limit (unchanged); a slow CPU can hit it (504) even when `LLM_TIMEOUT_SECONDS` is larger. The smoke test and `run_query` are not subject to it.
- `create_app()` startup: with no arguments it builds the runtime in the lifespan. An explicit `runtime_factory=` is authoritative: if it fails, `/internal/v1/ready` and `/internal/v1/query` answer 503 `SERVICE_UNAVAILABLE` (an injected `pipeline=` is never served as a stand-in) and the runtime is closed exactly once at shutdown. A bare `pipeline=` is served as-is and stays owned by the caller (tests/embedding).
- A 3B model follows the strict JSON + `[Ck]` citation contract less reliably than hosted models; bad output is rejected, never repaired.

## Chạy test (từ gốc repo)
```
pip install -r team2_rag/requirements-dev.txt
python -m pytest team2_rag/tests -q
```
`pytest` là lệnh chuẩn: chạy được cả test dạng `unittest.TestCase` lẫn test dạng hàm/fixture của pytest. Các module `test_error_handlers`, `test_llm_config`, `test_response_models`,
`test_answer_citation_accuracy`, `test_internal_query_api` chỉ có hàm pytest, nên `python -m unittest ...` **không thu thập được** chúng (báo `Ran 0 tests` hoặc `ModuleNotFoundError: pytest`).
Chỉ dùng stdlib: `python3 -m unittest discover -s team2_rag/tests -t .` chạy được phần `TestCase` (các module pytest-only bị báo lỗi import nếu chưa cài pytest). Không cần API key; test thiếu
`jsonschema`/corpus sẽ bị skip (xem số skipped). Kiểm tra golden: `python -m team2_rag.validate_golden` (thoát mã 1 nếu thiếu corpus/golden, không coi là đạt).

## Chờ xác nhận (Người 1 / Team 1 / Team 2 / Team 3)
1. Reranker, BM25/Dense/Hybrid và pipeline draft đã có. `query()` trong `service.py` vẫn là mock; API mới dùng `RAGPipeline.query()`. Chưa nghiệm thu chạy model + LLM thật toàn luồng.
2. Output Reranker giữ nguyên 12 trường Team 1, điểm rerank lưu riêng; Context Builder dùng thứ tự danh sách, không sort lại `rank`.
3. Chốt model/provider chính thức + context window; tokenizer cho Gemini/Qwen nếu dùng. Chưa kiểm chứng `tiktoken` với model thật.
4. Golden trên bản draft này có 40 mẫu (30 mẫu cũ + `gold_031`–`gold_040`); 7 mẫu cũ cần hơn 5 chunk nguồn, vượt giới hạn context mặc định. Bộ validate đã kiểm tra tham chiếu chunk nhưng chưa chứng minh chất lượng trả lời.
5. Kiểm tra citation chỉ chứng minh nguồn khớp chunk đã gửi; việc nguồn có thật sự hỗ trợ câu trả lời cần đánh giá thủ công.
6. `team2_rag.api.handlers` (VLRA-47) và `models.response.RAGResponse` (VLRA-39) đã có trong repo: `create_app` luôn cài handler và dùng `RAGResponse` làm model mặc định (JSON Schema vẫn là chốt chặn hợp đồng). Test endpoint dùng pipeline giả; chưa nghiệm thu chạy model + LLM thật.
