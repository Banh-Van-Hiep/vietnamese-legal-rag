# Tasks: Task02 — API mock query/document

Ghi chú tổ chức tài liệu 09/10/2026: đường dẫn báo cáo trong tài liệu này là vị trí bàn giao
hiện tại (verification.md trong spec); baseline/log gốc vẫn ghi đường dẫn docs/ trước khi chuyển.
Snapshot lúc plan và checkbox/evidence đã kiểm chứng được giữ nguyên; không chạy lại test khi dọn tài liệu.

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/README.md, quickstart.md, decisions.md.
**Status**: 18/18 task đã kiểm chứng local; package74, runner37, HTTP8 PASS. Review hash/diff147 files không thay đổi ngoài phạm vi, cleanup0 PID/cổng. Bàn giao: [verification.md](verification.md). Nhánh feature/team3/tuan giữ nguyên.
[P] chỉ file độc lập sau prerequisite. Không Maven/test song song với sửa Java hoặc Maven khác.
Tests được spec yêu cầu; không thêm framework/TDD policy/coverage. Existing endpoint/DTO/input/store/CORS
không được tạo lại; chỉ guard/scenario/assertion còn thiếu. Checkbox cần evidence mới.

## Phase 1: Setup
- [X] T001 Ghi baseline branch/HEAD/status/diff/hash và môi trường JDK25/wrapper vào team3_fullstack/backend/target/t02/baseline.txt và baseline-hashes.json; giữ code/T01/.env đang có, verify ignores và fixture isolation.

## Phase 2: Foundational — shared selector và guard
- [X] T002 [P] Tạo team3_fullstack/backend/src/test/java/com/legalai/backend/MockScenarioTests.java cho query enum 5 mode, article enum 4 mode, legacy answered/insufficient_context, invalid/blank config, tuple missing404 trước scenario; fixture citation-document đồng nhất; dựa source không mock luật thật.
- [X] T003 [P] Tạo team3_fullstack/backend/src/test/java/com/legalai/backend/AiResponseValidatorTests.java: null/status/text, “answer nonblank 1–12000 code point”, “content nonblank 1–200000 code point”, “answered 1–10; insufficient_context rỗng và không marker”, “citation_id C1..C10 duy nhất”, “chunk_id/document_id 1–200, article_id 1–100, document_title 1–500, article 1–100, clause/point null hoặc 1–100, source_url HTTPS tuyệt đối 1–2048”; first mention C1..Cn, C0/C11/C01, duplicate chunk/ID, unused marker/citation, reversed citation array hợp lệ, emoji boundary và article ID mismatch →502(false).
- [X] T004 Sửa team3_fullstack/backend/src/main/java/com/legalai/backend/ai/MockAiClient.java và team3_fullstack/backend/src/main/resources/application.properties: query/article config độc lập theo plan, nested fallback giữ legacy valid hai status, constructor legacy còn dùng được; modes fail đúng500/503/504; shared tuple metadata; không route/DTO field mới.
- [X] T005 Mở whitelist/snapshot hai key MOCK_QUERY_SCENARIO/MOCK_ARTICLE_SCENARIO trong team3_fullstack/backend/run-local.ps1, chú thích team3_fullstack/backend/.env.example và case capture/precedence/fallback/invalid/restoration trong team3_fullstack/backend/src/test/powershell/RunLocalConfigurationTests.ps1; Q2/nguyên tắc blank/Maven exit T01 giữ nguyên.
- [X] T006 Tạo team3_fullstack/backend/src/main/java/com/legalai/backend/ai/AiResponseValidator.java theo constraints T003/data-model; typed query/article guard, 502 UPSTREAM_INVALID_RESPONSE false/message an toàn, không sửa/normalize ID sai hoặc thêm dependency/public malformed scenario.

## Phase 3: US1 — query success/ID (P1, MVP)
**Independent test**: hai success + IDs/new/followup/new conversation + input validation; không UI/AI.
- [X] T007 [US1] Gọi query guard trong team3_fullstack/backend/src/main/java/com/legalai/backend/chat/ChatService.java sau ai.query, trong try trước complete để failed502 giữ conversation ID; không rewrite accept/replay/history.
- [X] T008 [US1] Bổ sung controlled spy invalid RagAnswer/status/null trong team3_fullstack/backend/src/test/java/com/legalai/backend/BackendConfigurationTests.java: HTTP502, envelope/retryable=false, conversation ID đúng lượt và failed state, không secret; không public probe mới.
- [X] T009 [US1] Chạy wrapper focused guard/scenario/MockApiTests/InsufficientContextApiTests/BackendConfigurationTests trong team3_fullstack/backend/mvnw.cmd; lưu team3_fullstack/backend/target/t02/query-tests.log, xác nhận success/ID/input và query malformed502.

## Phase 4: US2 — citation/document (P1)
**Independent test**: known tuple/success/full source/newline và400/404/502, không UI.
- [X] T010 [US2] Guard ArticleResponse trong team3_fullstack/backend/src/main/java/com/legalai/backend/document/DocumentService.java trước return theo request IDs; giữ404 source và common handler.
- [X] T011 [US2] Bổ sung spy invalid article tuple/schema→HTTP502 trong team3_fullstack/backend/src/test/java/com/legalai/backend/BackendConfigurationTests.java; sau T008/T009 cùng file, không endpoint/test scenario public.
- [X] T012 [US2] Bổ sung full citation-to-article ID/title/article/source/content/newline assertions trong team3_fullstack/backend/src/test/java/com/legalai/backend/MockApiTests.java, giữ input/body/query/404 tests hiện có.
- [X] T013 [US2] Chạy wrapper focused guard/scenario/MockApiTests/BackendConfigurationTests tại team3_fullstack/backend/mvnw.cmd; lưu team3_fullstack/backend/target/t02/document-tests.log và archive reports, kiểm chứng full fixture/doc errors.

