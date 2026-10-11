# Feature Specification: Task02 — API mock query/document và fixture Team 3

**Feature Branch**: feature/team3/tuan
**Nhóm / phụ trách / task**: Team 3 / Tuấn / T02.
**Feature Directory**: specs/002-t02-mock-api
**Created**: 2026-10-09
**Status**: Implemented và kiểm chứng local ngày 2026-10-09: 8/8 AC PASS, wrapper package 74 tests, runner 37 cases, HTTP matrix 8 records. Quyết định CL-T02-01/02 do Codex chọn theo ủy quyền, chờ Tuấn review; không thay nghiệm thu nhóm. Xem [báo cáo T02](verification.md).
**Input**: T02 của Tuấn từ spec tuần 2, API/luồng/kiến trúc Team 3 đã thống nhất,
nền T01 và code Backend hiện có. Giữ nhánh/diff; chưa sửa code ở bước specify.

Không tìm thấy spec T02 riêng khi quét specs; đây là thư mục T02 duy nhất.
.specify/feature.json trỏ tới thư mục này; T01 vẫn ở thư mục 001.

## Clarifications

### Session 2026-10-09

Nguồn quyền quyết định: người dùng yêu cầu tự quyết và chạy clarify → plan → tasks →
analyze → sửa → implement khi người dùng vắng. Đây là lựa chọn triển khai của Codex theo
ủy quyền, không giả định Team 3 đã phê duyệt lựa chọn mới. Xem [decisions.md](decisions.md).

- Q: Scenario được chọn thế nào mà không đổi public API? → A: CL-T02-01: cấu hình theo instance khi khởi động; query/document có lựa chọn độc lập, đổi scenario bằng config/restart, không magic question/header/endpoint. Giữ MOCK_ANSWER_STATUS tương thích khi không khai báo lựa chọn query mới; nguồn từng key theo Q2, cấu hình sai phải fail rõ.
- Q: Phạm vi lỗi document trong T02 gồm những gì? → A: CL-T02-02: document có success/400/404 và 500 INTERNAL_ERROR false, 503 SERVICE_UNAVAILABLE true, 504 UPSTREAM_TIMEOUT true cho tuple mock tồn tại; syntax sai vẫn 400, document/article vắng vẫn 404. Output sai schema/ID → 502 chỉ qua test kiểm soát, không scenario malformed public.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hai kết quả hỏi đáp mock đúng định dạng (Priority: P1)

Thành viên tích hợp gửi câu hỏi hợp lệ, nhận câu trả lời có nguồn hoặc thông báo thiếu căn cứ,
với các ID giữ đúng hội thoại. Dữ liệu mẫu được nhận diện rõ là mock.

**Why this priority**: Đây là dữ liệu đầu vào cho Chat và tích hợp T04, không cần AI thật.
**Independent Test**: Gọi query với hai trạng thái thành công, kiểm tra field/ID/citation
và câu tiếp dùng đúng hội thoại; không cần UI.

**Acceptance Scenarios**:

1. **Given** answered và request hợp lệ, **When** hỏi lần đầu bỏ/null conversation_id,
   **Then** HTTP 200, answer có marker ánh xạ citation, đủ ID hội thoại/lượt/message và thời gian.
2. **Given** insufficient_context, **When** gửi lượt mới, **Then** HTTP 200, thông báo không rỗng,
   citations=[], không marker; vẫn đủ ID/thời gian.
3. **Given** hội thoại từ lượt trước, **When** hỏi tiếp bằng ID đó và client_request_id mới,
   **Then** giữ conversation_id, có message/lượt mới; không khẳng định mock AI hiểu history.
4. **Given** chọn hội thoại mới bằng cách bỏ/null ID, **When** gửi lượt mới,
   **Then** nhận hội thoại khác; đổi scenario không đổi public schema.

### User Story 2 - Mở đúng điều luật mẫu từ citation (Priority: P1)

Thành viên tích hợp lấy document_id/article_id từ citation, gọi document API và nhận đúng
nội dung mẫu giữ xuống dòng để Viewer dùng ở bước sau.

**Why this priority**: Query/document phải dùng cùng phiên bản/ID, tránh mở sai nguồn.
**Independent Test**: Từ mỗi citation answered, gọi document và so metadata/content/source;
kiểm tra ID sai định dạng và ID hợp lệ không tồn tại.

**Acceptance Scenarios**:

