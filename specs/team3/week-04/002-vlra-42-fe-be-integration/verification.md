# Kiểm chứng VLRA-42 — Frontend ↔ Backend v2.0

**Ngày:** 23/10/2026. **Kết luận:** cơ chế FE–BE đã được kiểm chứng, sẵn sàng review.
**Chưa phải nghiệm thu RAG thật hoặc MVP/VLRA44**; user chỉ định chờ service Team2.
Không sửa Jira/Team1/Team2/shared contracts. Không push.

## Nguồn và baseline

- Docs v2.0 §8.6–8.7/§9, Jira VLRA42 và quyết định người dùng áp dụng v2.0.
- Nền Java VLRA41:841280d, live HTTP service của Team2 chưa bàn giao ở develop3d64c4d
  được fetch/đối chiếu trong lượt trước. Không có fetch/merge nguồn mới trong lượt42.
- Giữ thay đổi docs chung và draft43/44 ngoài các commit42.
- Frontend ban đầu:20test PASS, build PASS; main chat JSON/snake/UUID, chưa parserSSE.

## Kết quả theo lớp

| Kiểm tra | Kết quả | Bằng chứng / giới hạn |
| --- | --- | --- |
| npm test | 56/56 PASS | 20test cũ +24SSE +6adapter +6receipt |
| npm run build | PASS | TypeScript strict ES2020 và Vite production build |
| Maven Wrapper package |119/119 PASS,0skip | gồm13store tests trên PostgreSQL18 và12StreamApiTests; test fixture, không liveLLM |
| Browser Edge thật |11/11 PASS | Vite→Java rag→PostgreSQL riêng→HTTP fixture,0uncaught JS exception |
| Public wire | PASS | request camelCase, positive safe integer conv IDs, UUIDv4; không history/scenario từ FE |
| Git diff/scope/links | kiểm tra trước bàn giao | không .env thật, log/build hoặc dữ liệu cá nhân trong commit |

Môi trường: Node24.21, Vitest2.1.9, React18/TS/Vite5; Java25.0.1/SpringBoot4.1.1;
PostgreSQL18 test cluster riêng, Edge headless profile riêng. Không thay dependency runtime.
Lần npm baseline trong sandbox bị esbuild spawn EPERM; chạy lại với quyền thực thi đạt.
Không đổi TypeScript target/Vitest version để làm test pass.

## Kịch bản browser

| # | Kịch bản | Actual |
| --- | --- | --- |
| B01 | Gửi câu đầu, hỏi tiếp, mở nguồn | PASS;1AI fixture call/lượt, history câu tiếp có1cặp, URL conv số, nguồn nguyên văn thử |
| B02 | Reload hội thoại hoàn tất | PASS; tải history, không gọi RAG thêm |
| B03 | insufficient_context | PASS; notice riêng, không citation giả |
| B04 | Lỗi SERVICE_UNAVAILABLE đã chốt rồi retry | PASS; UUID mới, gọi fixture lượt mới |
| B05 | Dừng nhận khi pending rồi nhận lại | PASS; UUID giữ nguyên,1AI call,1cặp message, answer không nhân đôi |
| B06 | Mất mạng trước meta, reload, retry | PASS; UUID giữ qua sessionStorage, chỉ1AI call được nhận |
| B07 | Reload khi Backend pending | PASS; chặn gửi mới, refresh history khi hoàn tất, không queryAI lại |
| B08 | Đổi hội thoại trước khi stream cũ xong | PASS; không gắn answer cũ vào lựa chọn mới |
| B09 | Nguồn404 | PASS; lỗi trong drawer, giữ answer |
| B10 | CORS | PASS; origin test được phép, origin ngoài danh sách403 không allow-origin |
| B11 | Viewer URL v2.0/deep link/reload | PASS; nguyên văn đúng document/article IDs |

Browser harness dùng Node builtin WebSocket/CDP, không thêm framework/dependency.
`tests/browser/rag-stub.mjs` là fixture TEST ONLY, không phải API của Team2 và không
thực hiện retrieval/rerank/LLM. Answer và article có nhãn dữ liệu giả lập; banner mock
hiển thị trong browser. Không dùng kết quả này đánh giá độ đúng pháp luật.

## Lệnh đã chạy

Tại frontend:

```powershell
npm test
npm run build
npm test -- --reporter=json --outputFile=../backend/target/vlra42-vitest.json
node tests/browser/vlra42-smoke.mjs
```

Tại backend, với test cluster riêng cổng55442/tài khoản test:

```powershell
$env:JAVA_HOME='D:/Java/jdk-25'
.\mvnw.cmd -B -ntp '-Dtest.postgres.url=jdbc:postgresql://127.0.0.1:55442/postgres' '-Dtest.postgres.user=vlra42' package
```

Stack browser: FE127.0.0.1:15173, Java127.0.0.1:18043, fixture127.0.0.1:18042,
CDP127.0.0.1:19242; CORS chỉ origin test. PostgreSQL cluster tại backend/target/vlra42-postgres,
không dùng database chung. Đã dừng đúng các tiến trình/cụm tạm, không giữ service giả chạy nền.

