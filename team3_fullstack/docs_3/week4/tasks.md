# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 4
## Phân Hệ: Fullstack & System (Team 3)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 4 (Quy đổi học phần: Tuần 1 cũ + 3 = Tuần 4 mới).
- **Mục tiêu trọng tâm:**
  - Thiết kế kiến trúc tổng thể của Java Spring Boot Backend kết nối cơ sở dữ liệu PostgreSQL và React + TypeScript Frontend (Client Gateway & State Management).
  - Thiết kế mô hình dữ liệu quan hệ (Entity Data Model) trên PostgreSQL: `Conversation`, `Message`, `Citation`, và bảng kiểm soát chống gửi trùng `RequestReceipt`.
  - Thiết kế giao thức truyền tải trực tuyến Public Chat SSE (`POST /api/v1/chat/stream`) với 5 loại frame (`meta`, `: heartbeat`, `delta`, `complete`, `error`) và quy chuẩn `camelCase` + ID số an toàn.
  - Thiết kế cơ chế đảm bảo tính Idempotency và kiểm soát xung đột đồng thời bằng khóa phiên `clientRequestId` (UUID v4).
  - Thiết kế Wireframe giao diện Chat panel, Sidebar lịch sử và Legal Document Viewer dạng slide-over.
  - Khởi tạo repository, cấu hình nhánh Git, template PR và đạt nghiệm thu **Gate G1 (Document Baseline)**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T3-01** | **Thiết kế Kiến trúc Backend Spring Boot & Mô hình Dữ liệu PostgreSQL**<br>- Thiết kế cấu trúc phân tầng Java: Controller $\rightarrow$ Service $\rightarrow$ Repository $\rightarrow$ DTO/Entity.<br>- Thiết kế schema cơ sở dữ liệu cho 4 entity chính: `conversations`, `messages`, `citations`, `request_receipts`.<br>- Thiết lập các ràng buộc toàn vẹn: unique constraint `(conversation_id, sequence_no)`, khóa ngoại, chỉ mục tìm kiếm và khóa an toàn. | - Tài liệu Entity-Relationship Diagram (ERD) hoàn tất.<br>- Script migration DDL (`schema.sql`) được khởi tạo.<br>- Được thông qua trong tài liệu `docs/ARCHITECTURE.md`. |
| **VLRA-T3-02** | **Đặc tả Giao thức Public Chat SSE & Wireframe Trải nghiệm Người dùng**<br>- Thiết kế giao thức Server-Sent Events cho endpoint `POST /api/v1/chat/stream`.<br>- Quy định cấu trúc dữ liệu cho 5 frame: `meta` (khởi tạo ID), `: heartbeat` (giữ kết nối 10s), `delta` (nối chuỗi), `complete` (kết quả chuẩn 8 trường), `error` (báo sự cố).<br>- Thiết kế Wireframe UI Chat, Sidebar hội thoại và Document Viewer (hỗ trợ responsive từ 360px). | - Đặc tả Public Contract SSE hoàn chỉnh, tuân thủ `camelCase` và ID số.<br>- Bộ bản vẽ Wireframe / Mockup UI được cả nhóm phê duyệt. |
| **VLRA-T3-03** | **Thiết kế Giải thuật Idempotency & State Machine Tin Nhắn**<br>- Thiết kế ma trận 12 kịch bản chống gửi trùng (`IDEM-01` đến `IDEM-12`) dựa trên `clientRequestId` (UUID v4).<br>- Định nghĩa máy trạng thái vòng đời của `Message`: `pending` $\rightarrow$ `completed` / `failed`.<br>- Thiết kế cơ chế khóa luồng (Row-level Locking trên `Conversation`) và background job phục hồi các request bị treo quá 60s (`PROCESSING_INTERRUPTED`). | - Bảng quy tắc State Transition và Ma trận Idempotency được viết chi tiết.<br>- Thiết kế giải thuật đảm bảo không xảy ra race condition giữa hai request gửi đồng thời. |
| **VLRA-T3-04** | **Khởi tạo Project Skeleton: Spring Boot Backend & React Frontend**<br>- Tiếp tục project Java 25, Spring Boot 4.1.1, Maven Wrapper hiện có; cấu hình `pom.xml`, biến môi trường `.env`.<br>- Khởi tạo project React 18, TypeScript, Vite, Tailwind CSS, cấu hình React Router.<br>- Thiết lập nhánh `main`, `develop`, branch protection và PR template. | - Cả hai project Backend và Frontend build thành công cục bộ.<br>- Skeleton được push lên nhánh `develop` trên GitHub. |
| **VLRA-T3-05** | **Kế hoạch Điều phối & Định dạng Golden Dataset Phase 1**<br>- Thống nhất format JSON cho tập câu hỏi kiểm thử ban đầu `golden_phase1_30cai.json`.<br>- Phân bổ chỉ tiêu mỗi thành viên trong nhóm đóng góp 5–10 câu hỏi pháp luật doanh nghiệp P0 kèm căn cứ chuẩn.<br>- Thiết kế script kiểm tra tính hợp lệ cú pháp của dataset. | - Cấu trúc file JSON Golden Dataset được ban hành.<br>- Checklist câu hỏi P0 được giao cho các thành viên. |

