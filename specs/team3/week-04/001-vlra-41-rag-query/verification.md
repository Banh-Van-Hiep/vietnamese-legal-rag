# Kiểm chứng VLRA-41 — API chat SSE v2.0

**Ngày:** 23/10/2026. **Kết luận:** implementation Java đã có và được kiểm chứng;
**chưa nghiệm thu toàn bộ VLRA-41** vì chưa có service HTTP RAG thật trên develop.
Không sửa Jira, FE, Team1/2 hoặc shared contracts. Báo cáo lập trước commit; người dùng sau đó yêu cầu commit riêng VLRA-41 vào nhánh bàn giao được người dùng chỉ định, chưa push.

## 1. Căn cứ và snapshot

- Người dùng chốt làm theo Docs v2.0 ngày 23/10, giải quyết W4-Q1. Public
  `POST /api/v1/chat/stream`; Java gọi JSON `POST /internal/v1/query`.
- Fresh `git fetch origin develop`: commit `3d64c4d38b93f11ac321623159f74e5202d1e953`
  ngày 20/10; source Team1/2/3 không khác baseline HEAD trước triển khai.
- Nhánh làm việc `test/retrieval-verification`, HEAD `27ef448f02f63075404093b7ac772eda8b2cd513`;
  đây là snapshot khi kiểm thử. Commit bàn giao nằm trên nhánh bàn giao được người dùng chỉ định theo yêu cầu sau đó; các thay đổi tài liệu chung khác được giữ ngoài commit VLRA-41.
- Trên develop: HttpAiClient rỗng, service.query Python trả make_mock_response,
  chưa thấy HTTP server RAG được bàn giao. Không suy kết quả sang nhánh riêng Team2.

## 2. Thay đổi đã thực hiện

- Profile `rag`: public SSE/camelCase/ID số an toàn. Không đăng ký `/api/v1/query`
  trong profile này; `mock` là profile JSON v1.2 lịch sử, không bật cùng rag.
- HttpAiClient gửi question/history và trace; strict required/unknown/duplicate/type/
  trailing JSON, kiểm marker/citation; timeout toàn bộ body, connect≤2s, không retry AI.
- PostgreSQL/JDBC transaction cho conversation/messages/citations/receipt; unique UUID,
  khóa hội thoại, unique sequence và pending, chốt cùng assistant row; không giữ
  transaction khi gọi HTTP. Complete chỉ phát sau validate và commit.
- History tối đa 5 cặp answered/completed, ≤20000 code point, bỏ nguyên cặp cũ.
- Idempotency/replay, conflict/busy, fail snapshot/logical status, recovery>60s,
  bảo vệ late output, delete/tombstone không giữ content/fingerprint/snapshot.
- SSE meta/heartbeat/delta/complete/error, bounded worker, async55s/no-store;
  disconnect không hủy AI, không biến completed thành failed vì lỗi truyền.
- Conversation API arrays hỗ trợ đọc/reconcile/delete. Chưa triển khai Viewer v2.0
  hoặc parser/UI Frontend trong VLRA-41.
- Schema public trong [contracts/chat-v2.schema.json](contracts/chat-v2.schema.json).
  Không dùng query_request.schema v0.1 để validate request SSE.

## 3. Lệnh và kết quả

JDK thực dùng `D:/Java/jdk-25`, Java 25.0.1. Maven Wrapper theo repository.

```powershell
cd team3_fullstack/backend
$env:JAVA_HOME = 'D:/Java/jdk-25'
.\mvnw.cmd -B -ntp '-Dtest.postgres.url=jdbc:postgresql://127.0.0.1:55441/postgres' package
```

Lệnh trên yêu cầu cụm PostgreSQL **test riêng** đã chạy, không trỏ vào database dùng chung.
Kết quả full suite: **117 executions, 0 failure, 0 error, 0 skipped; BUILD SUCCESS**.

| Nhóm | Số executions | Kết quả |
| --- | ---: | --- |
| Legacy mock/configuration/validator | 74 | PASS |
| HttpAiClientTests | 7 | PASS |
| ChatStoreTests — H2 | 13 | PASS |
| PostgresChatStoreTests — PostgreSQL 18 | 13 | PASS |
| StreamApiTests — Tomcat real port, HTTP stub/H2 | 10 | PASS |

13 ca store được chạy lại trên PostgreSQL là cùng bộ hành vi, không tính là 26
kịch bản nghiệp vụ độc lập. Full suite cuối cùng đã bao gồm sửa khóa replay/delete,
test timeout khi headers đã nhận nhưng body chậm, payload wire/schema, gate415 và
query parameter. Không đổi code production sau lần full suite cuối.

Evidence local (ignored, không đưa log có đường dẫn máy vào tài liệu public):
`team3_fullstack/backend/target/` gồm `vlra41-final-package.log` (full suite cuối), `vlra41-package.log`, `vlra41-postgres-test.log`,
`vlra41-http-final.log`, `vlra41-wire-final.log`, `vlra41-stream-final.log`,
`surefire-reports/TEST-*.xml`, `vlra41-contract-examples.json`, `vlra41-runtime/results.json`.
Các log target được tái tạo bằng lệnh kiểm chứng, không phải nguồn yêu cầu.

