# Biên bản kiểm chứng nhiệm vụ Team 3 — Tuần 8

**Ngày kiểm tra:** 28/10/2026 (Asia/Saigon).
**Căn cứ hiện hành:** [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) (đặc tả chính),
[CODING_CONVENTIONS.md](../../../docs/CODING_CONVENTIONS.md) (quy chuẩn/DoD),
[tasks.md](tasks.md) (phân rã nhiệm vụ tuần). Jira phục vụ theo dõi công việc.
**Source kiểm tra:** `62c3556bab16e106e2e6ff29b0280a96fb738146` cùng thay đổi tài liệu chưa commit; không sửa code nghiệp vụ/test hoặc dataset để làm kết quả đạt.
**Môi trường:** Windows, JDK25/Spring Boot4.1.1, Maven Wrapper3.9.16, Node24.21,
Python3.12 trong venv kiểm thử riêng, PostgreSQL18 database riêng, Edge headless profile riêng.
**Phạm vi kết luận:** kiểm chứng kỹ thuật; chưa thay phê duyệt nhóm/gate hoặc trạng thái Jira.

**Đối chiếu nguồn ngày 28/10:** ARCHITECTURE §8.1 và CODING_CONVENTIONS §3.3/§7 cho ngân sách thời gian, tài nguyên và bằng chứng; số phiên/query, phase timing và latency badge được cụ thể hóa tại tasks tuần8. Các phép đo mock chưa thay benchmark live/Dev Set.
Kết luận dựa trên baseline/quy chuẩn/task hiện hành, không loại tiêu chí chỉ vì Jira cũ
chưa ghi. Lượt cập nhật nguồn này không chạy lại build/test hoặc thay số liệu đã đo.

## 1. Kết luận

**Chưa nghiệm thu trọn tuần8.** Đã kiểm tra tải mock 5 phiên / 50 query, Viewer và mạng3G.
Chưa có benchmark Dev Set với RAG thật, đo từng pha, Retrieval v2 và profiling frontend đầy đủ.

## 2. Đối chiếu từng task

| Task | Expected / DoD | Actual và căn cứ | Kết luận |
| --- | --- | --- | --- |
| VLRA-T3-15 | Runner latency, p50/90/95/99, từng pha, Dev Set/live p95≤45s | Probe local đo 50 query mock và20 article; có percentile nhưng không chạy retrieval/rerank/LLM, không Dev Set/phase timings. Báo cáo JSON kèm theo ghi rõ mock và phần thiếu. | Đạt phép đo mock, chưa đạt benchmarklive |
| VLRA-T3-16 |5 user,≥50 query,100%success, pool ổn định và recovery tự giải phóng |50/50mock query qua5 conv thành công; sốconnection DB10 trước/10 sau, không thấy pool timeout trong log. Đây là tải ngắn, không chứng minh khôngleak dài hạn. Recovery chỉ startup/theo yêu cầu, chưa cóquétđịnh kỳ30s. | Đạt tải mock; recovery còn thiếu |
| VLRA-T3-17 |Regression trên Retrieval v2 thật, giữ12 candidate/6 article/publicAPI | Tests contract/mapping/SSE và mock API đạt nhưng không có môi trường index v2 được cấu hình để chạy tuyến thật; live ready 503. Không suy tính tương thích Retrieval v2 từ fixture. | Chưa kiểm chứng v2 |
| VLRA-T3-18 |Giảmre-render, debug latency badge, slow 3G, dừng nhận an toàn | Slow 3G functional đạt; FEunit timeout/abort và Backend disconnect tests đạt. Chưa có latency badge trong UI, chưa có profiling render/frame-drop hay tối ưu code trong lượt này. | Đạt một phần |

## 3. Số liệu mới đo — chỉ HTTP mock

| Chỉ số | Actual |
| --- | --- |
| Phiên đồng thời / request |5 phiên, mỗi phiên10 lượt, tổng 50 |
| Thành công / lỗi |50 /0 |
| Chat full-response p50 /p90 /p95 /p99 |83.96 /197.72 /212.3 /360.32 ms |
| ViewerAPI20 lookup p95 |10.16ms |
| Connection DB trước/sau |10/10 (không phải peak monitoring) |
| UI kiểm bổ sung |Viewer360px/768px không tràn ngang, sourceHTTPS/rel an toàn; hỏiđáp slow 3G hoàn tất |

[Báo cáo máy đọc](latency_report_week8.json) chứa mode, samples và phần chưa đo; không điền
số liệu giả vào phases/retrieval/LLM. Đây là probe HTTP Node builtin trong môi trường kiểm thử,
không phải triển khai runner k6/JMeter/Locust chính thức hoặc nghiệm thu Dev Set.
Không so p95 mock≈0.212s với target 45s rồi kết luận live đạt.

## 4. Lệnh, evidence và giới hạn

[Lệnh/setup chung](../week5/verification.md#3-lệnh-chạy-lại); sau khi app mock Team2
được bật với `RAG_MOCK_SCENARIO=answered`, probe tạo5 worker concurrent, mỗi worker gửi10 lượt
nối tiếp trong conv riêng. Mỗi lượt dùngUUIDv4, đọc đến complete, kiểm answered/citation;
đo từ trước fetch đến khi đọc hết SSE bằng performance.now, không đo 50 lượt trên cùng conv.
Article đo 20GETtuần tự, không gọi LLM. Dùng nearest-rank cho các percentile.

Script/raw local ignored: `backend/target/week-acceptance-20261028/{probe.mjs,mock-performance.json,ui-probe.mjs,ui-probe.json}`.
Reproduce: bật stack mock như tuần5, chạy `node <audit-dir>/probe.mjs` và
`node <audit-dir>/ui-probe.mjs`; cần đúng ports15173/18043/18044/19242 và live-readiness18049.
Đó là script kiểm chứng local, chưa là runner chia sẻ của sản phẩm. JSON summary ở tuần8
được lưu cùng báo cáo để review; người nhận không coi file JSON đó là test đã chạy trên máy mình.

## 5. Việc còn thiếu

1. Chốt Dev Set, index v2 và live runtime/model/provider; chạy lại50 query/5 user trên tuyến thật.
2. Bổ sung instrumentation từng pha và log trace; đopeak/pool ổnđịnh và leak lâu hơn nếu cần.
3. Thực hiện recovery định kỳ theo task hoặc quyết định lại yêu cầu trước khi sửa implementation.
4. Triển khai/đo re-render và debug latency badge; bổ sung kiểm chứng stop receiving trên UI sau thay đổi.
5. Không sửa code, task DoD hoặc dataset để nâng kết luận trong lượt nghiệm thu.