1. **Given** citation answered, **When** mở đúng cặp ID, **Then** 200 ArticleResponse đủ field,
   metadata/source nhất quán, content toàn điều luật mock và giữ xuống dòng.
2. **Given** ID hợp lệ không có trong fixture, **When** gọi document, **Then** 404
   DOCUMENT_NOT_FOUND/ARTICLE_NOT_FOUND, không thay bằng phiên bản khác.
3. **Given** ID sai định dạng hoặc body/query parameter không được phép, **When** gọi document,
   **Then** 400 INVALID_REQUEST theo quy ước có sẵn.

### User Story 3 - Demo lỗi qua API chạy local (Priority: P2)

Thành viên chọn scenario rồi gửi request bình thường để quan sát lỗi qua API local,
thay vì cần probe chỉ tồn tại trong test.

**Why this priority**: T01 kiểm tra handler; T02 cần fixture lỗi để FE tích hợp T04.
**Independent Test**: Lặp scenario đã công bố, kiểm tra status/envelope/header và input sai,
không gọi AI thật hoặc yêu cầu UI đã xong.

**Acceptance Scenarios**:

1. **Given** query lỗi ngoài dự kiến/không sẵn sàng/timeout, **When** gửi input hợp lệ,
   **Then** 500 INTERNAL_ERROR false, 503 SERVICE_UNAVAILABLE true, 504 UPSTREAM_TIMEOUT true;
   chỉ error, không answer/status nghiệp vụ.
2. **Given** đang chọn lỗi hệ thống, **When** gửi input sai, **Then** vẫn nhận lỗi
   validation/status tương ứng, không bị scenario che thành lỗi hệ thống hoặc 200.
3. **Given** lượt query đã tiếp nhận, **When** scenario gây lỗi, **Then** X-Conversation-ID đúng
   hội thoại, X-Request-ID có mặt; không leak/provider/stack hoặc insufficient_context.
4. **Given** scenario được công bố, **When** làm theo hướng dẫn, **Then** lặp kết quả bằng
   request đúng schema, không thêm field/endpoint/header điều khiển vào public contract.
5. **Given** tuple document mock tồn tại và scenario lỗi đã chọn, **When** mở document,
   **Then** nhận 500/503/504 với envelope/retryable đúng; input sai hoặc tuple vắng vẫn 400/404.

### Edge Cases

- Question thiếu/null/blank/sai kiểu, vượt 2000 Unicode code point sau trim;
  client_request_id thiếu/sai UUID v4, conversation_id rỗng/sai UUID → 400.
- JSON malformed/trùng key/field lạ/trailing token/coercion bị từ chối; POST vượt
  16 KiB → 413, media type sai → 415, method sai → 405 kèm Allow.
- GET document không body/query; ID chỉ ASCII chữ/số/_/-, độ dài theo nguồn.
- answered 1–10 citation; marker liên tục theo xuất hiện đầu tiên, không citation thừa/chunk
  trùng; clause/point có key kể cả null. insufficient_context không marker/citation.
- source_url HTTPS tuyệt đối; fixture cấu trúc mock không phải nguồn Ground Truth.
- Đổi scenario không đổi ý nghĩa cặp ID/version; restart mất dữ liệu memory.
- Replay completed/failed giữ kết quả/lỗi đã lưu theo behavior hiện có; dùng client_request_id
  mới để thử scenario khác. Không thêm nhiệm vụ production concurrency.
- Config scenario sai báo rõ, không âm thầm fallback; giữ Q2.
- CORS không bắt JSON 403; giữ xử lý 406 hiện có, ngoài contract/AC theo Q3.

## Requirements *(mandatory)*

### Mục tiêu, phạm vi và ngoài phạm vi

**Mục tiêu**: Hoàn thiện DTO/fixture query-document đúng Team 3, có trạng thái thành công/lỗi,
cách chọn và bằng chứng kiểm tra lặp lại được.

**Trong T02**: BE-03; validation query, public response/Citation/ArticleResponse; fixture
answered/insufficient_context và lỗi query; nhận/trả ID câu đầu/câu tiếp/hội thoại mới
(phần Backend AC-05); document 200/400/404 và lỗi đã chốt; hướng dẫn/bằng chứng từng scenario.
Health/CORS/envelope/runtime T01 là nền tái sử dụng.

