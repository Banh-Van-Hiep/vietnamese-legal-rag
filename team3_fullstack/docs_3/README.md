# Team 3 — Nhiệm vụ theo tuần

Mỗi thư mục tuần chỉ giữ `tasks.md`: mã công việc, mục tiêu, nội dung, DoD và phụ thuộc.

| Tuần | Nhiệm vụ |
| --- | --- |
| 4 | [tasks.md](week4/tasks.md) |
| 5 | [tasks.md](week5/tasks.md) |
| 6 | [tasks.md](week6/tasks.md) |
| 7 | [tasks.md](week7/tasks.md) |
| 8 | [tasks.md](week8/tasks.md) |

Đặc tả dùng chung nằm trong [docs/team3_fullstack](../../docs/team3_fullstack/README.md).
[ARCHITECTURE](../../docs/ARCHITECTURE.md) là baseline hiện hành;
[CODING_CONVENTIONS](../../docs/CODING_CONVENTIONS.md) quy định triển khai và DoD;
schema giao tiếp nằm trong `contracts/`.

## Quy trình thực hiện nhiệm vụ

**Quyền sửa nhiệm vụ:** phải hỏi và được người dùng cho phép trước khi sửa bất kỳ
file `tasks.md` nào của Team 3, kể cả hồ sơ local, thêm/xóa task hoặc đổi checkbox.

1. Đọc nhiệm vụ tuần và đúng phần đặc tả chức năng liên quan; đối chiếu code/config/test.
2. Tiếp tục quy trình Spec Kit: specify → clarify → plan → tasks → analyze → sửa vấn đề → implement → validate.
3. Hồ sơ triển khai chi tiết và kết quả kiểm chứng chỉ lưu local tại
   `specs/local-team3/weekN/<jira>-<chuc-nang>/`; đặt `SPECIFY_FEATURE_DIRECTORY` trỏ tới bộ task này.
   Cập nhật bộ đã có, tránh tạo bản trùng. Toàn bộ `specs/` được bỏ qua
   bằng quy tắc `/specs/` trong `.git/info/exclude` trên máy làm việc.
4. Ghi kết quả kiểm chứng cần thiết trong hồ sơ local: tiêu chí, expected/actual,
   pass/fail/chưa chạy, source/môi trường, bằng chứng và phụ thuộc còn mở.
   Không viết báo cáo nghiệm thu tổng hợp theo tuần hoặc đưa hồ sơ này lên Git.
5. Chỉ kết luận hoàn thành khi có bằng chứng phù hợp; phân biệt mock và live.
   Khi baseline/schema/nhiệm vụ mâu thuẫn, báo rõ trước khi sửa phần phụ thuộc.

```text
team3_fullstack/docs_3/weekN/
└── tasks.md

specs/local-team3/weekN/           # Chỉ trên máy local
└── <jira>-<chuc-nang>/
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    └── validation.md
```

Hồ sơ cũ đã chuyển nguyên nội dung sang `specs/local-team3/weekN/`.
Quyết định tổ chức này áp dụng Team 3 từ 03/11/2026.
