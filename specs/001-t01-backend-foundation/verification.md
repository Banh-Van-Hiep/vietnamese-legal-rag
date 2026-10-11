# T01 — Kết quả kiểm chứng và bàn giao nền tảng Backend

**Nhóm / phụ trách:** Team 3 / Tuấn. **Task:** T01.
**Kết quả:** 23/23 task, 8/8 AC đã kiểm chứng local ngày 09/10/2026; chưa thay nghiệm thu nhóm.
**Yêu cầu:** [spec.md](spec.md). **Tái hiện kiểm tra:** [quickstart.md](quickstart.md).
**Nguồn API:** [Team 3 v1.2](../../docs/team3_fullstack/team3.md); phạm vi từ
[kế hoạch tuần 2](../../docs/team3_fullstack/team3-week2-spec.md).

## Bàn giao cho thành viên và AI khác

- Backend tiếp tục Spring Boot/Maven/Java25, profile mock không cần AI hoặc DB.
- Cấu hình Q2 theo từng key; CORS theo danh sách origin; lỗi HTTP/JSON/trace đã kiểm tra.
  RuntimeException sau accept giữ conversation ID, lưu failed và trả thông báo an toàn.
- Không đổi public schema, triển khai persistence, HTTP AiClient hoặc UI trong T01.
  T02 kế thừa nền này; kết quả regression T02 nằm ở [verification T02](../002-t02-mock-api/verification.md).
- Log gốc nằm dưới team3_fullstack/backend/target/t01/ được ignore, chỉ có trên máy kiểm chứng.
  Thành viên khác dùng quickstart để tự chạy; không coi báo cáo hoặc class tồn tại là bằng chứng mới.

| Mốc | Commit / nguồn |
| --- | --- |
| Lúc kiểm chứng | bb1bb26017d2c90578635a29ad625e502dee09b6 + working tree chưa commit, như log gốc |
| Bàn giao code | 594e24a (nền/config), d6d1055 (test T01 và guard T02 cùng file) |
| Bàn giao tài liệu | d15aa51 (specs), 530710e (báo cáo trước khi chuyển về specs/) |

Commit bàn giao có thêm phần T02; không gán kết quả 25 test T01 cho một lần chạy trên commit
cuối. Việc tổ chức lại tài liệu không chạy lại build/test hoặc thay trạng thái phê duyệt.
Các phần dưới giữ riêng lịch sử 07/10 và kiểm chứng spec 09/10.

## 1. Phạm vi và kết quả lịch sử ngày 07/10/2026

T01 đối chiếu code/contract và hoàn thiện dependency, mock mode, môi trường/CORS, lỗi. Những phần đã có được giữ lại và kiểm tra; không dựng lại Backend. DTO và query/document fixture thuộc T02; UI thuộc T03, nối FE–BE thuộc T04.

| Hạng mục | Hiện trạng khi bắt đầu | Kết quả T01 |
| --- | --- | --- |
| Runtime/dependency | Spring Boot 4.1.1, Java 25, Maven Wrapper 3.9.16; Web MVC, Validation, JPA, PostgreSQL driver và test starter | Giữ phiên bản/dependency hiện có vì đủ cho T01; điền name/description của project; package đạt |
| Mock mode | Profile mặc định `mock`; MockAiClient; tắt datasource/JPA trong profile mock | Kiểm tra ứng dụng có đúng một AiClient là MockAiClient và không tạo DataSource; script báo rõ chỉ hỗ trợ profile mock |
| `.env` | Script đọc file local và khôi phục biến môi trường khi kết thúc | Thêm `-EnvFile`, `-Port`, `-AllowedOrigins`; ghi thứ tự ưu tiên và cách chạy bằng biến môi trường |
| CORS | Danh sách origin, preflight, expose tracing/Location | Kiểm tra origin cấu hình được; cấu hình trống, wildcard hoặc URL có path bị từ chối khi khởi động; origin ngoài danh sách không được cấp CORS |
| Lỗi | ApiException, error envelope, GlobalExceptionHandler và tracing đã có | Đặt Content-Type JSON cho lỗi; kiểm tra HTTP 500/503/504, retryable, header và không lộ chi tiết lỗi trong response |

Các file triển khai mới/sửa trong T01: `backend/pom.xml`, `backend/.env.example`, `backend/run-local.ps1`, `backend/src/main/java/com/legalai/backend/common/config/CorsConfig.java`, `backend/src/main/java/com/legalai/backend/common/exception/GlobalExceptionHandler.java` và `backend/src/test/java/com/legalai/backend/BackendConfigurationTests.java`. File này ghi bằng chứng triển khai lịch sử; spec tuần 2 có liên kết đến báo cáo. Tồn tại code hoặc kết quả PASS cũ không tự xác nhận yêu cầu của spec T01 riêng đã được nghiệm thu.

