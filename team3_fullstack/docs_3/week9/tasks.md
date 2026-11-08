# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 9

## Phân Hệ: Fullstack & System (Team 3)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm

- **Giai đoạn:** Tuần 9.
- **Nguồn giao việc:** Epic [VLRA-4](https://banhvanhiep.atlassian.net/browse/VLRA-4), gồm [VLRA-69](https://banhvanhiep.atlassian.net/browse/VLRA-69) và [VLRA-70](https://banhvanhiep.atlassian.net/browse/VLRA-70).
- **Phụ trách:** Team 3; chưa phân công thành viên cho từng nhiệm vụ.
- **Trạng thái giao việc:** To Do cho cả hai nhiệm vụ; chưa xác nhận hoàn thành.
- **Mục tiêu trọng tâm:**
  - Giữ thống nhất contract giữa Java Backend và RAG Pipeline v2, đặc biệt dữ liệu citation và ánh xạ giữa API nội bộ với API public.
  - Cập nhật UI hiển thị câu trả lời, nguồn trích dẫn, lỗi và thông báo thiếu ngữ cảnh theo contract.
  - Kiểm tra bộ đọc SSE và tối ưu render dữ liệu streaming trên giao diện hiện có.
- **Căn cứ:** [ARCHITECTURE](../../../docs/ARCHITECTURE.md), [CODING_CONVENTIONS](../../../docs/CODING_CONVENTIONS.md), [thiết kế chung Team 3](../../../docs/team3_fullstack/README.md) và [Contract](../../../contracts/v0.1/CONTRACT.md).

Giữ đúng hai nhiệm vụ Jira, không tạo task con. Tiếp tục trên Backend/Frontend hiện có; đối chiếu phần đã triển khai và kiểm chứng các tuần trước để xác định phần cần cập nhật hoặc kiểm thử hồi quy.

---

## 2. Bảng Nhiệm Vụ & Tiêu Chí Hoàn Thành

| Mã Jira | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-69** | **Cập nhật Backend tương thích RAG v2 và đảm bảo thống nhất Contract Citation**<br>- Giữ vững contract dữ liệu giữa Backend và pipeline RAG mới; thống nhất schema, phiên bản và kiểm thử tương thích với Team 2.<br>- Cập nhật hoặc tái sử dụng lớp tiếp nhận, kiểm tra và ánh xạ payload phản hồi RAG v2 trên Backend hiện có.<br>- Khóa chặt contract: không tự ý thêm field hoặc trạng thái cảnh báo khi chưa qua phê duyệt. | - Backend gọi RAG v2 theo giao diện đã thống nhất và xử lý đúng response `answered`, `insufficient_context` cùng các lỗi theo contract.<br>- Citation được kiểm tra và ánh xạ đầy đủ từ `snake_case` sang `camelCase`; giữ nguyên giá trị ID, metadata và URL nguồn.<br>- Payload sai cấu trúc hoặc citation không hợp lệ theo contract bị từ chối, không phát thành kết quả thành công.<br>- Kiểm thử tương thích/hồi quy xác nhận public API và dữ liệu citation không thay đổi ngoài dự kiến; ghi rõ phiên bản/commit RAG và schema đã đối chiếu trong kết quả local.<br>- **Đầu ra:** Backend API tương thích RAG v2 theo schema và phiên bản đã thống nhất. |
| **VLRA-70** | **Cập nhật giao diện hiển thị câu trả lời, nguồn trích dẫn, lỗi và cảnh báo thiếu ngữ cảnh**<br>- Cập nhật hoặc tái sử dụng UI hiển thị answer và các thẻ citation có liên kết căn cứ pháp luật.<br>- Hiển thị thông báo theo `insufficient_context` và các mã lỗi được contract quy định.<br>- Kiểm tra bộ đọc SSE và tối ưu hóa luồng render dữ liệu streaming. | - UI hiển thị đúng answer và citation của kết quả `answered`; bấm citation mở đúng văn bản/Điều luật theo ID trả về.<br>- `insufficient_context` có thông báo rõ ràng, không tạo thẻ citation giả và không bị hiển thị như lỗi hệ thống.<br>- Lỗi có thông báo an toàn; hành vi thử lại tuân thủ `retryable` và quy tắc định danh lượt hiện hành.<br>- Bộ đọc SSE xử lý đúng `meta`, `delta`, `complete`, `error` và heartbeat, kể cả khi frame/ký tự UTF-8 bị chia qua nhiều lần đọc; thiếu terminal không được coi là thành công.<br>- Nội dung cuối khớp `complete`; không lặp, mất nội dung hoặc gắn dữ liệu vào hội thoại khác sau khi dừng/đổi hội thoại. Kiểm tra render bằng kịch bản streaming đã có và đối chiếu trước/sau nếu có thay đổi tối ưu.<br>- **Đầu ra:** Frontend hiển thị chuẩn xác câu trả lời, căn cứ trích dẫn và các thông báo giới hạn. |

---

## 3. Thiết Kế Kỹ Thuật & Luồng Tích Hợp

### 3.1. Backend và ranh giới contract — VLRA-69

```text
Frontend React
    │ POST /api/v1/chat/stream — camelCase
    ▼
Java Backend — tiếp nhận lượt, lưu pending và commit
    ├─ Phát meta về Frontend, duy trì heartbeat khi chờ
    │ POST /internal/v1/query — snake_case, X-Request-ID
    ▼
RAG Pipeline v2 — Team 2
    │ status + answer + citations hoặc ErrorResponse
    ▼
Java Backend — kiểm tra payload, ánh xạ và lưu trạng thái
    ├─ Thành công: commit → delta (nếu answered) → complete
    └─ Thất bại: xử lý/lưu lỗi theo state machine → error
    ▼
Frontend React
```

- Tái sử dụng Java 25 / Spring Boot 4.1.1 và kiến trúc hiện tại.
- Phần liên quan: `team3_fullstack/backend/src/main/java/com/legalai/backend/ai/`, `chat/stream/` và `document/` trong cùng package Backend.
- Kiểm tra payload trước khi chốt kết quả thành công; duy trì transaction, state machine và idempotency hiện hành.
- RAG nội bộ trả JSON hoàn chỉnh; SSE public do Java điều phối. Không yêu cầu đổi API nội bộ sang stream token trực tiếp từ model.
- Ánh xạ timeout, mất kết nối và payload không hợp lệ theo bảng lỗi đã thống nhất; không chuyển lỗi kỹ thuật thành `insufficient_context`.
- Chi tiết: [tích hợp RAG](../../../docs/team3_fullstack/rag-integration-specification.md) và [API public](../../../docs/team3_fullstack/public-api-specification.md).

### 3.2. Giao diện và xử lý streaming — VLRA-70

- Tái sử dụng React/TypeScript, component answer/citation/Document Viewer, hook hội thoại và bộ đọc SSE hiện có.
- Phần liên quan: `team3_fullstack/frontend/src/api/`, `src/hooks/`, `src/components/chat/`, `src/components/citation/` và phần Viewer hiện hành.
- Phân biệt đang nhận dữ liệu, kết quả có căn cứ, thiếu ngữ cảnh và lỗi; dùng nội dung chuẩn từ `complete` để chốt câu trả lời.
- Giữ xử lý an toàn khi dừng nhận, đổi hội thoại, retry hoặc reload; đối chiếu tối ưu render đã có trước khi bổ sung thay đổi.
- Thông báo thiếu ngữ cảnh dùng trạng thái hiện hành; không tự thêm field `warning` hoặc event SSE mới.
- Mốc so sánh render: kết quả profiler tuần 8 (`run_week8_acceptance.py --mode profile`, median render ChatWindow 699,9 → 36,1 ms trong môi trường development, xem [đo hiệu năng](../../../docs/team3_fullstack/performance-measurement.md)). Backend hiện phát **một** event `delta` chứa toàn bộ câu trả lời vì RAG nội bộ trả JSON hoàn chỉnh; tối ưu tuần này chỉ cần thiết khi đo lại thấy hồi quy so với mốc trên.
- Chi tiết: [thiết kế Frontend](../../../docs/team3_fullstack/frontend-design.md) và [thiết kế hội thoại](../../../docs/team3_fullstack/conversation-design.md).

---

## 4. Interface, Contract & Mock Data

### 4.1. Các hợp đồng cần đối chiếu

| Biên giao tiếp | Cấu trúc/quy tắc cần giữ | Nguồn chuẩn |
| :--- | :--- | :--- |
| Backend → RAG | `POST /internal/v1/query`, request gồm `question`, `history`; truyền `X-Request-ID`. | [ARCHITECTURE §3.2](../../../docs/ARCHITECTURE.md), [tích hợp RAG](../../../docs/team3_fullstack/rag-integration-specification.md) |
| RAG → Backend | Response gồm đúng `status`, `answer`, `citations`. `answered` có 1–10 citation và marker khớp nguồn; `insufficient_context` có `citations: []`, không marker trích dẫn. | [rag_response.schema.json](../../../contracts/v0.1/rag_response.schema.json), [Contract](../../../contracts/v0.1/CONTRACT.md) |
| Citation nội bộ → public | Chín trường: `citation_id` → `citationId`, `chunk_id` → `chunkId`, `document_id` → `documentId`, `article_id` → `articleId`, `document_title` → `documentTitle`, `article`, `clause`, `point`, `source_url` → `sourceUrl`. `clause`/`point` nullable nhưng không bỏ key. | [RAG schema](../../../contracts/v0.1/rag_response.schema.json), [SSE schema](../../../contracts/v0.1/chat_stream.schema.json) |
| Backend → Frontend | `POST /api/v1/chat/stream`; request camelCase, conversation/message ID số, `clientRequestId` UUIDv4; kết quả qua SSE. | [query_request.schema.json](../../../contracts/v0.1/query_request.schema.json), [chat_stream.schema.json](../../../contracts/v0.1/chat_stream.schema.json) |
| Lỗi | Envelope `error` gồm `code`, `message`, `retryable`; trước khi mở SSE trả HTTP error JSON, sau khi mở dùng event `error`. | [error_response.schema.json](../../../contracts/v0.1/error_response.schema.json), [API public](../../../docs/team3_fullstack/public-api-specification.md) |
| Viewer | Public `GET /api/v1/documents/{documentId}?articleId={articleId}`; mở đúng nguồn theo ID citation. | [API public](../../../docs/team3_fullstack/public-api-specification.md), [internal_article.schema.json](../../../contracts/v0.1/internal_article.schema.json) |

Tên RAG v2 chỉ phiên bản pipeline cần tích hợp; không mặc định đổi phiên bản schema hoặc đường dẫn API. Nếu bàn giao làm thay đổi contract, phải thống nhất trước khi cập nhật Backend/Frontend.

`insufficient_context` là trạng thái kết quả nghiệp vụ trong `complete`; lượt vẫn có state `completed`. Không thêm state cảnh báo vào vòng đời `pending`/`completed`/`failed`.

### 4.2. Dữ liệu mock cho tích hợp độc lập

Tái sử dụng mock/fixture hiện có và ghi rõ môi trường mock khi kiểm thử. Bộ dữ liệu cần bao quát `answered` có citation hợp lệ, `insufficient_context`, lỗi upstream và response sai contract; không bổ sung endpoint public chỉ để kích hoạt tình huống kiểm thử.

Mẫu `answered` với đầy đủ chín trường citation, cùng các mẫu `meta`/`delta`/`complete` và lỗi, nằm tại [public_examples.json](../../../contracts/v0.1/public_examples.json). Tái sử dụng [validator contract](../../../contracts/v0.1/validate_public_contract.py) và [kiểm thử SSE](../../frontend/src/api/chatStream.test.ts); các mẫu này là fixture kiểm thử giao tiếp.

Ví dụ response nội bộ thiếu ngữ cảnh:

```json
{
  "status": "insufficient_context",
  "answer": "Tài liệu được truy xuất chưa đủ căn cứ để trả lời.",
  "citations": []
}
```

Ví dụ SSE public tương ứng, không cần event `delta`:

```text
event: meta
data: {"conversationId":101,"clientRequestId":"44444444-4444-4444-8444-444444444444","userMessageId":201,"assistantMessageId":202,"createdAt":"2026-11-04T00:00:00Z"}

event: complete
data: {"conversationId":101,"clientRequestId":"44444444-4444-4444-8444-444444444444","userMessageId":201,"assistantMessageId":202,"status":"insufficient_context","answer":"Tài liệu được truy xuất chưa đủ căn cứ để trả lời.","citations":[],"createdAt":"2026-11-04T00:00:00Z"}

```

Ví dụ lỗi public sau khi mở SSE:

```text
event: error
data: {"error":{"code":"UPSTREAM_INVALID_RESPONSE","message":"Phản hồi từ dịch vụ xử lý không hợp lệ.","retryable":false}}

```

Mock xác nhận hành vi tích hợp theo schema; khả năng tương thích với bản RAG v2 bàn giao cần được kiểm chứng riêng trên dịch vụ đó.

---

## 5. Phụ Thuộc Liên Team, Blockers & Risks

| Nhiệm vụ | Phụ thuộc | Ảnh hưởng và cách xử lý trong phạm vi Team 3 |
| :--- | :--- | :--- |
| **VLRA-69** | Phiên bản RAG v2, schema/payload và cách chạy dịch vụ được Team 2 thống nhất bàn giao. | Đối chiếu contract và kiểm thử tương thích trên phiên bản bàn giao. Nếu chưa đủ điều kiện chạy, kiểm thử Backend độc lập bằng fixture và ghi rõ phần kiểm chứng còn thiếu trong hồ sơ local. |
| **VLRA-70** | API public và citation từ Backend; dịch vụ tra cứu nguyên văn nguồn cho Viewer. | Kiểm thử UI/SSE bằng mock chuẩn contract trước; xác nhận lại luồng answer/citation/Viewer khi Backend kết nối RAG v2. |
| **VLRA-69** | "RAG v2" là PR #54 của Team 2 (VLRA-66, 67, 68: Pipeline v2, prompt v3, Verification), chưa merge tại 08/11/2026 (head `d1b32c3`). Diff của PR không sửa `team2_rag/api/`, `team2_rag/errors.py`, `team2_rag/models/response.py` hoặc `contracts/`. | Kiểm tương thích trên commit của PR (hoặc commit sau khi merge) và ghi commit đó cùng phiên bản `contracts/v0.1` vào hồ sơ local. Nếu bản merge khác commit đã kiểm và chạm các phần trên thì kiểm lại. |
| **VLRA-69, VLRA-70** | Ghi nhận 08/11/2026: AI Service trên `develop` trả mã lỗi public (`SERVICE_UNAVAILABLE` 503, `UPSTREAM_TIMEOUT` 504, `UPSTREAM_INVALID_RESPONSE` 502) trong khi `HttpAiClient` chỉ nhận mã nội bộ (`LLM_UNAVAILABLE`, `RETRIEVAL_TIMEOUT`…), nên lỗi 503/504 bị đổi thành 502 `UPSTREAM_ERROR`, `retryable = false`. [CONTRACT](../../../contracts/v0.1/CONTRACT.md) hiện không liệt kê mã lỗi nội bộ. | Backend nhận cả mã nội bộ và mã public tương ứng rồi ánh xạ theo bảng lỗi [ARCHITECTURE §7](../../../docs/ARCHITECTURE.md); thống nhất danh sách mã lỗi AI Service gửi sang với Team 2 trong phạm vi VLRA-69. |
| **Cả hai** | Baseline, schema và payload bàn giao thống nhất. | Nếu khác tên trường, kiểu dữ liệu, trạng thái hoặc phiên bản nguồn, ghi rõ mâu thuẫn và chờ quyết định phần phụ thuộc; không tự thêm field/trạng thái hoặc sửa dữ liệu nguồn để che lỗi. |

- Không đồng nhất kết quả mock với kết quả chạy RAG v2 thật hoặc xác nhận tính đúng pháp lý.
- Tái sử dụng kiểm thử đã có; cập nhật hoặc bổ sung trong phạm vi hai nhiệm vụ khi có khoảng thiếu hoặc thay đổi liên quan.
- Hồ sơ Spec Kit và kết quả validate lưu local theo [quy trình Team 3](../README.md#quy-trình-thực-hiện-nhiệm-vụ); thư mục tuần chỉ giữ `tasks.md`.
