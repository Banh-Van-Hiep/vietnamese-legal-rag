# Data Model — Task01

T01 không tạo bảng, entity JPA, migration hoặc thay DTO nghiệp vụ. Mô hình dưới đây mô tả
dữ liệu cấu hình/truy vết và bằng chứng kiểm tra cần cho runner và nền tảng hiện có.

## ConfigurationCandidate

| Thuộc tính | Ý nghĩa |
| --- | --- |
| key | Một key được runner hiện hỗ trợ: JAVA_HOME, SPRING_PROFILES_ACTIVE, SERVER_PORT, CORS_ALLOWED_ORIGINS, MOCK_ANSWER_STATUS |
| source | ExplicitArgument, ProcessEnvironment, DotEnv hoặc SpringDefault |
| supplied | Nguồn có cung cấp key/argument hay không; độc lập với giá trị có hợp lệ không |
| raw_value | Giá trị trước validation; không thực thi như biểu thức hoặc ghi secret ra log |
| effective_value | Giá trị thắng theo Q2; khi dùng mặc định Spring có thể để env vắng và chờ Spring bind |

Tham số hiện có chỉ override SERVER_PORT qua `-Port` và CORS_ALLOWED_ORIGINS qua
`-AllowedOrigins`; không thêm CLI parameter để đủ mọi key. `-EnvFile` chọn file, không phải
một nguồn cấu hình có priority mới. `-Task`/`-Maven` điều khiển runner, không phải field API.

Quan hệ: một key có nhiều candidate, chỉ chọn một nguồn thắng. Nguồn vắng cho phép fallback;
giá trị được chọn không hợp lệ đi tới lỗi, không chọn lại nguồn thấp hơn để che lỗi.

## SupportedSettings và validation kế thừa

| Key | Mặc định / kiểm tra |
| --- | --- |
| JAVA_HOME | Không có default; đường dẫn chứa bin/javac.exe, runner kiểm tra JDK 25 |
| SPRING_PROFILES_ACTIVE | Không cung cấp thì Spring dùng default mock; runner hiện chỉ hỗ trợ mock |
| SERVER_PORT | Spring mặc định 8080; `-Port` hiện nhận 1–65535; giữ validation numeric/binding server hiện có, không tự đặt policy port mới |
| CORS_ALLOWED_ORIGINS | Spring mặc định localhost/127.0.0.1:5173; danh sách HTTP(S) origins; giữ parser/validation CorsConfig hiện có, không mở wildcard |
| MOCK_ANSWER_STATUS | Spring mặc định answered; MockAiClient hiện nhận answered hoặc insufficient_context |

Runner cần phát hiện giá trị rỗng đã chọn trước khi phép gán env làm mất thông tin cung cấp
và gây fallback âm thầm. Validation semantic hiện có ở runner/Spring/CorsConfig/MockAiClient
tiếp tục được dùng; không nhân bản tất cả logic Java sang PowerShell.

## EnvironmentSnapshot

- Bản cũ của từng biến sẽ bị runner thay đổi và trạng thái key đã tồn tại/vắng.
- Working directory trước khi Push-Location vào Backend.
- Chỉ giữ trong bộ nhớ của lần gọi; dùng để khôi phục trong finally khi thành công hoặc lỗi.
- Không ghi đè `.env` local, không lưu nội dung env/secret thành artifact tracked.

Luồng runner: đọc snapshot → parse → chọn nguồn theo Q2 → kiểm tra/apply → gọi Maven
→ trả kết quả/lỗi → finally khôi phục env/location. Failure trước/sau apply đều phải khôi phục
phần đã thay đổi; không báo sẵn sàng khi Maven hoặc khởi động thất bại.

## Health, PublicError và TraceMetadata

- **Health:** status=up của HTTP Backend; không truy xuất dữ liệu hay gọi AI để kiểm tra.
- **PublicError:** error.code/error.message/error.retryable, theo Team 3 mục 1.10;
  không trộn answer/status nghiệp vụ. Message an toàn, không có secret/provider detail/stack trace.
- **TraceMetadata:** X-Request-ID cho lần gọi; X-Conversation-ID sau tiếp nhận lượt; Location
  khi tạo tài nguyên. CORS expose các header có ý nghĩa với response, không sinh ID giả cho lỗi.

CORS rejection không bắt buộc JSON 403. 406 hiện có chỉ là observation; không tạo enum/field
hoặc thay handler để đưa nó thành yêu cầu T01. Chi tiết giao tiếp tại [contracts](contracts/README.md).

## VerificationEvidence

Một record gồm AC/FR liên quan, commit và tình trạng working tree, môi trường, command/thao tác,
expected/actual, pass/fail, log path và giới hạn. Output runtime có thể nằm ở `backend/target/t01/`
được Git bỏ qua; chỉ đưa tóm tắt đã kiểm tra vào báo cáo khi thực sự chạy.

Lifecycle: Planned → Executed → Reviewed. Spec/plan tồn tại chỉ tương ứng Planned, không tự
đổi sang PASS. Mock conversation/message/citation giữ cấu trúc hiện tại và mất sau restart;
không được thiết kế thêm persistence, idempotency hoặc history trong data model T01.