## 2. Contract đã đối chiếu

Nguồn trên nhánh hiện tại đã đối chiếu; ngày 2026-10-09 đính chính vai trò tài liệu theo
xác nhận của Tuấn. Tại thời điểm kiểm chứng, nội dung working tree chưa commit không được gán toàn bộ cho commit nền; commit bàn giao hiện được ghi ở bảng trên.

| Nguồn | Nội dung / kết luận |
| --- | --- |
| [`contracts/README.md`](../../contracts/README.md) | `contracts/` chỉ có README; dẫn tới tài liệu và schema Team 2, không có JSON Schema trong thư mục. Nhãn proposal của tài liệu được dẫn không phủ nhận tài liệu Team 3 đã thống nhất |
| [`docs/team3_fullstack/team3.md`](../../docs/team3_fullstack/team3.md) | Tài liệu gốc v1.2 đã được Team 3 thống nhất theo Tuấn; căn cứ API, luồng, kiến trúc; mục 1.10 quy định envelope/mã/HTTP/retryable |
| [Spec tuần 2](../../docs/team3_fullstack/team3-week2-spec.md) | Xác định phạm vi T01; không thay thế tài liệu gốc cho API/luồng/kiến trúc |
| [`request.schema.json`](../../docs/team2_rag/schemas/request.schema.json) | Chỉ question, maxLength=10000, additionalProperties=false; khác Team 3 mục 1.6 yêu cầu client_request_id UUID v4, conversation_id tùy chọn/null và question 1–2000 code point sau trim |
| [`rag_response.schema.json`](../../docs/team2_rag/schemas/rag_response.schema.json) | Chỉ answer/citations, additionalProperties=false; thiếu status nội bộ theo Team 3 mục 1.9. Schema được dẫn cho public query nhưng không mô tả ID/thời gian do Backend bổ sung ở mục 1.6 |
| [`citation.schema.json`](../../docs/team2_rag/schemas/citation.schema.json) | Dùng claim/chunk_id/document/article/clause/source; khác 9 field tại Team 3 mục 1.7, thiếu citation_id/document_id/article_id/document_title/point/source_url và ràng buộc URL HTTPS |
| [`error_response.schema.json`](../../docs/team2_rag/schemas/error_response.schema.json) | Envelope code/message/retryable khớp; không quy định bảng HTTP/public code/retryable theo từng lỗi. Ví dụ PROVIDER_TIMEOUT khác mã public UPSTREAM_TIMEOUT của Team 3 mục 1.10 |
| History, health, article và [`retrieval_output.schema.json`](../../docs/team2_rag/schemas/retrieval_output.schema.json) | Schema được dẫn chưa biểu diễn history/health/article theo mục 1.8/1.9; candidate retrieval dùng 7 field, khác 12 field tại mục 1.9.1, thiếu các ID/version/metadata/order liên quan |

**Căn cứ của T01:** áp dụng health, header và lỗi theo `team3.md` trong phạm vi spec tuần 2.
Error envelope và HTTP/public code lấy từ yêu cầu Team 3 đã thống nhất, không lấy sự hiện hữu
của code hoặc báo cáo Codex để quyết định phê duyệt. Không sửa request/response/citation hoặc
schema dùng chung trong lượt đính chính này.

**Khác biệt cần phối hợp đồng bộ:** các schema/tài liệu do `contracts/README.md` dẫn tới chưa
biểu diễn đầy đủ yêu cầu Team 3 nêu trên. Ghi nhận để Team 1/Team 2/Team 3 phối hợp ở T02 hoặc
bước tích hợp liên quan; không yêu cầu phê duyệt lại tài liệu gốc Team 3 để tiếp tục T01.
Ngày 2026-10-09, Tuấn đã quyết định Q2: tham số chạy > biến terminal > `.env` > mặc định;
ở thời điểm clarify/plan runner cần sửa; kết quả triển khai đã đạt được ghi ở mục 6. Việc triển khai và kiểm chứng mới theo [spec T01](spec.md) được ghi ở mục 6, tách khỏi kết quả lịch sử.
Q3 cũng đã chốt: nghiệm thu origin được phép/ngoài danh sách theo AC-02, không bắt buộc
body JSON 403. 406/NOT_ACCEPTABLE là hành vi hiện có, không phải contract/tiêu chí nghiệm
thu T01 và không bị xóa/đổi xử lý vì lý do đó. Các kết quả lịch sử không chứng minh việc
triển khai các quyết định mới đã hoàn thành.

