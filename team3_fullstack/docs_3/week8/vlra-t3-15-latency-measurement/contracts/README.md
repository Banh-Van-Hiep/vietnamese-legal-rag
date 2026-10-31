# Interface — T3-15 benchmark CLI và timing log

Product API dùng nguyên [contracts/v0.1](../../../../../contracts/v0.1/CONTRACT.md).
Không thay request/response hoặc thêm trường SSE.

CLI: measure_latency.py --mode mock|exploratory|live --dataset PATH --base-url ORIGIN
--output PATH [--users 1..5] [--warmup N] [--timeout-seconds N] [--timing-log PATH]
[--split-report PATH] [--rag-url ORIGIN]. Không retry và không ghi đè output.

Live bắt buộc split report/timing-log/rag-url; chặn data Test, hash sai, mock/readiness lỗi.
Exit0: công cụ đo đúng trong mode đã chọn; exit1: request/timing/ngưỡng thất bại;
exit2: cấu hình/preflight/output bị chặn. Exit0 với mock không là nghiệm thu live.

Log mỗi lượt accepted worker khi bật CHAT_LATENCY_ENABLED:
CHAT_LATENCY {JSON Backend timing như data-model}. Parser chỉ lấy field whitelist,
không xuất raw log, error body hoặc nội dung pháp lý.

Report theo [data-model](../data-model.md), JSON format_version1. live_target_verified
chỉ true khi preflight/provenance/trace-origin/timing đủ; latency_api_pass còn cần
không lỗi và hai ngưỡng p95. viewer_ui_verified luôn false trong runner API này.
