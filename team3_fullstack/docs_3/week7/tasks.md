# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 7
## Phân Hệ: Fullstack & System (Team 3)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 7 (Quy đổi học phần: Tuần 4 cũ + 3 = Tuần 7 mới).
- **Mục tiêu trọng tâm:**
  - Hoàn thiện toàn diện cơ chế **Idempotency** và kiểm soát đồng thời trên bảng `RequestReceipt` (đáp ứng 100% bộ kiểm thử 12 kịch bản `IDEM-01` đến `IDEM-12`).
  - Hoàn thiện component **Legal Document Viewer** dạng side-panel trên React kết nối với API Backend `GET /api/v1/documents/{documentId}?articleId={articleId}` (hỗ trợ hiển thị Markdown, cuộn mượt mà, tải nội dung tức thì).
  - Chủ trì điều phối, deduplicate, phân tầng (tỷ lệ 60% Dev / 40% Test, xấp xỉ 75% answerable / 25% unanswerable) và **đóng băng chính thức bộ dữ liệu Golden Dataset v1 (100–150 câu hỏi)**.
  - Tổng duyệt và tích hợp toàn hệ thống, nghiệm thu thành công **Gate G2 (Mock Integration)** và **Gate G4 (Live RAG MVP)**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T3-11** | **Triển khai Cơ chế Chống Gửi Trùng & Tái Phát Kết Quả (Idempotency Engine)**<br>- Tra cứu `clientRequestId` trên bảng `RequestReceipt` trước khi tạo transaction hội thoại.<br>- Nếu trùng ID và đang xử lý $\rightarrow$ Trả về HTTP 409 `REQUEST_IN_PROGRESS`.<br>- Nếu trùng ID nhưng khác nội dung câu hỏi/hội thoại $\rightarrow$ Trả về HTTP 409 `REQUEST_ID_CONFLICT`.<br>- Nếu trùng ID và đã `completed` $\rightarrow$ Mở SSE phát lại (replay) toàn bộ các frame `meta`, `delta`, `complete` từ `response_snapshot` mà không gọi lại AI. | - Bộ kiểm thử tự động `IdempotencyIntegrationTest` (12 test cases) pass 100%.<br>- Tuyệt đối không tạo bản ghi hội thoại hoặc tin nhắn trùng lặp khi người dùng click liên tục nút "Gửi". |
| **VLRA-T3-12** | **Hoàn thiện Document Viewer & Tối ưu Trải nghiệm Tra cứu Điều luật**<br>- Nâng cấp component Document Viewer: slide-over panel bên phải, hỗ trợ hiển thị tiêu đề văn bản, số Điều, tên Điều và toàn bộ nội dung nguyên văn.<br>- Kiểm tra xác thực khớp nối: `documentId` và `articleId` trả về từ API phải trùng khớp chính xác với tham số yêu cầu.<br>- Bổ sung nút "Mở nguồn gốc" mở trực tiếp liên kết HTTPS của cơ quan nhà nước trên tab mới an toàn (`rel="noopener noreferrer"`). | - Document Viewer tải nội dung mượt mà dưới 1 giây.<br>- Xử lý chuẩn xác mã HTTP 404 khi người dùng truy cập Điều luật không tồn tại.<br>- Giao diện co giãn tốt trên màn hình tablet và mobile. |
| **VLRA-T3-13** | **Chủ trì Phân Tầng, Đánh Giá & Đóng Băng Golden Dataset v1 (100–150 câu)**<br>- Tập hợp câu hỏi từ 3 team, mở rộng quy mô từ 30–50 câu lên 100–150 câu đã qua rà soát nghiệp vụ.<br>- Thực hiện phân chia ngẫu nhiên có phân tầng (Stratified Split): 60% Dev Set (phục vụ tối ưu tuần 8–10) và 40% Test Set (khóa chặt phục vụ benchmark tuần 11).<br>- Sinh mã băm SHA-256 và đóng băng manifest `team2_rag/data/golden/golden_dataset_v1.manifest.json`. | - Golden Dataset v1 đạt quy mô 100–150 câu, tỷ lệ phân chia đúng chuẩn.<br>- Toàn bộ thành viên ký biên bản đóng băng dữ liệu đánh giá.<br>- Sửa lỗi validator của repo để kiểm tra đúng trạng thái `answered`. |
| **VLRA-T3-14** | **Điều phối Kiểm thử Toàn trình E2E & Nghiệm thu Gate G4 (Live RAG MVP)**<br>- Tổ chức buổi tổng duyệt kịch bản demo trực tiếp luồng người dùng trên môi trường local.<br>- Demo thành công 3 trường hợp: (1) Câu hỏi nghiệp vụ P0 có trích dẫn nhấp mở được Điều luật; (2) Câu hỏi ngoài phạm vi trả về `insufficient_context`; (3) Thử nghiệm gửi trùng UUID nhận kết quả replay tức thì. | - Cả 3 team nghiệm thu đạt yêu cầu Gate G4.<br>- Có video và ảnh chụp lưu trữ làm bằng chứng kỹ thuật. |

---

## 3. Thiết Kế Kiến Trúc, State Machine & Luồng SSE Frame

### 3.1. Bảng Xử Lý Ma Trận Idempotency Toàn Diện (IDEM-01 đến IDEM-12)

