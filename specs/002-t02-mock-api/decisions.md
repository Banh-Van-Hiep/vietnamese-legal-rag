# T02 — quyết định để Tuấn review

**Ngày:** 2026-10-09. **Nhánh:** feature/team3/tuan. Không commit/push.
Nguồn quyền: người dùng ủy quyền tự quyết và tiếp tục chuỗi workflow khi vắng mặt;
quyết định dưới đây do Codex chọn, không tự gọi là phê duyệt mới của Team 3.

| ID | Quyết định | Lý do / phương án bỏ | Ảnh hưởng |
| --- | --- | --- | --- |
| CL-T02-01 | Scenario query/document độc lập theo cấu hình instance khi khởi động | Giữ input/API đã chốt; bỏ magic question/header/endpoint vì lẫn dữ liệu người dùng với điều khiển mock | Đổi scenario cần restart; giữ legacy MOCK_ANSWER_STATUS và Q2 |
| CL-T02-02 | Document tuple tồn tại có success/500/503/504; syntax/tuple vắng giữ 400/404 | Viewer T04 cần quan sát error response thật; chỉ test probe không phục vụ demo | Thêm cấu hình mock nội bộ; không thêm public field/route hoặc nguồn AI/luật thật |
| D03 | Guard DTO output query/article theo constraint Team 3 và 502 UPSTREAM_INVALID_RESPONSE | Output sai ID/schema không được trở thành 200; không dựng upstream thật | Kiểm tra ở Backend với AiClient hiện có; malformed chỉ dùng test, không scenario public |
| D04 | Giữ một tuple mock_v1/art1 và dữ liệu cấu trúc hiện có | Đã phù hợp mẫu Team 3; không có yêu cầu luật thật/nhiều fixture | Không fabricate GT/chunk thật; citation và article cùng metadata/source |
| D05 | Query selector vắng fallback tới property app.mock.answer-status đã phân giải | Raw env fallback bỏ qua property override của test/cấu hình Spring hiện có; kiểm thử InsufficientContextApiTests chứng minh tương thích | Không đổi Q2 cho env/runner; không fallback khi selector có giá trị sai; chưa thêm công nghệ/dependency |

Không thay Q1–Q3 T01, shared schema, công nghệ hoặc frontend/team khác. Các thay đổi
đặc biệt quan trọng được ghi ở đây và báo cáo T02; Tuấn review sau khi quay lại.
Đã implement và kiểm chứng local theo các lựa chọn này: wrapper package74 tests,
runner37 cases, HTTP8 records PASS. Xem [báo cáo T02](verification.md);
không còn lựa chọn chặn công việc. Đây không phải biên bản nhóm phê duyệt.
