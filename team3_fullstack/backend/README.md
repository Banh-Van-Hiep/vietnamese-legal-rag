# Backend mock — VLRA-22

## Công nghệ và phạm vi

Giữ Java/Spring Boot theo xác nhận của Tuấn ngày 07/10/2026. Ticket VLRA-22 ghi FastAPI/Flask cần được cập nhật bởi nhóm. `pom.xml` hiện dùng Spring Boot 4.1.1, Java 25 và Maven Wrapper 3.9.16.

Profile mặc định `mock` phục vụ API bằng dữ liệu kiểm thử và lưu hội thoại trong bộ nhớ. Không cần PostgreSQL, Docker, API key hay dịch vụ Team 2. Tắt ứng dụng thì mất toàn bộ dữ liệu, kết quả gửi lại và dấu nhận diện request đã xóa. Đây là skeleton để FE kiểm thử tích hợp; dữ liệu mẫu không phải nội dung pháp luật.

`Conversation`/`Message` là snapshot của mock, chưa phải entity JPA. Hai repository JPA hiện là placeholder bị tắt trong profile `mock`; trước khi dùng PostgreSQL cần triển khai entity/persistence riêng. `HttpAiClient`, history gửi Team 2, timeout upstream thật và việc khôi phục pending sau sự cố chưa được triển khai. Hiện chỉ hỗ trợ chạy profile `mock`.

## Tài liệu đã đối chiếu

- Nhánh làm việc khi rà soát: `feature/team3/tuan`. Tài liệu hiện có là [README Team 3](../README.md), đặc tả **đề xuất** v1.2; `contracts/README.md` trên nhánh này chỉ nêu nguyên tắc, chưa có schema.
- Bản `origin/develop` đã lưu local tại commit `58aac307e7565cd52a4470ce1ef4c6a75cbb49d9` có [contract v0.1 Revision 2](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/blob/58aac307e7565cd52a4470ce1ef4c6a75cbb49d9/contracts/v0.1/README.md) và tài liệu `docs/team3_fullstack/team3.md`. Chỉ đọc đối chiếu, chưa fetch/merge hoặc đưa các file đó vào nhánh này.
- Revision 2 vẫn ghi **Proposal**, corpus demo ưu tiên Bộ luật Lao động 2019. Schema public query, RagResponse và ErrorResponse khớp phần tương ứng của đặc tả Team 3. Không coi history hoặc API điều luật nội bộ đã được đóng băng. Mock dùng `mock_v1`/`art1`, không tự chọn corpus pháp luật thật.

## Kết quả rà soát và triển khai

| Hạng mục | Trước khi triển khai | Hiện tại |
| --- | --- | --- |
| Cấu trúc Backend | Có package theo tính năng; class/DTO rỗng | Giữ cấu trúc; thêm DTO, controller và service mock |
| API query | Chưa có mapping hoặc validation | Query đồng bộ, UUID v4 request, snake_case, response có đầy đủ ID |
| Local configuration | PostgreSQL và mật khẩu ghi trực tiếp trong properties | Mock không dùng DB; `.env.example` và script nạp `.env` |
| CORS/lỗi | Chưa có | Origin cấu hình được; JSON lỗi tập trung và tracing headers |
| Hội thoại | Repository placeholder, chưa có entity | Tạo/xem/xóa, lịch sử và chống gửi trùng trong bộ nhớ |
| Team 2 | `AiClient` rỗng, chưa có mock | `MockAiClient` hoạt động; HTTP integration để sau |
| Frontend VLRA-23 | React/Vite/Router, các page và component placeholder | Build đã kiểm tra; UI chưa hoàn chỉnh, chưa có Tailwind/UI library |

Frontend cần đối chiếu: `chatApi.ts`/`useChatStream.ts` đang dùng SSE `POST /api/v1/chat/stream`, trong khi mock cung cấp `POST /api/v1/query` đồng bộ. Types đang dùng camelCase, ID số và chưa có `client_request_id`; API danh sách đang chờ array thay vì PageResponse. Document client hiện gọi `/documents/{docId}` thay vì `/documents/{document_id}/articles/{article_id}`. Phần này dành cho bạn phụ trách Frontend cập nhật; build thành công chưa chứng minh tích hợp FE–BE thành công.

## Chạy trên Windows PowerShell

Yêu cầu: JDK 25. Máy được rà soát có `java` trên PATH là 25.0.1, nhưng `JAVA_HOME` trỏ JDK 24.0.2, khiến Maven chọn sai JDK. Hãy dùng đường dẫn JDK 25 thực tế của máy.

Từ gốc repo:

```powershell
Set-Location .\team3_fullstack\backend
Copy-Item -LiteralPath .env.example -Destination .env
```

Sửa `.env`, bỏ dấu `#` trước `JAVA_HOME` và điền đường dẫn JDK 25. Ví dụ trên máy Tuấn: `JAVA_HOME=D:/Java/jdk-25`. Không ghi secret vào repo. Script chỉ đọc `KEY=value`, có thể bao giá trị bằng dấu nháy; không thực thi biểu thức trong `.env`.

```powershell
.\run-local.ps1
```

Nếu terminal chặn script, chạy riêng tiến trình này:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run-local.ps1
```

Maven Wrapper tự tải Maven/dependency ở lần đầu, cần mạng. Nếu đã có Maven, dùng `.\run-local.ps1 -Maven mvn.cmd`. Script nạp `.env` vào tiến trình hiện tại và khôi phục các biến đã nạp khi kết thúc; Spring Boot tự nó không đọc file `.env`.

Backend mặc định phục vụ `http://localhost:8080`. Dừng bằng Ctrl+C. Không cần khởi động Docker; tại lần rà soát Docker CLI đã có nhưng engine chưa chạy.

