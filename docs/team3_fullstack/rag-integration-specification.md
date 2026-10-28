# Tích hợp Java với dịch vụ RAG

**Loại:** thiết kế chung Team 3. **Đối chiếu source:** `62c3556`, ngày 28/10/2026.
**Căn cứ:** [ARCHITECTURE](../ARCHITECTURE.md) và [CODING_CONVENTIONS](../CODING_CONVENTIONS.md).
Mô tả implementation không tự thay yêu cầu hoặc chứng minh đã nghiệm thu.

## 1. Interface nội bộ và owner

Theo ARCHITECTURE §2.2/§3.2 và CODING_CONVENTIONS §2/§3.2/§4.
Team 3 sở hữu [AiClient](../../team3_fullstack/backend/src/main/java/com/legalai/backend/ai/AiClient.java),
[HttpAiClient](../../team3_fullstack/backend/src/main/java/com/legalai/backend/ai/HttpAiClient.java),
[AiResponseValidator](../../team3_fullstack/backend/src/main/java/com/legalai/backend/ai/AiResponseValidator.java).
Team 2 sở hữu Python service/pipeline; Team 1 sở hữu retrieval/article store.
Java không gọi LLM trực tiếp, tự tạo legal chunk hoặc sửa corpus để làm citation hợp lệ.

## 2. Request/response

| Thao tác | Giao tiếp hiện tại |
| --- | --- |
| Query |POST `{RAG_BASE_URL}/internal/v1/query`, JSON question/history, X-Request-ID |
| Article |GET `{RAG_BASE_URL}/internal/v1/documents/{document_id}/articles/{article_id}`, X-Request-ID |
| Casing |Internal snake_case; Java map sang public camelCase |
| History |Tối đa5 cặp completed/answered,20.000 code point; dựng từ DB, không nhận từ FE |

```json
{"question":"Câu hỏi kiểm thử giao tiếp","history":[]}
```

Query response có đúng status/answer/citations. Answer1–12000 code point; answered có1–10
citation, insufficient_context có[] và không marker. Mỗi citation có đúng9 key:
citation_id, chunk_id, document_id, article_id, document_title, article, clause, point,
source_url. clause/point nullable. Article response có đúng6 key: document_id,
document_title, article_id, article, content, source_url; IDs phải khớp request.

Mapping thuần tại [StreamDtos](../../team3_fullstack/backend/src/main/java/com/legalai/backend/chat/stream/StreamDtos.java)
và [PublicDocumentController](../../team3_fullstack/backend/src/main/java/com/legalai/backend/document/PublicDocumentController.java).
Không sửa ID/URL/title để che sai phiên bản; không thêm snippet không có nguồn.
History lọc/ghép cặp chi tiết tại [thiết kế hội thoại](conversation-design.md#4-history-và-tiêu-đề).

## 3. Validation và mapping lỗi

HttpAiClient dùng JDK HttpClient, không follow redirect, connect timeout2s; deadline
sendAsync + đọc toàn bộ body tối đa50s. Timeout được giới hạn cấu hình ≤50000 ms.
Không tự retry provider/HTTP query; FE quyết định replay UUID dựa trên trạng thái.

- Kiểm Content-Type application/json; từ chối body query>262144 byte, article>2000000 byte.
- Từ chối duplicate key/trailing token, sai kiểu, thiếu/extra key.
- AiResponseValidator kiểm status, answer, nguồnHTTPS/host, lengths và legal IDs ASCII.
- Marker phải liên tục C1..Cn theo lần nhắc đầu, tối đa10; membership với array đúng,
  không marker/citation thừa hoặc chunk trùng. Điều này không chứng minh claim đúng luật.
- Article content tối đa200000 code point, title500, article100; giữ nguyên toàn Điều.
  Không gọi LLM hoặc ghép kết quả retrieval để dựng nguyên văn.

| Internal response | Public logical status/code | Retryable |
| --- | --- | --- |
|502 INVALID_LLM_OUTPUT/CITATION_INVALID hoặc body sai|502 UPSTREAM_INVALID_RESPONSE|false |
|503 RETRIEVAL_UNAVAILABLE/LLM_UNAVAILABLE hoặc không kết nối được|503 SERVICE_UNAVAILABLE|true |
|504 RETRIEVAL_TIMEOUT/LLM_TIMEOUT hoặc timeout client|504 UPSTREAM_TIMEOUT|true |
|Query4xx|502 UPSTREAM_CONTRACT_ERROR|false |
|Article404 DOCUMENT_NOT_FOUND/ARTICLE_NOT_FOUND đúng envelope|404 cùng code|false |
|Upstream lỗi khác đúng envelope|502 UPSTREAM_ERROR|false |

Error nội bộ phải đúng error/code/message/retryable. Java trả thông báo an toàn,
không đưa raw exception/provider payload cho FE. Sau khi SSE mở, status trên là logical
status để lưu/replay; frame lỗi truyền trong HTTP200. Xem [API public](public-api-specification.md).

## 4. Profile, deadline và readiness

| Thành phần | Giá trị/quy tắc |
| --- | --- |
| HttpAiClient |Profile rag, base URL http(s) không userinfo/query/fragment |
| AI deadline theo baseline |≤45s, Python chịu trách nhiệm pipeline |
| Java HTTP wait / SSE |≤50s /55s |
| FE chat / article |60s /15s; article FE có thể hết chờ trước timeout HTTP nội bộ |
| Persistence |Transaction5s, đóng trước khi gọi AI; không đồng nghĩa deadline pipeline5s |
| Worker |Mặc định8, bounded; overload trả SERVICE_UNAVAILABLE |

Team 2 có app `team2_rag.api:create_app` và mock factory
`team2_rag.api.mock_app:create_mock_app`. Sự tồn tại của app/route không chứng minh index,
model, provider hoặc snapshot đã sẵn sàng. Liveness Java không thay readiness Python.
Mock được cấu hình tường minh; không fallback ngầm khi live lỗi. Không ghi API key vào docs.

## 5. Những điểm chưa được nâng thành contract

CODING_CONVENTIONS §2.2 quy định legal ID lowercase; validator hiện nhận cả uppercase
qua regex `[A-Za-z0-9_-]+`. Cần thống nhất cách siết validation trước khi thay API,
không mô tả regex rộng là quyết định thay chuẩn ID. NFC cũng cần đối chiếu theo API public.
Snapshot/applicability/grounding phải được Team 1/2 xác minh; schema PASS không xác nhận pháp lý.

Bộ test nguồn để đối chiếu, không phải báo cáo chạy mới:
[HttpAiClientTests](../../team3_fullstack/backend/src/test/java/com/legalai/backend/HttpAiClientTests.java),
[AiResponseValidatorTests](../../team3_fullstack/backend/src/test/java/com/legalai/backend/AiResponseValidatorTests.java),
[publicApi.test.ts](../../team3_fullstack/frontend/src/api/publicApi.test.ts).
