# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 5
## Phân Hệ: Fullstack & System (Team 3)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 5 (Quy đổi học phần: Tuần 2 cũ + 3 = Tuần 5 mới).
- **Mục tiêu trọng tâm:**
  - Lập trình **Mock SSE Controller** trên Java Spring Boot cho endpoint `POST /api/v1/chat/stream`, phát đầy đủ các frame `meta`, `: heartbeat`, `delta`, `complete`, `error` để kiểm chứng luồng streaming.
  - Xây dựng khung giao diện **Frontend React + TypeScript**: Chat Panel, Sidebar quản lý hội thoại, bộ phân giải frame SSE (`fetch` + `ReadableStream`), và stub **Document Viewer** mở Điều theo cặp `documentId` + `articleId`.
  - Cung cấp các REST endpoints quản trị hội thoại cơ bản (`/api/v1/conversations`, `/messages`, `DELETE`).
  - Chủ trì thu thập, loại bỏ trùng lặp và rà soát định dạng cho tập câu hỏi **Golden Dataset ban đầu (30–50 câu)** đóng góp từ cả 3 team.
  - Đáp ứng các tiêu chí Jira: **VLRA22**, **VLRA23**, **VLRA24** và đạt điều kiện nghiệm thu cổng **Gate G2 (Mock Integration)**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA22** | **Lập trình Mock SSE Controller & REST Endpoints trên Java Spring Boot**<br>- Cấu hình Spring MVC `SseEmitter` bất đồng bộ, `async timeout = 55s`, header `Cache-Control: no-store`.<br>- Lập trình Mock SSE Controller cho `POST /api/v1/chat/stream`: phát `meta` ngay lập tức, phát heartbeat giả lập độ trễ, phát các mảnh `delta`, và chốt bằng `complete` hoặc `error`.<br>- Triển khai các REST endpoints cơ bản: `GET /api/v1/conversations`, `GET /messages`, `DELETE /conversations/{id}`. | - Controller chạy độc lập, phát đúng chuẩn SSE RFC.<br>- Kiểm thử thành công qua `curl -N -X POST /api/v1/chat/stream`.<br>- Xử lý ngắt kết nối an toàn khi client đóng tab giữa chừng (`emitter.onCompletion`, `onTimeout`). |
| **VLRA23** | **Khởi tạo Khung Giao Diện React & SSE Parser Client**<br>- Dựng layout giao diện chuẩn: Sidebar danh sách hội thoại bên trái, Chat Panel chính ở giữa, Document Viewer trượt từ bên phải.<br>- Viết custom hook `useChatStream`: sử dụng `fetch` + `ReadableStream` đọc buffer nhị phân, xử lý an toàn UTF-8 đa byte và ghép dòng `event:` / `data:`.<br>- Lập trình component stub **Legal Document Viewer**: gọi API mở Điều theo `documentId` + `articleId`, hiển thị nguyên văn và nút đóng panel. | - Frontend chạy mượt mà tại `http://localhost:5173`, kết nối thông suốt với Mock Backend.<br>- Xử lý mượt mà việc nối chuỗi text từ các event `delta`.<br>- Nhấp vào citation `[C1]` trong tin nhắn mock mở được Document Viewer hiển thị đúng nội dung giả lập. |
| **VLRA24** | **Chủ trì Thu thập, Hợp nhất & Đóng gói Golden Dataset Phase 1**<br>- Thu thập các câu hỏi đóng góp từ thành viên Team 1, Team 2 và Team 3.<br>- Thực hiện deduplicate, chuẩn hóa chính tả và kiểm tra tính nhất quán giữa `expected_status`, `ground_truth` và `gold_chunk_ids`.<br>- Đóng gói thành file `team2_rag/data/golden/golden_phase1_30cai.json` đạt quy mô từ 30 đến 50 câu. | - File JSON Golden Dataset hoàn thiện, pass qua schema validator.<br>- Đảm bảo phân bổ đều các nhóm nghiệp vụ P0: thành lập (10 câu), vốn/cổ đông (8 câu), quản trị (8 câu), giải thể (4 câu), thiếu dữ kiện (10 câu). |
| **VLRA-T3-06** | **Cấu hình CORS, Môi trường & Script Kiểm Thử Tự Động Mock**<br>- Cấu hình Spring Security / WebMvcConfigurer cho phép CORS từ origin `http://localhost:5173`, expose các header `X-Request-ID`, `X-Conversation-ID`.<br>- Viết script kiểm thử tự động `test_sse_mock.sh` hoặc test suite JUnit 5 kiểm tra tính toàn vẹn của chuỗi frame SSE. | - Frontend gọi API Backend không bị chặn CORS.<br>- Toàn bộ test integration mock pass 100%. |

---

## 3. Thiết Kế Kiến Trúc, State Machine & Luồng SSE Frame

### 3.1. Kỹ Thuật Xử Lý SSE Phía Client (React Fetch + ReadableStream)
Do `EventSource` nguyên bản của trình duyệt chỉ hỗ trợ HTTP GET và không cho phép gửi kèm body JSON, Frontend bắt buộc phải dùng `fetch` phối hợp với `ReadableStreamDefaultReader`:
```typescript
// Ý tưởng giải thuật xử lý buffer chia đoạn của SSE Parser
async function readChatStream(response: Response, onMeta, onDelta, onComplete, onError) {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || ""; // Giữ lại phần chưa kết thúc dòng đôi

    for (const block of lines) {
      if (block.startsWith(":")) continue; // Bỏ qua comment heartbeat
      
      const eventMatch = block.match(/^event:\s*(\w+)/m);
      const dataMatch = block.match(/^data:\s*(.+)$/m);
      
      if (eventMatch && dataMatch) {
        const eventType = eventMatch[1];
        const data = JSON.parse(dataMatch[1]);
        
        switch (eventType) {
          case "meta": onMeta(data); break;
          case "delta": onDelta(data.text); break;
          case "complete": onComplete(data); break;
          case "error": onError(data.error); break;
        }
      }
    }
  }
}
```

