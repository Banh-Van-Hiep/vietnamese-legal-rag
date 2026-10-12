# Shared feature specifications

Thư mục specs/ được chia sẻ qua Git để các thành viên và AI hiểu thay đổi sau khi merge code.
Nơi đây quản lý phân rã task, phạm vi kỹ thuật, spec/plan/tasks, dependency, tiêu chí kiểm chứng
và bằng chứng nghiệm thu. Nhiệm vụ chung theo tuần/Jira và kiến trúc/API cấp nhóm thuộc `docs/`.
Hai thư mục độc lập về nội dung; liên kết chỉ để truy vết nguồn yêu cầu, không sao chép bảng task/test.
Có spec hoặc checkbox hoàn thành không tự chứng minh yêu cầu đã được phê duyệt hay toàn bộ hệ thống đã chạy.

## Các phần đã có

| Nhóm | Task / phụ trách | Chức năng | Trạng thái tại bàn giao | Điểm đọc |
| --- | --- | --- | --- | --- |
| Team 3 | T01 / thành viên phụ trách | Nền Backend, runtime/env, CORS, lỗi chung | Kiểm chứng local 23/23 tasks, 8/8 AC; chưa thay nghiệm thu nhóm | [Spec](team3-week2/001-t01-backend-foundation/spec.md), [bàn giao](team3-week2/001-t01-backend-foundation/verification.md) |
| Team 3 | T02 / thành viên phụ trách | Query/document mock, fixture/scenario, guard output | Kiểm chứng local 18/18 tasks, 8/8 AC; lựa chọn vận hành chờ review của thành viên phụ trách | [Spec](team3-week2/002-t02-mock-api/spec.md), [bàn giao](team3-week2/002-t02-mock-api/verification.md) |
| Team 3 | Tuần 2 / Team 3 | Phân rã T01–T06 và nghiệm thu từ task lên 3 nhiệm vụ Jira | T01–T04 PASS kỹ thuật local; T05 chờ review pháp lý, T06 chờ thành viên khác xác nhận chạy lại | [Task](team3-week2/tasks.md), [nghiệm thu task → Jira](team3-week2/verification.md) |

T01: 25 Java tests /31 runner cases tại vòng kiểm chứng riêng. T02: full package74 /runner37 /
HTTP8 records, gồm regression T01; đây là kết quả ngày 09/10/2026 trước các commit bàn giao.
Không cộng các con số thành tổng test mới hoặc tự gán PASS cho lần merge khác.
T03–T06 được theo dõi trong [bộ tuần 2](team3-week2/tasks.md), chưa tạo thư mục spec riêng.
Kết quả kiểm chứng hiện tại nằm trong [verification](team3-week2/verification.md). Tài liệu Team 1/2 hiện nằm trong
[docs/](../docs/README.md); bảng trên không kết luận trạng thái code của các team khác.

## Đọc sau khi nhận hoặc merge code

1. Đọc nhiệm vụ tuần theo Jira và kiến trúc/API trong docs để hiểu đầu ra chung.
2. Đọc phân rã trong specs để chọn task, dependency và ánh xạ Jira; với Team 3 xem `team3-week2/tasks.md`.
3. Đọc spec/plan/tasks của chức năng nếu đã có; xem Clarifications/decisions trước khi sửa.
4. Đối chiếu từng task với tiêu chí và bằng chứng trong verification, sau đó tổng hợp lên Jira.
5. Đọc quickstart/hướng dẫn chạy lại; đối chiếu code/config/test và Git diff hiện tại.

Với Team 3, API/luồng/kiến trúc lấy từ [team3.md v1.2](../docs/team3_fullstack/team3.md);
3 nhiệm vụ tuần 2 lấy từ [week2.md](../docs/team3_fullstack/week2.md);
phạm vi task và tiêu chí chi tiết lấy từ [phân rã tuần 2](team3-week2/tasks.md).
Q1–Q3 và lựa chọn vận hành cụ thể nằm trong spec/verification; code hiện tại không tự đổi contract.
Không suy ra đã có PostgreSQL, Python/RAG thật, UI chính thức hoặc nghiệm thu nhóm từ một fixture mock.

## Quy trình nhận VLRA và thực hiện task

1. Khi nhận từng VLRA, cập nhật nhiệm vụ chung theo tuần tại `docs/<team>/week<N>.md`:
   mã Jira, mục tiêu, đầu ra, phạm vi và nguồn yêu cầu. Kiểm tra đã có nhiệm vụ đó để tránh trùng.
2. Phân rã thành task ở `specs/<team>-week<N>/tasks.md`, ghi task → VLRA, phạm vi và phụ thuộc.
   Đây là danh sách tổng của tuần; `tasks.md` trong từng thư mục task là các bước triển khai nhỏ.
3. Khi bắt đầu một task, kiểm tra code và bộ spec hiện có. Tái sử dụng/cập nhật nếu đã có;
   task mới dùng thư mục `specs/<team>-week<N>/<NNN>-<task>-<chuc-nang>/`.
4. Chạy **`$speckit-specify` → `$speckit-clarify` → `$speckit-plan` → `$speckit-tasks`
   → `$speckit-analyze` → sửa vấn đề → `$speckit-implement`** cho đúng task được chọn.
   Mỗi bước ghi kết quả riêng; analyze chỉ báo vấn đề, bước sửa mới thay tài liệu.
   Phân biệt quyết định đã chốt và phần cần làm rõ; không tự đổi API/công nghệ/phạm vi.
5. Sau implement, kiểm tra từng bước và tiêu chí của task rồi cập nhật `verification.md`.
   Chỉ đánh dấu hoàn thành khi có bằng chứng; ghi phần chưa chạy hoặc còn chờ review.
6. Tổng hợp task đã kiểm chứng vào `specs/<team>-week<N>/verification.md`, đối chiếu với
   đầu ra từng VLRA trong docs, rồi mới kết luận nghiệm thu tuần. Không tự commit/push.

Với Spec Kit, chỉ định **`SPECIFY_FEATURE_DIRECTORY`** là thư mục task đầy đủ để giữ đúng
vị trí theo tuần; `.specify/feature.json` lưu lựa chọn trên máy, không được push.
Ví dụ task mới: `specs/team3-week2/003-t03-frontend/`. Không trỏ vào thư mục tổng tuần,
không tạo lại task đã có hoặc tự chạy lại workflow T01/T02 chỉ vì chuyển thư mục.

Cấu trúc Team 3 tuần 2:

```text
specs/team3-week2/
├── tasks.md                       # Phân rã task → VLRA của tuần
├── verification.md                # Nghiệm thu task → VLRA → tuần
├── 001-t01-backend-foundation/     # Bộ Spec Kit của T01
└── 002-t02-mock-api/               # Bộ Spec Kit của T02
```

Đây là quy trình đã được người dùng xác nhận. Khi thêm tuần/task khác, áp dụng cùng cách
tổ chức; mỗi bộ tài liệu vẫn đọc được khi thành viên dùng công cụ AI khác hoặc không cài Spec Kit.

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
