# Tasks — T3-13 Golden split

## Setup / design

- [x] T001 Đọc nguồn và lưu hash Phase1/corpus/validator vào backend/target/t3-13-golden-split-20261029/preservation.json; bảo toàn worktree.
- [x] T002 Chốt spec/clarify/plan/data-model/CLI trong docs_3/week7/vlra-t3-13-golden-split theo phân công mới.

## US1 / US3 — chia và từ chối lỗi

- [x] T003 [US1] Viết bộ test meaningful150/rounding/reproducibility/disjoint/preserve trong team3_fullstack/tests/test_split_golden_dataset.py.
- [x] T004 [US1] Triển khai validate/split và làm tròn phân tầng tại team3_fullstack/tools/split_golden_dataset.py (FR001–004).
- [x] T005 [US3] Thêm CLI/validation lỗi/không ghi đè và rollback output trong cùng tool; test các ca size50/duplicate/schema/status/NFC/output tồn tại (FR006–007).

## US2 — đối chiếu bàn giao

- [x] T006 [US2] Xuất2 tập và golden_dataset_v1.split.json với SHA256/seed/phân bố/split_only trong cùng tool; kiểm CLI end-to-end bằng fixture150 (FR005).
- [x] T007 Chạy unittest, thử từ chối Phase1 thật50, đối chiếu hash/link/diff và ghi validation.md cùng cập nhật week7/verification.md.
- [ ] T008 Khi Team1 bàn giao150 đã được Team2 kiểm chứng: chạy tool lên nguồn thật, bàn giao90 Dev/60 Test và split report. Không tự review/freeze hoặc tạo mẫu thay họ.

T003→T004→T005→T006→T007. T008 phụ thuộc dữ liệu thật, không đánh dấu từ fixture.
Không đánh dấu song song vì sửa cùng tool/test. Không commit/push tự động.
