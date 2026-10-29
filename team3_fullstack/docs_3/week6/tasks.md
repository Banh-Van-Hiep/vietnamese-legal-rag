# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 6
## Phân Hệ: Fullstack & System (Team 3)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 6 (Quy đổi học phần: Tuần 3 cũ + 3 = Tuần 6 mới).
- **Mục tiêu trọng tâm:**
  - Hoàn thiện module tích hợp HTTP Client trên Java Backend (`HttpAiClient`) sử dụng `RestClient` hoặc `WebClient` có cấu hình connection timeout 2 giây và read timeout 50 giây để gọi sang FastAPI AI Service (`POST /internal/v1/query`).
  - Triển khai lớp chuyển đổi dữ liệu (Data Mapping Layer) 2 chiều chuẩn mực giữa `snake_case` nội bộ (Team 1 & 2) và `camelCase` phía public client.
  - Hoàn thiện cỗ máy trạng thái (State Machine) trên cơ sở dữ liệu PostgreSQL cho cặp tin nhắn: quản lý chặt chẽ trạng thái `pending`, `completed`, `failed`.
  - Nâng cấp bộ giải mã frame SSE trên React Frontend: xử lý an toàn lỗi mạng, ngắt kết nối giữa chừng và hiển thị mượt mà từng mảnh `delta`.
  - Đạt điều kiện nghiệm thu cổng **Gate G3 (Real Data Ready)** cho luồng tích hợp tầng Backend/Frontend.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T3-07** | **Lập trình `HttpAiClient` kết nối FastAPI AI Service (Port 8001)**<br>- Xây dựng component `HttpAiClient` gọi `POST /internal/v1/query` với payload `InternalQueryRequest`.<br>- Tự động cấp phát và truyền header truy vết phân tán `X-Request-ID` (UUID) xuyên suốt sang AI Service.<br>- Cấu hình giới hạn thời gian chờ: connect timeout $\le 2$s, read timeout $\le 50$s; xử lý ném ngoại lệ khi AI Service quá tải hoặc mất kết nối. | - Java Backend gọi trực tiếp và nhận dữ liệu RAG thành công từ AI Service của Team 2.<br>- Xử lý chuẩn xác các mã HTTP 502, 503, 504 từ upstream.<br>- Không giữ DB connection/transaction trong suốt thời gian chờ AI phản hồi. |
| **VLRA-T3-08** | **Xây dựng Lớp Ánh Xạ Dữ Liệu Hai Chiều (Snake $\leftrightarrow$ Camel Mapping)**<br>- Lập trình `AiContractMapper`: chuyển đổi từ DTO nội bộ `RagResponse` (`citation_id`, `chunk_id`, `document_id`...) sang `PublicCitation` và `ChatCompleteResponse` (`citationId`, `chunkId`, `documentId`...).<br>- Lập trình `DocumentService`: gọi endpoint nội bộ `GET /internal/v1/documents/{doc_id}/articles/{art_id}` và ánh xạ sang `PublicArticleResponse`. | - 100% các trường dữ liệu được map chính xác, không làm biến dạng giá trị URL và chuỗi ASCII của các legal IDs.<br>- Unit test kiểm tra tính toàn vẹn của mapper pass 100%. |
| **VLRA-T3-09** | **Hoàn thiện State Machine & Quản lý Lịch sử Tin Nhắn trong DB**<br>- Triển khai logic luân chuyển trạng thái tin nhắn trên `MessageRepository`:<br>  + Khởi tạo: User completed, Assistant pending.<br>  + Thành công: Cập nhật Assistant completed, lưu citations vào bảng con trong 1 transaction.<br>  + Thất bại: Cập nhật Assistant failed, lưu `errorCode`.<br>- Lập trình phương thức dựng `history` gửi xuống AI Service: trích xuất tối đa 5 cặp gần nhất có trạng thái `completed` và `answer_status = "answered"`. | - Dữ liệu hội thoại và trích dẫn được lưu trữ nhất quán trên PostgreSQL.<br>- Không bao giờ gửi các tin nhắn bị `failed` hoặc `insufficient_context` vào mảng `history` gửi xuống AI. |
| **VLRA-T3-10** | **Nâng cấp Bộ Giải Mã SSE Client & Quản lý UI State trên React**<br>- Nâng cấp `useChatStream`: hỗ trợ tự động nhận diện `conversationId` từ `meta` event và cập nhật URL trình duyệt `/c/:conversationId`.<br>- Xử lý trạng thái nút bấm "Gửi": disable khi hội thoại đang `pending`.<br>- Render định dạng Markdown an toàn cho nội dung câu trả lời (chống tấn công XSS, sanitize HTML). | - Giao diện cập nhật mượt mà khi nhận các event `delta`.<br>- Hiển thị đúng trạng thái khi gặp kịch bản `insufficient_context` (không hiển thị khung trích dẫn rỗng). |

---

## 3. Thiết Kế Kiến Trúc, State Machine & Luồng SSE Frame

### 3.1. Thiết Kế Phân Tầng Dịch Vụ Backend (Service Layer Architecture)
```
[Client SSE Request]
       │
       ▼
[ChatStreamController] ──> Kiểm tra tính hợp lệ & Cấp phát X-Request-ID
       │
       ▼
[ChatService] ───────────> 1. Mở Transaction: Tạo User Message + Assistant Pending
       │                    2. Commit Transaction (Giải phóng DB Connection Pool)
       │
       ▼
[HttpAiClient] ──────────> 3. HTTP POST /internal/v1/query (Chờ AI tối đa 50s)
       │                    Header: X-Request-ID
       ▼
[FastAPI AI Service] ────> 4. Trả về JSON RagResponse (status, answer, citations)
       │
       ▼
[ChatService] ───────────> 5. Mở Transaction mới: 
       │                       - Update Assistant Message sang "completed"
       │                       - Insert các bản ghi vào bảng "citations"
       │                       - Update "request_receipt"
       ▼
[ChatStreamController] ──> 6. Phát Event 'delta' (tách câu) và Event 'complete'
```