---

## 3. Thiết Kế Kiến Trúc, State Machine & Luồng SSE Frame

### 3.1. Mô Hình Dữ Liệu Quan Hệ (PostgreSQL ERD Schema)

ERD vật lý và từ điển đầy đủ 4 bảng/36 cột được duy trì tại
[thiết kế persistence chung](../../../docs/team3_fullstack/persistence-design.md#2-erd-theo-schema-hiện-tại),
đối chiếu [DDL hiện hành](../../backend/src/main/resources/db/chat-schema.sql).
Không sao chép một sơ đồ khác trong nhiệm vụ tuần.

Tên `Conversation`, `Message`, `Citation`, `RequestReceipt` trong nhiệm vụ là các
thực thể logic; tên bảng vật lý lần lượt là `chat_conversations`, `chat_messages`,
`chat_citations`, `chat_receipts`. File DDL được khởi tạo là `chat-schema.sql`;
chưa dùng công cụ migration theo phiên bản.

- `chat_messages.conversation_id` và `chat_citations.assistant_message_id` có FK cascade.
- Receipt giữ binding bằng ID, không có FK tới nội dung bị xóa để tombstone vẫn tồn tại.
- Snapshot là TEXT chứa JSON; trạng thái xóa dùng `state='deleted'` và `deleted_at`.
- Citation dùng PK kép `(assistant_message_id, citation_id)`, không có cột id riêng.
- `title` lưu VARCHAR(400); API/title builder vẫn giới hạn 100 Unicode code point.

Nội dung trên ghi đúng implementation đã kiểm chứng, không tự thay yêu cầu nghiệp vụ
hoặc xác nhận nhóm đã duyệt mô hình vật lý. Điều kiện thông qua thiết kế theo baseline
và các điểm cần xác nhận được theo dõi tại [biên bản](verification.md).

### 3.2. Vòng Đời Trạng Thái (State Machine) & Concurrency
- **Transaction Khởi Tạo Lượt:** Khi nhận request từ client, Backend thực hiện trong 1 transaction:
  1. Tạo `user message` với `state = "completed"`.
  2. Tạo `assistant message` với `state = "pending"`, `content = null`.
  3. Ghi `request_receipt` với `state = "pending"`.
- **Hoàn thành thành công:** Nhận kết quả từ AI Service $\rightarrow$ cập nhật `assistant message` sang `state = "completed"`, lưu trích dẫn vào bảng `citations`, cập nhật `request_receipt` sang `state = "completed"` kèm `response_snapshot`.
- **Gặp sự cố:** Cập nhật `assistant message` sang `state = "failed"`, gán `error_code`, cập nhật `request_receipt` lưu `error_snapshot`.
- **Background Recovery (Quá hạn 60s):** Định kỳ mỗi 30 giây, một background scheduler quét các `messages` có trạng thái `pending` với tuổi tạo $> 60$ giây $\rightarrow$ tự động chuyển sang `state = "failed"`, gán mã lỗi `PROCESSING_INTERRUPTED`, `retryable = true`.

### 3.3. Luồng Sự Kiện SSE Streaming Toàn Trình
```
Client (React)                Backend (Spring Boot)           AI Service (FastAPI)
      │                                │                                │
      │ POST /api/v1/chat/stream       │                                │
      ├───────────────────────────────►│                                │
      │                                │ Check Idempotency              │
      │                                │ DB Transaction (User + Pending)│
      │ HTTP 200 (text/event-stream)   │                                │
      │◄───────────────────────────────┤                                │
      │ event: meta                    │                                │
      │◄───────────────────────────────┤                                │
      │                                │ POST /internal/v1/query        │
      │                                ├───────────────────────────────►│
      │ : heartbeat (định kỳ 10s)      │                                │ (Đang retrieve,
      │◄───────────────────────────────┤                                │  rerank & call LLM)
      │                                │                                │
      │                                │ JSON RagResponse (200 OK)      │
      │                                │◄───────────────────────────────┤
      │                                │ Validate & Persist DB          │
      │ event: delta (0..N mảnh)       │                                │
      │◄───────────────────────────────┤                                │
      │ event: complete (8 trường)     │                                │
      │◄───────────────────────────────┤                                │
      │ Đóng stream an toàn            │                                │
```

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Quy Ước Casing & Giới Hạn Kiểu Dữ Liệu
- **Public Client:** Toàn bộ request/response sử dụng định dạng JSON UTF-8 với quy chuẩn **`camelCase`**.
- **Định danh số an toàn:** `conversationId`, `userMessageId`, `assistantMessageId` là số nguyên dương trong giới hạn an toàn JavaScript: $1 \le \text{ID} \le 9.007.199.254.740.991$ (`Number.MAX_SAFE_INTEGER`). Java sử dụng kiểu `Long`, Database sử dụng `BIGINT`.
- **IDempotency Key:** `clientRequestId` bắt buộc là chuỗi UUID v4 chuẩn.

### 4.2. DTO Lớp Request & Response (Java Spring Boot)
```java
public record ChatRequest(
    @NotBlank @Size(min = 1, max = 2000) String question,
    @NotNull UUID clientRequestId,
    Long conversationId
) {}

public record StreamMetaResponse(
    Long conversationId,
    UUID clientRequestId,
    Long userMessageId,
    Long assistantMessageId,
    Instant createdAt
) {}

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

public record ChatCompleteResponse(
    Long conversationId,
    UUID clientRequestId,
    Long userMessageId,
    Long assistantMessageId,
    String status, // "answered" hoặc "insufficient_context"
    String answer,
    List<PublicCitation> citations,
    Instant createdAt
) {}
```

### 4.3. Ví Dụ Cấu Trúc Toàn Bộ Các Frame SSE Chuẩn

#### Frame 1: Khởi tạo phiên Stream (`event: meta`)
```http
event: meta
data: {"conversationId":101,"clientRequestId":"44444444-4444-4444-8444-444444444444","userMessageId":201,"assistantMessageId":202,"createdAt":"2026-10-07T04:00:00Z"}

```

#### Frame 2: Nhịp tim duy trì kết nối (`: heartbeat`)
```http
: heartbeat

```

#### Frame 3: Mảnh nội dung câu trả lời (`event: delta`)
```http
event: delta
data: {"text":"Theo quy định của pháp luật doanh nghiệp [C1]."}

```

#### Frame 4: Kết thúc thành công (`event: complete`)
```http
event: complete
data: {"conversationId":101,"clientRequestId":"44444444-4444-4444-8444-444444444444","userMessageId":201,"assistantMessageId":202,"status":"answered","answer":"Theo quy định của pháp luật doanh nghiệp [C1].","citations":[{"citationId":"C1","chunkId":"luat-59-2020-qh14-v1__dieu-12__k1__0","documentId":"luat-59-2020-qh14-v1","articleId":"dieu-12","documentTitle":"Luật Doanh nghiệp 2020","article":"Điều 12","clause":"Khoản 1","point":null,"sourceUrl":"https://vbpl.vn/..."}],"createdAt":"2026-10-07T04:00:00Z"}

```

#### Frame 5: Báo sự cố (`event: error`)
```http
event: error
data: {"error":{"code":"UPSTREAM_TIMEOUT","message":"Thời gian xử lý của dịch vụ AI vượt quá ngân sách quy định.","retryable":true}}

```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 3 $\rightarrow$ Team 2 (RAG)** | - Đặc tả yêu cầu giao tiếp nội bộ `POST /internal/v1/query` (JSON `snake_case`, Header `X-Request-ID`).<br>- Giới hạn lịch sử hội thoại: tối đa 5 cặp `(role, content)` gần nhất, tổng code points $\le 20.000$. | Team 2 xây dựng FastAPI adapter tiếp nhận request chuẩn xác từ Backend. | Tài liệu `docs/ARCHITECTURE.md` & họp kỹ thuật. |
| **Team 3 $\rightarrow$ Team 1 (Retrieval)** | - Đặc tả yêu cầu tra cứu nguyên văn Điều luật: `GET /internal/v1/documents/{document_id}/articles/{article_id}`. | Team 1 tối ưu hàm `get_article()` trả về đủ 6 trường dữ liệu phục vụ Document Viewer. | [Contract internal article](../../../contracts/v0.1/internal_article.schema.json). |
| **Team 3 $\rightarrow$ Cả nhóm (Golden Dataset)** | - Mẫu cấu trúc chuẩn và quy trình đóng góp câu hỏi Golden Dataset Phase 1 (30–50 câu). | Team 1 và Team 2 đóng góp câu hỏi kiểm thử chuyên sâu theo phân hệ phụ trách. | File mẫu `team2_rag/data/golden/golden_phase1_30cai.json`. |

## 6. Kết quả kiểm chứng hiện hành

Đối chiếu từng task/DoD và phần còn thiếu tại [verification.md](verification.md), ngày 29/10/2026.
Không suy hoàn thành từ kế hoạch hoặc từ số test PASS; mock và live được kết luận riêng.
