# T02 — Kết quả kiểm chứng và bàn giao API mock

**Nhóm / phụ trách:** Team 3 / Tuấn. **Task:** T02.
**Kết quả:** 18/18 task, 8/8 AC đã kiểm chứng local ngày 09/10/2026; chưa thay nghiệm thu nhóm.
**Yêu cầu:** [spec.md](spec.md). **Tái hiện kiểm tra:** [quickstart.md](quickstart.md).
**Nguồn API:** [Team 3 v1.2](../../docs/team3_fullstack/team3.md); phạm vi từ
[kế hoạch tuần 2](../../docs/team3_fullstack/team3-week2-spec.md).

## Bàn giao cho thành viên và AI khác

- T02 kế thừa [nền T01](../001-t01-backend-foundation/verification.md), không dựng lại Backend.
- Query/article có selector độc lập ở cấu hình instance; giữ legacy và Q2. Đổi mode cần restart.
  Lỗi hệ thống dùng 500/503/504; input sai vẫn400, missing tuple404. Không thêm field/endpoint chọn scenario.
- Output sai →502 qua guard; query giữ conversation ID sau accept. Một fixture mock_v1/art1
  chia sẻ cùng metadata/citation/source; không phải luật thật hoặc GT.
- T03/T04 có thể dùng API/fixture này. Trang thử FE là thay đổi riêng, không nghiệm thu T03/T04.
  Team 2 thật, DB production/auth/streaming/history AI vẫn ngoài scope.

| Mốc | Commit / nguồn |
| --- | --- |
| Lúc kiểm chứng | bb1bb26017d2c90578635a29ad625e502dee09b6 + working tree trước commit, như log gốc |
| Bàn giao code | 06964cd (scenario), d6d1055 (guard/API tests); runner key mới cùng nền/config 594e24a |
| Bàn giao tài liệu | d15aa51 (specs), 530710e (báo cáo trước khi chuyển về specs/) |
| FE thử riêng | fec29d8; 9 browser checks ở backend/target/frontend-playground/, không thuộc AC T02 |

Commit được đối chiếu từ lịch sử Git local; chưa xác nhận PR/merge. Lần sắp xếp tài liệu này
không chạy lại build/test và không gán số liệu cũ thành kiểm chứng mới.

## Nguồn và workflow

[Team 3 v1.2](../../docs/team3_fullstack/team3.md) là căn cứ API/luồng/kiến trúc; [tuần 2](../../docs/team3_fullstack/team3-week2-spec.md)
xác định phạm vi T02. Q1–Q3 trong [T01 spec](../001-t01-backend-foundation/spec.md) giữ nguyên.
T01 được kiểm tra bằng source và bằng chứng gốc (25 Java tests, 31 runner cases, 8 smoke records);
T02 không được đánh dấu hoàn thành dựa vào báo cáo T01.

Các bước được chạy riêng: specify → clarify → plan → tasks → analyze → sửa U1/C1 → implement.
[Analysis](analysis.md) ghi vấn đề và remediation trước implement.
[Plan](plan.md), [tasks](tasks.md),
[quickstart](quickstart.md) và [decisions](decisions.md)
là bộ tài liệu T02. Không AGENTS.md trong repository/các ancestor đã tìm; constitution được đọc;
không extensions.yml/hook. Checklist spec 14/16 giữ hai ngoại lệ về chi tiết API kế thừa theo yêu cầu
người dùng; không đổi marker của reviewer để tạo kết quả nghiệm thu.

## Đã thay đổi gì

- MockAiClient giữ constructor legacy, thêm selector query/article độc lập theo instance.
  Query: answered, insufficient_context, internal_error, service_unavailable, upstream_timeout.
  Article: success và ba mode lỗi tương ứng. ID/mock tuple và metadata nguồn cũ được giữ, citation lấy
  metadata từ cùng ArticleResponse; không thêm endpoint/field request hoặc magic question.
- AiResponseValidator kiểm typed output theo ràng buộc Team 3: code point, nullable, giới hạn citations,
  ID/chunk duy nhất, marker theo lần nhắc đầu C1..Cn, HTTPS và đúng tuple document/article.
  Output sai →502 UPSTREAM_INVALID_RESPONSE, retryable=false, thông báo an toàn; không tự sửa ID sai.
- ChatService gọi guard trong try trước complete; lỗi sau accept giữ X-Conversation-ID và lưu lượt failed.
  DocumentService guard trước return; validation input và missing tuple vẫn được xử lý trước scenario.
- application.properties, runner whitelist/snapshot và .env.example hỗ trợ hai biến mới.
  Thứ tự Q2 và khôi phục env/location/exit của T01 được giữ. Chỉ chú thích selector trong .env.example
  để không vô tình che legacy; .env cá nhân không sửa.
- Bổ sung 47 ca guard/scenario và 2 HTTP spy tests; mở rộng assertions citation → article và GET body/query;
  runner harness thêm hai key, tổng 37 ca. Không thêm dependency hoặc sửa public DTO.

## Quyết định cần Tuấn review

CL-T02-01/02 và D03–D05 nằm trong decisions.md: selector qua cấu hình khởi động, document có ba mode
lỗi, guard 502, giữ một fixture và fallback query tới property legacy đã phân giải.
Các lựa chọn này do Codex quyết định theo ủy quyền của Tuấn ngày 2026-10-09; không tự gọi là quyết định
mới đã được Team 3 phê duyệt. Đổi mode cần restart. Không còn câu hỏi chức năng chặn implement.
contracts/ chứa schema Team 2 khác API Team 3 về question/IDs/status/citation và timeout code;
đã ghi cụ thể trong spec/research, giữ nguyên shared schema và không triển khai upstream thật.

