# team2_rag — Context → LLM → Answer + chunk_id

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
  Gemini/Qwen phải tự cung cấp `TokenCounter`. Prompt cố định vượt giới hạn → `ContextBudgetError`.
- Không truyền `token_budget` → budget **ký tự xấp xỉ** (`LLM_MAX_CONTEXT_CHARS`=9000), **chưa đáp ứng spec token**, chỉ dùng dev/test (có log cảnh báo).
- Không có chunk dùng được → `insufficient_context`, không gọi LLM.
- Citation phải khớp nhãn + toàn bộ metadata của chunk đã gửi LLM; sai → `CitationInvalidError` (`CITATION_INVALID`). Citation được đánh lại `C1..Cn`
  theo lần xuất hiện đầu tiên trong answer (marker đổi theo). JSON/form sai → `LLMBadOutputError` (`INVALID_LLM_OUTPUT`); lỗi provider giữ nguyên `LLMError`.
- Response không có field `chunk_ids` riêng vì `rag_response.schema.json` có `additionalProperties:false`; dùng `cited_chunk_ids()`.

## Chạy test (từ gốc repo)
`python3 -m unittest discover -s team2_rag/tests -t .` (cần `pip install jsonschema` để các test schema chạy; không cần API key).

## Chờ xác nhận (Người 1 / Team 1 / Team 2 / Team 3)
1. Chưa có Reranker và `retrieve()` trong repo (mọi nhánh); `query()` trong `service.py` vẫn là mock. Chưa chạy integration test thật.
2. Người 1 xác nhận output Reranker = 12 trường Team 1 (đã xếp theo rerank, có thể kèm `rerank_score`).
3. Chốt model/provider chính thức + context window; tokenizer cho Gemini/Qwen nếu dùng. Chưa kiểm chứng `tiktoken` với model thật.
4. Golden (`golden_phase1_30cai.json` trên `main`) có 7/30 mẫu cần 6–11 chunk nguồn, vượt giới hạn context 5 chunk; nhánh `feature/team2-rag` đã rút golden còn 15 mẫu.
5. Kiểm tra citation chỉ chứng minh nguồn khớp chunk đã gửi; việc nguồn có thật sự hỗ trợ câu trả lời cần đánh giá thủ công.