## 3. Hướng dẫn tái hiện

Cách chạy, biến môi trường, Q2 và ma trận kiểm tra được tập trung trong [quickstart.md](quickstart.md).
Báo cáo này ghi lệnh đã thực hiện và kết quả; không duy trì thêm một bản hướng dẫn chạy.

## 4. Bằng chứng lịch sử ngày 07/10/2026

Lệnh đã chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run-local.ps1 -Task package
```

**Kết quả:** BUILD SUCCESS, **24 test, 0 failure, 0 error, 0 skipped**; tạo JAR trong `backend/target/`. Log local nằm tại `backend/target/t01/package.log`; báo cáo test tại `backend/target/surefire-reports/`. Những output này được Git bỏ qua.

Kiểm tra chạy thật dùng file cấu hình riêng trong target, không sửa `.env` của người dùng. File đó đặt port 18081 và origin localhost:55172; lệnh chạy ghi đè bằng `-Port 59383 -AllowedOrigins http://127.0.0.1:55173`. Khi kiểm tra xong đã dừng đúng tiến trình kiểm tra.

| Kiểm tra | Expected | Actual | Kết quả |
| --- | --- | --- | --- |
| Build/mock không có dịch vụ AI/API key/DB | Package được; không có DataSource, AiClient là mock | BUILD SUCCESS; assertions đạt | PASS |
| Health tại port được ghi đè | HTTP 200, status=up tại port 59383 | status=up | PASS |
| Preflight từ origin được ghi đè | HTTP 200 và Allow-Origin đúng 127.0.0.1:55173 | 200, đúng origin | PASS |
| Origin cũ trong file env | Không được cấp CORS | HTTP 403, không có Allow-Origin | PASS |
| Mock mode lấy từ EnvFile | insufficient_context và citations=[] | Đúng kết quả cấu hình | PASS |
| Headers trên lỗi từ origin cho phép | X-Request-ID, X-Conversation-ID; expose hai header và Location | Test HTTP đạt | PASS |
| Lỗi hệ thống | 500/503/504 với error envelope; không có answer/status; không lộ chi tiết provider | Test HTTP đạt | PASS |
| Endpoint probe phục vụ test | Không tồn tại khi chạy ứng dụng thật | HTTP 404 | PASS |

Kết quả smoke được ghi local tại `backend/target/t01/smoke-result.json`. Các route phát sinh lỗi 500/503/504 chỉ tồn tại trong cấu hình test, không thêm endpoint/scenario vào ứng dụng thật. Scenario lỗi hệ thống cho demo query/document thuộc T02.

Liên hệ tiêu chí tuần 2: phần Backend của AC-01 và cấu hình/CORS phía Backend của AC-02 đã kiểm tra. T01 kiểm tra error envelope hỗ trợ AC-03. Chưa đánh dấu toàn bộ AC-01/AC-02/AC-03 hoặc tuần 2 hoàn thành; kiểm tra FE/build, fixture theo contract cuối và UI tích hợp cần các task tiếp theo.

## 5. Giới hạn

Backend vẫn là mock, dùng bộ nhớ tạm và mất dữ liệu khi restart. Chưa có PostgreSQL persistence, gọi Team 2 thật hoặc AI hiểu history. T01 không thay Frontend, DTO hay fixture query/document, không triển khai T02–T06. Khác biệt tài liệu/schema liên team cần được đồng bộ theo tài liệu gốc Team 3; runtime/dependency giữ nguyên theo repository. Vòng đính chính nguồn/clarify/plan ngày 2026-10-09 chỉ sửa tài liệu; kết quả chạy mới trong vòng implement cùng ngày được ghi riêng dưới đây.

## 6. Kiểm chứng spec T01 riêng ngày 09/10/2026

Đã thực hiện T001–T023 theo thứ tự phụ thuộc trên Backend hiện có. Q1–Q3 giữ nguyên:
`team3.md` v1.2 là nguồn đã thống nhất; ưu tiên explicit > terminal > file > defaults;
CORS không bắt body JSON 403 và giữ nguyên handler 406 ngoài tiêu chí T01.
Các trạng thái PASS của lần kiểm chứng dưới đây là **kiểm chứng local trong phạm vi T01**, không tự xác nhận
UI, Team 2 thật, T02–T06 hoặc nghiệm thu toàn tuần 2.