### Schema

Dùng Python/jsonschema[format] thuộc test extra hiện có trong pyproject:

```powershell
# từ repository root, sau StreamApiTests
python specs/team3/week-04/001-vlra-41-rag-query/contracts/validate-examples.py
```

ChatRequest, Meta, Delta và Complete lấy từ HTTP wire thực của StreamApiTests:
**4/4 PASS**. Ba payload âm: ID sai kiểu, field lạ, UUID không phải v4: **3/3 PASS**.
Schema không chứng minh grounding/provenance pháp lý, history hoặc state machine.

### JAR và persistence qua restart

Chạy JAR đóng gói với profile rag, cổng18041, PostgreSQL18 tạm cổng55441; upstream
trỏ cổng không có service55442 để kiểm failure rõ ràng, không gọi provider thật.

| Kiểm tra | Expected / actual |
| --- | --- |
| Startup + health | PASS, PostgreSQL schema init, HTTP liveness up |
| Query khi upstream unavailable | PASS, HTTP200 SSE meta→error SERVICE_UNAVAILABLE, không complete |
| Messages | PASS, 2 message, ID số, assistant failed |
| Route JSON lịch sử trong rag | PASS, POST /api/v1/query trả404 |
| Restart JAR, replay cùng UUID | PASS, HTTP503 JSON lỗi đã lưu, cùng conv, vẫn 2 message |

Runtime smoke JAR/restart trên thực hiện trước chỉnh lý khóa replay/delete cuối;
bản cuối kiểm chứng lại toàn bộ 117 test, gồm nhánh khóa đó trên PostgreSQL/H2.

PostgreSQL test cluster được tạo bằng initdb/pg_ctl trong backend/target, chỉ listen
127.0.0.1:55441; mỗi store test dùng schema riêng rồi drop schema của nó. Đã dừng
cụm tạm và tiến trình JAR test; service PostgreSQL có sẵn của máy vẫn Running.
Không sửa pg_hba của máy hoặc truy cập database người dùng bằng credential đoán.

## 4. Đối chiếu nghiệm thu

| Tiêu chí | Trạng thái / căn cứ |
| --- | --- |
| FR001/008 — public SSE, ID, event/state | PASS trong HTTP test; meta/pending/heartbeat trước kết quả; no delta cho insufficient; lỗi persist không complete |
| FR002–005 — HTTP boundary/validation/error | PASS với stub: success, malformed/extra/duplicate/type/citation, timeout body, unavailable, mapping4xx/502/503/504, safe errors |
| FR006/009 — history/idempotency/recovery | PASS H2 và PostgreSQL: replay, pending, conflict, concurrent UUID/conv/query-delete, 5 cặp/20k, rollback, late result |
| FR010 — reconcile/delete | PASS arrays/message fields và tombstone bỏ nội dung; pending không xóa được |
| FR007/SC004 — evidence | PASS: commands, source/profile và giới hạn được ghi rõ |
| SC002/SC003 | PASS trong phạm vi Java/stub/database đã kiểm tra |
| SC001 — RAG thật, nguồn/citation thật | **NOT RUN / OPEN**: W4-D1/D2 chưa bàn giao trên develop |
| Jira VLRA-41 toàn bộ | **Chưa chốt nghiệm thu**: API Java sẵn sàng, chưa có evidence gọi pipeline thật |

## 5. Giới hạn và bàn giao

- HTTP stub kiểm tra protocol và state, không thực hiện retrieval/rerank/LLM. Không
  có corpus/model/index snapshot cho một lượt live trong lượt này.
- PostgreSQL tests kiểm tra nhiều repository/transaction manager kết nối cùng DB;
  chưa chạy load/benchmark hoặc nhiều tiến trình backend đồng thời.
- PowerShell runner không sửa, vẫn dành mock; không chạy lại test runner stub vì
  không có thay đổi script. Quickstart v2.0 dùng Maven Wrapper và process env.
- Lần baseline đầu bị quyền sandbox ghi target và JAVA_HOME JDK24; chọn JDK25 và
  chạy lại có quyền ghi build. Đây là lỗi môi trường, không tính vào kết quả final.
- H2 2.4.240 có lỗi CHECK(IN) đa connection; H2 test-only được ghim2.5.250 đã sửa
  ([upstream issue](https://github.com/h2database/h2database/issues/4302)). Không bỏ constraint để làm test pass.
- Task còn mở **T014**: Team2 bàn giao internal HTTP live, cấu hình/lệnh chạy và
  snapshot retrieval/corpus/model; chạy SC001 và thu evidence answer/citation thật.
  VLRA42/43/44 chưa triển khai trong lượt này.

Cách chạy: [quickstart.md](quickstart.md). Chi tiết tiến độ: [tasks.md](tasks.md).
