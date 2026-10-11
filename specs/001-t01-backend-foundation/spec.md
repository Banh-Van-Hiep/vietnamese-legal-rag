# Feature Specification: Task01 — Nền tảng Backend/API Team 3

**Feature Branch**: `feature/team3/tuan`
**Nhóm / phụ trách / task**: Team 3 / Tuấn / T01.

**Feature Directory**: `specs/001-t01-backend-foundation`

**Created**: 2026-10-09

**Status**: Đã triển khai và kiểm chứng local ngày 2026-10-09 theo [tasks.md](tasks.md) và [verification.md](verification.md#6-kiểm-chứng-spec-t01-riêng-ngày-09102026); Q1–Q3 giữ nguyên, kết quả chờ nhóm review, không xác nhận toàn tuần 2.

**Input**: Chuẩn bị spec riêng cho Task01 từ spec tuần 2, tài liệu API/kiến trúc Team 3,
báo cáo T01 và việc đọc code Backend; phân biệt yêu cầu với hiện trạng, chỉ viết tài liệu.

Không tìm thấy spec riêng cho Task01 trong repo lúc rà soát. Spec tuần 2 là nguồn yêu cầu
tổng; báo cáo T01 là tài liệu triển khai. File này là spec riêng duy nhất được tạo trong lượt này.
Nhánh Git được giữ nguyên; mã thư mục feature độc lập với tên nhánh.

## Clarifications

### Session 2026-10-09

- Q: Task01 dùng nguồn nào cho API, luồng và kiến trúc khi các tài liệu ghi khác trạng thái? → A: Tuấn xác nhận `docs/team3_fullstack/team3.md` là tài liệu gốc đã được Team 3 thống nhất và là căn cứ cho API, luồng, kiến trúc; spec tuần 2 xác định phạm vi T01 từ nhiệm vụ Jira và đầu vào; báo cáo T01 do Codex sinh chỉ ghi triển khai, không có quyền thay đổi trạng thái phê duyệt. Đối chiếu `contracts/` để ghi khác biệt cụ thể, không dùng chúng hoặc hành vi code để phủ nhận yêu cầu Team 3 đã chốt.
- Q: Khi `.env` và biến môi trường terminal đặt cùng một biến, nguồn nào được ưu tiên? → A: Tuấn chọn B: tham số chạy > biến môi trường terminal > `.env` > mặc định. Cập nhật spec; đưa sửa runner và kiểm tra cấu hình trùng vào plan/tasks; chưa sửa code trong clarify.
- Q: Trong Task01, lỗi CORS 403 và HTTP 406 cần được nghiệm thu theo quy định nào? → A: Tuấn chọn A: nghiệm thu origin được phép và origin ngoài danh sách theo AC-02, không bắt buộc body JSON 403. Ghi nhận 406/NOT_ACCEPTABLE là hành vi triển khai hiện tại, không phải contract đã thống nhất hoặc tiêu chí nghiệm thu T01; không xóa hay đổi xử lý 406 vì lý do đó.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thành viên nhóm chạy Backend mock local (Priority: P1)

Tuấn hoặc thành viên nhận bàn giao có thể chuẩn bị môi trường theo hướng dẫn, chạy Backend
mock và biết dịch vụ đã phục vụ HTTP, khi dịch vụ AI thật chưa chạy và không có API key thật.
Người chạy có thể chọn cấu hình local mà không phải sửa source ứng dụng.

**Why this priority**: Đây là nền tảng để các thành viên kiểm thử và phát triển song song.

**Independent Test**: Chuẩn bị môi trường được khai báo, tắt dịch vụ AI thật, chạy chế độ mock
với cấu hình hợp lệ rồi kiểm tra health. Không cần hoàn thiện UI hoặc fixture của T02.

**Acceptance Scenarios**:

1. **Given** môi trường đáp ứng dependency được khai báo và AI thật không chạy,
   **When** thành viên chạy chế độ mock, **Then** Backend khởi động được và health báo đang phục vụ HTTP.
2. **Given** hai cấu hình local có port/origin khác nhau, **When** áp dụng từng cấu hình,
   **Then** người kiểm thử quan sát được port/origin tương ứng và không cần sửa source ứng dụng.
3. **Given** cấu hình không hợp lệ hoặc port bị chiếm, **When** khởi động,
   **Then** thành viên nhận thông báo lỗi và không được thông báo rằng Backend đã sẵn sàng.
4. **Given** cùng một giá trị được khai báo ở nhiều nguồn, **When** khởi động,
   **Then** tham số chạy được ưu tiên hơn biến terminal, biến terminal hơn `.env`,
   `.env` hơn mặc định; hướng dẫn phản ánh đúng thứ tự này.

### User Story 2 - Frontend kiểm tra quyền truy cập từ origin dev (Priority: P1)

Thành viên Frontend kiểm tra được yêu cầu từ origin dev đã cấu hình, gồm preflight,
và đọc được các header phục vụ truy vết. Origin ngoài danh sách không được cấp quyền CORS.

**Why this priority**: Cấu hình này cần cho việc nối FE–BE ở T04 mà không mở quyền cho mọi origin.

**Independent Test**: Dùng một origin có trong danh sách và một origin ngoài danh sách;
kiểm tra preflight, yêu cầu thực tế và response lỗi. Việc hiển thị trên UI thuộc T04.

**Acceptance Scenarios**:

1. **Given** origin được phép cùng method/header thuộc API áp dụng, **When** gửi preflight
   và yêu cầu thực tế, **Then** response cấp CORS đúng origin và cho đọc các header đã chốt.
2. **Given** origin ngoài danh sách, **When** gửi yêu cầu,
   **Then** response không cấp quyền CORS cho origin đó; không bắt buộc body JSON 403
   để nghiệm thu T01 theo AC-02 tuần 2.
3. **Given** lỗi API từ origin được phép, **When** Backend trả lỗi,
   **Then** Frontend vẫn đọc được error envelope và header truy vết thuộc contract áp dụng.

### User Story 3 - Thành viên tích hợp phân biệt lỗi với kết quả nghiệp vụ (Priority: P2)

Thành viên tích hợp có thể nhận biết đầu vào sai, dịch vụ không sẵn sàng, timeout và lỗi ngoài
dự kiến qua response lỗi, thay vì hiểu chúng là câu trả lời pháp luật hoặc thiếu căn cứ.

**Why this priority**: Response lỗi nhất quán giúp Frontend xử lý đúng và tránh hiển thị sai kết quả.

**Independent Test**: Kích hoạt lỗi trong kiểm thử độc lập của cơ chế xử lý lỗi; không cần
gọi AI thật hoặc thêm endpoint tạo lỗi vào ứng dụng chạy thực tế. Fixture demo thuộc T02.

**Acceptance Scenarios**:

1. **Given** một yêu cầu không hợp lệ theo interface áp dụng, **When** xử lý,
   **Then** trả lỗi đầu vào thay vì kết quả nghiệp vụ thành công.
2. **Given** lần lượt lỗi ngoài dự kiến, không sẵn sàng và timeout, **When** xử lý,
   **Then** mỗi response là lỗi HTTP riêng, có envelope, mã và retryable theo `team3.md` mục 1.10; không có answer/status nghiệp vụ.
3. **Given** lỗi gốc chứa chi tiết provider hoặc thông tin nhạy cảm, **When** trả response,
   **Then** người gọi chỉ nhận thông báo an toàn và không thấy stack trace, secret hay lỗi thô.
4. **Given** yêu cầu đã được gắn hội thoại, **When** trả lỗi,
   **Then** giữ X-Conversation-ID theo `team3.md` mục 1.6 khi lượt hỏi đã được tiếp nhận.

### Edge Cases

- Không có `.env` mặc định nhưng đã có biến môi trường hợp lệ: hướng dẫn phải nêu cách chạy được hỗ trợ.
- Người chạy chỉ định một file cấu hình không tồn tại: phải nhận lỗi rõ ràng, không âm thầm dùng file khác.
- Cấu hình chứa giá trị trống, port sai, mode không hỗ trợ hoặc runtime không phù hợp: không báo sẵn sàng.
- Origin không trùng scheme/host/port trong danh sách: không được cấp quyền CORS; CORS không phải cơ chế đăng nhập.
- Cấu hình origin trống, wildcard, URL có path/query: code hiện từ chối; quy tắc cụ thể chưa được nguồn tuần 2 chốt.
- Không có header Origin: không tự coi yêu cầu là vi phạm phân quyền; Task01 không bổ sung auth.
- JSON hỏng, body quá lớn, media type/method sai, đường dẫn không tồn tại: đi qua cơ chế lỗi chung
  nếu thuộc interface áp dụng; giới hạn/schema nghiệp vụ được đối chiếu ở T02, không tự sửa trong T01.
- Preflight từ origin ngoài danh sách: nghiệm thu không cấp quyền CORS, không bắt buộc body JSON 403.
- Accept không hỗ trợ: 406/NOT_ACCEPTABLE là hành vi code hiện tại, không là điều kiện nghiệm thu
  T01 hoặc bổ sung contract; không được xóa/đổi xử lý đó chỉ vì không thuộc yêu cầu nghiệm thu.
- Header hội thoại hoặc Location chỉ có khi thao tác thực sự sinh/biết thông tin tương ứng; không tạo ID giả cho lỗi đầu vào.
- Khởi động lại mock dùng bộ nhớ tạm: mất dữ liệu đã lưu; không đồng nghĩa đã có persistence hoặc AI hiểu history.

## Requirements *(mandatory)*

### Mục tiêu, phạm vi và phần ngoài phạm vi

**Mục tiêu**: Task01 cung cấp nền tảng Backend local có thể chạy, cấu hình được, kiểm tra
truy cập từ Frontend và xử lý lỗi nhất quán để các task tích hợp tiếp tục.

**Trong phạm vi**: đối chiếu code/contract; dependency cần cho khung hiện tại; mock mode;
cấu hình môi trường và cách nạp; CORS/preflight/header; health để kiểm tra chạy local;
cơ chế lỗi dùng chung; tiêu chí và bằng chứng kiểm tra các phần này.

**Ngoài phạm vi**: thiết kế lại DTO; fixture answered/insufficient_context và lỗi cho demo
query/document của T02; UI/Router/Search/Viewer của T03; nối và nghiệm thu UI FE–BE của T04;
Ground Truth T05; toàn bộ bàn giao tuần 2 T06. Không yêu cầu RAG thật, retrieval, prompt,
LLM client, auth, streaming, persistence đầy đủ, transaction/concurrency production,
đối soát pending, deployment hoặc chuyển công nghệ.

Health là điều kiện kiểm tra nền tảng local của T01. Việc đã có query/document trong code
không chuyển các yêu cầu fixture/DTO của T02 sang T01. Tài liệu nghiệm thu T01 không thay
nghĩa vụ bàn giao tổng thể của T06.

### Nguồn yêu cầu và mức độ xác nhận

| Nguồn | Vai trò và trạng thái |
| --- | --- |
| [Spec Team 3 tuần 2 v1.2](../../docs/team3_fullstack/team3-week2-spec.md), mục 2–4 | Nguồn phạm vi T01, BE-01/BE-02 và phần Backend của AC-01/AC-02; các task T02–T06 được tách riêng |
| [Tài liệu Team 3](../../docs/team3_fullstack/team3.md), kiến trúc và mục 1.1/1.4/1.6/1.8/1.10 | Tài liệu gốc v1.2 đã được Team 3 thống nhất, theo xác nhận của Tuấn ngày 2026-10-09; căn cứ API, luồng và kiến trúc trong phạm vi T01 |
| [Báo cáo triển khai T01](verification.md) | Do Codex sinh để ghi lựa chọn triển khai và kết quả lịch sử ngày 07/10/2026; không có quyền thay đổi trạng thái phê duyệt yêu cầu và không tự nghiệm thu spec này |
| Constitution 1.0.0 (nguồn local tại lúc lập spec) | Giữ tương thích, ranh giới team, kiến trúc và kiểm chứng; ngày phê chuẩn còn TODO. Xem [specs README](../README.md) để đọc bộ tài liệu chia sẻ không phụ thuộc công cụ local |
| [contracts/README.md](../../contracts/README.md) và [schema lỗi Team 2](../../docs/team2_rag/schemas/error_response.schema.json) | README dẫn tới proposal/schema Team 2; đây là nội dung cần đối chiếu và đồng bộ, không thay đổi trạng thái tài liệu Team 3 đã thống nhất |

**Đã chốt theo phạm vi được giao**: giữ công nghệ và khung hiện tại; T01 của Tuấn tập trung
dependency/mock/môi trường/CORS/lỗi; mock không cần AI/API key thật; cấu hình port/origin/mode;
origin ngoài danh sách không được cấp CORS; kiểm chứng và ghi giới hạn; giữ ranh giới team.
API, luồng và kiến trúc Team 3 dùng `team3.md` làm căn cứ; spec tuần 2 xác định phần cần làm
trong T01. Xác nhận này không đồng nghĩa code đã đáp ứng yêu cầu hoặc spec này đã được nghiệm thu.

**Đã chốt qua Q2**: tham số chạy > biến môi trường terminal > `.env` > mặc định.
Đây là yêu cầu đã được Tuấn xác nhận; tại vòng clarify runner còn khác yêu cầu. Vòng implement
đã sửa và kiểm chứng Q2, với bằng chứng riêng trong báo cáo mục 6.

**Đã chốt qua Q3**: CORS nghiệm thu origin được phép và ngoài danh sách theo AC-02;
không bắt buộc body JSON 403. 406/NOT_ACCEPTABLE chỉ ghi là hành vi triển khai, không phải
contract hoặc tiêu chí nghiệm thu T01; giữ nguyên xử lý đó. Những quy tắc khác chỉ xuất hiện
trong implementation không tự được nâng thành yêu cầu mới.
Khác biệt schema liên team được ghi tại Q1 đã làm rõ để phối hợp đồng bộ, không tạo một
vướng mắc phê duyệt mới cho API Team 3. Các chi tiết API dưới đây kế thừa tài liệu gốc,
không tự thay đổi public interface.

### Functional Requirements

- **FR-001**: Nền tảng PHẢI kế thừa kiến trúc và dependency được khai báo của Backend;
  không dựng lại project, đổi công nghệ hoặc thay interface chung trong Task01.
- **FR-002**: Thành viên PHẢI có hướng dẫn chuẩn bị dependency, build/chạy và kiểm tra local;
  phiên bản môi trường lấy từ repository, không thêm runtime hoặc dịch vụ bắt buộc ngoài phạm vi.
- **FR-003**: Chế độ mock PHẢI chạy khi AI thật chưa hoạt động và không có API key thật;
  không gọi AI thật để xác nhận readiness. Task01 không buộc hoàn thiện persistence.
- **FR-004**: Người chạy PHẢI cấu hình được port, origin Frontend và mock mode qua môi trường
  được hướng dẫn, có file mẫu không chứa secret; phải nêu rõ cơ chế nạp `.env`.
- **FR-005**: Khi nhiều nguồn đặt cùng một biến, cấu hình có hiệu lực PHẢI ưu tiên:
  tham số chạy > biến môi trường terminal > `.env` > mặc định. Nếu nguồn ưu tiên không
  cung cấp giá trị thì dùng nguồn tiếp theo; giá trị được chọn không hợp lệ phải được báo
  theo FR-006, không bị che bằng giá trị ở nguồn thấp hơn. Hướng dẫn phải ghi đúng thứ tự này.
- **FR-006**: Cấu hình/runtime không hợp lệ hoặc lỗi khởi động PHẢI được báo cho người chạy;
  không được thông báo health sẵn sàng cho một tiến trình đã khởi động thất bại.
- **FR-007**: Health PHẢI chỉ biểu thị Backend đang phục vụ HTTP, không gọi AI/retrieval/LLM
  và không khẳng định toàn pipeline sẵn sàng; `GET /api/v1/health` trả `200 {"status":"up"}`
  theo `team3.md` mục 1.8, không nhận parameter hoặc request body.
- **FR-008**: Origin dev có trong cấu hình PHẢI được cấp CORS cho method/header của API áp dụng;
  preflight và yêu cầu thực tế thuộc phạm vi hỗ trợ phải kiểm tra được.
- **FR-009**: Origin ngoài danh sách PHẢI không được cấp quyền CORS; không biến yêu cầu này
  thành auth hoặc quyền người dùng. Nghiệm thu cả origin được phép và ngoài danh sách theo
  AC-02 tuần 2; không yêu cầu body JSON 403 cho trường hợp bị chặn.
- **FR-010**: Từ origin được phép, Frontend PHẢI đọc được header truy vết và thông tin thao tác
  theo `team3.md`: X-Request-ID cho mỗi lần gọi; X-Conversation-ID sau khi tiếp nhận lượt hỏi
  kể cả khi trả lỗi; Location khi tạo tài nguyên. Chỉ yêu cầu header có ý nghĩa với thao tác,
  không buộc T01 triển khai thêm API tạo hội thoại để kiểm tra CORS.
- **FR-011**: Lỗi API nghiệp vụ PHẢI dùng envelope JSON an toàn và tách khỏi answer/status
  nghiệp vụ; cấu trúc/mã/status/retryable theo `team3.md` mục 1.10. T01 không yêu cầu body
  JSON 403 CORS và không dùng 406/NOT_ACCEPTABLE làm tiêu chí nghiệm thu hoặc contract đã
  thống nhất. Không xóa/đổi xử lý 406 hiện có chỉ vì nó không nằm trong tiêu chí nghiệm thu.
- **FR-012**: Đầu vào và cách gọi sai thuộc interface áp dụng PHẢI bị từ chối theo cơ chế lỗi
  chung. Không tự thêm field hoặc sửa giới hạn request/DTO của T02 để đạt tiêu chí T01.
- **FR-013**: Lỗi ngoài dự kiến, không sẵn sàng và timeout PHẢI phân biệt được với thiếu căn cứ;
  không trả chúng thành insufficient_context. Kiểm tra cơ chế lỗi không yêu cầu gọi AI thật
  hoặc thêm endpoint tạo lỗi vào ứng dụng phục vụ người dùng.
- **FR-014**: Response lỗi PHẢI không chứa secret, stack trace hoặc chi tiết provider thô;
  giữ header hội thoại khi đã có thông tin đó theo contract áp dụng.
- **FR-015**: Bàn giao PHẢI ghi nguồn/phiên bản contract, trường hợp kiểm tra, expected/actual,
  lệnh/thao tác, kết quả và giới hạn. Không dùng trạng thái PASS cũ hoặc code hiện tại để
  tự đánh dấu các yêu cầu của spec mới đã hoàn thành.
- **FR-016**: Phần dependency/schema chưa được team cung cấp hoặc còn mâu thuẫn PHẢI được ghi rõ;
  chỉ trì hoãn phần bị ảnh hưởng, cho phép tiếp tục phần cấu hình độc lập trong T01.

### Key Entities *(include if feature involves data)*

- **Cấu hình local**: port, danh sách origin, mode; mỗi giá trị có nguồn và thứ tự ưu tiên
  để thành viên biết cấu hình nào thực sự có hiệu lực.
- **Kết quả health**: trạng thái phục vụ HTTP của Backend; không phải trạng thái AI hoặc dữ liệu.
- **Lỗi công khai**: mã lỗi, thông báo an toàn, khả năng thử lại; độc lập với kết quả nghiệp vụ RAG.
- **Thông tin truy vết**: định danh lần gọi, hội thoại và Location khi có; phục vụ việc đối chiếu lỗi.
- **Bằng chứng kiểm tra**: nguồn/phiên bản, môi trường, thao tác, expected/actual, pass/fail và giới hạn.

### Đầu vào, đầu ra và lỗi liên quan

| Tình huống | Đầu vào | Đầu ra mong muốn / trạng thái quyết định |
| --- | --- | --- |
| Khởi động mock | Môi trường đáp ứng dependency; cấu hình local hợp lệ | Phục vụ ở port được chọn, không cần AI/key thật; lỗi khởi động được báo riêng, không yêu cầu HTTP envelope khi chưa có server |
| Health | `GET /api/v1/health`, không body/query | `200 {"status":"up"}` theo `team3.md` mục 1.8; chỉ kiểm tra phục vụ HTTP |
| CORS | Origin, method/header yêu cầu trong preflight và yêu cầu thực tế | Origin được phép nhận quyền phù hợp; origin ngoài danh sách không được cấp; không bắt buộc body JSON 403 theo quyết định Q3 |
| Truy vết | Mỗi lần gọi; hội thoại/địa chỉ tài nguyên nếu thao tác đã có | X-Request-ID; X-Conversation-ID sau khi tiếp nhận lượt kể cả lỗi; Location khi có tạo tài nguyên; FE đọc được qua CORS theo `team3.md` mục 1.1/1.4/1.6 |
| Lỗi nghiệp vụ HTTP | Yêu cầu sai hoặc lỗi xử lý thuộc interface áp dụng | JSON UTF-8 `{"error":{"code":"...","message":"...","retryable":false}}` theo `team3.md` mục 1.10; giá trị retryable phụ thuộc mã lỗi, không có answer/status nghiệp vụ |

Bảng mã dưới đây **kế thừa tài liệu gốc Team 3 v1.2 mục 1.10 đã thống nhất**, theo xác nhận
của Tuấn. Đây là căn cứ kiểm tra T01, không phải phiên bản contract mới do Codex tạo ra.

| Trường hợp | HTTP / mã theo Team 3 | Retryable | Ranh giới Task01 |
| --- | --- | --- | --- |
| Yêu cầu không hợp lệ | 400 / INVALID_REQUEST | false | Kiểm tra cơ chế lỗi chung, không hoàn thiện toàn DTO T02 |
| Đường dẫn API không tồn tại | 404 / NOT_FOUND | false | Cơ chế lỗi chung |
| Method không hỗ trợ | 405 / METHOD_NOT_ALLOWED; header Allow | false | Cơ chế lỗi chung |
| Body quá lớn / media type sai | 413 / PAYLOAD_TOO_LARGE; 415 / UNSUPPORTED_MEDIA_TYPE | false | Kế thừa giới hạn POST body 16 KiB tại `team3.md` mục 1.1; không tự đổi giới hạn |
| Lỗi ngoài dự kiến | 500 / INTERNAL_ERROR | false | Không lộ chi tiết lỗi trong response |
| Dịch vụ không sẵn sàng | 503 / SERVICE_UNAVAILABLE | true | Kiểm tra cơ chế lỗi bằng lỗi được kiểm soát; scenario demo T02 |
| Timeout | 504 / UPSTREAM_TIMEOUT | true | Kiểm tra cơ chế lỗi; chưa thực hiện deadline/retry upstream thật |

Theo Q3, nghiệm thu CORS theo AC-02 tuần 2, không buộc response bị chặn có body JSON 403.
406/NOT_ACCEPTABLE nằm ngoài bảng mã đã thống nhất và tiêu chí nghiệm thu T01; được ghi
như hành vi code hiện tại, không bị xóa hoặc thay đổi chỉ vì không có trong bảng yêu cầu.

Schema query/citation, lỗi idempotency và mã document/article tham chiếu nguồn API để
giữ tương thích; chi tiết hoàn thiện và fixture của chúng thuộc T02. Chuyển đổi lỗi provider
thật, lỗi DB/persistence và ngân sách timeout upstream không phải điều kiện hoàn thành T01.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Một thành viên nhận bàn giao có thể chuẩn bị môi trường đã khai báo, chạy mock
  và xác nhận Backend đang phục vụ, khi AI thật không hoạt động và chưa cung cấp key thật.
- **SC-002**: Hai bộ cấu hình khác nhau được kiểm tra cho kết quả port/origin/mode đúng
  hướng dẫn; cấu hình trùng xác nhận được tham số thắng terminal, terminal thắng `.env`,
  `.env` thắng mặc định và nguồn vắng mặt không chặn fallback hợp lệ.
- **SC-003**: Cả hai nhóm origin được phép và ngoài danh sách có kết quả truy cập đúng;
  thành viên tích hợp đọc được thông tin truy vết đã chốt trên thành công và lỗi.
- **SC-004**: Cả ba nhóm lỗi ngoài dự kiến, không sẵn sàng và timeout đều được nhận diện
  là lỗi; không trường hợp nào hiển thị thành câu trả lời hoặc thiếu căn cứ, không lộ chi tiết nhạy cảm.
- **SC-005**: Mỗi yêu cầu trong phạm vi có ít nhất một trường hợp kiểm tra được đối chiếu
  expected/actual; tất cả mục chưa quyết định hoặc chưa kiểm tra được ghi riêng khi bàn giao.

Không đặt SLA, ngưỡng coverage, tải đồng thời hoặc số test tối thiểu chưa được nhóm chốt.
Các số lượng trên là phạm vi mẫu kiểm tra của đặc tả, không phải mục tiêu hiệu năng mới.

### Tiêu chí nghiệm thu có thể kiểm tra

Lượt soạn spec chưa đánh giá các tiêu chí dưới đây. Sau implement, 8/8 AC đã PASS bằng kiểm chứng local ngày 09/10/2026 trong [verification.md](verification.md#6-kiểm-chứng-spec-t01-riêng-ngày-09102026); không thay nghiệm thu nhóm.

| Mã | Cách kiểm tra và kết quả cần có | Truy vết | Phụ thuộc quyết định |
| --- | --- | --- | --- |
| AC-T01-01 | Làm theo hướng dẫn từ dependency tới mock; build/chạy được và health trả 200/status=up khi AI/key thật vắng mặt; giữ khung/interface hiện có | FR-001–003, FR-007; US1; SC-001; phần BE của AC-01 tuần 2 | Căn cứ `team3.md`; kết quả local tại verification.md |
| AC-T01-02 | Chạy với hai bộ port/origin/mode; xác nhận giá trị thực tế. Với cùng một biến, kiểm tra tham số chạy thắng terminal/.env, terminal thắng .env, .env được dùng khi hai nguồn trên vắng, mặc định được dùng khi cả ba nguồn vắng; giá trị ưu tiên sai không bị âm thầm thay thế; không sửa source để đổi local | FR-004–006; US1; SC-002; phần BE của AC-02 tuần 2 | Q2 đã chốt; runner/test đã kiểm chứng local, xem verification.md |
| AC-T01-03 | Kiểm tra cấu hình/runtime sai và port đang bận; nhận lỗi và không có thông báo sẵn sàng giả | FR-006; US1; SC-001–002 | Không cần chọn contract query |
| AC-T01-04 | Origin được phép: preflight và yêu cầu thực tế thành công về CORS; đọc header trên thành công/lỗi khi có ý nghĩa với thao tác | FR-008, FR-010; US2; SC-003 | Header theo `team3.md` mục 1.1/1.4/1.6 |
| AC-T01-05 | Origin ngoài danh sách không có quyền CORS; kiểm tra trường hợp từ chối preflight/yêu cầu thực tế cùng trường hợp được phép ở AC-T01-04 | FR-009; US2; SC-003; AC-02 tuần 2 | Q3 đã chốt: không bắt buộc body JSON 403 |
| AC-T01-06 | Kiểm tra lỗi đầu vào/method/media type/đường dẫn/body theo interface áp dụng; đúng mã/status/envelope, không có answer/status | FR-011–012; US3; SC-004 | Mã lỗi theo `team3.md`; 406/NOT_ACCEPTABLE không là điều kiện nghiệm thu, không yêu cầu thay đổi xử lý hiện tại |
| AC-T01-07 | Kiểm tra 3 nhóm lỗi hệ thống; đúng retryable và response an toàn; không trả insufficient_context; header hội thoại sau khi đã tiếp nhận lượt | FR-013–014; US3; SC-004 | Theo `team3.md`; không cần AI thật hay endpoint lỗi công khai |
| AC-T01-08 | Bàn giao hướng dẫn, nguồn yêu cầu, môi trường, expected/actual, lệnh/thao tác và giới hạn; liệt kê từng quyết định/chưa kiểm tra | FR-002, FR-015–016; SC-005 | Q1–Q3 đã chốt; chưa ghi PASS cho phần chưa triển khai/kiểm tra theo yêu cầu mới |

Nghiệm thu T01 không đồng nghĩa toàn bộ AC-01/AC-02/AC-03 tuần 2 hoặc T02–T06 đã đạt.
Phần UI gọi Backend trong trình duyệt và render lỗi thuộc T04; T01 chứng minh điều kiện CORS
phía Backend bằng yêu cầu kiểm tra tương ứng.

## Assumptions

### Ràng buộc kế thừa và phụ thuộc

- Kiến trúc được giữ theo nguồn bạn chỉ định và constitution: Backend Java/Spring Boot/Maven,
  package theo tính năng; Controller/Service/DTO/Repository và AiClient. Frontend giữ React/TypeScript/Vite.
  Đây là quyết định kế thừa, không phải lựa chọn công nghệ mới của spec này.
- Phiên bản runtime/dependency lấy từ cấu hình repository tại thời điểm lập kế hoạch/kiểm tra.
  Có dependency persistence không buộc T01 hoàn thiện database; chỉ mock local đang được yêu cầu.
- **Team 2**: phối hợp đồng bộ schema/interface nhận từ Team 3 theo `team3.md`; các khác biệt
  với schema do `contracts/README.md` dẫn tới được ghi cụ thể bên dưới. Không cần service AI thật
  chạy để kiểm tra T01; đồng bộ query/history/citation thuộc T02 hoặc tích hợp sau, không làm
  mất hiệu lực yêu cầu API Team 3 trong T01.
- **Thành viên Frontend Team 3**: cung cấp origin dev và header cần đọc; sử dụng cấu hình được
  hướng dẫn. Không sửa hoặc nghiệm thu UI/API client Frontend trong Task01.
- **Team 1**: không có phụ thuộc runtime trực tiếp của T01. Nội dung/metadata/chunk/corpus thật
  phục vụ các task sau; không dùng một chunk để khẳng định đã có toàn điều luật.
- **Nhóm dự án**: Q1–Q3 đã được Tuấn làm rõ; tiếp tục phối hợp
  đồng bộ tài liệu liên team. Task01 không tự chỉnh schema/interface dùng chung để che khác biệt.
- Kiểm tra cơ chế lỗi có thể dùng đầu vào/lỗi được kiểm soát trong môi trường kiểm thử.
  Không suy ra rằng đã có fixture lỗi trên API demo hoặc adapter gọi Team 2 thật.

### Hiện trạng đọc code — thông tin tham khảo, không phải nghiệm thu

Rà soát trước triển khai ngày 2026-10-09 trên nhánh hiện tại, HEAD `bb1bb26017d2c90578635a29ad625e502dee09b6`.
Working tree có thay đổi chưa commit; không gọi HEAD là commit của toàn bộ nội dung đã đọc.

| File/nhóm đã đọc | Quan sát |
| --- | --- |
| [pom.xml](../../team3_fullstack/backend/pom.xml) | Có dependency web, validation, JPA, PostgreSQL và test starter; Java 25/Spring Boot 4.1.1 đang được cấu hình |
| [runner](../../team3_fullstack/backend/run-local.ps1), [.env.example](../../team3_fullstack/backend/.env.example), [application.properties](../../team3_fullstack/backend/src/main/resources/application.properties) | Có nạp env, lựa chọn port/origin/file; thứ tự ưu tiên và whitelist biến là lựa chọn triển khai hiện tại |
| [application-mock.properties](../../team3_fullstack/backend/src/main/resources/application-mock.properties) | Profile mock tắt datasource/JPA; không chứng minh mọi dependency đã chạy đúng trong lượt này |
| [CorsConfig](../../team3_fullstack/backend/src/main/java/com/legalai/backend/common/config/CorsConfig.java) | Origin chính xác, kiểm tra định dạng, preflight và expose header; chưa có nguồn phê chuẩn mọi quy tắc định dạng |
| [GlobalExceptionHandler](../../team3_fullstack/backend/src/main/java/com/legalai/backend/common/exception/GlobalExceptionHandler.java), [ApiError](../../team3_fullstack/backend/src/main/java/com/legalai/backend/common/exception/ApiError.java), filter/interceptor | Có envelope, JSON, trace và giới hạn body; code có 406 trong khi bảng Team 3 chưa nêu mã này; CORS 403 không đi qua envelope nghiệp vụ hiện tại |
| [AiClient](../../team3_fullstack/backend/src/main/java/com/legalai/backend/ai/AiClient.java), [MockAiClient](../../team3_fullstack/backend/src/main/java/com/legalai/backend/ai/MockAiClient.java), HttpAiClient | Có client mock cho query/article; client HTTP thật còn placeholder; chưa có history nội bộ |
| ChatController/ChatService, DocumentController/DocumentService, ConversationService và model/repository | Có endpoint/điều phối/mock store; model là record, chưa phải entity JPA; query/document DTO và persistence không được nghiệm thu bởi spec T01 |
| [BackendConfigurationTests](../../team3_fullstack/backend/src/test/java/com/legalai/backend/BackendConfigurationTests.java) và các test hiện có | Có ca mock/CORS/lỗi và controller probe chỉ phục vụ test; tồn tại test không đồng nghĩa test đã chạy/đạt trong lượt này |

Báo cáo T01 ghi 24 test đạt và smoke PASS ngày 07/10/2026. Lượt soạn spec chỉ đọc code/tài liệu,
không build, chạy test, mở dịch vụ hoặc xác minh lại các kết quả đó. Tài liệu Team 3 ghi class
còn rỗng/JPA/HTTP client đã có vai trò thiết kế; phần mô tả hiện trạng đó lệch code được đọc.
Cần đối chiếu và cập nhật trạng thái khi nghiệm thu, không chọn một bên làm bằng chứng hoàn thành.
Những mô tả hiện trạng cũ hoặc nhãn “đề xuất” trong tài liệu không thay đổi xác nhận của Tuấn
rằng `team3.md` là tài liệu gốc đã thống nhất; code và báo cáo không có quyền phê duyệt yêu cầu.

### Quyết định đã làm rõ, khác biệt tài liệu và điểm còn mở

#### Q1 — Nguồn yêu cầu Task01 đã được Tuấn làm rõ

**Nguồn quyết định:** Tuấn xác nhận ngày 2026-10-09: `team3.md` là tài liệu gốc đã được Team 3
thống nhất; dùng cho API, luồng và kiến trúc. File tuần 2 được xây dựng từ nhiệm vụ Jira và
tài liệu đầu vào, xác định phạm vi T01. Báo cáo T01 do Codex sinh không có quyền thay đổi
trạng thái phê duyệt yêu cầu. Q1 đã đóng theo xác nhận này, không phải lựa chọn dùng nguồn tạm.

**Đối chiếu `contracts/` ngày 2026-10-09:** thư mục chỉ có README, không có JSON Schema bên trong.
README dẫn tới `docs/team2_rag/rag-io-specification.md` và schema tại `docs/team2_rag/schemas/`.
Các file được dẫn có khác biệt sau với tài liệu gốc Team 3; không suy ra Team 3 chưa thống nhất:

| Nội dung | Tài liệu gốc Team 3 | Nội dung được `contracts/README.md` dẫn tới |
| --- | --- | --- |
| Public query request | Mục 1.6: question 1–2000 code point sau trim; client_request_id UUID v4 bắt buộc; conversation_id UUID tùy chọn/null | `request.schema.json`: chỉ question, maxLength=10000; additionalProperties=false nên request có hai field ID bị từ chối |
| RAG/public query response | Mục 1.9: kết quả nội bộ có status/answer/citations; mục 1.6: Backend bổ sung conversation_id, client_request_id, user_message_id, assistant_message_id, created_at vào public response | `rag_response.schema.json`: chỉ answer/citations và additionalProperties=false; thiếu status. Schema được tài liệu Team 2 gắn với public query nhưng không biểu diễn ID/thời gian public; không yêu cầu Team 2 tự sinh các ID đó |
| Citation | Mục 1.7: citation_id, chunk_id, document_id, article_id, document_title, article, clause, point, source_url; nguồn là URL HTTPS | `citation.schema.json`: claim, chunk_id, document, article, clause, source; thiếu các ID để mở đúng viewer, khác tên field và không ràng buộc source là URL HTTPS |
| Error envelope và mã lỗi | Mục 1.10: error gồm code/message/retryable cùng bảng HTTP/public code và retryable; timeout công khai UPSTREAM_TIMEOUT | `error_response.schema.json`: cấu trúc envelope khớp, không quy định bảng HTTP/mã/retryable theo từng lỗi; ví dụ dùng PROVIDER_TIMEOUT, không phải mã public đã nêu trong Team 3 |
| History nội bộ, health và xem điều luật | Mục 1.8/1.9 có health, public/internal article và question/history nội bộ | README/schema được dẫn chưa mô tả các interface này; request chỉ question, không biểu diễn history |
| Candidate retrieval | Mục 1.9.1 dùng 12 field, gồm document_id/article_id/document_title/point/source_url/rank/retrieval_method | `retrieval_output.schema.json` dùng 7 field chunk_id/content/document/article/clause/source/score; thiếu metadata/version/ordering theo Team 3; ngoài phạm vi triển khai T01 |

T01 áp dụng health/header/lỗi của `team3.md` trong phạm vi được giao. Các khác biệt trên
là việc đồng bộ liên team cần ghi nhận, không tự sửa API đã thống nhất hoặc mở rộng T01.
Không đổi schema/code trong lượt làm rõ này và không dùng báo cáo Codex làm nguồn thay thế.

#### Q2 — Thứ tự ưu tiên cấu hình đã được Tuấn quyết định

**Quyết định ngày 2026-10-09:** chọn B, tham số chạy > biến môi trường terminal > `.env`
> mặc định. Q2 đã đóng; FR-005, US1, SC-002 và AC-T01-02 áp dụng thứ tự này.

**Hiện trạng trước triển khai:** runner và hướng dẫn tại vòng clarify dùng tham số chạy > `.env` > terminal
> mặc định. Đây là hành vi code cũ chưa được sửa trong clarify, không phải yêu cầu được giữ lại.
Báo cáo T01 mô tả kết quả lịch sử theo hành vi đó, không chứng minh AC-T01-02 mới đã đạt.

**Kế hoạch và nhiệm vụ hiện tại:** [plan.md](plan.md) là kế hoạch kỹ thuật Phase 0/1 đầy đủ
cho T01; [tasks.md](tasks.md) chia thành 23 nhiệm vụ theo story/phụ thuộc, bao gồm sửa runner,
hướng dẫn, kiểm tra cấu hình trùng/fallback và nghiệm thu. Hai task nháp Q2 đã được mở rộng,
ánh xạ trong tasks hiện tại; không còn là danh sách hai task nháp. Q1–Q3 giữ nguyên.
Các vòng specify/clarify/plan/tasks chỉ cập nhật tài liệu, chưa sửa runner hoặc chạy build/test.
Vòng implement sau đó đã thực hiện và kiểm chứng T001–T023; kết quả local và giới hạn được ghi
trong [báo cáo mục 6](verification.md#6-kiểm-chứng-spec-t01-riêng-ngày-09102026), không thay quyết định Q1–Q3 hoặc yêu cầu chức năng.

#### Q3 — Phạm vi nghiệm thu CORS và 406 đã được Tuấn quyết định

**Quyết định ngày 2026-10-09:** chọn A. CORS nghiệm thu cả origin được phép và origin ngoài
danh sách theo AC-02 tuần 2; không bắt buộc body JSON 403 cho yêu cầu bị chặn.

406/NOT_ACCEPTABLE được ghi nhận là hành vi triển khai hiện tại, không phải contract đã
thống nhất hoặc tiêu chí nghiệm thu T01. Không xóa hay thay đổi xử lý 406 chỉ vì nó chưa
phải yêu cầu nghiệm thu. Q3 đã đóng; FR-009/011, US2, Edge Cases và AC-T01-05/06 phản ánh
quyết định này. Không thêm public code mới hoặc task sửa 403/406 từ vòng clarify.

Mô tả entity/persistence/HTTP trong tài liệu Team 3 lệch hiện trạng là vấn đề trạng thái tài liệu,
không tự mở rộng T01: phạm vi task tuần 2 được ưu tiên. Các lựa chọn CORS định dạng, whitelist env,
port/header mặc định từ code chỉ được ghi là hiện trạng; nếu muốn nâng thành yêu cầu bắt buộc,
phải có nguồn xác nhận. Không thêm công nghệ, SLA hoặc tiêu chuẩn mới để lấp chỗ chưa rõ.
