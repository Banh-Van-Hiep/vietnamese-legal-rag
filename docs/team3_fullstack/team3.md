# Team 3 — Kiến trúc, API và luồng tích hợp

**Vai trò:** đặc tả chức năng thứ cấp của Team 3, diễn giải từ Docs v2.0 và Jira.
**Đối chiếu:** 23/10/2026. Đây là đích thiết kế, không phải báo cáo triển khai đã hoàn thành.

## 1. Nguồn áp dụng và xử lý khác biệt

Nguồn yêu cầu gốc chỉ gồm:

- [Docs v2.0 — Legal RAG](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0),
  đặc biệt §5, §8, §9, §10.4–10.5 và §11.1.2. Đã đọc nội dung liên quan ngày 23/10;
  bản Docs hiện trả về tiêu đề Legal RAG, phần mở đầu ghi v2.0, modifiedTime 13/10/2026.
- Ticket Jira được giao; tuần 4 gồm VLRA-41/42/43/44, nguyên văn đã cung cấp được
  giữ tại [yêu cầu tuần 4](../../specs/team3/week-04/requirements.md).

Tài liệu này, các specs, báo cáo phối hợp và shared contract files là thứ cấp.
Nếu thứ cấp khác nguồn gốc thì sửa thứ cấp; nếu hai nguồn gốc xung đột thì báo
người dùng và chờ quyết định ở phần phụ thuộc, không tự đặt thứ tự ưu tiên.
Code/config/test dùng để xác định hiện trạng, không tự tạo yêu cầu.

**W4-Q1 đã chốt ngày 23/10/2026:** người dùng yêu cầu triển khai VLRA-41 theo
Docs v2.0: public `/api/v1/chat/stream`, internal `/internal/v1/query`. Tên route
cũ trong Jira được giữ nguyên văn để truy vết; chưa sửa Jira trực tiếp.
Yêu cầu JSON của VLRA-42 không tự mâu thuẫn SSE: mỗi SSE data là một object JSON.

## 2. Kiến trúc và ranh giới trách nhiệm

Theo Docs v2.0 §5/§8:

Phạm vi MVP là pháp luật doanh nghiệp và quy định liên quan từ luật khác theo
corpus/snapshot được công bố (§1.4–1.5). Grounding, provenance và hiệu lực đơn vị
Điều/Khoản/Điểm theo §6/§7; lịch sử hội thoại không là bằng chứng pháp lý.

```text
React Frontend → Java Backend → Python RAG → thư viện retrieval/article Team 1
                    ↕                ↕
               PostgreSQL        LLM provider
```

- Team 1 sở hữu corpus/registry, cleaning/chunking, metadata/applicability,
  BM25/Dense/Hybrid/RRF và thư viện lấy nguyên văn Điều.
- Team 2 sở hữu query processing, reranker, context, prompt, LLM clients,
  output/citation validation và service HTTP JSON nội bộ.
- Team 3 sở hữu API public, hội thoại/persistence/idempotency, Frontend, Viewer,
  tích hợp và kiểm thử ứng dụng. Chỉ package `ai/` giao tiếp dịch vụ Python;
  các service phụ thuộc boundary client, không gọi LLM trực tiếp.
- Kế thừa Java/Spring Boot/Maven, React/TypeScript/Vite và cấu trúc theo feature.
  Controller → application service → repository/client adapter; không giữ DB
  transaction khi chờ AI. Docs v2.0 §8.1 dùng MVC SSE và worker có giới hạn.

## 3. Public API theo Docs v2.0

### 3.1. Endpoint và quy ước

| Method / path | Kết quả đích | Nguồn |
| --- | --- | --- |
| `POST /api/v1/chat/stream` | `200 text/event-stream`, chat chính | §9.2–9.4; người dùng chốt áp dụng tuần 4 |
| `GET /api/v1/conversations` | Array Conversation, không PageResponse | §9.2/9.6 |
| `GET /api/v1/conversations/{conversationId}/messages` | Array Message theo sequenceNo | §9.2/9.6 |
| `DELETE /api/v1/conversations/{conversationId}` | 204; không xóa khi pending | §9.2/9.6/9.7 |
| `GET /api/v1/documents/{documentId}?articleId={articleId}` | PublicArticleResponse | §9.11/9.12 |
| `POST /api/v1/conversations` | Tùy chọn bổ sung: 201 Conversation + Location | §9.2 |
| `GET /api/v1/conversations/{conversationId}` | Tùy chọn bổ sung: detail | §9.2 |
| `GET /api/v1/health` | HTTP liveness, không kiểm tra pipeline | §9.2 |