**Ngoài T02**: UI/Router/Search/Viewer T03, browser FE–BE T04, GT T05, toàn bộ bàn giao T06;
làm lại T01, Python/LLM/retrieval, auth/streaming, DB production/history nội bộ, concurrency/
transaction/pending đầy đủ. Không API Search, không thay contract liên team. History/replay
hiện có được bảo toàn và dùng kiểm tra cần thiết, không mở rộng thành nhiệm vụ persistence.

### Nguồn và quyết định kế thừa

| Nguồn | Vai trò |
| --- | --- |
| [team3.md v1.2](../../docs/team3_fullstack/team3.md), 1.1/1.6/1.7/1.8/1.10 | API/luồng/kiến trúc đã thống nhất theo Q1 và yêu cầu hiện tại |
| [Spec tuần 2 v1.2](../../docs/team3_fullstack/team3-week2-spec.md), BE-03, T02, AC-03/05/06 | Giới hạn task; phần UI không chuyển vào Backend |
| [T01](../001-t01-backend-foundation/spec.md), [plan](../001-t01-backend-foundation/plan.md), [tasks](../001-t01-backend-foundation/tasks.md) | Nền local đã kiểm chứng; Q1–Q3 giữ nguyên |
| Constitution 1.0.0 (nguồn local tại lúc lập spec) | Tương thích, ranh giới team, kiến trúc hiện có, kiểm chứng; ngày phê chuẩn còn TODO. Công cụ local không là dependency của bộ tài liệu chia sẻ; xem [specs README](../README.md) |
| Code/test, [báo cáo T01](../001-t01-backend-foundation/verification.md) | Quan sát/bằng chứng, không tự định nghĩa yêu cầu hoặc nghiệm thu T02 |

Không tìm thấy AGENTS.md trong repository/các thư mục cha đã kiểm tra; dùng README,
constitution và skill. Giữ công nghệ/package/AiClient hiện có; không runtime/test framework
hoặc SLA/coverage mới. Chi tiết API dưới đây kế thừa nguồn, không thiết kế contract mới.

### Functional Requirements

- **FR-001**: PHẢI tiếp tục trên Backend hiện có, giữ interface Team 3; không sửa Frontend,
  Team 1/2 hoặc shared schema để che khác biệt nguồn.
- **FR-002**: Query PHẢI chỉ nhận ba field đã chốt, từ chối input sai theo bảng tham chiếu;
  validation hoạt động ở cả scenario thành công/lỗi.
- **FR-003**: answered PHẢI trả 200, đầy đủ public response, answer không rỗng,
  citation/marker đúng schema và fixture có nhãn mock.
- **FR-004**: insufficient_context PHẢI trả 200, answer không rỗng, citations=[],
  không marker; vẫn đủ ID/thời gian.
- **FR-005**: PHẢI tạo/giữ/chuyển hội thoại theo bỏ/null/UUID và client_request_id;
  message/lượt đúng lần tiếp nhận, không đòi AI history thật.
- **FR-006**: Mọi citation answered PHẢI trỏ tới ArticleResponse tồn tại, cùng cặp ID/
  metadata/source; không dùng tên hiển thị sinh ID hoặc thay version.
- **FR-007**: Document PHẢI trả nội dung mẫu đúng schema/ID, plain text không rỗng giữ xuống dòng;
  không dùng LLM ghép chunk thành nguyên văn.
- **FR-008**: Document PHẢI từ chối ID/body/query sai, 404 đúng khi document/article vắng;
  không thay bằng bản khác.
- **FR-009**: Query API mock chạy thực PHẢI có fixture 500/503/504 theo bảng Team 3,
  độc lập answered/insufficient_context; probe test T01 không đủ nghiệm thu.
- **FR-010**: Error PHẢI an toàn, code/status/retryable đúng, giữ trace/CORS T01 và
  X-Conversation-ID sau tiếp nhận kể cả lỗi; không đổi 406/ép JSON 403.
- **FR-011**: Thành viên PHẢI chọn/lặp scenario theo cấu hình instance và restart, query/document
  độc lập, không magic question/header/endpoint/field API. Giữ legacy MOCK_ANSWER_STATUS khi
  query scenario mới vắng; Q2 áp dụng từng key; config sai fail rõ, không fallback để che lỗi.
- **FR-012**: Document PHẢI có success và fixture 500/503/504 đúng code/retryable cho tuple
  mock tồn tại; validation input/404 giữ precedence. Không thêm scenario malformed public.
