# Team 3 — Fullstack

Điểm đọc nhiệm vụ chung, kiến trúc và API của Team 3.

## Tài liệu chung

| Tài liệu | Dùng để |
| --- | --- |
| [team3.md](team3.md) | Kiến trúc, API v1.2 và luồng đã được Team 3 thống nhất; phân biệt thiết kế với hiện trạng |
| [week2.md](week2.md) | 3 nhiệm vụ chung tuần 2: VLRA-22 Backend, VLRA-23 Frontend, VLRA-24 Golden Dataset |

Các file ở đây đủ để đọc bối cảnh và đầu ra chung. Phân rã task, dependency, tiêu chí
kỹ thuật và báo cáo kiểm chứng thuộc `specs/`; không đặt bảng task hoặc test count trong `docs/`.

## Theo dõi triển khai

- [Phân rã task tuần 2](../../specs/team3-week2/tasks.md): task và ánh xạ tới Jira.
- [Nghiệm thu tuần 2](../../specs/team3-week2/verification.md): kiểm tra từng task, rồi đối chiếu VLRA.
- [Mục lục specs](../../specs/README.md): bộ chi tiết từng chức năng và bàn giao sau merge.

Các liên kết là điểm truy vết; nội dung triển khai chỉ được duy trì ở specs.
Hướng dẫn cá nhân nằm ở `.local/team3/`, không được push. Quy trình tiếp nhận VLRA và thực hiện
task đã được ghi trong [specs README](../../specs/README.md#quy-trình-nhận-vlra-và-thực-hiện-task).
Khi nhận VLRA mới, cập nhật nhiệm vụ chung ở `week<N>.md`; phân rã và đặc tả từng task ở
`specs/team3-week<N>/`, rồi kiểm chứng task trước khi tổng hợp nghiệm thu VLRA.

## Nguồn và ranh giới

Dùng `team3.md` cho API/luồng/kiến trúc, `week2.md` cho nhiệm vụ Jira;
specs cho phạm vi kỹ thuật, task và nghiệm thu. `contracts/` là điểm phối hợp interface liên team.
Không tự sửa shared schema hoặc phần Team 1/2 để khớp mock.

Controller nhận HTTP, service điều phối, DTO biểu diễn interface; chỉ package ai/ giao tiếp Python
khi tích hợp được triển khai. Giữ project Spring Boot/Maven và React/TypeScript/Vite hiện có.
Đọc kết quả và phần còn mở trong specs trước khi tiếp tục một task sau merge.