Public field dùng camelCase; conversation/message ID là số nguyên dương an toàn
cho JavaScript (≤9.007.199.254.740.991), Java Long. clientRequestId là UUID v4 do FE
cấp cho lượt mới. Legal IDs vẫn là string theo phiên bản nguồn; không đổi kiểu
âm thầm để khớp code cũ. Thời gian RFC3339 UTC. CORS allowlist, expose các header
trace/conversation/Location theo §9.1. Không dùng phân trang v1.2 làm contract đích.

ChatRequest có question (sau trim 1–2.000 code point), clientRequestId và
conversationId tùy chọn/null; không nhận history/model/scenario/context từ FE.
FE gửi request JSON, nhận SSE theo §9.3; JSON là định dạng dữ liệu, SSE là transport
response. Không suy từ chữ JSON rằng toàn bộ response phải trả một lần.

### 3.2. SSE và kết quả cuối

Theo §9.4: validate/nhận lượt và commit trước khi mở stream. Phát meta, heartbeat
khi chờ; kết quả RAG phải được validate và lưu thành công rồi mới phát answer.

| Event | Nội dung / invariant |
| --- | --- |
| meta | Event đầu, đúng một lần; conversationId, clientRequestId, userMessageId, assistantMessageId, createdAt |
| delta | 0..N đoạn text có thứ tự, chỉ từ answer đã validate và persist |
| complete | Kết quả chuẩn: conversationId, clientRequestId, userMessageId, assistantMessageId, status, answer, citations, createdAt |
| error | ErrorResponse an toàn; terminal lỗi, không đi kèm complete cùng lượt |
| Heartbeat | Comment khi chờ, không phải answer hoặc sự kiện nghiệp vụ, không kéo dài deadline |

Mỗi stream phục vụ đầy đủ có đúng một terminal complete hoặc error rồi đóng.
FE parse event/data và các frame bị chia, UTF-8, LF/CRLF; complete thay answer/citation
bằng bản chuẩn. Không nối mọi data thành văn bản. SSE MVP không yêu cầu truyền token
trực tiếp từ provider, không yêu cầu hiển thị suy nghĩ nội bộ LLM (§1.5/§9.4).

## 4. Internal JSON và mapping nguồn

Theo §7.2/§9.8/§9.9, Java gọi `POST /internal/v1/query`, truyền `X-Request-ID` và
JSON chỉ gồm question/history. Python trả đúng status/answer/citations hoặc error.
History tối đa 5 cặp user/assistant answered + completed gần nhất, cũ → mới,
tổng content ≤20.000 code point. Không gửi lượt hiện tại, pending/failed/insufficient
hoặc public IDs. History hỗ trợ giải tham chiếu, không là căn cứ pháp lý.

InternalCitation có 9 field snake_case, Java map sang PublicCitation:

| Internal | Public |
| --- | --- |
| citation_id | citationId |
| chunk_id | chunkId |
| document_id | documentId |
| article_id | articleId |
| document_title | documentTitle |
| article, clause, point | Giữ tên; clause/point nullable, key vẫn bắt buộc |
| source_url | sourceUrl |

Giữ nguyên giá trị provenance. Answer không rỗng, tối đa 12.000 code point;
answered có 1–10 citation; insufficient_context có array rỗng, không marker.
Marker ánh xạ đúng citation, theo thứ tự xuất hiện; không chunk trùng hoặc citation
thừa. Không thêm snippet khi contract chưa có; schema PASS không chứng minh nguồn
hỗ trợ đầy đủ kết luận pháp lý. Unit applicability/grounding theo §6.4–6.6/§7.6.

Viewer lấy documentId/articleId từ citation, gọi public document endpoint rồi Java
gọi `GET /internal/v1/documents/{document_id}/articles/{article_id}`. Nội dung là
nguyên văn toàn Điều trong article store cùng phiên bản, không gọi LLM/ghép chunk
để dựng nguyên văn. Trả 404 khi không có, không âm thầm thay phiên bản (§9.11–9.12).

## 5. Hội thoại, lỗi và retry

Theo §8.2–8.5/§9.7, tạo user completed + assistant pending + receipt trong một
transaction. Chốt cùng assistant thành completed hoặc failed; receipt bảo vệ gửi
trùng. Persist/constraint phải được kiểm chứng, map in-memory không chứng minh đạt
đích nhiều thread/instance. Xem lịch sử không gọi lại AI.

- Cùng clientRequestId/payload pending → REQUEST_IN_PROGRESS; completed → replay
  kết quả đã lưu; failed → trả lỗi đã lưu, không gọi lại AI.
