# Team 3 — Kế hoạch và phạm vi tuần 2

**Dự án:** Vietnamese Legal RAG Assistant  
**Phạm vi:** VLRA-22, VLRA-23 và nhiệm vụ Team 3 trong kế hoạch tuần 2.  
**Trạng thái:** T01/T02 đã kiểm chứng local; chưa xác nhận toàn tuần 2 hoàn thành.

**Phiên bản yêu cầu:** 1.2 — 07/10/2026. **Cập nhật tổ chức và trạng thái:** 09/10/2026.

## 1. Mục tiêu và cơ sở triển khai

Hoàn thiện khung Backend/Frontend đã tạo để chạy local, kiểm tra luồng Chat → API mock → Document Viewer và bàn giao 5–10 câu hỏi pháp lý kèm Ground Truth.

Kế thừa cấu trúc package, đặc tả API và luồng đã xây dựng ở tuần 1; không dựng lại dự án hoặc viết lại contract. Backend dùng **Java + Spring Boot/Maven**; Frontend tiếp tục **React/TypeScript/Vite** hiện có. Phiên bản runtime/dependency theo cấu hình repository.

[team3.md v1.2](team3.md) là căn cứ API, luồng và kiến trúc đã được Team 3 thống nhất theo xác nhận của Tuấn (Q1). File này xác định phạm vi task tuần 2; [specs/](../../specs/README.md) mô tả từng task và kết quả bàn giao. [contracts/](../../contracts/README.md) là nơi phối hợp interface liên team; các schema Team 2 được dẫn còn khác API Team 3 và được ghi trong [verification T01](../../specs/001-t01-backend-foundation/verification.md#2-contract-đã-đối-chiếu). Không tự đổi interface để khớp schema khác; làm rõ phần tích hợp bị ảnh hưởng và tiếp tục phần độc lập. Team 1/Team 2 chỉ là nguồn dữ liệu/interface cần nhận, không thuộc phạm vi triển khai của file này.

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

Endpoint, DTO, citation, HTTP/code/retryable và luồng hội thoại dùng [API Team 3](team3.md#api);
không lặp lại schema ở đây. Mỗi task dẫn đúng nguồn áp dụng; API hiện hữu không tự là bằng chứng phê duyệt.

- Tuần 2 kiểm tra tạo hội thoại, hỏi tiếp và bắt đầu mới theo ID trong API. Chưa yêu cầu
  đầy đủ history AI, chống trùng đồng thời, transaction hay đối soát pending.
- Mock được nhận diện rõ, citation/document cùng ID và phiên bản; dữ liệu trong bộ nhớ mất
  sau restart. Mock không chứng minh AI hiểu ngữ cảnh và không là nguồn luật/GT thật.
- Fixture có hai kết quả nghiệp vụ và lỗi hệ thống tách riêng theo Team 3. Cách chọn
  scenario T02 ở [quickstart](../../specs/002-t02-mock-api/quickstart.md), không thêm field ngoài contract.
- Ground Truth dùng corpus nhóm chốt, nguồn/metadata thật và reviewer nhóm chỉ định;
  không lấy response mock, không tự tạo chunk_id. Chưa có format thì chỉ là draft.
  Mapping chunk chỉ được chờ nếu schema cho phép và nhóm chấp thuận. 30–50 câu là mục tiêu
  dataset chung, không phải chỉ tiêu riêng Team 3.

## 3. Task và phân công

| Task | Phụ trách | Phạm vi | Trạng thái và bàn giao |
| --- | --- | --- | --- |
| T01 | Tuấn — Backend/API | Code/contract, dependency, mock mode, cấu hình/CORS và lỗi chung | Kiểm chứng local; [spec](../../specs/001-t01-backend-foundation/spec.md), [verification](../../specs/001-t01-backend-foundation/verification.md) |
| T02 | Tuấn — Backend/API | DTO, query/document mock và fixture cho các trạng thái | Kiểm chứng local; [spec](../../specs/002-t02-mock-api/spec.md), [verification](../../specs/002-t02-mock-api/verification.md) |
| T03 | Thành viên phụ trách UI | Router, styling, Chat/Search và Document Viewer | Chưa có bằng chứng nghiệm thu task đầy đủ; trang thử Backend không thay T03 |
| T04 | Hai thành viên | API client FE–BE mock và kiểm tra response/lỗi | Chưa có bằng chứng nghiệm thu luồng UI đầy đủ |
| T05 | Team 3 | Soạn, review và bàn giao 5–10 câu hỏi + Ground Truth | Chưa có bộ GT đã review trong bàn giao này |
| T06 | Hai thành viên | Runtime, cấu hình, lệnh chạy/build, scenario, giới hạn và bằng chứng | T01/T02 có tài liệu; còn kiểm chứng chạy lại và bàn giao các phần khác của tuần 2 |

T02 và T03 có thể làm song song sau khi thống nhất contract/fixture; T04 cần cả hai sẵn sàng. T05 thực hiện song song khi có format và nguồn.

Kết quả T01/T02 là kiểm chứng local trong phạm vi task. Các AC tuần 2 dưới đây gồm cả FE, tích hợp và GT; không tự đánh dấu toàn bộ PASS từ build Backend hoặc từ trang thử tạm.

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
