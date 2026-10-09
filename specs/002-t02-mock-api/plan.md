# Implementation Plan: Task02 — API mock query/document
**Branch**: feature/team3/tuan | **Date**: 2026-10-09 | **Spec**: [spec.md](spec.md)
**Status**: Đã implement và kiểm chứng local: package74/runner37/HTTP8 PASS. Nhánh thực khác feature key 002, không switch. Xem [báo cáo T02](../../docs/team3_fullstack/t02-mock-api.md); không thay nghiệm thu nhóm.

## Summary
Giữ Backend/T01, bổ sung cấu hình mock query/document độc lập, guard output theo Team 3
và kiểm chứng fixture/API thực. Không đổi route/field/status hoặc frontend/shared schema.

## Technical Context
**Language/Version**: Java 25, PowerShell 5.1.
**Primary Dependencies**: Spring Boot 4.1.1, Maven Wrapper 3.9.16 và starters hiện có; không thêm.
**Storage**: ConversationService memory; không migration/DB/history AI mới.
**Testing**: JUnit/SpringBootTest/Mockito hiện có, PowerShell harness T01 và HTTP smoke local.
**Target Platform**: Windows local; không deploy/container hay Linux runner mới.
**Project Type**: Backend hiện có.
**Performance Goals**: Không SLA/coverage/load mới; kích hoạt timeout bằng fixture, không chờ upstream.
**Constraints**: Q1–Q3 T01, source Team3 v1.2, lựa chọn Codex theo ủy quyền trong decisions.md.
**Scale/Scope**: Một tuple mock_v1/art1; 5 query modes, 4 article modes; không luật thật/GT.

## Constitution Check
| Nguyên tắc | Pre/post design |
| --- | --- |
| API | PASS: trích Team3 1.6–1.8/1.10; không field/endpoint mới, giữ 406 |
| Ranh giới team | PASS: Backend Team3 + tài liệu; không FE/Team1/2/schema chung |
| Tái sử dụng | PASS: AiClient/MockAiClient/services/DTO/store, dependency không đổi |
| Kiểm chứng | PASS: input/output/config/unit/HTTP/regression T01 + expected/actual |
Checklist spec 14/16: hai ngoại lệ API tham chiếu kế thừa được ghi; không functional ambiguity.
Quyết định vận hành không tự mang nhãn nhóm phê duyệt; người dùng đã ủy quyền ghi lại để review.

## Project Structure
### Documentation (this feature)
specs/002-t02-mock-api/{spec,plan,research,data-model,quickstart,decisions,tasks}.md,
contracts/README.md, checklists/requirements.md; report triển khai sau tại docs/team3_fullstack/t02-mock-api.md.

### Source Code (repository root)
| Path | Đã có | Tác động dự kiến |
| --- | --- | --- |
| team3_fullstack/backend/src/main/java/com/legalai/backend/ai/MockAiClient.java | Success + tuple mock | Thêm query/article scenario, giữ constructor legacy |
| team3_fullstack/backend/src/main/java/com/legalai/backend/ai/AiResponseValidator.java | Chưa có | Guard typed DTO, 502 nếu sai |
| team3_fullstack/backend/src/main/java/com/legalai/backend/chat/ChatService.java | accept/complete/fail | Guard query trong try trước complete để lưu failed/trace đúng |
| team3_fullstack/backend/src/main/java/com/legalai/backend/document/DocumentService.java | trả AiClient trực tiếp | Guard response trước return, kiểm tra tuple yêu cầu |
| team3_fullstack/backend/src/main/resources/application.properties | legacy status | Thêm query/article properties với fallback tương thích |
| team3_fullstack/backend/run-local.ps1, .env.example | Q2 + whitelist 5 key | Whitelist/snapshot hai key mới, giữ Q2/finally/warnings |
| team3_fullstack/backend/src/test/powershell/RunLocalConfigurationTests.ps1 | Harness T01 | Ma trận key mới + regression, không framework mới |
| team3_fullstack/backend/src/test/java/com/legalai/backend/AiResponseValidatorTests.java | Chưa có | Boundary/nullable/marker/ID/HTTPS/Unicode guard |
| team3_fullstack/backend/src/test/java/com/legalai/backend/MockScenarioTests.java | Chưa có | Modes, fixture liên kết, legacy/error precedence |
| team3_fullstack/backend/src/test/java/com/legalai/backend/BackendConfigurationTests.java | Spy/probe T01 | HTTP controlled invalid query/article →502; không public probe mới |
| docs/team3_fullstack/t02-mock-api.md | Chưa có | Hướng dẫn/scenario/evidence/limitations |
POM, DTO field definitions, controllers/routes, store, CORS/exception handler/406 giữ nguyên.
Khi DTO không đáp ứng nguồn phải ghi vấn đề; không tự đổi schema.

