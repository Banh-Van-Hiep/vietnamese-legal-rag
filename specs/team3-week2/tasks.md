# Team 3 — Phân rã task tuần 2

**Cập nhật:** 12/10/2026. **Nhóm:** Team 3.

Đây là nguồn chi tiết triển khai: phạm vi task, yêu cầu kỹ thuật, phụ thuộc và tiêu chí
kiểm chứng. [docs/team3_fullstack/week2.md](../../docs/team3_fullstack/week2.md)
giữ 3 nhiệm vụ Jira chung; [team3.md](../../docs/team3_fullstack/team3.md)
giữ API, luồng và kiến trúc đã thống nhất.

Nội dung yêu cầu BE/FE/GT, T01–T06 và AC-01–AC-08 được chuyển từ tài liệu phạm vi tuần 2
v1.2 trước đây. Việc chuyển vị trí không sửa yêu cầu kỹ thuật, Q1–Q3 hoặc trạng thái nghiệm thu.
Không lập lại spec/plan/tasks T01/T02 đã có trong các thư mục task bên trong bộ tuần 2.

## 1. Truy vết và thứ tự nghiệm thu

T01–T06 là task triển khai của Team 3; chúng không phải 6 nhiệm vụ Jira riêng.
Các mã T001… trong `001-t01-backend-foundation/tasks.md` hoặc `002-t02-mock-api/tasks.md`
là bước nhỏ bên trong task tương ứng.

| Task | Nhiệm vụ Jira liên quan | Yêu cầu chi tiết | Tiêu chí đối chiếu |
| --- | --- | --- | --- |
| T01 — Nền Backend | VLRA-22 | BE-01, BE-02, xử lý lỗi chung | Phần Backend của AC-01/02/03; AC riêng trong spec T01 |
| T02 — API mock | VLRA-22 | BE-03, DTO/fixture/query/document | Phần API của AC-03/05/06; AC riêng trong spec T02 |
| T03 — Frontend | VLRA-23 | FE-01–FE-04 | Phần FE của AC-01/04/06 |
| T04 — Kết nối FE–BE | VLRA-22, VLRA-23 | BE-02/03 và FE-02/04 trong luồng tích hợp | AC-02/04/05/06 trên trình duyệt |
| T05 — Golden Dataset | VLRA-24 | GT-01 | AC-07 |
| T06 — Bàn giao | VLRA-22, VLRA-23, VLRA-24 | Hướng dẫn, bằng chứng, xác nhận chạy lại và bàn giao liên quan | AC-08, theo phần bàn giao của từng Jira |

Nghiệm thu theo thứ tự: **task → bằng chứng/AC → nhiệm vụ Jira → kết luận tuần**.
T06 phục vụ cả 3 Jira; khi tổng hợp, chỉ xét phần bàn giao tương ứng với từng Jira.
Kết quả và phần còn mở nằm trong [verification.md](verification.md).

