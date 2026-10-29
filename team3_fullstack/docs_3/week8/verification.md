# Biên bản nghiệm thu Team 3 — Tuần 8

**Ngày kiểm chứng:** 30/10/2026. **Nhiệm vụ:** [tasks.md](tasks.md).

## 1. Kết luận

**Chưa đủ điều kiện nghiệm thu tuần 8.**

Tải mock50/50 và kiểm tra chức năng slow3G đạt. Còn thiếu benchmark Dev Set/live,
số đo từng pha, hồi quy Retrieval v2 thật, recovery định kỳ và tối ưu Frontend
theo T3-15–18.

## 2. Đối chiếu từng task

| Task | Expected / DoD | Actual | Kết luận |
| --- | --- | --- | --- |
| T3-15 | Runner, p50/p90/p95/p99, thời gian từng pha và Dev Set/live | Có số đo50 query mock và20 article; chưa có Dev Set/phase timing/live | Đạt phép đo mock; còn thiếu benchmark live |
| T3-16 | 5 người dùng, ít nhất50 query, thành công100%, pool/recovery ổn định | 50/50 query mock qua5 hội thoại thành công; connection trước/sau10/10, không thấy pool timeout; chưa có recovery định kỳ | Đạt tải mock; còn thiếu recovery và kiểm tải live |
| T3-17 | Hồi quy Retrieval v2, giữ12 field candidate/6 field article và public API | Contract/mapping/SSE với fixture đạt; chưa có kiểm chứng trên index v2 thật | Chưa nghiệm thu v2 |
| T3-18 | Tối ưu re-render, latency badge, slow3G và dừng nhận an toàn | Luồng3G và test timeout/abort/disconnect đạt; thiếu latency badge và profiling/frame-drop | Đạt một phần |

## 3. Số liệu đo — HTTP mock

| Chỉ số | Actual |
| --- | --- |
| Phiên đồng thời / request | 5 phiên, mỗi phiên10 lượt, tổng 50 |
| Thành công / lỗi | 50 /0 |
| Chat full-response p50 /p90 /p95 /p99 | 36.64 /109.7 /272.99 /583.76 ms |
| ViewerAPI20 lookup p95 | 10.45ms |
| Connection DB trước/sau | 10/10 (không phải peak monitoring) |
| UI kiểm bổ sung | Viewer360px/768px không tràn ngang, sourceHTTPS/rel an toàn; hỏiđáp slow 3G hoàn tất |

[Báo cáo máy đọc](latency_report_week8.json).

## 4. Bằng chứng và giới hạn

Probe tạo5 worker, mỗi worker10 lượt trong hội thoại riêng; đo đến khi nhận complete.
Article được đo qua20 GET tuần tự. Phân vị tính theo nearest-rank.

Kết quả tại `backend/target/final-acceptance-20261030/mock-performance.json` và
`ui-probe.json`. Chưa có số đo từng pha hoặc benchmark Dev Set/live.

## 5. Việc còn thiếu

1. **Team1/2:** bàn giao Retrieval v2, runtime live và dữ liệu đánh giá.
2. **Team3:** hoàn thiện runner/instrumentation từng pha; chạy5 người dùng/50 query trên Dev Set thật.
3. **Team3:** kiểm p95 chat≤45 giây, Viewer≤1 giây; giám sát pool và recovery định kỳ.
4. **Team3:** bổ sung latency badge, profiling và tối ưu re-render/frame drop.