## Kiểm chứng thực tế ngày 09/10/2026

Java 25.0.1 ở D:\Java\jdk-25, Maven Wrapper 3.9.16, Spring Boot 4.1.1, PowerShell 5.1.
Chỉ đặt JAVA_HOME đúng trong tiến trình kiểm thử (terminal ban đầu kế thừa JDK24); không sửa cấu hình cá nhân.
Các log dưới team3_fullstack/backend/target/t02/ được ignore, chỉ có trên máy kiểm chứng.
Bảng dưới chia sẻ expected/actual và tên evidence; người khác chạy lại qua quickstart, không phụ thuộc log local.

| Bước | Kết quả và bằng chứng |
| --- | --- |
| Foundation | 47 tests, 0 fail/error/skip; foundation-tests.log |
| Query | 70 tests, 0 fail/error/skip; query-tests.log; gồm legacy insufficient context và HTTP502 sau accept |
| Document | 70 tests, 0 fail/error/skip; document-tests.log + document-surefire/ |
| Runner | 37/37 PASS; runner-tests.log dẫn results.json ở target/t01/runner-2c56713cb8d44927be38ab1d6f1facae/ |
| Server thật | 6 instance success/error +2 invalid startup, 8/8 PASS; http-smoke.log và http-smoke-results.json chứa command/owned PID/checks |
| Full package | 74 tests, 0 fail/error/skip, BUILD SUCCESS lúc 22:25:27 +07:00; final-validation.log, final-surefire/, final-test-summary.json |
| Production JAR | Guard có trong JAR; 0 test/probe entries; jar-review.json |
| Cleanup | 0 owned PID còn sống; 0 listener cổng18084; process-cleanup-review.json |

Lệnh package đã chạy qua run-local.ps1 -Task package -EnvFile target/t02/build.env,
với JDK25, legacy answered và hai selector mới absent. Cách tạo fixture và chạy lại ở
[quickstart.md](quickstart.md).

Focused tests gọi mvnw.cmd -B -ntp -Dtest=... test; tên classes đầy đủ được ghi ở tasks/quickstart.
Harness gọi src/test/powershell/RunLocalConfigurationTests.ps1 với JDK25.
Smoke chạy target/t02/SmokeValidation.ps1: Start-Process Hidden, runner + Maven Wrapper,
PID/creation-time ownership, port readiness và cleanup chỉ process do helper tạo.
Với GET body, curl.exe có sẵn được dùng vì HTTP stack .NET Framework/PS5.1 cấm gửi body GET.
Mọi instance kiểm health, CORS được phép/origin ngoài, trace, probe404, query400,
document400/404, extra query400 và GET body400; các mode lỗi không che input validation.
500/503/504 dùng error envelope, code/retryable đúng; query error giữ conversation ID và history failed.
Invalid selector terminal thắng file hợp lệ nhưng startup exit1, không báo readiness giả.

Hai lần helper smoke đầu chưa hoàn tất (PowerShell dynamic scope trong cleanup response và GET body
bị transport cấm) được lưu log riêng, không tính PASS. Một assertion test ban đầu tìm chữ mock trong
content đã sửa để kiểm nhãn “kiểm thử” vốn có trong document_title; không đổi fixture để chiều test.
document-tests-first-failure.log giữ failure cũ; kết quả cuối ở document-tests.log và final package.
Không có bước kiểm chứng bắt buộc nào bị bỏ qua.

## Truy vết tiêu chí nghiệm thu

| AC | Kết quả | Bằng chứng |
| --- | --- | --- |
| AC-T02-01 | PASS — query JSON/type/UUID/code point/body/media/method, validation trước scenario | MockApiTests, final-surefire, mọi HTTP instance query400 |
| AC-T02-02 | PASS — answered/insufficient_context đủ fields/IDs/time, marker/citations/nullable và biên output | MockApiTests, InsufficientContextApiTests, AiResponseValidatorTests, success smoke |
| AC-T02-03 | PASS — omitted/null ID, followup giữ hội thoại, new conversation/message IDs | MockApiTests và success smoke |
| AC-T02-04 | PASS — toàn bộ citation mock mở đúng tuple/title/article/source, full content xuống dòng | MockScenarioTests, MockApiTests, explicit-answered smoke |
| AC-T02-05 | PASS — query500/503/504, envelope/retryable/trace/failed state | internal-error/unavailable/timeout smoke |
| AC-T02-06 | PASS — document400/404, extra query/body400 trước cả error modes | MockApiTests và 6 HTTP instance |
| AC-T02-07 | PASS — document500/503/504; malformed query/article502 với safe message, query giữ ID | HTTP smoke, guard43 tests và BackendConfigurationTests spy |
| AC-T02-08 | PASS — wrapper package74, runner37, smoke8, JAR/protected hash/PID review | final logs/JSON, baseline-hashes.json, scope-review.json |

## Phạm vi và giới hạn

Tiếp tục project Backend hiện có. T01 changes, frontend, code team khác, shared schema và .env
được bảo toàn theo hash trước implement; review status/diff không reset/stash hoặc tạo branch mới.
Scope review kiểm 147 baseline files: 133 unchanged, 14 thay đổi đúng danh sách dự kiến;
4 file mới dự kiến có mặt, 0 thay đổi ngoài phạm vi. git diff --check đạt.
Không sửa pom.xml/CORS/common error handler/DTO/store cho T02.
Q3 giữ 406 là hành vi hiện có; CORS không bắt buộc JSON403. Mock là dữ liệu cấu trúc,
không phải luật thật/GT; không nghiệm thu UI/T03/T04, DB/auth/streaming/timeout HTTP/upstream thật.
Scenario timeout là fixture lỗi504, không đo thời gian hay đặt SLA mới.
