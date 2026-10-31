# Biên bản nghiệm thu Team 3 — Tuần 8

**Ngày kiểm chứng T3-15:**31/10/2026. **Nhiệm vụ:** [tasks.md](tasks.md).

## 1. Kết luận

**Chưa đủ điều kiện nghiệm thu tuần8.**

T3-15 đã có runner và timing bốn pha, đạt smoke50/50 chat +50/50 lookup.
Chưa có benchmark Dev Set/live. T3-16 còn recovery/giám sát pool và kiểm tải live;
T3-17 chờ Retrieval v2/Article Store; T3-18 còn latency badge/profiling/tối ưu render.

## 2. Đối chiếu từng task

| Task | Expected / DoD | Actual | Kết luận |
| --- | --- | --- | --- |
| T3-15 | Runner, p50/p90/p95/p99, thời gian từng pha và Dev Set/live | Locust finite runner;50 chat/50 lookup mock, warm-up1 riêng;50/50 timing đủ4 pha; thiếu Dev90/runtime live | Công cụ/guard đạt; chưa khép benchmark live |
| T3-16 | 5 người dùng,≥50 query, pool/thread/recovery ổn định | Runner hỗ trợ cấu hình5 users; chưa có recovery định kỳ và giám sát pool/long-duration cho task này | Còn thiếu recovery, giám sát tài nguyên và kiểm tải live |
| T3-17 | Hồi quy Retrieval v2,12 field candidate/6 field article và public API | Public contract/mapping đạt với fixture; chưa có index v2 bàn giao; API article trên nhánh Team2 chưa tích hợp và fallback sai thứ tự Khoản | Chưa nghiệm thu v2/Viewer thật |
| T3-18 | Re-render, latency badge, slow3G và dừng nhận | Hành vi parser/abort/disconnect hiện có; chưa có latency badge hoặc bằng chứng profiling/frame-drop | Chưa khép tối ưu FE |

## 3. Số liệu đo — HTTP mock

| Chỉ số T3-15 | Actual |
| --- | --- |
| Users cấu hình / mẫu chat | 5 users,50 lượt mới/50 hội thoại; khác kịch bản5 hội thoại×10 lượt của T3-16 |
| Chat thành công / lỗi | 50 /0 |
| Article thành công / lỗi | 50 /0 |
| Warm-up | 1 chat+lookup, loại khỏi phân vị chính |
| Chat p50/p90/p95/p99 | 79.751 /152.934 /181.887 /227.617 ms |
| Article API p95 | 75.952 ms |
| Timing bốn pha | 50/50, trace/mã lượt khớp |
| P95 init / AI / DB / stream | 62.986 /39.743 /34.710 /16.575 ms |
| Thiếu căn cứ / upstream ngừng | Complete không lookup / giữ lỗi và timing failed, p95 thành công=null |

[Báo cáo máy đọc](latency_report_week8.json) ·
[Kiểm chứng T3-15](vlra-t3-15-latency-measurement/validation.md).

## 4. Bằng chứng và giới hạn

T3-15: `backend/target/t3-15-latency-20261031/` và `integration-release/`.
Maven130/130, Python33/33 (20 mới +13 hồi quy), public contract76/76 +4 wire payload.
Runner đo tới terminal/body, không dùng native Locust header metric hoặc cộng warm-up.
Phân vị nearest-rank. AI Service time chưa tách Retrieval/Rerank/LLM; article API chưa
bao gồm render UI. Mock luôn MOCK_ONLY; live thiếu đầu vào bị BLOCKED, không tự tạo Dev.

## 5. Việc còn thiếu

1. **Team1/2:** Dev Set đã kiểm chứng, snapshot/index và pipeline live; Article Store đúng nguyên văn/thứ tự.
2. **Team3 — T3-15:** chạy Dev90 với split report và timing đủ; đối chiếu p95 chat≤45s/article API≤1s.
3. **Team3 — T3-16:** recovery định kỳ, giám sát pool/thread, kiểm5 hội thoại/≥50 query và tải live.
4. **Team3 — T3-17/18:** hồi quy v2 thật; latency badge, profiling/tối ưu render, kiểm Viewer UI/slow3G/dừng nhận.