T01/T02 tiếp tục dùng [spec Backend nền tảng](001-t01-backend-foundation/spec.md)
và [spec API mock](002-t02-mock-api/spec.md). T03–T06 được theo dõi ở bộ tuần 2 này,
chưa tạo thêm thư mục spec riêng hoặc tuyên bố đã qua workflow Spec Kit riêng.
Khi bắt đầu một task mới hoặc tiếp tục task cần đặc tả, tạo/cập nhật bộ riêng theo
[quy trình đã thống nhất](../README.md#quy-trình-nhận-vlra-và-thực-hiện-task), rồi nghiệm thu task trước khi tổng hợp lên Jira.


## 2. Yêu cầu triển khai chi tiết

| Mã | Phần việc | Yêu cầu |
|---|---|---|
| BE-01 | Backend skeleton | Hoàn thiện khung hiện có, dependency và cấu trúc API/service/model. Controller nhận HTTP; service điều phối; DTO theo schema; `MockAiClient` trả fixture. Backend mock chạy không cần dịch vụ AI/API key thật. Dùng bộ nhớ tạm hoặc DB local phù hợp khung hiện có; ghi rõ cách chạy, không yêu cầu hoàn thiện persistence tuần này. |
| BE-02 | Môi trường và CORS | Có `.env.example`, cơ chế nạp `.env`/biến môi trường được hướng dẫn; cấu hình được port, origin FE và mock mode. Không mặc định Spring Boot tự đọc `.env`. Cho phép origin dev đã cấu hình, xử lý preflight và expose header mà FE cần theo contract. |
| BE-03 | API mock | Có health, query và document mock phục vụ UI, đúng schema/status/lỗi đã thống nhất. Query hỗ trợ fixture `answered`, `insufficient_context` và lỗi hệ thống; request sai phải bị từ chối. Cách chọn scenario được ghi rõ, không thêm field ngoài contract. |
| FE-01 | Frontend skeleton | Hoàn thiện Router và chọn Tailwind hoặc UI library phù hợp khung hiện có. Chat/Search/Viewer truy cập được qua route hoặc tab; route được công bố phải mở/reload được theo hướng dẫn. FE chạy dev/build được; base URL Backend cấu hình qua môi trường và có file mẫu. |
| FE-02 | Chat UI | Có vùng tin nhắn, ô nhập, nút gửi, loading, answer/citation và lỗi. Chặn câu hỏi rỗng/toàn khoảng trắng và bấm gửi trùng khi đang chờ. Gọi Backend qua API client; phân biệt thiếu căn cứ với lỗi hệ thống. |
| FE-03 | Search skeleton | Có ô nhập từ khóa, thao tác tìm, vùng kết quả/không có kết quả. Dùng fixture có nhãn mock; kết quả có ID để mở viewer. Không yêu cầu retrieval thật hoặc tự tạo API Search khi chưa có contract. |
| FE-04 | Legal Document Viewer | Chọn citation/kết quả mẫu để mở đúng văn bản/điều luật bằng ID. Hiển thị tên, nội dung giữ xuống dòng, nguồn; có loading, not found, lỗi và đóng/quay lại. Viewer lỗi không làm mất answer Chat. |
| GT-01 | Ground Truth Team 3 | Mỗi thành viên đóng góp **5–10 câu hỏi khác nhau + đáp án chuẩn + chunk_id** theo VLRA-24 và định dạng Golden của Team 2; mục tiêu dataset chung 30–50 câu. File có thể gộp nhiều thành viên, không giới hạn 10 mẫu cho cả file. Mỗi mẫu có ID, câu hỏi, đáp án/ý bắt buộc và căn cứ đối chiếu được. Nguồn, phiên bản luật và đáp án phải được review trước nghiệm thu; đóng góp từng thành viên được xác nhận trong bàn giao nội bộ. |

### Quy tắc tích hợp

Endpoint, DTO, citation, HTTP/code/retryable và luồng hội thoại dùng [API Team 3](../../docs/team3_fullstack/team3.md#api);
không lặp lại schema ở đây. Mỗi task dẫn đúng nguồn áp dụng; API hiện hữu không tự là bằng chứng phê duyệt.

- Tuần 2 kiểm tra tạo hội thoại, hỏi tiếp và bắt đầu mới theo ID trong API. Chưa yêu cầu
  đầy đủ history AI, chống trùng đồng thời, transaction hay đối soát pending.
- Mock được nhận diện rõ, citation/document cùng ID và phiên bản; dữ liệu trong bộ nhớ mất
  sau restart. Mock không chứng minh AI hiểu ngữ cảnh và không là nguồn luật/GT thật.
- Fixture có hai kết quả nghiệp vụ và lỗi hệ thống tách riêng theo Team 3. Cách chọn
  scenario T02 ở [quickstart](002-t02-mock-api/quickstart.md), không thêm field ngoài contract.
- Ground Truth dùng corpus nhóm chốt, nguồn/metadata thật và reviewer nhóm chỉ định;
  không lấy response mock, không tự tạo chunk_id. Chưa có format thì chỉ là draft.
  Mapping chunk chỉ được chờ nếu schema cho phép và nhóm chấp thuận. 30–50 câu là mục tiêu
  dataset chung, không phải chỉ tiêu riêng Team 3.

## 3. Task và phân công

| Task | Phụ trách | Phạm vi | Trạng thái và bàn giao |
| --- | --- | --- | --- |
| T01 | thành viên phụ trách — Backend/API | Code/contract, dependency, mock mode, cấu hình/CORS và lỗi chung | Kiểm chứng local; [spec](001-t01-backend-foundation/spec.md), [verification](001-t01-backend-foundation/verification.md) |
| T02 | thành viên phụ trách — Backend/API | DTO, query/document mock và fixture cho các trạng thái | Kiểm chứng local; [spec](002-t02-mock-api/spec.md), [verification](002-t02-mock-api/verification.md) |
| T03 | Thành viên phụ trách UI | Router, Tailwind CSS v4, Chat/Search và Document Viewer | PASS kỹ thuật local; build và browser ngày 12/10/2026 trong [nghiệm thu tuần 2](verification.md) |
| T04 | Hai thành viên | API client FE–BE mock và kiểm tra response/lỗi | PASS kỹ thuật local; 20 unit tests và browser/retry timeout, lịch sử 2 → 2; [nghiệm thu tuần 2](verification.md) |
| T05 | Team 3 | Soạn, review và bàn giao 5–10 câu mỗi thành viên + Ground Truth | Validator PASS 13 mẫu, 12 có căn cứ; còn review pháp lý, xác nhận đóng góp nội bộ và cách bàn giao mẫu 008 |
| T06 | Hai thành viên | Runtime, cấu hình, lệnh chạy/build, scenario, giới hạn và bằng chứng | Đã cập nhật [ma trận AC và hướng dẫn chạy lại](verification.md); còn xác nhận chạy lại của thành viên khác và các phần chờ nhóm review |

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
| AC-07 | Mỗi thành viên đóng góp 5–10 câu GT theo VLRA-24, được xác nhận nội bộ; file gộp đúng format, không trùng ID/câu hỏi; mẫu answered có chunk_id đối chiếu được, nguồn/phiên bản/đáp án đã review. Mẫu thiếu căn cứ như 008 không tính vào chỉ tiêu có Ground Truth và chunk_id khi chưa được nhóm chấp thuận; cách bàn giao phải được ghi rõ. |
| AC-08 | Thành viên khác chạy được FE → BE mock → viewer theo hướng dẫn. Mỗi AC ghi commit, command/thao tác, expected/actual và pass/fail. Repository không chứa secret, .env thật, node_modules hoặc output build. Không đánh dấu hoàn thành khi chưa kiểm tra. |

**Truy vết:** BE-01 → AC-01; BE-02 → AC-02; BE-03 → AC-03/05/06; FE-01 → AC-01/08; FE-02 → AC-04/05; FE-03/04 → AC-06; GT-01 → AC-07.

## 5. Ràng buộc khi dùng AI coding

- Đọc spec, hướng dẫn repository, contract và code hiện tại trước khi sửa; chỉ triển khai task được giao.
- Giữ công nghệ/cấu trúc đã có; không tự đổi schema/API hoặc mở rộng sang RAG thật, auth, streaming, DB production hay deployment.
- Không commit secret, `.env` thật, `node_modules` hoặc output build; không tự push/merge nếu chưa được giao.
- Kết thúc task, báo file thay đổi, kiểm tra đã chạy, kết quả và giới hạn mock. Ghi rõ việc chưa xác minh; không coi class rỗng là chức năng hoàn thành.

**Hoàn thành tuần 2:** T01–T06 được bàn giao, AC-01–AC-08 đạt và có bằng chứng. Spec này không yêu cầu lập trình preprocessing, retrieval, prompt hoặc LLM client của các team khác.

## 6. Quyết định kế thừa

- Q1: `docs/team3_fullstack/team3.md` là nguồn API/luồng/kiến trúc đã thống nhất;
  `docs/team3_fullstack/week2.md` ghi 3 nhiệm vụ Jira; file này giữ phần phân rã và phạm vi kỹ thuật.
  Báo cáo hoặc code không tự thay trạng thái phê duyệt yêu cầu.
- Q2: tham số Port/AllowedOrigins được truyền rõ > biến terminal > `.env` > mặc định Spring,
  theo từng key; winner rỗng/sai báo lỗi, chỉ fallback khi nguồn vắng.
- Q3: CORS nghiệm thu origin được phép/ngoài danh sách, không bắt body JSON 403.
  Handler 406 giữ nguyên; 406/NOT_ACCEPTABLE là hành vi triển khai, không nâng thành contract/AC T01.
- Scenario T02 và guard 502 được ghi trong [decisions.md](002-t02-mock-api/decisions.md)
  theo ủy quyền đã có; không tự gọi là phê duyệt mới của nhóm.