### 3.2. Cấu Trúc Giao Diện Người Dùng (Wireframe Layout)
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Vietnamese Legal RAG Assistant (Pháp luật Doanh nghiệp)                     │
├──────────────┬───────────────────────────────────────────────┬───────────────┤
│ [Cuộc trò    │ Chat Panel:                                   │ Document      │
│  chuyện mới] │                                               │ Viewer:       │
│              │ [User]: Công ty TNHH 2 thành viên ai đại diện?│               │
│ Lịch sử:     │                                               │ Điều 12.      │
│ - Thành lập  │ [Assistant]:                                  │ Người đại     │
│   công ty    │ Theo quy định, công ty TNHH có thể có một     │ diện theo     │
│ - Đại diện   │ hoặc nhiều người đại diện theo pháp luật [C1].│ pháp luật     │
│   pháp luật  │                                               │               │
│ - Góp vốn    │ ── Căn cứ trích dẫn ───────────────────────── │ Nội dung      │
│              │ [C1] Điều 12 - Luật Doanh nghiệp 2020 (Mở ↗)  │ nguyên văn... │
│              ├───────────────────────────────────────────────┤               │
│              │ [ Nhập câu hỏi pháp lý...              ] [Gửi]│ [Đóng]        │
└──────────────┴───────────────────────────────────────────────┴───────────────┘
```

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Cấu Trúc Request Chat Public (`POST /api/v1/chat/stream`)
```json
{
  "clientRequestId": "44444444-4444-4444-8444-444444444444",
  "question": "Công ty TNHH 2 thành viên ai là người đại diện theo pháp luật?",
  "conversationId": null
}
```

### 4.2. Chuỗi Frame SSE Mẫu Được Phát Ra Từ Mock Controller
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream;charset=UTF-8
Cache-Control: no-store
Connection: keep-alive
X-Request-ID: 88888888-8888-8888-8888-888888888888
X-Conversation-ID: 101

event: meta
data: {"conversationId":101,"clientRequestId":"44444444-4444-4444-8444-444444444444","userMessageId":201,"assistantMessageId":202,"createdAt":"2026-10-07T04:00:00Z"}

: heartbeat

event: delta
data: {"text":"Nội dung phản hồi giả lập từ Mock Service. "}

event: delta
data: {"text":"Theo quy định kiểm thử, doanh nghiệp có các quyền và nghĩa vụ luật định [C1]."}

event: complete
data: {"conversationId":101,"clientRequestId":"44444444-4444-4444-8444-444444444444","userMessageId":201,"assistantMessageId":202,"status":"answered","answer":"Nội dung phản hồi giả lập từ Mock Service. Theo quy định kiểm thử, doanh nghiệp có các quyền và nghĩa vụ luật định [C1].","citations":[{"citationId":"C1","chunkId":"mock_v1_art1_clause1","documentId":"mock_v1","articleId":"art1","documentTitle":"Văn bản thử nghiệm tích hợp Mock","article":"Điều 1","clause":"Khoản 1","point":null,"sourceUrl":"https://example.com/mock-law"}],"createdAt":"2026-10-07T04:00:00Z"}

```

### 4.3. Cấu Trúc Dữ Liệu Document Viewer (`GET /api/v1/documents/{documentId}?articleId={articleId}`)
```json
{
  "documentId": "mock_v1",
  "documentTitle": "Văn bản thử nghiệm tích hợp Mock",
  "articleId": "art1",
  "article": "Điều 1",
  "content": "Điều 1. Quy định kiểm thử tích hợp\nNội dung mẫu này được dùng để chứng minh luồng mở Document Viewer hoạt động độc lập mà không cần nạp toàn bộ cơ sở dữ liệu thật.",
  "sourceUrl": "https://example.com/mock-law"
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 3 $\rightarrow$ Cả nhóm (G2)** | - Khung ứng dụng Web chạy hoàn chỉnh trên nền Mock Data.<br>- Video / Ảnh chụp minh chứng nghiệm thu Gate G2: người dùng gửi câu hỏi, nhận stream text, nhấp citation xem toàn văn Điều luật. | Cả nhóm có sản phẩm demo sớm để báo cáo tiến độ và kiểm chứng trải nghiệm người dùng (UX). | Demo trực tiếp trong buổi họp nghiệm thu tuần 5. |
| **Team 2 $\rightarrow$ Team 3 (AI Mock)** | - Triển khai FastAPI Mock Server cổng 8001 của Team 2 trả về 2 kịch bản `answered` và `insufficient_context`. | Team 3 kiểm thử kết nối Backend Java $\leftrightarrow$ AI Service qua mạng HTTP nội bộ. | Endpoint `POST /internal/v1/query`. |
| **Team 1 $\rightarrow$ Team 3 (Viewer Mock)** | - Hàm mock `get_article(..., is_mock=True)` với cặp dữ liệu mẫu `mock_v1` / `art1`. | Team 3 kết nối và hiển thị nội dung nguyên văn trên component Document Viewer. | Endpoint tra cứu Điều luật nội bộ. |