- **FR-013**: Fixture PHẢI được kiểm chứng mọi field/kiểu/độ dài/ID/marker/nullable/code point
  và liên kết query-document, không chỉ kiểm tra response có key.
- **FR-014**: Output sai schema/ID ở ranh giới DTO PHẢI bị từ chối theo mapping nguồn,
  502 UPSTREAM_INVALID_RESPONSE thay vì 200. Kiểm tra bằng output sai được kiểm soát;
  không thêm scenario public malformed, không nối AI thật.
- **FR-015**: Hướng dẫn PHẢI có request mẫu/scenario mặc định/lỗi/cách đổi, ID để hỏi tiếp/
  mới/mở document, cấu hình Q2 và giới hạn memory/mock.
- **FR-016**: Nghiệm thu PHẢI ghi source/working tree, command, expected/actual, giới hạn,
  build/test/HTTP mới và regression T01; không dùng PASS T01 thay nghiệm thu T02.

### Key Entities *(include if feature involves data)*

- **Lượt hỏi**: question, client_request_id, conversation_id tùy chọn, cặp message Backend.
- **Query result**: ID hội thoại/lượt/message, status, answer, citations, created_at.
- **Citation**: marker/chunk/văn bản/điều luật, metadata/source, liên kết điều luật mock.
- **ArticleResponse**: đúng phiên bản/ID/metadata, toàn nội dung mẫu, source_url.
- **Scenario**: kết quả mock được chọn ngoài public payload, không field DTO mới.
- **Bằng chứng**: case/AC, input/config, expected/actual, command, working tree, giới hạn.

### Đầu vào/đầu ra — contract kế thừa

| Interface | Input | Output/lỗi |
| --- | --- | --- |
| POST /api/v1/query | JSON UTF-8, chỉ question/client_request_id/conversation_id; không query parameter | 200 hai status; error cho input/system |
| GET /api/v1/documents/{document_id}/articles/{article_id} | Hai path ID, không body/query | 200 ArticleResponse; 400/404; mapping 500/502/503/504 nguồn Team 3 |
| GET /api/v1/health | Không body/query | 200 status=up, nền T01; không pipeline readiness |

Query request: question string bắt buộc 1–2000 Unicode code point sau trim, không null/blank;
client_request_id UUID v4 bắt buộc; conversation_id tùy chọn/null/UUID, không rỗng.
JSON malformed/field lạ/key trùng/sai kiểu/trailing bị từ chối; POST tối đa 16 KiB.

Query response: đủ conversation_id/client_request_id/user_message_id/assistant_message_id/
status/answer/citations/created_at; ID UUID, time RFC3339 UTC; answer 1–12000 code point.
answered: 1–10 citation và marker ánh xạ; insufficient_context: citations=[] không marker.

Citation: đủ 9 key citation_id (C1…C10 duy nhất), chunk_id/document_id (1–200),
article_id (1–100), document_title (1–500), article (1–100), clause/point (null hoặc 1–100),
source_url (HTTPS tuyệt đối tối đa 2048). Chỉ clause/point nullable; document_id/article_id
ASCII chữ/số/_/-. Marker liên tục theo xuất hiện, không nguồn thừa hoặc chunk trùng.

ArticleResponse: đủ document_id/document_title/article_id/article/content/source_url;
metadata/ID/source như citation; content 1–200000 code point plain text giữ xuống dòng.
Fixture là mẫu cấu trúc, không luật/GT thật.

| HTTP | Public code liên quan | Retryable |
| --- | --- | --- |
| 400 | INVALID_REQUEST | false |
| 404 | CONVERSATION_NOT_FOUND / DOCUMENT_NOT_FOUND / ARTICLE_NOT_FOUND / NOT_FOUND | false |
| 405 | METHOD_NOT_ALLOWED + Allow | false |
| 413 / 415 | PAYLOAD_TOO_LARGE / UNSUPPORTED_MEDIA_TYPE | false |
| 500 | INTERNAL_ERROR | false |
| 502 | UPSTREAM_INVALID_RESPONSE khi output/ID sai | false |
| 503 | SERVICE_UNAVAILABLE | true |
| 504 | UPSTREAM_TIMEOUT | true |

