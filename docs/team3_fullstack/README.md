# Team 3 — Fullstack

Điểm bắt đầu cho thành viên và AI làm Backend/Frontend của Team 3.

## Tài liệu chung

| Tài liệu | Dùng để |
| --- | --- |
| [team3.md](team3.md) | Kiến trúc, API v1.2 và luồng đã được Team 3 thống nhất; phân biệt thiết kế với hiện trạng |
| [team3-week2-spec.md](team3-week2-spec.md) | Phạm vi tuần 2, phân công T01–T06 và AC toàn tuần |
| [Mục lục specs](../../specs/README.md) | Tìm task theo nhóm/chức năng, đọc yêu cầu và bàn giao sau merge |

Không giữ thêm bản API hoặc báo cáo từng task trong thư mục này.
Hướng dẫn cá nhân nằm ở .local/team3/ và không được push.

## Hiện trạng bàn giao

| Phần | Kết quả và giới hạn | Chi tiết |
| --- | --- | --- |
| T01 — Tuấn | Nền Backend/env/CORS/lỗi đã kiểm chứng local; Q1–Q3 giữ nguyên | [Spec](../../specs/001-t01-backend-foundation/spec.md), [verification](../../specs/001-t01-backend-foundation/verification.md), [quickstart](../../specs/001-t01-backend-foundation/quickstart.md) |
| T02 — Tuấn | Query/document mock, selector và guard output đã kiểm chứng local | [Spec](../../specs/002-t02-mock-api/spec.md), [verification](../../specs/002-t02-mock-api/verification.md), [quickstart](../../specs/002-t02-mock-api/quickstart.md) |
| FE thử | Route /try-backend dùng Backend mock; build/browser9 đã kiểm tra trong vòng riêng | Commit fec29d8; không thay nghiệm thu UI T03/T04 |
| T03–T06 | Còn UI chính thức, tích hợp, GT và bàn giao đầy đủ theo tuần 2 | [Phân công](team3-week2-spec.md#3-task-và-phân-công) |

Backend hiện lưu memory, mất sau restart; HttpAiClient/Python, history AI và PostgreSQL persistence
chưa triển khai. Mock là dữ liệu kiểm thử cấu trúc, không phải luật thật/GT.
Kết quả local không tự xác nhận toàn bộ AC tuần 2 hoặc trạng thái PR/merge.

## Nguồn và ranh giới

Dùng team3.md cho API/luồng/kiến trúc, file tuần 2 cho phạm vi task, spec cho yêu cầu từng chức năng.
contracts/ là điểm phối hợp interface liên team; khác biệt schema với Team 2 được ghi trong
[verification T01](../../specs/001-t01-backend-foundation/verification.md#2-contract-đã-đối-chiếu).
Không tự sửa shared schema hoặc phần Team 1/2 để khớp mock.

Controller nhận HTTP, service điều phối, DTO biểu diễn interface; chỉ package ai/ giao tiếp Python
khi tích hợp được triển khai. Giữ project Spring Boot/Maven và React/TypeScript/Vite hiện có.
Đọc kết quả, giới hạn và dependency trong verification.md trước khi giao lại việc đã hoàn thành.
