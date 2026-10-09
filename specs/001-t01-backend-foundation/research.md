# Research — Task01 Backend/API

**Ngày:** 2026-10-09. **Phương pháp:** đọc tài liệu/code local, đối chiếu Git diff và rà soát
độc lập cách nghiệm thu. Không tìm công nghệ mới, chạy build/test hoặc gọi dịch vụ trong lượt plan.

## 1. Nguồn yêu cầu

- **Decision:** [team3.md](../../docs/team3_fullstack/team3.md) là căn cứ API/luồng/kiến trúc
  đã được Team 3 thống nhất theo Q1; [spec tuần 2](../../docs/team3_fullstack/team3-week2-spec.md)
  giới hạn T01; [spec riêng](spec.md) ghi Q1–Q3. Báo cáo T01 chỉ là bằng chứng lịch sử.
- **Rationale:** Tách yêu cầu khỏi code và báo cáo Codex; nhãn cũ trong tài liệu không phủ nhận
  xác nhận của Tuấn. Khác biệt schema do `contracts/README.md` dẫn tới đã được liệt kê trong spec.
- **Alternatives considered:** lấy schema Team 2 hoặc code hiện tại làm nguồn thay thế bị loại;
  sửa schema liên team hay đưa query/history thật vào T01 vượt phạm vi.

## 2. Runtime và dependency

- **Decision:** giữ Java 25, Spring Boot 4.1.1, Maven Wrapper 3.9.16 từ
  [pom.xml](../../team3_fullstack/backend/pom.xml) và [wrapper properties](../../team3_fullstack/backend/.mvn/wrapper/maven-wrapper.properties).
  Giữ Web MVC, Validation, JPA, PostgreSQL driver và test starter; không thêm dependency.
- **Rationale:** Khung và kiểm thử hiện có đủ cho nền tảng local. JPA/driver có trong POM nhưng
  bị loại khỏi auto-configuration ở profile mock; không cần chuyển persistence hoặc dựng project mới.
- **Alternatives considered:** đổi JDK/framework, thêm dotenv library, DB/H2 hoặc test framework
  khác không có nhu cầu trong T01. Runtime cấu hình không đồng nghĩa máy đã build thành công hôm nay.

## 3. Phân giải cấu hình theo Q2

- **Decision:** sửa runner hiện có thành tham số được truyền rõ > môi trường process/terminal
  > `.env` > mặc định Spring. Parse `.env` thành dữ liệu trước, không ghi đè terminal trong lúc parse.
  Chọn nguồn theo từng key rồi mới áp dụng và lưu bản cũ để khôi phục ở finally.
- **Rationale:** [runner](../../team3_fullstack/backend/run-local.ps1) hiện gọi SetEnvironmentVariable
  cho mọi key trong file nên terminal bị ghi đè. Đây là khoảng trống triển khai chắc chắn qua đọc code.
  Q2 đã chọn thứ tự mới; không cần hỏi lại hoặc coi hành vi cũ là contract.
- **Alternatives considered:** giữ `.env` ưu tiên hơn terminal đã bị Q2 loại; đổi precedence toàn
  Spring hay copy mặc định vào nhiều lớp gây thay đổi ngoài nhu cầu runner.
- **Chi tiết thiết kế:** dùng thông tin nguồn có cung cấp giá trị hay không, không dùng phép kiểm
  tra truthy để coi giá trị rỗng/sai là vắng. Nếu nguồn đã chọn sai, báo lỗi; nếu nguồn vắng mới
  fallback. Lỗi cú pháp file vẫn được xử lý theo parser hiện có; giá trị ở nguồn thấp hơn không
  được ghi đè giá trị đã chọn. Không tự mở rộng whitelist KEY=value.
- **Mặc định:** port/origin/answer status và default profile thuộc application.properties.
  JAVA_HOME không có mặc định runner; vẫn phải có JDK 25 hợp lệ. Trên PowerShell 5.1, biến bị
  xóa là nguồn vắng; một key rỗng ghi rõ trong `.env` là giá trị được cung cấp, cần validation.

## 4. CORS, lỗi và mock

- **Decision:** giữ CorsConfig, filter/interceptor, ApiError/ApiException/handler và MockAiClient.
  Nghiệm thu origin được phép/ngoài danh sách theo AC-02; không bắt JSON 403. Giữ 406/NOT_ACCEPTABLE
  như hành vi hiện tại, ngoài contract/tiêu chí T01; không tạo việc xóa/đổi handler 406.
- **Rationale:** Q3 đã đóng. Test có sẵn đã diễn đạt nhiều nhánh, nhưng việc test tồn tại hoặc
  báo cáo 24 test PASS ngày 07/10 không xác nhận nghiệm thu spec hiện tại.
- **Alternatives considered:** thêm public endpoint tạo lỗi, chuyển mọi lỗi thành insufficient_context,
  đổi body CORS hoặc chốt 406 thành mã mới đều không thuộc quyết định đã được giao.
- **Mock:** giữ answered/insufficient_context hiện có để quan sát cấu hình; 500/503/504 dùng
  probe chỉ trong test. Không gọi Python, LLM hoặc sinh nội dung luật thật.

## 5. Kiểm thử còn thiếu

- **Decision:** bổ sung harness PowerShell không dependency mới tại
  `backend/src/test/powershell/RunLocalConfigurationTests.ps1`; dùng Maven stub trong dữ liệu tạm
  để quan sát env được truyền và mô phỏng exit code; chạy smoke Spring riêng sau harness.
- **Rationale:** JUnit test HTTP hiện có không gọi runner nên không phát hiện precedence hoặc
  restoration sai. Harness phải kiểm tra same-process restoration; smoke kiểm tra giá trị đã bind
  vào Spring, không giả định Maven stub đã chứng minh cấu hình server thực tế.
- **Alternatives considered:** thêm Pester/npm/Python test stack bị loại vì không cần dependency mới;
  chỉ dùng smoke bỏ sót finally; chỉ dùng stub không chứng minh health/CORS thật.
- **Bổ sung nhỏ nếu cần:** assertion Allow-Methods/Allow-Headers, Location thực tế kèm Origin và
  retryable=false cho lỗi đầu vào trong các test Java hiện có. Không thiết kế lại DTO/fixture.

## Kết luận nghiên cứu

Không còn quyết định chức năng mở trong T01. Chi tiết triển khai được chốt từ khung hiện có và
Q1–Q3, không có yêu cầu nghiên cứu dịch vụ ngoài. Phase 1 có thể thiết kế; mọi kiểm tra runtime
vẫn cần chạy ở bước triển khai. Nguồn và phân công agent chỉ đọc được phản ánh trong plan.
