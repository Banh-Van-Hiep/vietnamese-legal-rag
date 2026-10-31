# Tasks — VLRA-T3-15

Nguồn: [spec](spec.md), [plan](plan.md). Chỉ sửa tasks.md trong bộ task này.

## Phase 1 — Setup

- [x] T001 Tạo bộ spec/clarify/plan/research/data-model/contracts/quickstart, kiểm constitution và analyze tại team3_fullstack/docs_3/week8/vlra-t3-15-latency-measurement/.
- [x] T002 Pin Locust2.43.1 trong team3_fullstack/requirements-performance.txt và tạo môi trường test riêng; không đổi pyproject của Team1/2.

## Phase 2 — Foundation

- [x] T003 Viết kiểm thử parser/dataset/percentile/log/provenance/output trong team3_fullstack/tests/test_latency_report.py: UTF8/CRLF/heartbeat/truncated/error/binding/không mẫu/duplicate/Dev hash sai/không overwrite (FR001/003/005/007/008/009).
- [x] T004 Triển khai helpers thuần Python tại team3_fullstack/tools/latency_report.py; reuse schema public/semantics; các pha chưa chạy null, thời gian hữu hạn≥0, output không overwrite, Dev90 từ report input150/test60 (FR001/003/004/005/007/008/009).

## Phase 3 — US1: đo đến terminal và report

- [x] T005 [US1] Kiểm thử finite jobs, timeout toàn lượt kể cả heartbeat, warm-up, failure/raw counts và response validation trong team3_fullstack/tests/test_measure_latency.py (FR002/003/004/005, SC001).
- [x] T006 [US1] Triển khai Locust CLI tại team3_fullstack/tools/measure_latency.py: clientRequestId mới và trace Backend trả, hàng đợi hữu hạn, runner quit ở main, terminal SSE metrics tách native headers; lookup citation đúng ID và JSON report (FR002/003/004/005/008, SC001).

## Phase 4 — US2: timing Backend

- [x] T007 [P] [US2] Kiểm thử timing thành công/exception/null/replay/tổng không chồng tại team3_fullstack/backend/src/test/java/com/legalai/backend/chat/stream/TurnTimingsTests.java; mở rộng StreamApiTests để kiểm opt-in JSON log/trace/outcome và public behavior giữ nguyên (FR006/007, SC002/003).
- [x] T008 [US2] Thêm TurnTimings.java, đo quanh accept/AI/complete/stream trong StreamService.java và CHAT_LATENCY_ENABLED mặc định false ở application-rag.properties; log whitelist không question/answer/secret, telemetry lỗi không đổi request (FR006/007, SC002/003).
- [x] T009 [US2] Ghép timing theo trace+client_request_id trong latency_report.py/measure_latency.py; chặn duplicate/replay/phase thiếu và upstream_origin sai trong live; kiểm parser chỉ xuất field whitelist (FR007/008/009, SC002).

## Phase 5 — US3: live preconditions và thresholds

- [x] T010 [US3] Bổ sung preflight live trong measure_latency.py: Dev report/hash/count/status khớp, RAG ready không mock; metadata SHA256/source/dependency, ngưỡng p95≤45s/≤1s, raw errors và exit0/1/2 đúng (FR008/009/010, SC004).
- [x] T011 [US3] Kiểm chứng live bị chặn khi thiếu Dev90/runtime bằng CLI hiện có, không gọi LLM hoặc tạo dataset thay thế; ghi evidence tại backend/target/t3-15-latency-20261031/ (FR009/010, SC004).

## Phase 6 — Integration và bàn giao

- [x] T012 Chạy Maven Wrapper package với PostgreSQL test riêng, Python tests, public schema/wire; smoke ít nhất20 chat/20 article qua Java/PG/FastAPI HTTP mock và đối chiếu4 pha (SC001/002/003).
- [x] T013 Cập nhật docs/team3_fullstack/performance-measurement.md/README.md, validation.md trong bộ task và week8/verification.md cùng latency_report_week8.json theo kết quả thực; giữ form, không mục lệnh hoặc sửa tasks.md tổng tuần; giới hạn Viewer UI/model được ghi rõ (SC001–004).
- [ ] T014 Chạy benchmark trên Dev90 đã kiểm chứng và pipeline live được bàn giao; đối chiếu hai ngưỡng, timing đủ, bàn giao số đo để khép T3-15; giữ mở khi thiếu phụ thuộc (SC004).

## Dependencies và parallel

T001→T002→T003→T004→T005→T006; T007 độc lập file với T005/006 sau foundation,
T008 sau T007; T009 sau T006/008; T010→T011 sau T009; T012→T013;
T014 phụ thuộc Dev Set và live bên ngoài. [P] là độc lập file, không là yêu cầu thêm agent.

MVP: US1 xuất số đo đúng; kế tiếp US2 timing; cuối US3 preflight/benchmark.
Không cộng warm-up/native Locust HTTP stats hoặc sub-suite vào tổng test khác.
