# Team 3 — Spec tuần 2

**Dự án:** Vietnamese Legal RAG Assistant  
**Phạm vi:** VLRA-22, VLRA-23 và nhiệm vụ Team 3 trong kế hoạch tuần 2.  
**Trạng thái:** Yêu cầu triển khai; chưa xác nhận hoàn thành.  
**Phiên bản:** 1.2 — 07/10/2026.

## 1. Mục tiêu và cơ sở triển khai

Hoàn thiện khung Backend/Frontend đã tạo để chạy local, kiểm tra luồng Chat → API mock → Document Viewer và bàn giao 5–10 câu hỏi pháp lý kèm Ground Truth.

Kế thừa cấu trúc package, đặc tả API và luồng đã xây dựng ở tuần 1; không dựng lại dự án hoặc viết lại contract. Backend dùng **Java + Spring Boot/Maven**; Frontend tiếp tục **React/TypeScript/Vite** hiện có. Phiên bản runtime/dependency theo cấu hình repository.

Contract đã thống nhất trong `contracts/` là nguồn chính thức cho endpoint, DTO, citation và lỗi; tài liệu Team 3 giải thích cách tích hợp. Trước coding, ghi đường dẫn và phiên bản/commit contract áp dụng. Nếu tài liệu khác contract hoặc thiếu schema, làm rõ phần đó trước khi sửa interface chung; các task độc lập vẫn tiếp tục. Team 1/Team 2 chỉ được nhắc như nguồn dữ liệu/interface cần nhận, không thuộc phạm vi triển khai của spec này.

## 2. Yêu cầu tuần 2

| Mã | Phần việc | Yêu cầu |
|---|---|---|
| BE-01 | Backend skeleton | Hoàn thiện khung hiện có, dependency và cấu trúc API/service/model. Controller nhận HTTP; service điều phối; DTO theo schema; `MockAiClient` trả fixture. Backend mock chạy không cần dịch vụ AI/API key thật. Dùng bộ nhớ tạm hoặc DB local phù hợp khung hiện có; ghi rõ cách chạy, không yêu cầu hoàn thiện persistence tuần này. |
| BE-02 | Môi trường và CORS | Có `.env.example`, cơ chế nạp `.env`/biến môi trường được hướng dẫn; cấu hình được port, origin FE và mock mode. Không mặc định Spring Boot tự đọc `.env`. Cho phép origin dev đã cấu hình, xử lý preflight và expose header mà FE cần theo contract. |
| BE-03 | API mock | Có health, query và document mock phục vụ UI, đúng schema/status/lỗi đã thống nhất. Query hỗ trợ fixture `answered`, `insufficient_context` và lỗi hệ thống; request sai phải bị từ chối. Cách chọn scenario được ghi rõ, không thêm field ngoài contract. |
| FE-01 | Frontend skeleton | Hoàn thiện Router và chọn Tailwind hoặc UI library phù hợp khung hiện có. Chat/Search/Viewer truy cập được qua route hoặc tab; route được công bố phải mở/reload được theo hướng dẫn. FE chạy dev/build được; base URL Backend cấu hình qua môi trường và có file mẫu. |
| FE-02 | Chat UI | Có vùng tin nhắn, ô nhập, nút gửi, loading, answer/citation và lỗi. Chặn câu hỏi rỗng/toàn khoảng trắng và bấm gửi trùng khi đang chờ. Gọi Backend qua API client; phân biệt thiếu căn cứ với lỗi hệ thống. |
| FE-03 | Search skeleton | Có ô nhập từ khóa, thao tác tìm, vùng kết quả/không có kết quả. Dùng fixture có nhãn mock; kết quả có ID để mở viewer. Không yêu cầu retrieval thật hoặc tự tạo API Search khi chưa có contract. |
| FE-04 | Legal Document Viewer | Chọn citation/kết quả mẫu để mở đúng văn bản/điều luật bằng ID. Hiển thị tên, nội dung giữ xuống dòng, nguồn; có loading, not found, lỗi và đóng/quay lại. Viewer lỗi không làm mất answer Chat. |
| GT-01 | Ground Truth Team 3 | Bàn giao **5–10 câu hỏi khác nhau + đáp án chuẩn** theo GT Specification/Evaluation Format của Team 2. Mỗi mẫu có ID, câu hỏi, đáp án/ý bắt buộc và căn cứ có thể đối chiếu. Nguồn, phiên bản luật và đáp án phải được review trước nghiệm thu. |

### Quy tắc tích hợp

