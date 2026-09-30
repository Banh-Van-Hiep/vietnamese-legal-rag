# Team 3 — Fullstack

## Responsibilities

- Backend and REST API
- Frontend and UI/UX
- Document viewer
- Integration and deployment

## Scope

Team 3 tự thiết kế implementation bên trong thư mục này. Dữ liệu trao đổi với Team 2 được thống nhất trong `contracts/`.

## Backend (`backend/`)

Spring Boot (Maven, Java) + PostgreSQL. Backend nhận câu hỏi từ frontend, gọi dịch vụ RAG của Team 2 (Python) để lấy câu trả lời kèm trích dẫn, và lưu lịch sử hội thoại.

Nguyên tắc: code chia theo tính năng (package-by-feature); mỗi tính năng gồm Controller → Service → Repository. Chỉ package `ai/` được nói chuyện với Python.

Gốc package: `backend/src/main/java/com/legalai/backend/`

### Gốc dự án

| File | Vai trò |
|---|---|
| `pom.xml` | Khai báo dependency (Spring Web MVC, JPA, Validation, PostgreSQL driver) và phiên bản Java/Spring Boot. |
| `mvnw`, `mvnw.cmd`, `.mvn/` | Maven Wrapper, chạy build mà không cần cài Maven. |
| `Dockerfile` | Đóng gói backend thành image để triển khai *(chưa có)*. |
| `src/main/resources/application.properties` | Cấu hình ứng dụng: kết nối PostgreSQL, JPA, địa chỉ dịch vụ AI (`AI_SERVICE_URL`). |
| `BackendApplication.java` | Điểm khởi chạy của Spring Boot (`main`). |
| `src/test/.../BackendApplicationTests.java` | Test kiểm tra ứng dụng khởi động được. |

### `chat/` — hỏi đáp

| File | Vai trò |
|---|---|
| `ChatController.java` | REST endpoint nhận câu hỏi từ frontend, trả câu trả lời. |
| `ChatService.java` | Xử lý luồng hỏi đáp: lưu câu hỏi, gọi `AiClient`, lưu câu trả lời và trích dẫn, trả kết quả. |
| `dto/ChatRequest.java` | Dữ liệu vào: nội dung câu hỏi, id hội thoại (nếu đang hỏi tiếp). |
| `dto/ChatResponse.java` | Dữ liệu ra: câu trả lời, danh sách trích dẫn, id hội thoại. |

### `conversation/` — lịch sử hội thoại

| File | Vai trò |
|---|---|
| `Conversation.java` | Entity JPA: một cuộc hội thoại (bảng `conversation`). |
| `Message.java` | Entity JPA: một tin nhắn (câu hỏi hoặc câu trả lời) thuộc một hội thoại. |
| `ConversationRepository.java` | Truy cập DB cho `Conversation` (Spring Data JPA). |
| `MessageRepository.java` | Truy cập DB cho `Message`, ví dụ lấy tin nhắn theo hội thoại. |
| `ConversationService.java` | Nghiệp vụ: tạo hội thoại, liệt kê, xem chi tiết, xóa, thêm tin nhắn. |
| `ConversationController.java` | REST endpoint cho lịch sử hội thoại (danh sách, chi tiết, xóa). |

### `document/` — xem nguyên văn điều luật

| File | Vai trò |
|---|---|
| `DocumentController.java` | REST endpoint để frontend mở nguyên văn điều luật khi bấm vào trích dẫn. |
| `DocumentService.java` | Lấy nội dung điều luật (qua `AiClient`, hoặc nguồn dữ liệu do các team thống nhất). |

### `ai/` — nơi duy nhất giao tiếp với Python (Team 2)

| File | Vai trò |
|---|---|
| `AiClient.java` | Interface: hợp đồng gọi dịch vụ AI (hỏi đáp, lấy đoạn luật). Các lớp khác chỉ phụ thuộc interface này. |
| `MockAiClient.java` | Cài đặt giả, trả dữ liệu mẫu để phát triển khi Team 2 chưa xong. |
| `HttpAiClient.java` | Cài đặt thật, gọi dịch vụ Python qua HTTP theo `contracts/`. |
| `dto/RagAnswer.java` | Kết quả RAG: câu trả lời và danh sách trích dẫn. |
| `dto/Citation.java` | Một trích dẫn: văn bản/điều luật được dùng làm căn cứ. |
| `dto/LegalChunk.java` | Một đoạn văn bản luật (chunk) lấy từ dữ liệu của Team 1/2. |

Các DTO trong `ai/dto/` phải bám theo schema trong `contracts/`.

### `common/` — dùng chung *(chưa có)*

| File | Vai trò |
|---|---|
| `config/CorsConfig.java` | Cho phép frontend gọi API từ domain khác (CORS). |
| `config/` (cấu hình `AiClient`) | Chọn `MockAiClient` hay `HttpAiClient` theo cấu hình. |
| `exception/GlobalExceptionHandler.java` | Bắt lỗi tập trung, trả JSON lỗi thống nhất. |
| `exception/ApiError.java` | Cấu trúc thông báo lỗi trả về cho client. |

### `user/` — đăng nhập *(để sau, nếu cần)*

## Trạng thái

Các class hiện mới là khung (chưa có logic). Mục đánh dấu *(chưa có)* chưa được tạo.