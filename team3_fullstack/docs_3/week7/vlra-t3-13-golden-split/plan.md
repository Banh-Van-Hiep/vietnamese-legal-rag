# Implementation Plan — T3-13 Golden split

**Nguồn:** [spec](spec.md). Dùng Python>=3.10 stdlib đã có trong repo; không thay
Java/React hoặc dependency. Giữ nhánh/worktree hiện tại, không commit/push tự động.

## Technical Context

Tool: team3_fullstack/tools/split_golden_dataset.py; test:
team3_fullstack/tests/test_split_golden_dataset.py. CLI nhận --input, --output-dir,
--seed (mặc định20261029), nhận150 mẫu và xuất90 Dev/60 Test.

Phân tầng theo expected_status. Với mỗi stratum, lấy floor(n*90/150), phân bổ số
còn lại theo phần dư giảm dần; tie-break tên status. Sort ID trước khi shuffle bằng
random.Random(seed), rồi shuffle hai tập cuối. Không phụ thuộc thứ tự input hoặc
random global. Chỉ chia, không sửa tỷ lệ75/25 của bộ nguồn hoặc tự sửa class hiếm.

## Constitution Check

Giữ record/schema; không đổi API. Ranh giới Team1 tạo dữ liệu, Team2 review, Team3
chia được người dùng xác nhận rõ. Tái sử dụng Python/JSON có sẵn, kiểm chứng bằng
fixture kỹ thuật; không gán kết quả fixture thành dữ liệu pháp luật hoặc freeze.

## Project Structure / Files

- Tool/test tại Team3; không sửa team2_rag/validate_golden.py hoặc bộ Phase1.
- Khi nhận150 thật, output được người chạy chọn folder tường minh:
  golden_dataset_v1.dev.json, golden_dataset_v1.test.json, golden_dataset_v1.split.json.
- File split.json là báo cáo kỹ thuật split_only, không dùng tên manifest freeze.
- Hồ sơ spec/clarify/plan/tasks/analyze/validation ở cùng thư mục task tuần7.

## Phase0 Research

Không còn quyết định phạm vi chặn công cụ. Các chi tiết seed/làm tròn là lựa chọn
triển khai có ghi nhận, không thêm ngưỡng chất lượng/phê duyệt. Có stratum1 mẫu hoặc
chỉ1 status: cảnh báo phân bố, không nhân bản/chuyển nhãn. Trùng ý do Team2 kiểm;
normalized duplicate là điều kiện từ chối cơ học.

## Phase1 Design

Đọc UTF-8, từ chối JSON duplicate key/NaN; kiểm các field bắt buộc/types/NFC/status/
chunk logic. Giữ nguyên field bổ sung. Kiểm disjoint/union/deep equality trước ghi.
Serialize ổn định, SHA-256 bytes gốc và outputs; report chỉ file basename, không
đường dẫn người dùng/author. Không ghi đè3 tên output; rollback các file mình tạo
nếu ghi lỗi. Không tự tạo output thật khi bộ hiện tại chỉ50.

## Verification

Test150 kỹ thuật cho2 kiểu làm tròn112/38 và113/37; reproducibility/order invariance,
seed khác, duplicates/NFC/type/status/chunk errors, CLI size50/no-overwrite/hashes.
Chạy unittest không dependency mới. Kiểm hash Phase1/corpus/validator và link/diff.
Không cần Maven/FE test vì không sửa app/config. Bộ150 thật giữ task chờ bàn giao.
