# RAG I/O Specification

Đây là proposal interface/API cho review liên team trong Week 1, không phải implementation contract đã được phê duyệt. Các JSON Schema đặt trong [`schemas/`](schemas/) là nguồn tham chiếu cấu trúc cho từng payload.

## API Contract

| Item | Proposal |
| --- | --- |
| Method and path | `POST /api/v1/query` |
| Request body | [`request.schema.json`](schemas/request.schema.json) |
| Success body | [`rag_response.schema.json`](schemas/rag_response.schema.json) |
| Error body | [`error_response.schema.json`](schemas/error_response.schema.json) |
| Request example | `{"question":"Người lao động được nghỉ phép bao nhiêu ngày?"}` |
| Success shape | `{"answer":"...","citations":[...]}` |

Team 3 owns the externally exposed REST API and backend integration. Whether Team 3 calls Team 2 as an in-process service or internal endpoint, HTTP status mapping, authentication, version negotiation and streaming are open decisions; this document does not prescribe an implementation.

## Payload Chain

### 1. Request Schema

Input to the query flow is one required, non-empty `question` string. See [`schemas/request.schema.json`](schemas/request.schema.json).

### 2. Retrieval Output Schema

Team 1 returns `question` and ordered `results`. Every result includes `chunk_id`, `content`, `document`, `article`, nullable `clause`, `source` and numeric `score`. See [`schemas/retrieval_output.schema.json`](schemas/retrieval_output.schema.json).

### 3. Reranker Output Schema

Team 2 returns the same question and candidate metadata. `score` is renamed to `retrieval_score`; `rerank_score` is added. Neither score overwrites the other. `results` are ordered by descending rerank score. See [`schemas/rerank_output.schema.json`](schemas/rerank_output.schema.json).

### 4. Context Schema

Context contains the original `question`, `token_budget`, `estimated_tokens`, ordered selected `chunks` and `groups`. Each chunk retains its identifier, content, source metadata, both scores and one-based `position`. Groups reference existing `chunk_id` values by `document` + `article`; they do not replace per-chunk metadata. See [`schemas/context.schema.json`](schemas/context.schema.json).

### 5. LLM Input Schema

The LLM input contains `system_instruction`, structured `legal_context`, `user_question` and `output_instruction`. Retrieved content is untrusted data, not instruction. See [`schemas/llm_input.schema.json`](schemas/llm_input.schema.json).

### 6. LLM Output Schema

The proposed structured output is `answer` plus `citations`. Each citation has `claim` and the source fields from Citation Schema. LLM output is unverified until Team 2 checks it against legal context. See [`schemas/llm_output.schema.json`](schemas/llm_output.schema.json).

### 7. Citation Schema

Citation maps one answer claim to `chunk_id`, `document`, `article`, `clause` and `source`. All source metadata must match an existing context chunk. See [`schemas/citation.schema.json`](schemas/citation.schema.json).

### 8. Final RAG Response

Success response has the required shape `{"answer":"...","citations":[...]}`. `citations` contains only citations passing the agreed provenance checks. See [`schemas/rag_response.schema.json`](schemas/rag_response.schema.json).

### 9. Error Response

Proposed error body is `{ "error": { "code": "...", "message": "...", "retryable": false } }`. It must not expose secrets or raw sensitive provider payloads. HTTP status mapping is to be agreed with Team 3. See [`schemas/error_response.schema.json`](schemas/error_response.schema.json).

## Team Interfaces

### Team 1 → Team 2

Team 1 owns legal data processing, chunking, metadata, BM25, dense retrieval, embedding, vector store/DB, hybrid retrieval, RRF and retrieval evaluation. It supplies Retrieval Output candidates. Hybrid Retrieval and RRF are explicitly Team 1 responsibilities. Team 2 preserves identifiers and metadata and separately records retrieval/rerank scores.

### Team 2 → Team 3

Team 2 owns reranker, context builder, prompt, LLM service abstraction, citation verification, RAG pipeline and answer-quality/grounding concerns. It proposes answer + verified citations as RAG Output. Team 3 owns backend, REST API, frontend, UI/UX, document viewer, integration and deployment; the frontend must not call an external LLM provider directly.

### Team 3 → Team 2

The user question enters through the query request. Team 3 owns the external API/backend boundary; exact internal call boundary and error/status mapping remain to be agreed.

## Cross-Team Decisions to Confirm

- **Team 1:** exact retrieval output envelope and field types; whether `article`/`document`/`source` are strings or structured identifiers; clause nullability; score meaning/direction; stable `chunk_id`; source provenance; candidate Top-K (initial proposal 20); empty-result behavior.
- **Team 3:** API ownership and service boundary; HTTP status/error mapping; authentication; request size limits; whether response includes request identifiers; frontend citation/document-viewer needs; timeout propagation.
- **Team 1 + Team 2:** retrieval/citation metadata preservation and versioning of schema changes.
- **Team 2:** reranker Top-K (initial proposal 5), context budget/tokenizer, provider structured-output support, invalid citation policy, and retry/timeout defaults.

## Week 2 Candidates

- Review and approve schemas with Team 1 and Team 3; record changes and contract versioning approach.
- Agree on metadata semantics, nullability, empty results, score semantics, API status codes and error behavior.
- Build representative evaluation fixtures and benchmark retrieval/reranking/context choices after ownership and data access are confirmed.
- Implement provider/service and RAG components only after design review; add integration tests against approved contracts.

## Week 1 Boundary

All payloads/examples and values are design proposals. Week 1 adds no Python implementation, endpoint, provider integration, database, frontend or legal corpus.