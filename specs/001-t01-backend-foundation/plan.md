# Implementation Plan: Task01 — Nền tảng Backend/API Team 3

Ghi chú tổ chức tài liệu 09/10/2026: đường dẫn báo cáo trong tài liệu này là vị trí bàn giao
hiện tại (verification.md trong spec); baseline/log gốc vẫn ghi đường dẫn docs/ trước khi chuyển.
Snapshot lúc plan và checkbox/evidence đã kiểm chứng được giữ nguyên; không chạy lại test khi dọn tài liệu.


**Branch**: `feature/team3/tuan` | **Date**: 2026-10-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification `specs/001-t01-backend-foundation/spec.md`, Q1–Q3 đã làm rõ.

**Status**: Phase 0/1 thiết kế đã lập; 23 nhiệm vụ trong [tasks.md](tasks.md) đã thực hiện và
kiểm chứng local ngày 2026-10-09, xem [báo cáo mục 6](verification.md#6-kiểm-chứng-spec-t01-riêng-ngày-09102026). Kết quả chờ nhóm review, không xác nhận toàn tuần 2.
Kế hoạch giữ Q1–Q3, kiểm tra fallback/restoration và ràng buộc không thay 406.
Hai task nháp Q2 đã được mở rộng và ánh xạ trong danh sách tasks hiện tại.

## Summary

Tiếp tục trên Backend hiện có, giữ Java/Spring Boot/Maven, package theo tính năng,
AiClient/mock store và API theo [tài liệu gốc Team 3](../../docs/team3_fullstack/team3.md).
Spec tuần 2 giới hạn T01 vào dependency/mock/môi trường/CORS/lỗi; không đưa T02–T06 vào kế hoạch này.

Hiện trạng lúc lập kế hoạch: runner để `.env` ghi đè terminal, trái Q2. Thiết kế chọn nguồn
theo từng key thành **explicit argument > process environment > `.env` > mặc định Spring**,
giữ báo lỗi giá trị sai và finally khôi phục env/location. Bổ sung kiểm tra runner và các assertion
HTTP còn thiếu; không dựng lại Backend hoặc đổi dependency để làm skeleton.

Q1: dùng team3.md cho API/luồng/kiến trúc; báo cáo Codex không quyết định phê duyệt.
Q3: CORS nghiệm thu hai nhóm origin theo AC-02, không bắt JSON 403; giữ 406/NOT_ACCEPTABLE
như hành vi hiện tại, ngoài contract/tiêu chí T01. Plan không có task xóa/đổi handler 406.

## Technical Context

**Language/Version**: Java 25 theo POM; runner PowerShell, host được đọc là Windows PowerShell
5.1.26100.9444. Không yêu cầu đổi lên PowerShell 7 hoặc chọn lại JDK.

**Primary Dependencies**: Spring Boot 4.1.1; Web MVC, Validation, Spring Data JPA, PostgreSQL
driver và các test starter đang có; Maven Wrapper 3.9.16. Không cần thêm dependency T01.

**Storage**: mock ConversationService dùng bộ nhớ tạm, mất sau restart. JPA/driver là nền cho
persistence sau; application-mock.properties loại datasource/JPA. Không tạo entity/migration/DB.

**Testing**: giữ JUnit/SpringBootTest và Java HttpClient hiện có. Bổ sung standalone PowerShell
harness không dependency mới, Maven stub trong dữ liệu tạm và smoke Spring thực tế riêng.

**Target Platform**: local Windows/PowerShell của nhóm, HTTP dev origins cấu hình được;
không mở rộng Linux runner, hosting hoặc container deployment.

**Project Type**: Backend web service hiện có cùng CLI hỗ trợ local; Frontend chỉ là client
liên quan đến origin/header, không thuộc danh sách file được sửa.

**Performance Goals**: không có SLA/throughput/coverage target mới cho T01; đo đúng các hành vi
trong SC-001–005 và AC-T01-01–08, không suy đoán hiệu năng production.

**Constraints**: giữ API, kiến trúc, Git diff có sẵn; Q2 thay precedence local; Q3 giữ 406.
Mock không cần AI/key thật, không gọi Team 1/2 hoặc thêm endpoint lỗi public.

**Scale/Scope**: một Backend local với cấu hình port/origin/mock mode và kiểm tra lỗi;
không đầy đủ history/concurrency/persistence, UI, Ground Truth hoặc deployment.

## Constitution Check

Gate đánh giá thiết kế, không phải kết quả build/test ứng dụng. Trước Phase 0 và sau Phase 1:

| Nguyên tắc | Kiểm tra thiết kế | Trước / sau |
| --- | --- | --- |
| Tương thích API | Health/header/lỗi kế thừa team3.md; không thay DTO/schema/endpoint; 406 giữ nguyên | PASS / PASS |
| Ranh giới team | Chỉ Backend Team 3 và tài liệu feature; không sửa Frontend, Team 1/2 hoặc contract chung | PASS / PASS |
| Tái sử dụng kiến trúc | Project/POM/package/AiClient hiện có; không thêm DB/framework/test stack | PASS / PASS |
| Kiểm chứng | Runner harness + HTTP tests + smoke + bảng AC; không tự dùng PASS lịch sử làm nghiệm thu mới | PASS / PASS |

Constitution 1.0.0 còn TODO ngày phê chuẩn; plan giữ các nguyên tắc đã xác định. Q1 của Tuấn
đã làm rõ vai trò team3.md, không tự diễn giải nhãn proposal cũ thành phủ nhận yêu cầu Team 3.
Checklist spec hiện 14/16: hai mục tránh tuyệt đối chi tiết API/kiến trúc là ngoại lệ đã ghi
do người dùng yêu cầu truy vết nguồn; không có câu hỏi chức năng mở hoặc vi phạm gate bị che.

## Project Structure

### Documentation (this feature)

```text
specs/001-t01-backend-foundation/
├── spec.md                       # Đã làm rõ, giữ nguyên trong plan
├── plan.md                       # Kế hoạch kỹ thuật Phase 0/1 hiện tại
├── research.md                   # Phase 0: quyết định, lý do, phương án loại
├── data-model.md                 # Phase 1: cấu hình/truy vết/bằng chứng, không model DB mới
├── quickstart.md                 # Phase 1: hướng dẫn validation sau triển khai
├── contracts/README.md           # Tham chiếu interface kế thừa, không contract mới
├── checklists/requirements.md    # Giữ trạng thái review spec
└── tasks.md                      # 23 task theo story/phụ thuộc, đã kiểm chứng local
```

### Source Code (repository root)

```text
team3_fullstack/backend/
├── pom.xml
├── .mvn/wrapper/maven-wrapper.properties
├── mvnw.cmd
├── .env.example
├── run-local.ps1
└── src/
    ├── main/
    │   ├── java/com/legalai/backend/{chat,conversation,document,ai,common}/
    │   └── resources/application*.properties
    └── test/
        ├── java/com/legalai/backend/              # Tests hiện có
        └── powershell/RunLocalConfigurationTests.ps1  # Dự kiến bổ sung, chưa tạo
docs/team3_fullstack/team3.md
specs/001-t01-backend-foundation/verification.md
team3_fullstack/frontend/                         # Không sửa
```

**Structure Decision**: dùng đường dẫn thực tế trên working tree, không chuyển code vào
`src/team3_fullstack/` chỉ vì README tổng còn ghi cấu trúc khác. Đã đọc git status/diff;
không phục hồi `backend/README.md` người dùng đã xóa/chuyển và không overwrite tài liệu gốc.

### Snapshot lúc lập plan: hiện trạng, khoảng trống và file dự kiến tác động

| Thành phần/file | Đã có qua đọc code | Cần sửa/bổ sung khi triển khai |
| --- | --- | --- |
| `backend/pom.xml`, wrapper | Đủ web/validation/test; runtime có cấu hình | Giữ nguyên dependency/runtime; chỉ build/kiểm tra, không upgrade |
| `backend/run-local.ps1` | Nạp .env, Port/AllowedOrigins/EnvFile, kiểm tra JDK/mock, gọi Maven, finally | Sửa chọn nguồn Q2, phân biệt supplied/invalid, giữ restoration và mã lỗi; phạm vi sửa chính |
| `backend/.env.example` | File mẫu và chú thích precedence cũ | Sửa chú thích theo Q2, giữ default/key hiện có; không sửa .env thật |
| `application*.properties` | Port/origin/status/default mock, loại DB/JPA | Giữ nguồn defaults/exclusions; không cần thay giá trị hoặc thêm profile thật |
| `common/config`, `common/web`, `common/exception` | CORS/preflight/header, trace, validation/envelope | Tái sử dụng và kiểm tra; không dự kiến đổi API/406/JSON CORS hoặc rewrite handler |
| `ai/MockAiClient`, `chat`, `document`, `conversation` | Mock query/article, history store trong bộ nhớ | Dùng fixture hiện có để quan sát config/header; không hoàn thiện DTO/fixture T02, HTTP AI hay entity |
| `src/test/powershell/RunLocalConfigurationTests.ps1` | Chưa có harness runner | Bổ sung isolated env/file/Maven stub, precedence/fallback/invalid/restoration; không framework mới |
| `src/test/java/.../BackendConfigurationTests.java`, `MockApiTests.java` | Mock, health, CORS, lỗi đã có nhiều ca | Bổ sung assertion Allow-Methods/Allow-Headers, Location actual + Origin, retryable=false ở đầu vào; test HTTP query trả 500 sau tiếp nhận bằng AI lỗi cô lập trong test, giữ test-only probe hiện có |
| `src/test/java/.../MockQueryServiceTests.java` | Có test service tiếp nhận lượt rồi lỗi 503/504 | Mở rộng test hiện có cho RuntimeException → 500/INTERNAL_ERROR, retryable=false, conversation ID đúng lượt và message an toàn; không sửa ChatService hoặc thêm scenario public |
| `specs/001-t01-backend-foundation/verification.md` | Báo cáo lịch sử và đính chính nguồn | Sau triển khai cập nhật hướng dẫn/bằng chứng mới, giữ ngày/giới hạn kết quả cũ; không đổi phê duyệt |

Các file ngoài bảng, Frontend, Team 1/2, `.specify`/template và contract chung không phải target.
Nếu triển khai phát hiện cần thay behavior API ngoài bảng, ghi lại thay vì tự mở rộng T01.

### Thiết kế sửa runner

1. Snapshot env process và working directory trước mọi thay đổi; chỉ xử lý key đã được hỗ trợ.
2. Parse file env thành dữ liệu KEY/value, giữ parser quoting/whitelist và lỗi file hiện có;
   không SetEnvironmentVariable cho từng dòng trong bước parse.
3. Với từng key chọn explicit argument nếu được truyền, rồi process snapshot, rồi file,
   rồi để Spring default khi có. Dùng trạng thái supplied, không coi giá trị trống/sai là vắng.
4. Validate giá trị đã chọn bằng kiểm tra hiện có, chặn giá trị rỗng trước khi gán env làm
   mất key và fallback âm thầm. Không copy default Spring sang runner hoặc thêm key mới.
5. Gọi goal Maven hiện có; nonzero/khởi động lỗi không thành readiness. Finally khôi phục
   key tồn tại/vắng và location cả khi parse/runtime/Maven lỗi; không sửa file cấu hình người dùng.

JAVA_HOME phải là JDK 25 theo nguồn thắng; terminal JDK 24 sẽ thắng file JDK 25 và báo lỗi,
không âm thầm lấy JDK thấp-priority. Hướng dẫn phải nêu điều này. Config mặc định chỉ áp dụng
cho key có default thật; không hứa chạy sans JAVA_HOME bằng PATH.

### Mock, interface và dependency liên team

Giữ profile mock mặc định, memory store, answered/insufficient_context để kiểm tra mode.
Health không gọi AI. Lỗi 500/503/504 kiểm tra qua probe hiện có trong src/test; probe không
xuất hiện khi chạy ứng dụng thật. Bổ sung riêng nhánh RuntimeException sau tiếp nhận lượt:
test service trong MockQueryServiceTests và test HTTP trên POST /api/v1/query hiện có trong
BackendConfigurationTests, với AI lỗi được cô lập chỉ trong test. Xác nhận 500/INTERNAL_ERROR,
retryable=false, conversation ID gắn đúng lượt đã tiếp nhận, response header và message an toàn;
không dùng probe 500 chưa tiếp nhận lượt làm bằng chứng cho nhánh này. Giữ các ca mock/probe
hiện có độc lập; không thêm endpoint, field chọn scenario hoặc fixture lỗi public của T02.

Interface T01 tại [contracts/README.md](contracts/README.md) trích team3.md. CORS/header được
kiểm tra trên endpoint có sẵn. 403 không cần JSON; 406 không là contract/nghiệm thu và giữ nguyên.
Team 2 chỉ cần phối hợp đồng bộ tài liệu/schema cho bước tích hợp liên quan; service thật không
là dependency chạy T01. Team 1 không có dependency runtime T01; Frontend chỉ cung cấp origin/header.

### Kiểm chứng từng tiêu chí nghiệm thu

| AC | Cách kiểm tra dự kiến | Khoảng trống/bằng chứng cần ghi |
| --- | --- | --- |
| AC-T01-01 | Wrapper package + mock startup + health; test MockAiClient và không DataSource | Build/run mới, JDK/commit/working tree; chưa chạy ở plan |
| AC-T01-02 | Harness mọi mức ưu tiên/fallback/invalid; smoke hai bộ port/origin/status và ca default không ép profile | Bỏ SPRING_PROFILES_ACTIVE ở terminal lẫn fixture, không truyền profile/port/origin override; giữ JAVA_HOME hợp lệ, log xác nhận default mock; stub không thay proof Spring bind |
| AC-T01-03 | Harness file/runtime/profile/config lỗi, Maven nonzero/restoration; smoke port bận | Không nhận health từ server cũ; xác định PID/port tiến trình mới, exit/lỗi thật |
| AC-T01-04 | JUnit preflight/actual/response lỗi cho origin cho phép | Thêm assertion method/header và Location actual nếu thiếu; không sửa UI |
| AC-T01-05 | Test preflight và actual origin ngoài danh sách | Không Allow-Origin; không bắt body JSON 403 |
| AC-T01-06 | Test 400/404/405+Allow/413/415, JSON envelope/trace/retryable | Assert false cho lỗi đầu vào; không redesign DTO và không đưa 406 vào gate |
| AC-T01-07 | Probe hiện có 500/503/504; bổ sung test service và HTTP RuntimeException → 500 sau tiếp nhận; smoke probe absent | false/true/true; riêng 500 sau tiếp nhận phải có conversation ID đúng lượt, header HTTP tương ứng và message an toàn, không answer/status/secret/provider detail |
| AC-T01-08 | Cập nhật báo cáo theo kết quả mới, log/command/expected/actual/giới hạn | Mỗi AC trạng thái thật; không dùng 24 test PASS cũ làm nghiệm thu yêu cầu mới |

Lệnh, dữ liệu mẫu, điều kiện port và cleanup trong [quickstart.md](quickstart.md).
Chạy harness trước, rồi package (gồm test Java), rồi smoke. Không đặt coverage/SLA hoặc số test
bắt buộc mới. Ca default Spring phải bỏ cả SPRING_PROFILES_ACTIVE, SERVER_PORT,
CORS_ALLOWED_ORIGINS và MOCK_ANSWER_STATUS ở terminal lẫn fixture, không truyền tham số
ép profile/port/origin; giữ JAVA_HOME JDK 25 hợp lệ. Log của tiến trình mới phải xác nhận
không ép active profile và default profile thực tế là mock; health một mình không đủ proof profile.
Nếu port default bị chiếm thì ghi chưa kiểm tra thành công, không dùng health server cũ,
Maven stub hoặc đọc properties làm proof runtime.

### Phase 0/1 và bàn giao

- Phase 0: [research.md](research.md) đã giải quyết quyết định kỹ thuật bằng nguồn local và Q1–Q3;
  rà soát độc lập chỉ đọc xác nhận test runner thiếu và ma trận AC, không chạy test/app.
- Phase 1: [data-model.md](data-model.md), [interface references](contracts/README.md),
  [quickstart.md](quickstart.md) mô tả thiết kế/validation; post-design constitution gates PASS.
- Danh sách [tasks.md](tasks.md) đã sinh và cập nhật thành 23 nhiệm vụ, giữ ý định hai task
  nháp Q2 và bổ sung kiểm chứng U1/C1. Vòng implement sau đó đã thực hiện tasks và lưu bằng
  chứng local vào báo cáo mục 6; trạng thái checkbox không dùng PASS của vòng lập tài liệu.

### Bảo toàn Git và rủi ro thực tế

Nhánh thật là `feature/team3/tuan`, HEAD `bb1bb26017d2c90578635a29ad625e502dee09b6`.
Spec Kit setup trả active feature key `001-t01-backend-foundation`; không tạo/switch nhánh.
Trước plan có 7 đường dẫn tracked dirty (gồm backend README bị xóa), nhiều tài liệu/test và
thư mục skill/spec chưa tracked; staged diff rỗng. Nội dung trong working tree không bị gán
toàn bộ cho HEAD hoặc coi là do lượt plan tạo.

Tại lượt plan chỉ ghi feature plan/research/data-model/contracts/quickstart. Hash các file
source/cấu hình/tài liệu đầu vào, spec/tasks/checklist và tracked diff được đối chiếu trước/sau.
Các thay đổi code đã có từ trước và việc chuyển tài liệu được bảo toàn. Không commit/push/merge.

Rủi ro được ghi tại vòng lập kế hoạch: runner cũ sai Q2; JAVA_HOME terminal sai sẽ làm fail sau đổi precedence;
fixture env và test property phải được cô lập; port cũ có thể tạo PASS giả; output/child process
phải được cleanup theo đúng nguồn tạo. Các rủi ro này được đưa vào harness/smoke, không tạo
auth/DB/protocol mới. Hai mục checklist style còn mở không phải hai quyết định chức năng chưa chốt.

## Complexity Tracking

Không có vi phạm constitution cần ngoại lệ kiến trúc. Harness PowerShell dùng nền hiện có,
không thêm project/service/library; các tham chiếu API giữ nguồn đã thống nhất.