- ID mới trong hội thoại pending → CONVERSATION_BUSY; payload khác với ID cũ →
  REQUEST_ID_CONFLICT. Không có tính năng nhận lời bổ sung/ngắt xử lý vào lượt đang chạy.
- Mất kết nối chưa biết kết quả → giữ ID, kiểm tra lịch sử/replay; failed đã xác định
  muốn hỏi lại thì dùng ID mới. “Dừng nhận” chỉ dừng nhận stream, không hứa hủy AI.
- Xóa hội thoại không xóa corpus; tombstone ngăn UUID cũ tạo lại hội thoại đã xóa.

ErrorResponse giữ envelope error/code/message/retryable, không chứa answer/secret.
Trước stream dùng HTTP error; sau khi đã mở 200 dùng event:error, không đổi HTTP
thành 502/503/504 nữa. Lỗi truyền output sau completed không đổi DB thành failed.

| Lỗi internal | Mã public / logical status | Nguồn |
| --- | --- | --- |
| INVALID_LLM_OUTPUT / CITATION_INVALID | UPSTREAM_INVALID_RESPONSE / 502, không retry | §9.14 |
| RETRIEVAL_UNAVAILABLE / LLM_UNAVAILABLE | SERVICE_UNAVAILABLE / 503, retryable | §9.14 |
| RETRIEVAL_TIMEOUT / LLM_TIMEOUT | UPSTREAM_TIMEOUT / 504, retryable | §9.14 |
| Query internal 4xx | UPSTREAM_CONTRACT_ERROR / 502, không retry | §9.14 |

Không copy nguyên mã Python làm mã lỗi public chỉ vì một báo cáo thứ cấp ghi như vậy.
Thiếu căn cứ là trạng thái nghiệp vụ hợp lệ, khác lỗi hệ thống. Đối chiếu đầy đủ
mã HTTP, persistence/recovery và deadline tại Docs v2.0 §3.2/§8.5/§9.13–9.14.

## 6. Frontend và kiểm chứng

Theo §8.6–8.7, UI có sidebar hội thoại, chat, citation và Viewer; thể hiện đúng
phạm vi dữ liệu/mock/live. Disable gửi mới khi hội thoại pending. Citation ở complete
là bản chuẩn, mở nguồn bằng IDs; loading/error/404 tại Viewer không xóa answer.
Không render HTML tùy ý từ LLM. Retry không tự tạo ID mới khi kết quả chưa rõ.

Theo §10.4–10.5: kiểm tra contract hai boundary, parser/state SSE, idempotency,
recovery, citation/Viewer và E2E với evidence. Tách G2 mock integration và G4 live
RAG; một gate không đạt chỉ vì có code, mock hoặc một lệnh build thành công.
Nhiệm vụ/AC cụ thể lấy từ Jira; không áp toàn bộ v2.0 vào một ticket ngoài phạm vi.

## 7. Hiện trạng và tài liệu triển khai

Tài liệu mô tả đích v2.0. Inventory develop ngày 21/10 tại
[yêu cầu tuần 4](../../specs/team3/week-04/requirements.md) gắn commit 3d64c4d:
public query/mock v1.2 còn có, HttpAiClient rỗng, Python entry query vẫn mock.
Chưa kiểm tra lại runtime hoặc develop mới vào ngày chuẩn hóa 23/10.

API v1.2 phục vụ đọc implementation và evidence cũ xem
[snapshot trong Git](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/blob/27ef448f02f63075404093b7ac772eda8b2cd513/docs/team3_fullstack/team3.md).
Bản đó là thứ cấp lịch sử, không ghi đè Docs v2.0 hoặc Jira. Không sửa kết quả
nghiệm thu tuần cũ để biến thành bằng chứng đã đạt đích v2.0.

Nhiệm vụ/đặc tả theo tuần: [specs Team 3](../../specs/team3/README.md).
W4-Q1 đã được người dùng giải quyết theo v2.0; khác biệt nguồn mới phải báo người dùng. Tài liệu
này không sửa Google Docs/Jira, shared schema hoặc implementation.

VLRA-41: profile `rag` triển khai SSE/JDBC PostgreSQL và internal HTTP adapter;
profile `mock` là API JSON lịch sử. Xem [báo cáo kiểm chứng](../../specs/team3/week-04/001-vlra-41-rag-query/verification.md)
và [cách chạy](../../specs/team3/week-04/001-vlra-41-rag-query/quickstart.md). Live RAG vẫn cần Team2 bàn giao service.