Envelope chỉ error:{code,message,retryable}, không answer/status; message tiếng Việt an toàn,
không provider/secret/stack. X-Request-ID mỗi lần gọi, X-Conversation-ID khi đã tiếp nhận,
FE đọc được qua CORS T01. Các mã replay/409 có sẵn giữ theo Team 3, không tạo lại như nhiệm vụ
production T02. Mapping lỗi output query theo mục 1.10 và document theo mục 1.8.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cả hai kết quả hỏi đáp thành công được tái hiện bằng input hợp lệ, đủ field/ID;
  không nhầm thiếu căn cứ với lỗi hệ thống.
- **SC-002**: 100% citation trong fixture answered mở đúng điều luật mẫu cùng metadata/source,
  giữ đầy đủ nội dung/xuống dòng và có nhãn mock.
- **SC-003**: Ba nhóm lỗi query ngoài dự kiến/không sẵn sàng/timeout chủ động tái hiện qua
  dịch vụ local; không error chứa answer/status hoặc chi tiết cần che.
- **SC-004**: Câu đầu/câu tiếp/hội thoại mới trả/giữ đúng ID; các nhóm input sai bị từ chối
  trong cả chế độ thành công/lỗi.
- **SC-005**: Thành viên khác chọn/lặp toàn bộ scenario đã chốt theo hướng dẫn; mỗi AC có
  expected/actual, command, giới hạn; không phụ thuộc AI/UI để kiểm tra.

Không tự đặt throughput/deadline/coverage/số fixture luật thật. 100% SC-002 chỉ xét bộ
fixture hữu hạn bàn giao, không corpus thật.

### Tiêu chí nghiệm thu

Lượt specify chưa đánh giá AC; sau implement, cả 8 AC đã PASS bằng kiểm chứng mới trong [báo cáo T02](verification.md). T01 PASS không tự nghiệm thu T02.

| AC | Kiểm tra và kết quả | Truy vết |
| --- | --- | --- |
| AC-T02-01 | Query input hợp lệ/sai ở biên/JSON/kiểu/ID, 400/413/415/405 đúng; scenario không che validation | FR-002/010/013; US1/3; SC-004; AC-03 tuần 2 |
| AC-T02-02 | Hai success 200 đúng toàn bộ field/kiểu/ID/time/marker/citation, không field scenario | FR-003/004/013; US1; SC-001; AC-03 |
| AC-T02-03 | Câu đầu bỏ/null ID, hỏi tiếp ID đã nhận, hỏi mới bỏ ID cũ; IDs đúng từng lượt | FR-005; US1; SC-004; Backend AC-05 |
| AC-T02-04 | Mọi citation → ArticleResponse cùng ID/metadata/source, content mẫu đầy đủ/xuống dòng | FR-006/007/013; US2; SC-002; Backend AC-06 |
| AC-T02-05 | Query chạy thật tái hiện 500/503/504, code/retryable/envelope/header an toàn | FR-009–011; US3; SC-003; CL-T02-01 đã chốt |
| AC-T02-06 | Document 400/404 đúng, không thay version; GET không body/query | FR-008/010; US2; SC-002; Backend AC-06 |
| AC-T02-07 | Lỗi document 500/503/504 theo CL-T02-02; output sai schema/ID → 502 qua test kiểm soát | FR-012/014; US2/3; CL-T02-02 đã chốt |
| AC-T02-08 | Build/test/HTTP mới, regression T01, hướng dẫn/evidence và diff bảo toàn | FR-001/015/016; SC-005; Backend AC-08 |

## Assumptions

### T01 và hiện trạng lúc specify — snapshot trước implement, không tự hoàn thành T02

Đã đối chiếu riêng báo cáo: 23/23 task T01; 5 XML surefire cuối tổng 25 test, 0 failure/
error/skipped; final-validation.log BUILD SUCCESS; runner log 31/31; smoke JSON 8 PASS,
4 startup error exit=1, default mock có log. Source/test sửa trước final package, runner
hiện phân giải Q2 và ca CORS/500 sau tiếp nhận đã có. Lượt specify chỉ đọc, không chạy lại.
T01 hoàn thành local; không suy ra review nhóm/toàn tuần 2. Câu hiện trạng Q2 cũ trong
quickstart T01 được đính chính tài liệu.

