# ĐẶC TẢ I/O CỦA RAG

Đây là đề xuất interface/API để review liên team trong Tuần 1, không phải implementation contract đã được phê duyệt. Các JSON Schema đặt trong [`schemas/`](schemas/) là nguồn tham chiếu cấu trúc cho từng payload.

## API Contract

| Hạng mục | Đề xuất |
| --- | --- |
| Method và path | `POST /api/v1/query` |
| Request body | [`request.schema.json`](schemas/request.schema.json) |
| Success body | [`rag_response.schema.json`](schemas/rag_response.schema.json) |
| Error body | [`error_response.schema.json`](schemas/error_response.schema.json) |
| Ví dụ request | `{"question":"Người lao động được nghỉ phép bao nhiêu ngày?"}` |
| Cấu trúc success | `{"answer":"...","citations":[...]}` |

Team 3 phụ trách REST API được expose ra bên ngoài và backend integration. Việc Team 3 gọi Team 2 dưới dạng in-process service hay internal endpoint, HTTP status mapping, authentication, version negotiation và streaming vẫn là các quyết định cần thống nhất; tài liệu này không quy định implementation cụ thể.

## Chuỗi Payload

### 1. Request Schema

Đầu vào của query flow là một trường `question` bắt buộc, kiểu chuỗi và không được rỗng. Xem [`schemas/request.schema.json`](schemas/request.schema.json).

### 2. Retrieval Output Schema

Team 1 trả về `question` và `results` theo thứ tự. Mỗi result bao gồm `chunk_id`, `content`, `document`, `article`, `clause` có thể là `null`, `source` và `score` kiểu số. Xem [`schemas/retrieval_output.schema.json`](schemas/retrieval_output.schema.json).

### 3. Reranker Output Schema

Team 2 trả về cùng câu hỏi và metadata của candidate. `score` được đổi tên thành `retrieval_score`; `rerank_score` được bổ sung. Hai score không ghi đè lên nhau. `results` được sắp xếp theo `rerank_score` giảm dần. Xem [`schemas/rerank_output.schema.json`](schemas/rerank_output.schema.json).

### 4. Context Schema

Context chứa `question` ban đầu, `token_budget`, `estimated_tokens`, các `chunks` được chọn theo thứ tự và `groups`. Mỗi chunk giữ lại identifier, content, metadata nguồn, cả hai score và `position` bắt đầu từ 1. Groups tham chiếu đến các `chunk_id` tồn tại theo `document` + `article`; chúng không thay thế metadata của từng chunk. Xem [`schemas/context.schema.json`](schemas/context.schema.json).

### 5. LLM Input Schema

LLM input bao gồm `system_instruction`, `legal_context` có cấu trúc, `user_question` và `output_instruction`. Nội dung được truy xuất được xem là dữ liệu không đáng tin cậy về mặt instruction, không phải chỉ thị. Xem [`schemas/llm_input.schema.json`](schemas/llm_input.schema.json).

### 6. LLM Output Schema

Output có cấu trúc đề xuất gồm `answer` và `citations`. Mỗi citation có `claim` và các trường nguồn từ Citation Schema. LLM output chưa được xác minh cho đến khi Team 2 kiểm tra lại với legal context. Xem [`schemas/llm_output.schema.json`](schemas/llm_output.schema.json).

### 7. Citation Schema

Citation ánh xạ một claim trong câu trả lời tới `chunk_id`, `document`, `article`, `clause` và `source`. Toàn bộ metadata nguồn phải khớp với một context chunk đang tồn tại. Xem [`schemas/citation.schema.json`](schemas/citation.schema.json).

### 8. Final RAG Response

Success response có cấu trúc bắt buộc `{"answer":"...","citations":[...]}`. `citations` chỉ chứa các citation vượt qua các bước kiểm tra provenance đã thống nhất. Xem [`schemas/rag_response.schema.json`](schemas/rag_response.schema.json).

### 9. Error Response

Error body được đề xuất là `{ "error": { "code": "...", "message": "...", "retryable": false } }`. Không được để lộ secrets hoặc raw sensitive provider payloads. HTTP status mapping sẽ được thống nhất với Team 3. Xem [`schemas/error_response.schema.json`](schemas/error_response.schema.json).

## Team Interfaces

### Team 1 → Team 2

Team 1 phụ trách legal data processing, chunking, metadata, BM25, Dense Retrieval, embedding, vector store/DB, Hybrid Retrieval, RRF và retrieval evaluation. Team 1 cung cấp Retrieval Output candidates. Hybrid Retrieval và RRF là trách nhiệm của Team 1. Team 2 giữ nguyên identifiers và metadata, đồng thời lưu riêng retrieval/rerank scores.

### Team 2 → Team 3

Team 2 phụ trách reranker, context builder, prompt, LLM service abstraction, citation verification, RAG pipeline và answer-quality/grounding. Team 2 cung cấp answer + verified citations dưới dạng RAG Output. Team 3 phụ trách backend, REST API, frontend, UI/UX, document viewer, integration và deployment; frontend không được gọi trực tiếp external LLM provider.

### Team 3 → Team 2

Câu hỏi của người dùng đi vào thông qua query request. Team 3 phụ trách external API/backend boundary; internal call boundary và error/status mapping vẫn cần được thống nhất.

## Các Quyết Định Cần Xác Nhận

- **Team 1:** exact retrieval output envelope và field types; `article`/`document`/`source` là string hay structured identifiers; clause có thể `null` hay không; score meaning/direction; stable `chunk_id`; source provenance; candidate Top-K (đề xuất ban đầu 20); empty-result behavior.
- **Team 3:** API ownership và service boundary; HTTP status/error mapping; authentication; request size limits; response có request identifiers hay không; frontend citation/document-viewer needs; timeout propagation.
- **Team 1 + Team 2:** retrieval/citation metadata preservation và versioning khi schema thay đổi.
- **Team 2:** reranker Top-K (đề xuất ban đầu 5), context budget/tokenizer, provider structured-output support, invalid citation policy và retry/timeout defaults.

## Công Việc Dự Kiến Trong Tuần 2

- Review và phê duyệt schemas với Team 1 và Team 3; ghi nhận thay đổi và thống nhất cách version hóa contract.
- Thống nhất metadata semantics, nullability, empty results, score semantics, API status codes và error behavior.
- Xây dựng evaluation fixtures đại diện và benchmark retrieval/reranking/context sau khi ownership và quyền truy cập dữ liệu được xác nhận.
- Chỉ implement provider/service và các thành phần RAG sau khi thiết kế được review; thêm integration tests dựa trên các contract đã được phê duyệt.

## Phạm Vi Tuần 1

Toàn bộ payload, examples và values đều là đề xuất thiết kế. Tuần 1 không có Python implementation, endpoint, provider integration, database, frontend hoặc legal corpus.