**Môi trường và working tree lúc kiểm chứng:** nhánh `feature/team3/tuan`, HEAD
`bb1bb26017d2c90578635a29ad625e502dee09b6`; working tree có thay đổi chưa commit từ trước.
Windows 11 amd64, Windows PowerShell 5.1.26100.9444, JDK 25.0.1 tại `D:\Java\jdk-25`,
Maven Wrapper 3.9.16, Spring Boot 4.1.1 theo POM. Không thêm dependency, không đổi POM.
Baseline gồm status/diff/hash tại `backend/target/t01/baseline.txt` và
`baseline-hashes.json`; không gán toàn bộ nội dung working tree cho HEAD.

**Thay đổi trong vòng implement:**

- `backend/run-local.ps1`: parse env thành dữ liệu, chọn nguồn Q2 theo từng key, chặn
  winner rỗng, giữ validation/finally; xử lý warning stderr theo exit code Maven trên PS 5.1.
- `backend/.env.example`: cập nhật chú thích ưu tiên, không đổi key/default hoặc .env thật.
- `backend/src/test/powershell/RunLocalConfigurationTests.ps1`: harness độc lập dùng JDK 25,
  Maven stub và fixture tạm; không thêm test framework.
- `BackendConfigurationTests.java`, `MockApiTests.java`, `MockQueryServiceTests.java`:
  assertion preflight method/header, Location với Origin, retryable=false cho lỗi đầu vào;
  RuntimeException sau tiếp nhận được kiểm tra ở service và HTTP với spy MockAiClient chỉ
  trong test. Không thêm endpoint/field/scenario public.
- Báo cáo này, trạng thái thực hiện trong spec/plan và checkbox/evidence trong tasks. POM, CorsConfig, handler 406 và các thay đổi
  đã có trước được bảo toàn; không sửa Frontend, Team 1/2 hoặc contract dùng chung.

**Lệnh và kết quả thực tế:** lệnh bên dưới chạy từ gốc repository với JDK 25 đã đặt trong
terminal kiểm tra. Package dùng fixture build riêng dưới target và origin mặc định có kiểm soát.

```powershell
.\team3_fullstack\backend\src\test\powershell\RunLocalConfigurationTests.ps1 -JavaHome 'D:\Java\jdk-25'
.\team3_fullstack\backend\run-local.ps1 -Task package -EnvFile 'D:\CVDHD\vietnamese-legal-rag\team3_fullstack\backend\target\t01\build.env'
```

Focused CORS chạy wrapper `-B -ntp -Dtest=BackendConfigurationTests,MockApiTests test`:
**20 test đạt**. Focused lỗi chạy wrapper
`-B -ntp -Dtest=MockApiTests,BackendConfigurationTests,MockQueryServiceTests test`:
**23 test đạt**. Final package: **BUILD SUCCESS, 25 test, 0 failure/error/skipped**;
gồm BackendApplicationTests 1, BackendConfigurationTests 5, MockApiTests 16,
MockQueryServiceTests 2, InsufficientContextApiTests 1. Harness cuối: **31/31 ca PASS**,
bao gồm env/location restoration sau thành công và lỗi. Không dùng skipTests.

Smoke theo [quickstart](quickstart.md) chạy qua runner
và Maven Wrapper `spring-boot:run`; helper local `backend/target/t01/SmokeValidation.ps1`
ghi lệnh/PID và dừng đúng cây process do nó tạo, không kill theo tên java/node.
Cổng đã kiểm tra trống trước khi chạy; các server kiểm tra đã được dừng.