### Cấu hình và tương thích
- MOCK_QUERY_SCENARIO: answered, insufficient_context, internal_error, service_unavailable, upstream_timeout.
- MOCK_ARTICLE_SCENARIO: success, internal_error, service_unavailable, upstream_timeout.
- MOCK_ANSWER_STATUS giữ answered/insufficient_context, mặc định answered.
- Query scenario mới vắng dùng legacy status; article mặc định success. Giá trị key cung cấp
  blank/ngoài enum fail, legacy status vẫn phải hợp lệ. Không magic question hoặc new CLI param.
- app.mock.query-scenario dùng MOCK_QUERY_SCENARIO khi có; khi vắng fallback tới property app.mock.answer-status đã phân giải (legacy), giữ tương thích test/property override hiện có; app.mock.article-scenario default success. Không fallback cho winner blank/sai. Xem D05 trong decisions.md.
  Không dùng empty string làm absent. Runner chỉ mở thêm hai supported key và test Q2 từng key.
- Giữ constructors gọi trực tiếp trong test; Spring dùng constructor cấu hình rõ ràng.
- Validate tuple tồn tại trước article scenario; input controller/parser trước service scenario.

### Guard output
AiResponseValidator static trong ai/ kiểm tra typed RagAnswer/ArticleResponse/Citation.
Query guard sau ai.query và trước complete, trong try; ApiException502 được fail(turn,error)
giữ conversation ID. Document guard kiểm schema/response IDs trùng request; 404 nguồn giữ nguyên.
Field strings nonblank/đúng max code point; status/nullable/UUID public metadata theo nguồn;
HTTPS absolute source, ID ASCII, citations 1–10 hoặc [] tùy status.
Marker numeric kể cả C0/C11/C01 phải bị xét; first distinct mentions C1..Cn, ID set tương ứng,
không thừa/trùng chunk. Marker lặp hợp lệ; không bắt citation array order ngoài contract.
Không gọi document mỗi query; liên kết fixture kiểm qua test. Không dùng response malformed
làm public scenario. Không normalize thành dữ liệu khác hoặc sinh ID giả để che output sai.

### Kiểm chứng
| AC | Evidence |
| --- | --- |
| 01 | Existing input tests + error mode HTTP 400; input không bị scenario che |
| 02 | success modes + full DTO/marker/constraints; legacy vẫn hoạt động |
| 03 | Existing replay/ID tests + HTTP new/followup/new conversation |
| 04 | Unit fixture linkage + document HTTP/source/newline |
| 05 | Real query 500/503/504 with trace/retryable/safe envelope |
| 06 | Document ID/body/query/404 tests and smoke |
| 07 | Article modes real HTTP; guard negative unit + HTTP spy 502, failed query/header |
| 08 | Wrapper package + harness + smoke, report, scope hash/working tree |

## Complexity Tracking
Không constitution violation hoặc kiến trúc mới. Guard/selector ở Backend hiện có; không HTTP AI.
