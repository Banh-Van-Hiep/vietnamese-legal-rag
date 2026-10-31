# Validation — VLRA-T3-15

**Ngày kiểm chứng:**31/10/2026. **Kết quả:** công cụ/timing đạt kiểm chứng mock;
T3-15 chưa khép DoD benchmark live.

## 1. Kết luận

Runner hữu hạn và timing bốn pha đã hoạt động qua Java/PostgreSQL/FastAPI HTTP mock.
Đạt50/50 chat,50/50 lookup; warm-up1 lượt được loại khỏi số liệu chính;50/50 trace
khớp clientRequestId và đủ bốn pha. Chưa có Dev90/runtime live để nghiệm thu hai ngưỡng.

## 2. Expected / Actual

| Tiêu chí | Expected | Actual | Kết quả |
| --- | --- | --- | --- |
| SC001 runner/report | ≥20 chat/20 lookup, raw counts/phân vị/lỗi đúng | 50/50 chat +50/50 lookup,5 users cấu hình,50 hội thoại mới; warm-up1 tách riêng; nearest-rank/raw samples | Đạt mock |
| SC002 timing | 100% lượt mới thành công ghép đủ4 pha | 50/50; backend_init/ai_service/db_persist/stream_finish, đơn vị ms; tổng/các pha không chồng | Đạt mock |
| SC003 compatibility | Public payload/persistence/error/replay không đổi | Backend130/130 gồm16 PostgreSQL;13 StreamApiTests;76 contract và4 wire payload hợp lệ | Đạt phạm vi đã kiểm |
| SC004 chống kết luận giả | Mock/thiếu precondition không đạt live | Mock exit0/MOCK_ONLY/live_target_verified=false; live thiếu Dev report exit2/BLOCKED | Đạt guard; benchmark live chưa chạy |
| Thiếu căn cứ | Complete hợp lệ, không lookup bịa | 1/1,0 article; đủ timing, exit0 | Đạt mock |
| Upstream ngừng | Giữ lượt lỗi, không lấy lỗi vào p95 thành công | 1 failed, error SERVICE_UNAVAILABLE, p95=null; timing failed giữ riêng, exit1 | Đạt nhánh lỗi |
| Unicode/deadline/output | UTF8/cp đúng, timeout toàn lượt, không overwrite | Request2000 emoji qua stack; heartbeat deadline và input/output guards qua unit tests | Đạt |

## 3. Kết quả kiểm chứng

- Maven Wrapper package:130 test,0 fail/error/skip; gồm4 TurnTimingsTests +13 StreamApiTests, là nhóm con của130.
- Python:33 test đạt, gồm20 test T3-15 và13 hồi quy công cụ chia Golden.
- Public schema/semantic:76/76 và4 payload/binding từ HTTP test mới.
- Script Locust finite thực: exit0 với50 chat/50 lookup; Không cộng native HTTP header stats hoặc warm-up vào tổng.

| Chỉ số API mock | Kết quả |
| --- | ---: |
| Chat p50/p90/p95/p99 (ms) | 79.751 /152.934 /181.887 /227.617 |
| Article p95 (ms) | 75.952 |
| Backend init p95 (ms) | 62.986 |
| AI Service p95 (ms) | 39.743 |
| DB persist p95 (ms) | 34.710 |
| Stream finish p95 (ms) | 16.575 |

## 4. Bằng chứng và giới hạn

`backend/target/t3-15-latency-20261031/`: backend-package.log, python-all-tests.log,
contract.json; `integration-release/`: smoke-report.json, insufficient-report.json,
unavailable-report.json, blocked-live-report.json, backend.log và integration-summary.json.

JDK25/Spring Boot4.1.1, Python3.12.15/Locust2.43.1, PostgreSQL18 test riêng.
Backend trace lấy từ response header theo ApiRequestFilter; không yêu cầu echo trace client.
AI timing gồm chờ HTTP và validation; chưa có số pha Retrieval/Rerank/LLM riêng.
Article timing là API body, không render Viewer. Không gọi provider/model thật.
Source hashes là checkout công cụ, không tự chứng minh revision server/model bên ngoài.
Công cụ không phê duyệt review pháp lý từ split report hoặc response đúng schema.

## 5. Điều kiện để khép T3-15

1. Team1 bổ sung150, Team2 kiểm chứng; Team3 chia90/60 và bàn giao Dev/split report đúng hash.
2. Team1/2 bàn giao snapshot/index và runtime query/article thật; article đúng nguyên văn/thứ tự.
3. Bật timing trên Backend; chạy Dev90, không lỗi, timing đủ và đạt p95 chat≤45s/article API≤1s; kiểm Viewer UI riêng để chốt toàn tuần.

- [x] Công cụ và timing được triển khai/kiểm chứng.
- [x] Contract, replay, nhánh lỗi và dữ liệu nguồn được bảo toàn theo kiểm tra.
- [ ] Benchmark live trên Dev90 bàn giao và xác nhận ngưỡng.

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Quickstart](quickstart.md) ·
[Nghiệm thu tuần8](../verification.md).
