# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 10

## Phân Hệ: Fullstack & System (Team 3)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm

- **Giai đoạn:** Tuần 10.
- **Nguồn giao việc:** Epic [VLRA-4](https://banhvanhiep.atlassian.net/browse/VLRA-4), gồm [VLRA-75](https://banhvanhiep.atlassian.net/browse/VLRA-75) và [VLRA-76](https://banhvanhiep.atlassian.net/browse/VLRA-76).
- **Phụ trách:** Team 3; chưa phân công thành viên cho từng nhiệm vụ.
- **Trạng thái giao việc:** To Do cho cả hai nhiệm vụ; chưa xác nhận hoàn thành.
- **Mục tiêu trọng tâm:**
  - Hoàn thiện Chat Panel: trạng thái chờ, thông báo lỗi mạng, thử lại an toàn và nút **Dừng nhận**; kiểm tra bố cục responsive và kết nối với RAG Pipeline v2.
  - Hoàn thiện Document Viewer: tự động cuộn và làm nổi bật Khoản/Điểm đang xem, nút mở văn bản nguồn gốc, dùng Article Store thật của Team 1.
  - Xây dựng và chạy một bộ kiểm thử E2E bao phủ đầy đủ các trạng thái UI, đạt 100%.
- **Căn cứ:** [ARCHITECTURE](../../../docs/ARCHITECTURE.md), [CODING_CONVENTIONS](../../../docs/CODING_CONVENTIONS.md), [thiết kế Frontend](../../../docs/team3_fullstack/frontend-design.md), [thiết kế hội thoại](../../../docs/team3_fullstack/conversation-design.md), [API public](../../../docs/team3_fullstack/public-api-specification.md) và [Contract](../../../contracts/v0.1/CONTRACT.md).

Giữ đúng hai nhiệm vụ Jira, không tạo task con. Phần lớn chức năng đã có từ các tuần trước (mục 3.1); tuần này đối chiếu với DoD, bổ sung phần thiếu và gom kiểm thử thành một bộ E2E chạy bằng một lệnh. Không đổi Public API, Internal API hoặc schema trong `contracts/v0.1`.

---

## 2. Bảng Nhiệm Vụ & Tiêu Chí Hoàn Thành

| Mã Jira | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-75** | **Hoàn thiện Chat Panel: trạng thái loading, lỗi mạng và nút Dừng nhận**<br>- Xử lý mượt trạng thái chờ từ lúc gửi câu hỏi đến khi nhận `complete` hoặc `error`.<br>- Thông báo lỗi mạng và cơ chế thử lại an toàn theo `retryable` và quy tắc định danh lượt (`clientRequestId`).<br>- Nút "Dừng nhận stream" cho phép người dùng chủ động ngắt luồng nhận câu trả lời.<br>- Kiểm tra bố cục responsive và kết nối giao diện với RAG Pipeline v2. | - Khi gửi: hiện chỉ báo đang chờ (có `role="status"`), khóa gửi trùng; mỗi lần bấm gửi chỉ tạo đúng một `POST /api/v1/chat/stream`.<br>- Mất kết nối, Backend tắt, stream đứt hoặc quá 60 giây: hiện thông báo an toàn, không lộ chi tiết kỹ thuật; lượt được đánh dấu chưa rõ kết quả và **thử lại dùng lại đúng `clientRequestId`** (phát lại kết quả nếu server đã xong), không tạo lượt thứ hai.<br>- Lỗi đã rõ từ server: chỉ có nút "Thử lại" khi `retryable = true` và là lượt cuối, theo bảng lỗi [ARCHITECTURE §7](../../../docs/ARCHITECTURE.md).<br>- "Dừng nhận" chỉ hiện khi đang nhận; bấm thì ngừng đọc stream ngay, **không** gửi yêu cầu hủy xử lý AI; lượt trên server vẫn hoàn tất và "Tải lại trạng thái" lấy được kết quả cuối mà không gọi AI lần nữa; nội dung không bị gắn vào hội thoại khác.<br>- Responsive: ở 360, 768 và 1280 px, Chat Panel, ô nhập, thẻ citation và nút Dừng nhận/Thử lại hiển thị đủ, không cuộn ngang trang.<br>- Kết nối RAG Pipeline v2 (`develop` sau PR #54): ít nhất một lượt `answered` và một lượt `insufficient_context` chạy thật qua UI; ghi commit RAG, cấu hình và LLM đã dùng trong kết quả local.<br>- **Đầu ra:** Chat Panel hoàn chỉnh các trạng thái chờ, lỗi, thử lại và dừng nhận, hoạt động với RAG Pipeline v2. |
| **VLRA-76** | **Hoàn thiện Document Viewer và bộ test E2E giao diện**<br>- Tự động cuộn và làm nổi bật Khoản/Điểm của Điều luật đang xem.<br>- Nút mở văn bản nguồn gốc.<br>- Xây dựng và chạy bộ kiểm thử tự động E2E bao phủ các trạng thái của UI (mục 4.2). | - Mở citation: Viewer tải đúng Điều theo `documentId`/`articleId`, tự cuộn tới Khoản/Điểm được trích và đánh dấu đoạn đó; chuyển sang citation khác thì cuộn và đánh dấu theo citation mới.<br>- Chỉ đánh dấu khi `locateCitedUnit` xác định được duy nhất một đoạn; nếu không, hiện toàn Điều kèm ghi chú rõ ràng, không đánh dấu sai.<br>- Nút "Văn bản nguồn gốc" mở `sourceUrl` ở tab mới với `noopener noreferrer`; khi Điều không tồn tại (404) vẫn có liên kết nguồn từ citation để đối chiếu.<br>- Kiểm trên Article Store thật của Team 1 (`data/doanh-nghiep/processed/articles.jsonl`, VLRA-71): nội dung là nguyên văn Điều, không phải chunk.<br>- Bộ E2E chạy bằng một lệnh, bao phủ toàn bộ trạng thái ở mục 4.2, **đạt 100%** ở chế độ mock; kết quả chạy với RAG v2 thật ghi riêng.<br>- **Đầu ra:** Frontend v2 và Document Viewer đầy đủ chức năng tra cứu; bộ test E2E các trạng thái UI đạt 100%. |

---

## 3. Thiết Kế Kỹ Thuật & Luồng Tích Hợp

### 3.1. Hiện trạng cần đối chiếu (trên `develop`, 13/11/2026)

| Phần | Đã có | Việc tuần 10 |
| :--- | :--- | :--- |
| Trạng thái chờ | `MessageBubble` hiển thị "Đang tra cứu căn cứ pháp lý…" (`role="status"`), ô nhập khóa khi đang gửi | Kiểm DoD bằng E2E, sửa nếu phát hiện thiếu |
| Lỗi mạng, thử lại | `client.ts`/`chatStream.ts` phân biệt `NETWORK_ERROR`, `CLIENT_TIMEOUT`, `STREAM_INTERRUPTED` (chưa rõ kết quả); `retryPolicy.ts`, `pendingTurn.ts` giữ UUID | Kiểm thông báo hiển thị và E2E Backend tắt/mạng đứt |
| Dừng nhận | `useChat.stopReceiving`, nút "Dừng nhận" trong `ChatPage.tsx`; E2E tuần 8 `U04_SLOW3G_STOP_REPLAY_SAME_UUID` | Gom vào bộ E2E mới |
| Responsive | E2E `CORPUS_VIEWPORT_360/768` chỉ kiểm Viewer | Thêm kiểm Chat Panel ở 360/768/1280 |
| Viewer | `DocumentViewer` có `scrollIntoView`, `<mark data-testid="cited-highlight">`, link nguồn và link dự phòng khi 404 | Kiểm trên Article Store thật, đổi nhãn nút nguồn gốc nếu cần |
| E2E | `vlra44-e2e.mjs` (E01–E10), `week8-ui.mjs` (U01–U05), `team3-acceptance.mjs` (CORPUS_*, G4_*) | Gom thành một bộ theo ma trận mục 4.2 |

### 3.2. Chat Panel — VLRA-75

- Tái sử dụng React/TypeScript, `useChat`, `chatStream`, `retryPolicy`, `pendingTurn` và component hiện có.
- Dừng nhận chỉ hủy việc đọc stream phía trình duyệt (AbortController). Lượt trên server tiếp tục theo state machine; kết quả lấy lại bằng replay cùng `clientRequestId` hoặc tải lại lịch sử.
- Không thêm event SSE, field hoặc endpoint public; không tự gửi lại câu hỏi với UUID mới khi kết quả chưa rõ.
- Chi tiết: [thiết kế Frontend §4](../../../docs/team3_fullstack/frontend-design.md) và [thiết kế hội thoại](../../../docs/team3_fullstack/conversation-design.md).

### 3.3. Document Viewer — VLRA-76

- Tái sử dụng `DocumentViewer`, `DocumentDrawer`, `useArticle`, `locateCitedUnit` và route `/documents/:documentId?articleId=…`.
- Nguồn nội dung: Backend `GET /api/v1/documents/{documentId}?articleId={articleId}` → AI Service `GET /internal/v1/documents/{document_id}/articles/{article_id}` → Article Store của Team 1 (VLRA-71, VLRA-72).
- Nội dung Điều render dạng text (`whitespace-pre-wrap`), không dùng `dangerouslySetInnerHTML`; liên kết nguồn chỉ nhận URL HTTPS đã được kiểm tra.
- Chi tiết: [thiết kế Frontend §5](../../../docs/team3_fullstack/frontend-design.md).

---

## 4. Interface, Contract & Mock Data

### 4.1. Các hợp đồng cần giữ

| Biên giao tiếp | Quy tắc | Nguồn chuẩn |
| :--- | :--- | :--- |
| Frontend → Backend | `POST /api/v1/chat/stream`, `clientRequestId` UUIDv4; SSE `meta`, `delta`, `complete`, `error`, heartbeat | [chat_stream.schema.json](../../../contracts/v0.1/chat_stream.schema.json), [API public](../../../docs/team3_fullstack/public-api-specification.md) |
| Viewer | `GET /api/v1/documents/{documentId}?articleId={articleId}` trả 6 trường; 404 `DOCUMENT_NOT_FOUND`/`ARTICLE_NOT_FOUND` | [API public](../../../docs/team3_fullstack/public-api-specification.md), [internal_article.schema.json](../../../contracts/v0.1/internal_article.schema.json) |
| Lỗi | Envelope `{code, message, retryable}`; hành vi thử lại theo `retryable` | [ARCHITECTURE §7](../../../docs/ARCHITECTURE.md), [error_response.schema.json](../../../contracts/v0.1/error_response.schema.json) |

### 4.2. Ma trận trạng thái UI cho bộ E2E — VLRA-76

| Mã | Trạng thái | Kỳ vọng chính | Có thể tái sử dụng |
| :--- | :--- | :--- | :--- |
| S01 | Chưa có hội thoại | Câu gợi ý, ô nhập sẵn sàng | — |
| S02 | Đang gửi/nhận | Chỉ báo chờ, khóa gửi trùng, một request | U04 |
| S03 | `answered` | Câu trả lời khớp `complete`, đủ thẻ citation | E02, U01, G4_P0_CITATION |
| S04 | `insufficient_context` | Thông báo thiếu căn cứ, không thẻ citation, không kiểu lỗi | E07, U02, G4_INSUFFICIENT |
| S05 | Lỗi retryable | Thông báo an toàn, nút Thử lại, thử lại thành công | E08, E09 |
| S06 | Lỗi không retryable | Thông báo an toàn, không nút Thử lại | U03 |
| S07 | Backend tắt / mạng đứt | Chưa rõ kết quả, thử lại cùng UUID, không tạo lượt mới | — |
| S08 | Dừng nhận | Ngừng đọc stream, tải lại trạng thái lấy kết quả cuối | U04 |
| S09 | Đổi hội thoại khi đang nhận | Kết quả cũ không gắn vào hội thoại mới | U05 |
| S10 | Lịch sử còn lượt pending | Chặn gửi mới, có nút tải lại trạng thái | — |
| S11 | Viewer mở citation | Đúng Điều, cuộn và đánh dấu Khoản/Điểm, đổi citation thì cập nhật | E03 |
| S12 | Viewer không xác định được đoạn | Toàn Điều, có ghi chú, không đánh dấu | — |
| S13 | Viewer 404 | Thông báo không tìm thấy, có liên kết nguồn từ citation | E06, CORPUS_404 |
| S14 | Văn bản nguồn gốc | Mở `sourceUrl` tab mới, `noopener noreferrer` | CORPUS_CONTENT |
| S15 | Responsive | Chat Panel và Viewer ở 360/768/1280 không cuộn ngang | CORPUS_VIEWPORT_* |

### 4.3. Dữ liệu mock

- Dùng HTTP mock của Team 2 (`team2_rag.api.mock_app`, kịch bản `answered`/`insufficient_context`) và fixture hiện có; lỗi và payload sai tạo bằng stub trong bộ test, không thêm endpoint public chỉ để kích hoạt tình huống kiểm thử.
- Kết quả mock ghi nhãn mock, không dùng để kết luận chất lượng RAG thật.

---

## 5. Phụ Thuộc Liên Team, Blockers & Risks

| Nhiệm vụ | Phụ thuộc | Ảnh hưởng và cách xử lý trong phạm vi Team 3 |
| :--- | :--- | :--- |
| **VLRA-75** | RAG Pipeline v2 đã merge (PR #54, 08/11/2026); mặc định `RAG_RERANK=false`, `RAG_RETRIEVAL_TIMEOUT=10`. | Ghi cấu hình thật vào kết quả local. LLM miễn phí có giới hạn số request: chạy tuần tự, ghi riêng lỗi do giới hạn LLM. |
| **VLRA-76** | Article Store của Team 1 (VLRA-71, VLRA-72) đã merge ngày 10/11/2026. | Kiểm Viewer trên Article Store thật; nếu thiếu Điều thì báo Team 1, không tự sửa dữ liệu nguồn. |
| **Cả hai** | Trình duyệt kiểm thử (Edge/Chrome qua CDP) và môi trường Windows của thành viên chạy test. | Bộ E2E tự bật/tắt các tiến trình do nó tạo và ghi rõ môi trường; trường hợp chỉ chạy được ở mock được ghi là giới hạn. |

- Không đồng nhất kết quả mock với kết quả chạy RAG v2 thật.
- "Đạt 100%" áp dụng cho toàn bộ trạng thái ở mục 4.2 trong cùng một lần chạy; ca bị bỏ qua không được tính là đạt.
- Hồ sơ Spec Kit và kết quả kiểm chứng lưu local theo [quy trình Team 3](../README.md#quy-trình-thực-hiện-nhiệm-vụ); thư mục tuần chỉ giữ `tasks.md`.