| AC | Expected | Actual / bằng chứng mới | Kết quả |
| --- | --- | --- | --- |
| AC-T01-01 | Wrapper package được, mock không cần AI/key/DB, health 200/up | Final package 25/25; test no DataSource/chỉ MockAiClient đạt; health trên cả ba bộ smoke đạt. `final-validation.log`, `final-surefire/`, `config-smoke.log` | PASS |
| AC-T01-02 | Thứ tự Q2, fallback, hai bộ cấu hình và default/profile thật; winner sai không bị che | Harness 31/31. A: file 18081/origin 55173/answered, terminal thắng → 18082/localhost:55174/insufficient_context. B: arguments thắng → 18083/localhost:55175, terminal status vắng → answered từ file. Default: fixture chỉ comment, bỏ cả SPRING_PROFILES_ACTIVE/port/origin/status ở process, không ép profile; log default mock, port 8080, cả localhost/127.0.0.1:5173, answered. `final-runner-tests.log`, `config-smoke-results.json`, `config-default-out.log` | PASS |
| AC-T01-03 | Runtime/config sai, Maven nonzero và port bận phải báo lỗi, không readiness giả | Harness bắt JDK 24 winner, missing/bad file/profile/blank/config và Maven exit 7. Spring thực: invalid port/origin/status và occupied port đều exit 1, có lỗi đúng nguyên nhân và không log Started BackendApplication; server smoke đầu vẫn health 200. `runner-tests.log`, `config-smoke.log`, các `invalid-*-out/err.log`, `occupied-port-out/err.log` | PASS |
| AC-T01-04 | Origin cho phép có preflight/actual/error CORS và header phù hợp | Assertion POST/Content-Type, create Location đúng tài nguyên, X-Request-ID/X-Conversation-ID/expose trên success/error đạt. `cors-tests.log`, `error-tests.log`, `final-surefire/` | PASS |
| AC-T01-05 | Outside origin không Allow-Origin trên actual/preflight; không bắt JSON 403 | Java tests và smoke GET/OPTIONS ngoài danh sách đạt; không assertion body JSON 403. `cors-tests.log`, `config-smoke.log` | PASS |
| AC-T01-06 | 400/404/405+Allow/413/415 đúng code/envelope/retryable=false, không answer/status | Assertions status/code/JSON/message/trace và retryable=false đạt, 413 giữ giới hạn 16 KiB. `error-tests.log`, `final-surefire/TEST-com.legalai.backend.MockApiTests.xml` | PASS |
| AC-T01-07 | 500/503/504 false/true/true, response an toàn; header sau tiếp nhận và probe vắng trên app thật | Probe các nhóm lỗi đạt; RuntimeException sau tiếp nhận trả 500/INTERNAL_ERROR false, X-Conversation-ID đúng hội thoại, lượt failed và không lộ sentinel/provider/stack trong response. JAR cuối không chứa test/probe; app thực GET probe 404/NOT_FOUND. `error-tests.log`, `probe-isolation.log`, `final-surefire/`, `config-smoke.log` | PASS |
| AC-T01-08 | Hướng dẫn, nguồn, runtime/working tree, lệnh, expected/actual, log và giới hạn | Quickstart và báo cáo mục 6 cùng tasks/evidence được đối chiếu; git diff --check đạt; kiểm tra hash/scope giữ thay đổi có sẵn. `baseline.txt`, `environment.txt`, `verification.md`, `scope-review.json` | PASS |

Mọi log/output nêu trong bảng nằm tại `team3_fullstack/backend/target/t01/`, được Git bỏ qua.
Surefire hiện tại tại `backend/target/surefire-reports/`; bản lưu cuối tại `target/t01/final-surefire/`.
Baseline 07/10 ở package.log/smoke-result.json được giữ riêng, không dùng thay kết quả mới.
Ma trận config-smoke-results.json có 8 record PASS (default kiểm tra hai origin);
4 ca khởi động lỗi đều có exit code 1. Fixture và command/PID chi tiết nằm trong log/helper.

**Các lần kiểm tra chưa đạt trước khi sửa:** runner cũ fail 15/29 ca Q2/blank/winner,
ghi ở runner-before-fix.log. Lần package đầu bị PS 5.1 coi warning Mockito stderr là lỗi;
runner đã sửa và có regression warning-exit-zero/Maven-nonzero. Helper smoke ban đầu có
lỗi cách gửi GET và chưa giữ handle nên thiếu exit code; đã sửa helper và chạy lại đầy đủ.
File config-smoke-incomplete-exitcodes.json đánh dấu ca thiếu exit là INCOMPLETE_EXIT_CODE,
không dùng nghiệm thu. Chỉ log/báo cáo PASS cuối được dùng ở bảng trên.

**Giới hạn bàn giao:** mock memory mất sau restart; không có AI/history nội bộ thật,
DB persistence, UI hoặc scenario lỗi public cho demo T02. Không còn bước T01 chưa chạy
trong phạm vi tasks. Checklist chất lượng spec vẫn 14/16: hai mục giữ chi tiết API/kiến trúc
là ngoại lệ đã ghi trong plan; không sửa marker checklist trong implement. Các kết quả local
vẫn cần nhóm review theo workflow; vòng kiểm chứng gốc không tự commit/push/merge; Tuấn đã tạo các commit bàn giao ở bảng trên. Chưa xác nhận PR/merge hoặc nghiệm thu nhóm.