## Phase 5: US3 — scenario local/error (P2)
**Independent test**: query/document500/503/504 qua instance config thật, input400/404 trước lỗi;
legacy/new selectors vàQ2, khôngprobe.
- [X] T014 [US3] Chạy team3_fullstack/backend/src/test/powershell/RunLocalConfigurationTests.ps1 với JDK25; lưu team3_fullstack/backend/target/t02/runner-tests.log; xác nhận base T01 và hai key mới priority/file fallback/blank/semantic wrong retained/restoration.
- [X] T015 [US3] Thực hiện HTTP matrix theo specs/002-t02-mock-api/quickstart.md bằng fixture/helper riêng ở team3_fullstack/backend/target/t02/: legacy insuff, explicit new answered, terminal key thắng file, internal/unavailable/timeout cho query/document; kiểm tra envelope/retryable/trace, query input400, doc400/404 và GET document ?extra=1/body {} đều400 trong success/error modes, health/CORS/probe absent và invalid config nonzero. Giữ PID/port ownership/Hidden/cleanup, ghi expected/actual/commands, không sửa .env thật.

## Phase 6: Polish và bàn giao
- [X] T016 Chạy final wrapper package qua team3_fullstack/backend/run-local.ps1 với build fixture dưới target/t02, không skipTests; archive reports và log team3_fullstack/backend/target/t02/final-validation.log; full T01/T02 tests/harness regression, JAR không test probe, không lặp smoke unchanged nếu không failure mới.
- [X] T017 Viết specs/002-t02-mock-api/verification.md và cập nhật trạng thái specs/002-t02-mock-api/{spec,plan,tasks,decisions,quickstart}.md từ kết quả thật: 8AC, sources/working tree/runtime/command/expected/actual/limits và quyền tự quyết; không gán quyết định mới là nhóm phê duyệt.
- [X] T018 Review status/diff/hash với team3_fullstack/backend/target/t02/baseline-hashes.json, giữ T01/source/FE/Team1/2/sharedschema/.env ngoài target; confirm no owned process/port leak, cập nhật checkbox trong specs/002-t02-mock-api/tasks.md chỉ khi evidence đạt; không commit/push/merge.

## Dependencies and parallel examples
| Task | Depends on |
| --- | --- |
| T001 | None |
| T002 | T001 |
| T003 | T001 |
| T004 | T002 |
| T005 | T004 |
| T006 | T003 |
| T007 | T004, T005, T006 |
| T008 | T007 |
| T009 | T008 |
| T010 | T006, T009 |
| T011 | T008, T010 |
| T012 | T011 |
| T013 | T012 |
| T014 | T005, T013 |
| T015 | T014 |
| T016 | T015 |
| T017 | T016 |
| T018 | T017 |

Shared T001→{T002,T003}→{T004,T005,T006}→US1(T007–009)→US2(T010–013)→US3(T014–015)→T016–018.
T002 và T003 có thể viết song song sau baseline (file khác); edits/test runs còn lại tuần tự.
US1: không[P] nội bộ; US2: cùng guard/test classes nên không[P]; US3: harness và smoke tuần tự,
không đồng thời thay process env/cổng hoặc build. Không cần đa agent implement.

## AC coverage / completion
| AC | Tasks |
| --- | --- |
| AC-T02-01 | T009, T013, T015 |
| AC-T02-02 | T002, T003, T006–009 |
| AC-T02-03 | T009, T015 |
| AC-T02-04 | T002, T012, T013, T015 |
| AC-T02-05 | T004, T005, T014, T015 |
| AC-T02-06 | T002, T012, T013, T015 |
| AC-T02-07 | T003, T006, T008, T010, T011, T013, T015 |
| AC-T02-08 | T001, T014–018 |

MVP query: T001–T009, kiểm chứng riêng trước document. Full T02 thêm US2/US3 và final evidence.
Tạo file/test không tự hoàn thành: task code cần diff + test; task run cần real log/exit;
report cần source/actual. Scenario error test/probe T01 không thay HTTP matrix T02.

## Evidence cuối — 2026-10-09
T001–006: baseline + foundation-tests.log47 + runner-tests.log37.
T007–009: query-tests.log70; T010–013: document-tests.log70 + document-surefire/.
T014–015: runner37 + http-smoke-results.json8 records; invalid startup exit1.
T016: final-validation.log BUILD SUCCESS74, final-surefire/ và jar-review.json.
T017–018: báo cáo T02, scope-review.json147 baseline/133 unchanged/14 expected changed,
4 new expected files, 0 unexpected; process-cleanup-review.json0 owned PID/0 listener18084.
Tất cả evidence dưới team3_fullstack/backend/target/t02/ (ignore); log runner dẫn fixture ở target/t01/.
Không task triển khai còn mở; Tuấn review quyết định trong decisions.md, không thay nghiệm thu nhóm.
