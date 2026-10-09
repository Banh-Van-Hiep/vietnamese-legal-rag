# Shared feature specifications

Thư mục specs/ được chia sẻ qua Git để các thành viên và AI hiểu thay đổi sau khi merge code.
Mỗi thư mục mô tả một chức năng/task: yêu cầu, thiết kế, công việc và kết quả bàn giao.
Có spec hoặc checkbox hoàn thành không tự chứng minh yêu cầu đã được phê duyệt hay toàn bộ hệ thống đã chạy.

## Các phần đã có

| Nhóm | Task / phụ trách | Chức năng | Trạng thái tại bàn giao | Điểm đọc |
| --- | --- | --- | --- | --- |
| Team 3 | T01 / Tuấn | Nền Backend, runtime/env, CORS, lỗi chung | Kiểm chứng local 23/23 tasks, 8/8 AC; chưa thay nghiệm thu nhóm | [Spec](001-t01-backend-foundation/spec.md), [bàn giao](001-t01-backend-foundation/verification.md) |
| Team 3 | T02 / Tuấn | Query/document mock, fixture/scenario, guard output | Kiểm chứng local 18/18 tasks, 8/8 AC; lựa chọn vận hành chờ review của Tuấn | [Spec](002-t02-mock-api/spec.md), [bàn giao](002-t02-mock-api/verification.md) |

T01: 25 Java tests /31 runner cases tại vòng kiểm chứng riêng. T02: full package74 /runner37 /
HTTP8 records, gồm regression T01; đây là kết quả ngày 09/10/2026 trước các commit bàn giao.
Không cộng các con số thành tổng test mới hoặc tự gán PASS cho lần merge khác.
T03–T06 chưa có bộ spec/verification riêng trong bàn giao này. Tài liệu Team 1/2 hiện nằm trong
[docs/](../docs/README.md); bảng trên không kết luận trạng thái code của các team khác.

## Đọc sau khi nhận hoặc merge code

1. Đọc README repository và hướng dẫn repository hiện có, rồi mục lục này để tìm nhóm/task.
2. Đọc spec.md để hiểu phạm vi và yêu cầu; xem phần Clarifications/decisions.md nếu có.
3. Đọc plan.md và tasks.md để hiểu cách triển khai, dependency và phần còn mở.
4. Đọc verification.md để biết code/commit đã bàn giao, kết quả thực tế, giới hạn và phần cần phối hợp.
5. Đọc quickstart.md khi chạy lại; đối chiếu code/config/test và Git diff hiện tại trước khi sửa.

Với Team 3, API/luồng/kiến trúc lấy từ [team3.md v1.2](../docs/team3_fullstack/team3.md);
phạm vi tuần 2 lấy từ [kế hoạch](../docs/team3_fullstack/team3-week2-spec.md).
Q1–Q3 và lựa chọn vận hành cụ thể nằm trong spec/verification; code hiện tại không tự đổi contract.
Không suy ra đã có PostgreSQL, Python/RAG thật, UI chính thức hoặc nghiệm thu nhóm từ một fixture mock.

## Vai trò các file

| File | Nội dung chính |
| --- | --- |
| spec.md | Mục tiêu, phạm vi, hành vi, lỗi, AC và quyết định làm rõ |
| plan.md | Thiết kế, dependency, thành phần tác động; phân biệt snapshot lúc plan với hiện trạng |
| tasks.md | Công việc theo dependency, checkbox và evidence; không đánh dấu từ việc tạo class |
| quickstart.md | Điều kiện, cấu hình, lệnh/thao tác và expected để chạy lại |
| verification.md | Kết quả đã chạy, commit/code bàn giao, expected/actual, giới hạn, việc còn mở |
| decisions.md, research.md, data-model.md, contracts/, checklists/, analysis.md | Tài liệu bổ trợ khi task có; không sao chép nguyên API chung để tạo nguồn khác |

Khi thêm hoặc bàn giao một task, cập nhật hàng tương ứng trong mục lục và ghi nhóm/phụ trách
ở spec.md. Đặt tên chức năng rõ, giữ cách đánh số thư mục hiện có; kiểm tra spec đã tồn tại để tránh trùng.
Một handoff hữu ích ghi ngắn: đã thay đổi gì, commit nào, API/config chịu ảnh hưởng,
kiểm chứng nào đã chạy, giới hạn và dependency còn lại. Đây là cách sử dụng tài liệu chung,
không thêm công nghệ, SLA/coverage hoặc tiêu chuẩn kỹ thuật mới.

## Phần local và phần chia sẻ

specs/ cùng docs/ được commit theo phạm vi được giao. .specify/, skill Spec Kit và .local/
là công cụ/ghi chú của từng máy, không phải điều kiện để người khác đọc bộ đặc tả.
Các dẫn chiếu constitution local trong tài liệu cũ là nguồn đã dùng tại thời điểm lập spec;
các nguyên tắc tương thích API, ranh giới team, tái sử dụng kiến trúc và kiểm chứng được phản ánh
trực tiếp trong spec/plan và tài liệu Team 3.

Log/raw reports dưới backend/target/ được ignore; verification.md chia sẻ kết quả và tên evidence,
quickstart.md giúp thành viên khác tự tái hiện. Thiếu log local trên máy mới không biến PASS cũ thành
bằng chứng mới; ghi rõ phần chưa chạy thay vì tự xác nhận nghiệm thu.