Evidence local được tái tạo theo quickstart, không đưa cache browser/log cá nhân lên Git:
`team3_fullstack/backend/target/vlra42-{package.log,vitest.json,build.log}`;
`target/vlra42-browser/{results.json,browser.png,backend.log,stub.log,vite.log}` và
`surefire-reports/TEST-*.xml`. Browser results chứa expected/actual assertion và request
fixture theo từng ca; không có API keys hoặc payload luật/người dùng thật.

## Commit và hoàn tác

| Thứ tự | Commit | Phạm vi |
| --- | --- | --- |
|1|d561f7f| SSE transport/types/validators/tests, chưa đổi UI callers |
|2|b632265| Public adapters + Java Viewer proxy/trace, chưa đổi UI callers |
|3|b695277| Nối UI, receipt/retry/reload/abort, browser harness |
|4|Commit chứa hồ sơ này| Spec/plan/tasks/evidence summary/quickstart/README |

Các commit dùng identity GitHub đã xác minh theo yêu cầu người dùng, không sửa tác giả
của commit cũ. Revert từ4→3→2→1 vì3 import modules của1/2. Dùng git revert, không reset
hoặc force push. Revert3 khôi phục main UI JSON v1.2; lúc đó cần backend profile mock
để chạy UI lịch sử, trong khi các adapter mới vẫn tồn tại nhưng chưa được UI gọi.

## Phần còn chờ

- **T014/live:** Team2 bàn giao FastAPI `/internal/v1/query`, pipeline thật và cấu hình/
  snapshot. Sau đó dùng cùng API contract, đổi RAG_BASE_URL và chạy live AC41/44.
- Kiểm tra source/grounding pháp lý thật và thiết kế/ACUI đầy đủ thuộc VLRA43/44.
- Không chạy load test, benchmark LLM, Docker build hoặc browser matrix khác Edge.
- SessionStorage bị chặn thì tab hiện tại vẫn hoạt động, nhưng không cam kết phục hồi
  UUID sau reload trước meta; hạn chế này được ghi rõ, không tự lưu question vĩnh viễn.
- Trang /try-backend là công cụ JSON v1.2 lịch sử, dùng profile mock riêng; không là
  main chat v2.0 hoặc bằng chứng RAG thật.

## Bổ sung W4-Q2 — tiêu đề từ câu hỏi đầu (23/10/2026)

Quyết định người dùng tại spec.md thay quy định không tự đổi title theo câu hỏi của
Docs v2.0 §9.2. `ChatStore` lưu title từ câu đầu trong transaction accept, chuẩn hóa
khoảng trắng/Unicode, tối đa 100 code point. Giữ title khi hỏi tiếp/replay/lỗi/reload,
giữ tên custom; conversation rỗng chưa hỏi vẫn dùng tên mặc định. Không thêm LLM/API.

- Ba ca mới trong `ChatStoreTests`, chạy lại cả H2 và PostgreSQL: Unicode/100codepoint,
  reload/replay/follow-up, default conversation rỗng, failed/retry, custom và dữ liệu cũ.
- Full suite ban đầu: **125/125 PASS**, nhưng package thất bại tại repackage vì backend
  preview đang giữ JAR trên Windows. Đây không phải build thành công.
- Sau khi dừng đúng preview và bổ sung guard title rỗng sau chuẩn hóa Unicode: chạy
  `mvnw.cmd -B -ntp -Dtest=ChatStoreTests,PostgresChatStoreTests,StreamApiTests
  -Dtest.postgres.url=jdbc:postgresql://127.0.0.1:55442/postgres -Dtest.postgres.user=vlra42 package`
  với JAVA_HOME trỏ JDK25: **44/44 PASS,0skip, BUILD SUCCESS** (16H2+16PG+12HTTP).
  Không tuyên bố full125 được chạy lại sau guard cuối; các ca liên quan đã chạy đủ.
- Khởi động lại Java từ JAR mới và chạy `node tests/browser/vlra42-smoke.mjs` với
  `EVIDENCE_DIR=../backend/target/vlra42-title-browser`: **11/11 PASS,0JS exception**.
  B01 xác minh title trên sidebar/header theo câu đầu và giữ sau follow-up; B02 xác
  minh title sau reload. Các ca source/retry/abort/pending/CORS vẫn đạt.
- Không đổi code FE/dependency nên không chạy lại npm build/unit cho thay đổi này;
  browser kiểm tra cùng bundle dev đã build/kiểm chứng ở baseline trên.
- Chỉ database preview `legal_rag_preview` ở cluster riêng127.0.0.1:55442 đã được cập
  nhật **4** title mặc định từ tin nhắn user sequence1. Không đổi timestamps/messages,
  không áp migration lên database khác. Dọn riêng hội thoại do browser test tạo qua
  request UUID của chính bài test; giữ các hội thoại có sẵn.
- Preview tiếp tục chạy FE15173/Java18043/fixture18042 cho người dùng. Edge headless
  kiểm thử đã dừng; dữ liệu trả lời vẫn là HTTP fixture, T014 live tiếp tục mở.

Evidence ignored: `backend/target/vlra42-title-{package,repackage}.log`,
`target/vlra42-title-browser/{results.json,browser.png}`, surefire reports và
`target/vlra42-preview/update-preview-titles.sql`. Lần này không sửa Google Docs/Jira,
Team1/Team2/shared contracts hoặc gom những thay đổi docs chung đang có.