| File hiện có | Quan sát | Cần kiểm chứng/bổ sung |
| --- | --- | --- |
| backend/chat/ và DTO ChatRequest/ChatResponse | Query đồng bộ, input parser, IDs/error sau tiếp nhận | Không tạo lại; kiểm chứng DTO trong từng scenario |
| backend/common/web/RequestParser, ApiRequestFilter, ApiRequestInterceptor | Strict input/code point/body limit/GET/trace | Tái dùng; input errors phải đi trước scenario |
| backend/ai/MockAiClient và DTO RagAnswer/Citation/ArticleResponse | Hai success qua MOCK_ANSWER_STATUS; mock_v1/art1 | Chưa fixture system errors API thực; chưa đầy đủ kiểm chứng constraints |
| backend/document/DocumentController, DocumentService | 200/400/404, validation ID | Chưa chọn lỗi document; chưa guard output ID/schema |
| backend/conversation/ConversationService | Memory accept/complete/fail/replay/history | Giữ behavior, không DB/concurrency/AI history mới |
| backend/src/test/java/.../MockApiTests, InsufficientContextApiTests | Success/input/article/schema cơ bản | Chưa toàn bộ constraint output/citation/matrix demo |
| backend/src/test/java/.../BackendConfigurationTests, MockQueryServiceTests | Probe/spy 500/503/504 và failed states | Lỗi chỉ trong test, không đủ chứng minh scenario API local |
| application.properties, run-local.ps1, .env.example | MOCK_ANSWER_STATUS hai status; Q2/whitelist | Scenario mới chưa có; không coi magic question là quyết định đã chốt |

### Khác biệt tài liệu và phụ thuộc tối thiểu

- Tại lúc specify, file tuần 2 nói contracts/ là nguồn chính thức; Team 3 còn nhãn đề xuất/class khung. Khi tổ chức lại tài liệu ngày 09/10/2026, các nhãn này đã được làm rõ theo Q1; phần dưới lưu đối chiếu lịch sử.
  Q1 và yêu cầu hiện tại xác nhận team3.md là căn cứ API/luồng/kiến trúc, tuần 2 giới hạn task.
  Nhãn cũ không mở lại phê duyệt.
- contracts/README dẫn schema Team 2: request chỉ question max10000/additionalProperties=false,
  khác IDs/question max2000 Team 3; rag response thiếu status/public IDs/time; citation
  dùng claim/document/source, thiếu 9 field/liên kết Viewer; error envelope khớp nhưng thiếu
  HTTP/code/retryable, ví dụ PROVIDER_TIMEOUT khác public UPSTREAM_TIMEOUT.
- Team 2 thiếu history/article tương ứng: đồng bộ tích hợp sau, không dependency mock T02;
  không sửa shared schema trong nhiệm vụ này.
- T01: runtime/mock/CORS/trace/error envelope và Q2; regression khi T02 đổi config/DTO.
- Frontend nhận field/ID/scenario cho T03/T04; không sửa hoặc nghiệm thu UI ở T02.
- Team 1/corpus/AI thật không cần cho fixture cấu trúc; không tạo chunk thật hoặc GT từ mock.
- Giữ ví dụ mock_v1/art1 hiện có làm fixture hợp lý; không tự tăng mẫu luật hoặc đổi thành
  nguồn luật thật. Các deadline/retry/upstream HTTP thật ngoài phạm vi.

### Quyết định đã clarify và cần người dùng review

| ID | Câu hỏi | Đề xuất / ảnh hưởng |
| --- | --- | --- |
| CL-T02-01 | Cấu hình instance khi khởi động hay quy ước question mẫu? | Đề xuất cấu hình instance, giữ input pháp lý nguyên nghĩa; không magic question/header/endpoint; đổi scenario cần restart và giữ cấu hình answered cũ |
| CL-T02-02 | Document chỉ 200/400/404 hay thêm 500/503/504? | Đề xuất thêm ba lỗi cho tuple hợp lệ để Viewer T04 thử lỗi; error contract giữ nguyên, không API/AI thật mới |

CL-T02-01/02 đã chốt theo ủy quyền và cập nhật FR/AC/flow; không còn marker cần clarify
trước plan. Bảng trên lưu các lựa chọn/lý do, không phải câu hỏi chờ user. Q1–Q3 T01 giữ
nguyên. Tuấn có thể review/đổi lựa chọn vận hành sau; không có thay đổi public API hoặc
yêu cầu nhóm chưa chốt bị tự gán trạng thái phê duyệt. Phần SLA/auth/DB/RAG thật vẫn ngoài scope.