### 3.2. Thuật Toán Trích Xuất Lịch Sử Hội Thoại Gửi Xuống AI (History Builder)
Theo quy tắc nghiệp vụ tại mục 8.4 Baseline v2.0:
```java
public List<InternalHistoryItem> buildHistoryForAi(Long conversationId) {
    // 1. Lấy danh sách tin nhắn của hội thoại sắp xếp theo sequenceNo ASC
    List<Message> messages = messageRepository.findByConversationIdOrderBySequenceNoAsc(conversationId);
    
    // 2. Lọc chỉ lấy các cặp user - assistant hoàn chỉnh đã hoàn thành và có câu trả lời
    List<InternalHistoryItem> history = new ArrayList<>();
    // Ghép cặp và lấy tối đa 5 cặp gần nhất
    // Loại trừ các lượt bị lỗi (failed) hoặc thiếu căn cứ (insufficient_context)
    
    // 3. Kiểm tra tổng độ dài nội dung (tối đa 20.000 Unicode code points)
    // Nếu vượt quá, loại bỏ cặp cũ nhất trọn vẹn, không cắt lẻ một tin nhắn
    return history;
}
```

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. DTO Ánh Xạ Giữa Hai Biên Giao Tiếp
```java
// DTO tiếp nhận từ AI Service (snake_case)
public record InternalRagResponse(
    String status,
    String answer,
    List<InternalCitation> citations
) {}

public record InternalCitation(
    @JsonProperty("citation_id") String citationId,
    @JsonProperty("chunk_id") String chunkId,
    @JsonProperty("document_id") String documentId,
    @JsonProperty("article_id") String articleId,
    @JsonProperty("document_title") String documentTitle,
    String article,
    String clause,
    String point,
    @JsonProperty("source_url") String sourceUrl
) {}

// DTO phát ra Public SSE (camelCase)
public record PublicCitation(
    String citationId,
    String chunkId,
    String documentId,
    String articleId,
    String documentTitle,
    String article,
    String clause,
    String point,
    String sourceUrl
) {}
```

### 4.2. Khung SSE Frame Khi Nhận Kết Quả RAG Thật Từ AI Service
```http
event: meta
data: {"conversationId":101,"clientRequestId":"99999999-9999-4999-9999-999999999999","userMessageId":201,"assistantMessageId":202,"createdAt":"2026-10-14T08:30:00Z"}

: heartbeat

event: delta
data: {"text":"Căn cứ theo Luật Doanh nghiệp 2020, "}

event: delta
data: {"text":"công ty trách nhiệm hữu hạn có thể có một hoặc nhiều người đại diện theo pháp luật [C1]."}

event: complete
data: {"conversationId":101,"clientRequestId":"99999999-9999-4999-9999-999999999999","userMessageId":201,"assistantMessageId":202,"status":"answered","answer":"Căn cứ theo Luật Doanh nghiệp 2020, công ty trách nhiệm hữu hạn có thể có một hoặc nhiều người đại diện theo pháp luật [C1].","citations":[{"citationId":"C1","chunkId":"luat-59-2020-qh14-v1__dieu-12__k2__0","documentId":"luat-59-2020-qh14-v1","articleId":"dieu-12","documentTitle":"Luật Doanh nghiệp số 59/2020/QH14","article":"Điều 12","clause":"Khoản 2","point":null,"sourceUrl":"https://vbpl.vn/bocongthuong/Pages/vbpq-toanvan.aspx?ItemID=143940"}],"createdAt":"2026-10-14T08:30:00Z"}

```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 3 $\rightarrow$ Team 2 (RAG)** | - Kết nối thành công `HttpAiClient` sang dịch vụ FastAPI nội bộ tại `http://localhost:8001/internal/v1/query`.<br>- Báo cáo kết quả kiểm thử gọi hàm trực tiếp. | Team 2 theo dõi log xử lý của Reranker và LLM tương ứng với từng `X-Request-ID`. | Mạng nội bộ HTTP / Docker Network. |
| **Team 2 $\rightarrow$ Team 3 (AI Service)** | - Cung cấp endpoint proxy `GET /internal/v1/documents/{document_id}/articles/{article_id}` để Backend lấy Điều luật. | Backend Team 3 phục vụ API Document Viewer cho giao diện Frontend. | REST Endpoint JSON UTF-8. |
| **Team 1 $\rightarrow$ Team 3 (Data)** | - Kiểm tra danh mục văn bản và các đường link HTTPS `source_url` hiển thị đúng trên UI. | Đảm bảo người dùng nhấp mở nguồn bên ngoài trỏ đúng về trang văn bản quy phạm pháp luật của nhà nước. | Kiểm tra đối soát trên database. |

## 6. Kết quả kiểm chứng hiện hành

Đối chiếu từng task/DoD và phần còn thiếu tại [verification.md](verification.md), ngày 29/10/2026.
Không suy hoàn thành từ kế hoạch hoặc từ số test PASS; mock và live được kết luận riêng.

Hồ sơ kiểm chứng07–10: [spec/plan/tasks](vlra-t3-07-10-integration/spec.md),
[validation](vlra-t3-07-10-integration/validation.md).09/10 đạt kỹ thuật;07/08 còn
phụ thuộc query/article thật và G3. Không giao lại implementation đã được kiểm chứng.