- Query: `POST /api/v1/query`; health: `GET /api/v1/health`; document: `GET /api/v1/documents/{document_id}/articles/{article_id}`, theo contract áp dụng.
- Health trả `200 {"status":"up"}`. Query trả `200` cho cả hai trạng thái nghiệp vụ; thiếu/null/blank `question` hoặc ID sai trả `400 INVALID_REQUEST`. Document fixture tồn tại trả `200`; ID hợp lệ nhưng không có dữ liệu trả `404` theo mã document/article của contract. Lỗi hệ thống dùng HTTP/error envelope riêng. Nếu contract đã chốt khác các ví dụ này, cập nhật spec trước khi coding phần liên quan.
- Tạo mới bỏ/null `conversation_id`; hỏi tiếp giữ ID Backend trả; chọn hội thoại mới bỏ ID cũ. `client_request_id` và hành vi gửi lại theo contract.
- Tuần 2 kiểm tra nhận/trả ID trong demo; chưa yêu cầu đầy đủ lịch sử, chống trùng đồng thời, transaction hay đối soát pending. Hành vi nào chưa mô phỏng phải được ghi rõ; không thay public schema. Nếu dùng bộ nhớ tạm, ghi rõ mất dữ liệu sau restart. Không coi mock là đã có AI hiểu ngữ cảnh thật.
- Citation fixture và document fixture phải dùng ID nhất quán. UI phải nhận diện chế độ mock; dữ liệu mẫu không phải tư vấn pháp luật thật.
- Ground Truth theo phạm vi corpus nhóm chốt, dùng nguồn/metadata thật, không lấy từ response mock và không tự tạo `chunk_id`. Người được nhóm chỉ định review nguồn/đáp án. Chưa có format thì chỉ bàn giao draft; chưa được tính là GT hoàn thành. Mapping chunk có thể chờ nếu schema cho phép và nhóm chấp thuận. 30–50 câu là mục tiêu dataset chung, không phải chỉ tiêu riêng Team 3.

## 3. Task và phân công

| Task | Phụ trách | Kết quả |
|---|---|---|
| T01 | Tuấn — Backend/API | Đối chiếu code và contract; hoàn thiện dependency, mock mode, cấu hình/CORS và lỗi |
| T02 | Tuấn — Backend/API | Hoàn thiện DTO, query/document mock và fixture cho các trạng thái |
| T03 | Thành viên phụ trách UI | Hoàn thiện Router, styling, Chat/Search và Document Viewer |
| T04 | Hai thành viên | Nối API client FE với BE mock; kiểm tra response và xử lý lỗi |
| T05 | Team 3 | Soạn, review và bàn giao 5–10 câu hỏi + Ground Truth |
| T06 | Hai thành viên | Ghi runtime, contract áp dụng, cấu hình, lệnh chạy/build, scenario mock, giới hạn và bằng chứng nghiệm thu |

T02 và T03 có thể làm song song sau khi thống nhất contract/fixture; T04 cần cả hai sẵn sàng. T05 thực hiện song song khi có format và nguồn.

Kết quả triển khai T01 và đối chiếu contract ngày 07/10/2026: [Nền tảng Backend/API và bằng chứng kiểm tra](t01-backend-foundation.md). Phần cấu hình/CORS/lỗi đã kiểm tra; chênh lệch contract được ghi rõ để làm rõ trước T02. Các task còn lại chưa được nghiệm thu bằng kết quả T01.

## 4. Tiêu chí nghiệm thu

| Mã | Điều kiện đạt |
|---|---|
| AC-01 | Backend build/chạy mock theo cấu hình local được hướng dẫn khi AI thật không chạy; health trả 200. FE cài theo lockfile, chạy dev và build thành công. |
| AC-02 | Cấu hình môi trường có hiệu lực; FE gọi BE từ origin cho phép không bị CORS chặn; origin khác không được cấp quyền CORS. |
| AC-03 | Query hợp lệ: answered có answer/citation đúng schema; insufficient_context có thông báo và citations rỗng. Thiếu/null/blank question hoặc ID sai trả lỗi validation theo contract. Scenario lỗi hệ thống trả non-2xx/error envelope, không trả insufficient_context. |
| AC-04 | Chat gửi request thật đến BE mock, hiển thị loading/answer/citation/error đúng; không gửi đầu vào rỗng hoặc gửi trùng khi đang chờ. |
| AC-05 | Câu đầu nhận ID mới; câu tiếp giữ ID; chọn hội thoại mới nhận ID khác. |
| AC-06 | Điều hướng/reload hoạt động theo FE-01; Search hiện đúng fixture hoặc trạng thái rỗng; citation/kết quả mở đúng document/article fixture; not found/lỗi được hiển thị và quay lại Chat được, giữ answer cũ. UI nhận diện mock. |
| AC-07 | Có 5–10 mẫu GT đúng format, không trùng ID; nguồn/đáp án đã review; mapping còn thiếu được ghi rõ và được nhóm chấp thuận khi bàn giao. |
| AC-08 | Thành viên khác chạy được FE → BE mock → viewer theo hướng dẫn. Mỗi AC ghi commit, command/thao tác, expected/actual và pass/fail. Repository không chứa secret, .env thật, node_modules hoặc output build. Không đánh dấu hoàn thành khi chưa kiểm tra. |

**Truy vết:** BE-01 → AC-01; BE-02 → AC-02; BE-03 → AC-03/05/06; FE-01 → AC-01/08; FE-02 → AC-04/05; FE-03/04 → AC-06; GT-01 → AC-07.

## 5. Ràng buộc khi dùng AI coding

- Đọc spec, hướng dẫn repository, contract và code hiện tại trước khi sửa; chỉ triển khai task được giao.
- Giữ công nghệ/cấu trúc đã có; không tự đổi schema/API hoặc mở rộng sang RAG thật, auth, streaming, DB production hay deployment.
- Không commit secret, `.env` thật, `node_modules` hoặc output build; không tự push/merge nếu chưa được giao.
- Kết thúc task, báo file thay đổi, kiểm tra đã chạy, kết quả và giới hạn mock. Ghi rõ việc chưa xác minh; không coi class rỗng là chức năng hoàn thành.

**Hoàn thành tuần 2:** T01–T06 được bàn giao, AC-01–AC-08 đạt và có bằng chứng. Spec này không yêu cầu lập trình preprocessing, retrieval, prompt hoặc LLM client của các team khác.