| Biến `.env` | Mặc định / ý nghĩa |
| --- | --- |
| `JAVA_HOME` | Đường dẫn JDK 25; cần đặt nếu Maven đang chọn JDK khác |
| `SPRING_PROFILES_ACTIVE` | `mock` |
| `SERVER_PORT` | `8080` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173`; phân tách bằng dấu phẩy |
| `MOCK_ANSWER_STATUS` | `answered` hoặc `insufficient_context`; đổi rồi khởi động lại |

Chế độ trả lời áp dụng cho lượt hỏi mới. Gửi lại request đã hoàn tất luôn trả kết quả cũ trong cùng lần chạy.

## API mock

| Method | Endpoint | Kết quả |
| --- | --- | --- |
| GET | `/api/v1/health` | `200 {"status":"up"}`; chỉ kiểm tra HTTP Backend |
| POST | `/api/v1/query` | `200` query response theo mục 1.6–1.7 của đặc tả |
| POST | `/api/v1/conversations` | `201` Conversation, header `Location` |
| GET | `/api/v1/conversations?page=0&size=20` | PageResponse; updated_at giảm dần |
| GET | `/api/v1/conversations/{id}` | Conversation hoặc 404 |
| GET | `/api/v1/conversations/{id}/messages?page=0&size=20` | PageResponse; sequence_no tăng dần |
| DELETE | `/api/v1/conversations/{id}` | `204` body rỗng; pending thì 409 |
| GET | `/api/v1/documents/mock_v1/articles/art1` | ArticleResponse chứa dữ liệu kiểm thử và xuống dòng |

Mọi response API có `X-Request-ID` mới. Query đã được tiếp nhận có `X-Conversation-ID` cả khi xử lý lỗi. CORS cho phép FE đọc hai header này và `Location`.

Question được strip hai đầu, dài 1–2000 Unicode code point; `client_request_id` bắt buộc UUID v4. Bỏ/null `conversation_id` để tạo mới; UUID có sẵn để hỏi tiếp. Không nhận field lạ, key JSON trùng, JSON hỏng/nhiều object hoặc ép số/boolean thành string. POST body tối đa 16 KiB. Các API GET/DELETE không nhận body; chỉ endpoint danh sách nhận query parameter `page`/`size`.

Một lượt mới lưu cặp user completed/assistant pending, gọi mock ngoài khóa của store, rồi lưu assistant completed trước khi trả HTTP 200. Cùng request ID và câu hỏi đã chuẩn hóa thì trả kết quả đã lưu, không tạo thêm message. ID dùng với câu hỏi/hội thoại khác trả `409 REQUEST_ID_CONFLICT`; lượt đang pending trả `409 REQUEST_IN_PROGRESS`; hội thoại có lượt khác pending trả `409 CONVERSATION_BUSY`. Xóa hội thoại giữ lại chỉ ID request đã xóa trong bộ nhớ, gửi lại nhận `404 REQUEST_NOT_FOUND`.

Ví dụ lượt đầu:

```powershell
Invoke-RestMethod -Uri http://localhost:8080/api/v1/health
$requestBody = @{
    client_request_id = [guid]::NewGuid().ToString()
    question = 'Câu hỏi dùng để kiểm thử tích hợp'
} | ConvertTo-Json
$result = Invoke-RestMethod -Method Post -Uri http://localhost:8080/api/v1/query `
    -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($requestBody))
$result | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/conversations/$($result.conversation_id)/messages"
Invoke-RestMethod -Uri http://localhost:8080/api/v1/documents/mock_v1/articles/art1
```

Hỏi tiếp: giữ `conversation_id` nhận được, tạo `client_request_id` mới. Khi gửi lại vì chưa rõ kết quả, giữ nguyên request ID cũ.

Ví dụ đầu vào sai, trả HTTP 400 với `error.code=INVALID_REQUEST`:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8080/api/v1/query `
    -ContentType application/json -Body '{"question":"","client_request_id":"bad-id"}'
```

`insufficient_context` vẫn là HTTP 200, assistant completed, citations=[]; không dùng trạng thái này cho lỗi dịch vụ/timeout. Mock không tạo timeout thật hoặc gọi LLM. Các nhánh lỗi upstream được kiểm thử bằng AiClient giả ở cấp service.

## Kiểm thử

```powershell
.\run-local.ps1 -Task test
.\run-local.ps1 -Task package
```

Kết quả ngày 07/10/2026, với JDK 25.0.1 và Maven 3.9.11 cài sẵn: **20 test, 0 failure, 0 error**. Bộ kiểm thử gồm context startup, HTTP thật trên cổng ngẫu nhiên, query/replay/hỏi tiếp/xóa, response schema, input thiếu/sai/field lạ/key trùng/ép kiểu, Unicode, body limit, media type, method, phân trang, document, health và CORS. Test service kiểm tra pending/concurrency, gọi AI ngoài khóa store và replay lỗi 503/504.

Đường chạy `.\run-local.ps1 -Task package` cũng đạt **BUILD SUCCESS** qua Maven Wrapper, đọc `.env` local để chọn JDK 25 và chạy profile mock. Đã tạo `target/backend-0.0.1-SNAPSHOT.jar`; bước package chạy lại đủ 20 test, đều đạt.

Frontend: `npm run build` đạt với Vite 5.4.21. Chưa kiểm tra lại npm audit; báo cáo vulnerability cũ chưa được xác minh hoặc xử lý trong nhiệm vụ Backend này.

Phạm vi còn lại trước tích hợp thật: cập nhật ticket công nghệ, chốt contract liên team và corpus, đồng bộ client FE, triển khai PostgreSQL/migration và HTTP AiClient cùng history/timeout. Skeleton hiện tại không cam kết persistence qua lần khởi động lại.
