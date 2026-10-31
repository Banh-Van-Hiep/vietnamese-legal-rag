# Data model — T3-15

| Entity | Fields / validation |
| --- | --- |
| Input sample | id/question bắt buộc, NFC, unique ID, question1–2000 code point; live giữ8 field Golden và không dùng split=test |
| Client sample | sample_id, client_request_id UUIDv4, trace_id UUIDv4 từ response (null khi chưa nhận header), warmup, outcome/error_code, elapsed_ms hữu hạn≥0, status/citation lookup ID; không question/answer |
| Backend timing | kind=chat, trace_id/client_request_id, outcome completed/failed/replayed/discarded, upstream_origin; phases_ms bốn field hoặc null; total_ms hữu hạn≥sum(pha), transport_connected |
| Run | format_version1, generated_at UTC, mode, test_id, counts, latency_distribution_seconds, article_latency_distribution_seconds, phases_breakdown_p95_seconds, thresholds, timing_coverage, samples/warmup, provenance và limits |
| Dev proof | split report từ T3-13: format_version1/status split_only/input.count150/outputs.dev.count90/test.count60; SHA256 file Dev và phân bố expected_status khớp. Không phải phê duyệt pháp lý |

Không mất lỗi khỏi tổng. Phân vị nearest-rank trên mẫu thành công sau warm-up;
tập rỗng có count0 và các phân vị null. AI service_ms không tách model nếu chưa có
trace pha từ Team2. HTTP complete và server finish không đồng nghĩa render DOM.
