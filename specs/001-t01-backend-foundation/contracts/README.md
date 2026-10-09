# Interface references — Task01

Đây là ghi chú giao tiếp kế thừa để thiết kế/kiểm tra T01, không phải contract thay thế.
Nguồn API/luồng/kiến trúc: [team3.md](../../../docs/team3_fullstack/team3.md), đã được Team 3
thống nhất theo Q1; phạm vi: [spec.md](../spec.md). Không sửa `contracts/` chung hoặc schema Team 2.

## HTTP và header cần kiểm tra

| Interface | Input | Output và căn cứ |
| --- | --- | --- |
| GET /api/v1/health | Không body/query | 200, JSON status=up; chỉ phục vụ HTTP, Team 3 mục 1.8 |
| OPTIONS/preflight trên API đã có | Origin, Access-Control-Request-Method, Access-Control-Request-Headers | Origin được phép nhận quyền tương ứng; origin ngoài danh sách không được cấp, theo AC-02 |
| ErrorResponse | Lỗi API thuộc interface áp dụng | JSON có error.code/message/retryable, không có answer/status nghiệp vụ, Team 3 mục 1.10 |
| Truy vết | Mỗi lần gọi; thông tin hội thoại/tài nguyên nếu đã có | X-Request-ID; X-Conversation-ID sau tiếp nhận kể cả lỗi; Location khi tạo, Team 3 mục 1.1/1.4/1.6 |

Header expose cần kiểm tra: X-Request-ID, X-Conversation-ID, Location. Preflight cho JSON
request phải cho phép Content-Type và method tương ứng. CorsConfig hiện hỗ trợ
GET/POST/DELETE/OPTIONS và Content-Type/Accept/X-Request-ID; T01 giữ danh sách hiện có.

| HTTP | Public code dùng trong kiểm tra T01 | Retryable |
| --- | --- | --- |
| 400 | INVALID_REQUEST | false |
| 404 | NOT_FOUND | false |
| 405 | METHOD_NOT_ALLOWED, kèm Allow | false |
| 413 | PAYLOAD_TOO_LARGE, POST body tối đa 16 KiB | false |
| 415 | UNSUPPORTED_MEDIA_TYPE | false |
| 500 | INTERNAL_ERROR | false |
| 503 | SERVICE_UNAVAILABLE | true |
| 504 | UPSTREAM_TIMEOUT | true |

Danh sách này trích phần liên quan của Team 3, không xóa các mã nghiệp vụ còn lại. Lỗi 500/503/504
có thể được kích hoạt trong test-only probe; không thêm endpoint tạo lỗi public. Khi health/config
chưa khởi động được, lỗi runner không bị ép thành HTTP envelope của một server chưa tồn tại.

**Q3:** CORS bị từ chối không bắt buộc body JSON 403. Giữ 406/NOT_ACCEPTABLE hiện có;
không gọi đây là contract đã thống nhất, không dùng làm tiêu chí nghiệm thu T01 hoặc tạo task xóa nó.

## CLI và cấu hình local hiện có

Runner: `team3_fullstack/backend/run-local.ps1`.

| Tham số | Hợp đồng runner kế thừa |
| --- | --- |
| -Task | run mặc định, test hoặc package |
| -Maven | `.\mvnw.cmd` mặc định; cho phép Maven đã cài hoặc stub dùng trong test |
| -EnvFile | `.env` mặc định, tương đối tính từ Backend; mặc định vắng được dùng env, file được chỉ định nhưng vắng báo lỗi |
| -Port | Argument được truyền rõ override SERVER_PORT; range hiện tại 1–65535 |
| -AllowedOrigins | Argument được truyền rõ override CORS_ALLOWED_ORIGINS |

Q2 yêu cầu theo từng key: explicit argument > process environment > file env > default Spring.
Không thêm field JSON hoặc CLI option mới để chọn nguồn/scenario. `.env` đọc KEY=value và
giá trị có thể bao bằng nháy; chỉ các key hiện được hỗ trợ, không thực thi shell expression.

Giá trị được chọn không hợp lệ phải báo lỗi thay vì fallback. Vắng nguồn khác với key rỗng
đã khai báo. Runner khôi phục env/location sau mỗi lần gọi và báo Maven nonzero là lỗi.
Mặc định Spring được tham chiếu từ application.properties; JAVA_HOME không có default.

## Các API chỉ tái sử dụng khi kiểm tra

POST /api/v1/query và POST /api/v1/conversations đã có, được dùng để quan sát cấu hình/headers
hoặc lỗi đầu vào trong test. Không thiết kế lại request/response, fixture hoặc history của chúng.
Query smoke dùng client_request_id UUID v4 và question theo Team 3 mục 1.6. Location kiểm tra
qua tạo conversation đã có, không tạo route mới. Viewer/article/metadata/retrieval không cần
triển khai thêm trong T01; khác biệt với schema được `contracts/README.md` dẫn tới giữ trong spec.