| Mã Test | Tình huống kiểm tra | Trạng thái hiện tại trong DB | Hành vi xử lý của Hệ thống |
| :--- | :--- | :--- | :--- |
| **IDEM-01** | UUID mới, không gửi `conversationId` | Chưa có trong bảng | Tạo hội thoại mới, tạo cặp message, phát SSE bình thường. |
| **IDEM-02** | UUID mới, gửi `conversationId` hợp lệ | Chưa có trong bảng | Thêm cặp message mới vào hội thoại, phát SSE. |
| **IDEM-03** | Cùng UUID, cùng câu hỏi, đang xử lý | `state = "pending"` | Trả về HTTP 409 `REQUEST_IN_PROGRESS`, không gọi AI thêm. |
| **IDEM-04** | Cùng UUID, cùng câu hỏi, đã xử lý xong | `state = "completed"` | Mở stream SSE replay lại kết quả từ `response_snapshot`. |
| **IDEM-05** | Cùng UUID, cùng câu hỏi, đã thất bại | `state = "failed"` | Trả về HTTP Error tương ứng từ `error_snapshot`. |
| **IDEM-06** | Cùng UUID nhưng gửi nội dung câu hỏi khác | Đã tồn tại | Trả về HTTP 409 `REQUEST_ID_CONFLICT` (chặn nhầm lẫn UUID). |
| **IDEM-07** | Cùng UUID nhưng gửi `conversationId` khác | Đã tồn tại | Trả về HTTP 409 `REQUEST_ID_CONFLICT`. |
| **IDEM-08** | Gửi lại cùng UUID nhưng bỏ `conversationId` | Đã gắn hội thoại cũ | Tự động liên kết đúng hội thoại đã gắn trước đó. |
| **IDEM-09** | Hai request gửi tới đồng thời cùng UUID | Đua tranh ghi DB | Transaction chặn race condition, chỉ 1 bên thành công, bên kia nhận 409. |
| **IDEM-10** | UUID mới nhưng hội thoại đang có lượt pending | Hội thoại bận | Trả về HTTP 409 `CONVERSATION_BUSY`. |
| **IDEM-11** | UUID thuộc về hội thoại đã bị xóa | Đã lưu tombstone | Trả về HTTP 404 `REQUEST_NOT_FOUND`. |
| **IDEM-12** | Gửi câu hỏi và xóa hội thoại đồng thời | Đua tranh khóa | Khóa theo dòng hội thoại, thao tác sau thấy busy hoặc not found. |

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Khung SSE Frame Replay (Khi gửi lại cùng `clientRequestId` đã hoàn thành)
Hệ thống không gọi lại AI Service mà tự động tái phát lại chính xác chuỗi sự kiện đã lưu trong `RequestReceipt`:
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream;charset=UTF-8
Cache-Control: no-store
X-Request-ID: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
X-Conversation-ID: 101

event: meta
data: {"conversationId":101,"clientRequestId":"44444444-4444-4444-8444-444444444444","userMessageId":201,"assistantMessageId":202,"createdAt":"2026-10-07T04:00:00Z"}

event: delta
data: {"text":"Theo quy định của pháp luật doanh nghiệp [C1]."}

event: complete
data: {"conversationId":101,"clientRequestId":"44444444-4444-4444-8444-444444444444","userMessageId":201,"assistantMessageId":202,"status":"answered","answer":"Theo quy định của pháp luật doanh nghiệp [C1].","citations":[{"citationId":"C1","chunkId":"luat-59-2020-qh14-v1__dieu-12__k1__0","documentId":"luat-59-2020-qh14-v1","articleId":"dieu-12","documentTitle":"Luật Doanh nghiệp 2020","article":"Điều 12","clause":"Khoản 1","point":null,"sourceUrl":"https://vbpl.vn/..."}],"createdAt":"2026-10-07T04:00:00Z"}

```

### 4.2. Khung HTTP Error Phản Hồi Xung Đột (HTTP 409 Conflict)
```json
{
  "error": {
    "code": "REQUEST_IN_PROGRESS",
    "message": "Lượt hỏi trước với cùng mã định danh đang được xử lý. Vui lòng đợi trong giây lát.",
    "retryable": true
  }
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 3 $\rightarrow$ Cả nhóm (G4)** | - Bản demo hệ thống Live RAG MVP hoạt động End-to-End đầy đủ tính năng.<br>- File Golden Dataset v1 (100–150 câu) đã phân tầng và đóng băng chính thức. | Mốc nghiệm thu kỹ thuật quan trọng nhất giữa kỳ; cung cấp tập dữ liệu để Team 1 và Team 2 bước vào tối ưu tuần 8–10. | Buổi báo cáo tiến độ chung & Git commit hash. |
| **Team 2 $\rightarrow$ Team 3 (AI Service)** | - Dịch vụ RAG Live ổn định, phản hồi trong ngân sách 45 giây.<br>- Không bị lỗi sai cấu trúc JSON hoặc trích dẫn rác. | Backend Java ánh xạ an toàn và phát stream ra ngoài giao diện cho người dùng cuối. | Endpoint `/internal/v1/query`. |
| **Team 1 $\rightarrow$ Team 3 (Viewer)** | - Dịch vụ tra cứu Điều luật siêu tốc `get_article()` đã test p95 $\le 200$ms. | Frontend Document Viewer hiển thị toàn văn Điều luật ngay tức thì khi người dùng nhấp vào trích dẫn. | API `/api/v1/documents/{documentId}?articleId={articleId}`. |
