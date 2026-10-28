# Team 3 — Fullstack

Điểm đọc đặc tả chức năng chung của Team 3. **Tài liệu thứ cấp**, đối chiếu ngày 23/10/2026.

## Nguồn yêu cầu gốc

Chỉ [Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0)
và các ticket Jira là nguồn gốc theo xác nhận của người dùng. Tài liệu trong repo,
specs và báo cáo phối hợp diễn giải hai nguồn này; có thể sửa khi khác nguồn gốc.
Code/test/config là căn cứ hiện trạng, không phải yêu cầu đã phê duyệt.
Nếu Docs v2.0 và Jira xung đột, báo người dùng và chờ quyết định ở phần phụ thuộc;
không tự đổi một nguồn để khớp nguồn kia.

## Tài liệu chung

| Tài liệu | Dùng để |
| --- | --- |
| [team3.md](team3.md) | Kiến trúc/API/luồng Team 3 diễn giải từ Docs v2.0; phân biệt đích thiết kế với implementation JSON/mock |
| [week2.md](week2.md) | Hồ sơ tiếp nhận Jira tuần 2 đã có; không thay thế Docs v2.0 hoặc ticket gốc |

Các file ở đây đủ để đọc bối cảnh và đầu ra chung. Phân rã task, dependency, tiêu chí
kỹ thuật và báo cáo kiểm chứng thuộc `specs/`; không đặt bảng task hoặc test count trong `docs/`.

## Theo dõi triển khai

- [Phân rã task tuần 2](../../specs/team3-week2/tasks.md): task và ánh xạ tới Jira.
- [Nghiệm thu tuần 2](../../specs/team3-week2/verification.md): kiểm tra từng task, rồi đối chiếu VLRA.
- [Yêu cầu tuần 4](../../specs/team3/week-04/requirements.md): VLRA-41–44 và quyết định W4-Q1 áp dụng v2.0 cho VLRA-41 ngày 23/10.
- [Mục lục specs](../../specs/README.md): bộ chi tiết từng chức năng và bàn giao sau merge.

Các liên kết là điểm truy vết; nội dung triển khai chỉ được duy trì ở specs.
Hướng dẫn cá nhân nằm ở `.local/team3/`, không được push. Quy trình tiếp nhận VLRA và thực hiện
task đã được ghi trong [specs README](../../specs/README.md#quy-trình-nhận-vlra-và-thực-hiện-task).
Các nhiệm vụ mới theo tuần nằm trong `specs/team3/week-NN/requirements.md`; phân rã
và đặc tả riêng cũng đặt trong tuần đó. `week2.md` giữ hồ sơ tiếp nhận cũ, không tạo
thêm bản nhiệm vụ tuần trùng trong docs. Kiểm chứng task trước khi tổng hợp nghiệm thu VLRA.

## Nguồn và ranh giới

Dùng Docs v2.0/Jira cho yêu cầu; `team3.md` là bản diễn giải chức năng, specs là hồ sơ
nhiệm vụ/triển khai/nghiệm thu. `contracts/` là hiện trạng artifact phối hợp liên team,
không được ưu tiên hơn nguồn gốc khi khác biệt. Không tự sửa shared schema hoặc
phần Team 1/2 để khớp mock; ghi khoảng thiếu/xung đột và phối hợp đúng owner.

Controller nhận HTTP, service điều phối, DTO biểu diễn interface; chỉ package ai/ giao tiếp Python
khi tích hợp được triển khai. Giữ project Spring Boot/Maven và React/TypeScript/Vite hiện có.
Đọc kết quả và phần còn mở trong specs trước khi tiếp tục một task sau merge.
