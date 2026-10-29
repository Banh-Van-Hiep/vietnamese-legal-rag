# Team 3 — Nhiệm vụ và nghiệm thu theo tuần

**Cập nhật:** 30/10/2026. Chỉ giữ bộ nhiệm vụ tuần hiện hành; không lưu các bản nhiệm vụ cũ.
Đặc tả chung của dự án/phân hệ nằm trong [docs/](../../docs/README.md).

## Bộ nhiệm vụ hiện hành

| Tuần | Nhiệm vụ | Nghiệm thu |
| --- | --- | --- |
| 4 | [tasks.md](week4/tasks.md) | [Đạt G1 — thiết kế và nền tảng](week4/verification.md) |
| 5 | [tasks.md](week5/tasks.md) | [Chưa chốt toàn tuần — mock đạt, Golden còn thiếu điều kiện](week5/verification.md) |
| 6 | [tasks.md](week6/tasks.md) | [Chưa đạt G3 — query/article thật chưa thông](week6/verification.md) |
| 7 | [tasks.md](week7/tasks.md) | [Chưa đạt G4 — chờ dữ liệu150 và demo live](week7/verification.md) |
| 8 | [tasks.md](week8/tasks.md) | [Chưa chốt — thiếu benchmark live, recovery và tối ưu Frontend](week8/verification.md) |

Backend giữ Java 25 / Spring Boot 4.1.1 theo quyết định 28/10/2026;
quy chuẩn tại [CODING_CONVENTIONS.md](../../docs/CODING_CONVENTIONS.md).

## Căn cứ áp dụng

[ARCHITECTURE.md](../../docs/ARCHITECTURE.md) là đặc tả chính hiện hành;
[CODING_CONVENTIONS.md](../../docs/CODING_CONVENTIONS.md) quy định cách thực hiện/DoD;
`weekN/tasks.md` phân rã nhiệm vụ theo baseline. Jira là công cụ quản lý/đối chiếu,
không loại bỏ tiêu chí hiện hành chỉ vì mô tả ticket cũ ngắn hơn.
G1–G4 là mốc trong kế hoạch tuần; các chỉ tiêu chất lượng ở ARCHITECTURE §8.2.B vẫn
phải kiểm riêng. Khi có sai lệch schema/baseline/nhiệm vụ thì ghi nhận và thống nhất,
không tự sửa API hoặc biến kết quả mock thành nghiệm thu live.

## Quy trình thực hiện nhiệm vụ

1. Tiếp nhận Jira vào `weekN/tasks.md`: mã gốc, phụ trách, mục tiêu, DoD và phụ thuộc.
   Mã nội bộ `VLRA-T3-*` không tự thay mã Jira thật; số tuần theo lịch học phần đã ghi trong task.
2. Đọc phần kiến trúc/API/quy chuẩn liên quan trong `docs/`; đối chiếu code/config/test
   trước khi giao việc, không suy tiến độ từ số file hoặc mô tả thiết kế.
3. Mỗi task khi bắt đầu triển khai phải có bộ Spec Kit tại `weekN/<jira>-<chuc-nang>/`,
   cập nhật bộ đã có để tránh tạo trùng, và thực hiện từng bước theo quy trình
   `$speckit-specify` → `$speckit-clarify` → `$speckit-plan` → `$speckit-tasks`
   → `$speckit-analyze` → sửa vấn đề → `$speckit-implement`.
   `SPECIFY_FEATURE_DIRECTORY` trỏ đúng thư mục nhiệm vụ, không trỏ thư mục tổng tuần.
4. Giữ spec/plan/tasks/quickstart và tài liệu bổ trợ trong cùng bộ nhiệm vụ;
   schema/interface chung tham chiếu phiên bản trong `contracts/`, không tạo chuẩn khác.
5. Lưu kết quả validate của task tại **`weekN/<jira>-<chuc-nang>/validation.md`**:
   kết quả analyze, các vấn đề đã sửa/còn mở, kết quả build/test/schema và expected/actual,
   trạng thái pass/fail/chưa chạy, môi trường/source và giới hạn mock/live.
   Checklist, analysis và evidence chia sẻ được đặt trong cùng bộ task thuộc tuần đó;
   loại secret/dữ liệu cá nhân, không đưa cache/build/browser profile vào tài liệu.
   Không tạo thêm bản validate hoặc bộ Spec Kit trong `specs/`.
6. Báo cáo nghiệm thu tổng hợp tại **`weekN/verification.md`**, dẫn kết quả validate
   của từng task thay vì chép lại toàn bộ, đối chiếu từng task/DoD,
   ghi expected/actual, source/commit, môi trường, evidence, giới hạn và việc cần làm.
   Chỉ tổng hợp lên Jira/gate khi đủ bằng chứng; mock và live được kết luận riêng.
7. Lệnh chạy và kiểm tra đặt trong `quickstart.md` của nhiệm vụ; biên bản nghiệm thu
   không có mục “Lệnh đã chạy”.

Ví dụ bố trí khi triển khai một task mới (không tạo trước thư mục rỗng):

```text
team3_fullstack/docs_3/weekN/
├── tasks.md
├── <jira>-<chuc-nang>/
│   ├── spec.md
│   ├── plan.md
│   ├── tasks.md
│   ├── validation.md
│   └── ...                 # analysis, checklist, quickstart và evidence phù hợp
└── verification.md         # Tổng hợp nghiệm thu tuần
```

Analyze chỉ báo vấn đề; sửa vấn đề ở bước kế tiếp rồi kiểm tra lại trước implement.
Chỉ đánh dấu task hoàn thành sau khi đã thực hiện và kiểm chứng đủ tiêu chí.

Không tự hạ tiêu chí tuần để khớp implementation. Lượt nghiệm thu chỉ sửa tài liệu,
không thực hiện các phần code còn thiếu hoặc sửa dataset để đổi kết quả thành PASS.
