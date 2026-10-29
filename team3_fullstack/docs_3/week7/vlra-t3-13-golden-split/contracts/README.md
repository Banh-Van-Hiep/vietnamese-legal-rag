# CLI/output contract

CLI --input PATH --output-dir PATH [--seed INTEGER]. Input150 theo record hiện hành;
output Dev90/Test60 và split report, không đổi API/schema chung. Status report luôn
split_only, có input/output SHA256 và phân bố theo expected_status. Tool giữ nguyên
mọi field record, không xác nhận review/hiệu lực pháp lý hoặc freeze.
