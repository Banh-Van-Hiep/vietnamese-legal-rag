# Team 3 — Kiểm chứng và nghiệm thu tuần 2

**Ngày kiểm chứng:** 12/10/2026 (Asia/Saigon).

**Code được kiểm tra:** `dcd80a22b74f8e80e7db3e9af3ba95c014d6c0bf`.

**Kết luận:** T01–T04 PASS kỹ thuật trong phạm vi local/mock. T05 chưa nghiệm thu pháp lý;
T06 đã có bàn giao kỹ thuật, còn xác nhận chạy lại của thành viên khác. Chưa đóng toàn tuần 2.

Nguồn yêu cầu: [nhiệm vụ Jira tuần 2](../../docs/team3_fullstack/week2.md),
[API/luồng/kiến trúc Team 3](../../docs/team3_fullstack/team3.md),
[T01](001-t01-backend-foundation/spec.md), [T02](002-t02-mock-api/spec.md)
và mô tả VLRA-24 đã được cung cấp: 5–10 câu mỗi thành viên, 30–50 câu cho dataset chung.
Phân rã và tiêu chí kỹ thuật nằm trong [tasks.md](tasks.md).
Q1–Q3 giữ nguyên. Đây là kết quả kiểm chứng, không thay biên bản nghiệm thu của nhóm.

## 1. Kết quả theo task

| Task | Kết quả | Bằng chứng và phần còn lại |
| --- | --- | --- |
| T01 — Backend nền tảng | PASS local | Package 74 Java tests; runner 37/37; 8 bản ghi smoke cấu hình/default/startup lỗi. JDK 25; không cần AI/API key/PostgreSQL thật. |
| T02 — API mock | PASS local | 8/8 bản ghi HTTP matrix: query/document success, insufficient_context, 500/503/504, validation, ID, CORS, trace, citation và trạng thái lưu. Output validator được kiểm tra trong Java suite. |
| T03 — Frontend | PASS local | `npm ci`, build TypeScript/Vite/Tailwind CSS v4 và kiểm tra browser Chat/Search/Viewer, reload, mobile 390px. Chênh lệch CSS thuần với FE-01 đã được giải quyết bằng commit `4d6acdd`. |
| T04 — FE–BE mock | PASS local | 20 unit tests API/retry; 27 kiểm tra browser và 1 ca retry timeout end-to-end. Commit `f5eaca9` đã sửa lỗi đọc JSON; retry giữ ID, history 2 → 2. |
| T05 — Golden Dataset | PASS dữ liệu; chưa nghiệm thu | Hai validator PASS 13 mẫu (12 answered, 1 insufficient_context); 10 ca regression validator PASS. Còn reviewer xác nhận pháp lý, đóng góp 5–10 câu/người và cách bàn giao mẫu 008. |
| T06 — Bàn giao | PARTIAL | Hướng dẫn và ma trận AC đã cập nhật; môi trường kiểm tra tái hiện được. Còn thành viên khác xác nhận chạy lại và nhóm xác nhận các phần đang chờ. |

## 2. Tổng hợp từ task lên nhiệm vụ Jira

Chỉ tổng hợp sau khi đối chiếu từng task ở mục 1 và bằng chứng/AC ở mục 3.
Phạm vi Jira lấy từ [nhiệm vụ chung tuần 2](../../docs/team3_fullstack/week2.md).
Các kết luận dưới đây là đánh giá trong repository, chưa đổi trạng thái trên Jira.

| Jira | Task làm căn cứ | Đối chiếu đầu ra Jira | Kết luận |
| --- | --- | --- | --- |
| VLRA-22 — Backend Skeleton | T01, T02, phần Backend của T04, phần bàn giao Backend của T06 | Khung Java/Spring Boot, cấu hình/CORS và API mock đã kiểm chứng; FE gọi được, schema/error/ID đúng trong phạm vi local/mock. Còn xác nhận chạy lại khi bàn giao. | Đạt kỹ thuật local; chờ xác nhận bàn giao, chưa đóng Jira |
| VLRA-23 — Frontend Skeleton | T03, phần Frontend của T04, phần bàn giao Frontend của T06 | Router/Tailwind/Chat/Viewer đã có và qua build/browser; còn xác nhận chạy lại khi bàn giao. | Đạt kỹ thuật local; chờ xác nhận bàn giao, chưa đóng Jira |
| VLRA-24 — Golden Dataset Phase 1 | T05, phần bàn giao GT của T06; phối hợp các team để tổng hợp dataset chung | Team 3 có 12 câu answered có chunk và 1 câu thiếu ngữ cảnh. Còn review pháp lý, xác nhận 5–10 câu/người và bàn giao; hai file hiện có tổng 18 mẫu, 17 có căn cứ, chưa đạt 30–50 câu chung. | Chưa đạt nghiệm thu Jira |

T06 được xét theo phần bàn giao liên quan từng Jira; review Golden không thay kết quả
kiểm chứng Backend/Frontend. Chỉ đóng tuần 2 sau khi cả 3 nhiệm vụ chung được nghiệm thu.

## 3. Ma trận tiêu chí nghiệm thu

| AC | Expected | Actual ngày 12/10/2026 | Kết quả |
| --- | --- | --- | --- |
| AC-01 | BE mock build/chạy, health 200; FE cài theo lockfile, dev/build thành công | Maven Wrapper package 74 tests, health up trên các tiến trình riêng; npm ci cài 113 packages, Vite dev và build PASS | PASS kỹ thuật |
| AC-02 | Ưu tiên cấu hình Q2; origin cho phép gọi được, origin ngoài danh sách không được cấp CORS | Runner 37/37; smoke A/B/default, actual/preflight và trace/expose headers PASS; browser gọi BE port 18085 từ FE port 5173 | PASS |
| AC-03 | Query đúng schema/status; validation sai bị từ chối; lỗi hệ thống có envelope an toàn | Java suite và HTTP matrix PASS cho answered, insufficient_context, 400/404 và 500/503/504. RuntimeException sau tiếp nhận và 502 output invalid được suite kiểm tra; không thêm contract nghiệm thu 406 hay body JSON 403 | PASS |
| AC-04 | Chat loading/answer/citation/error đúng; chặn rỗng, quá dài và gửi trùng | Browser PASS: blank, 2001 Unicode code points, loading, pending dedup, UTF-8; thiếu căn cứ và lỗi hệ thống hiển thị riêng. Timeout đọc body retry cùng ID | PASS |
| AC-05 | Lượt đầu có ID mới; hỏi tiếp giữ conversation ID; hội thoại mới có ID khác | Browser và HTTP smoke PASS, reload lịch sử đúng; retry chưa rõ kết quả không thêm lượt | PASS |
| AC-06 | Router/reload, Search fixture, Viewer theo ID; viewer lỗi giữ Chat, mobile và nhãn mock | Browser PASS: Search rỗng/kết quả/không kết quả, document reload, live 404, viewer 503 có kiểm soát + retry, giữ answer, xuống dòng, Escape và mobile | PASS local |
| AC-07 | Ground Truth có căn cứ, không trùng, nguồn/phiên bản/đáp án được review; 5–10 câu mỗi thành viên theo VLRA-24 | Team 3 có 13 mẫu, 12 có chunk; không trùng với 5 mẫu Team 2. Chưa có review pháp lý và xác nhận đóng góp nội bộ; mẫu 008 không tính vào chỉ tiêu có căn cứ khi chưa được nhóm chấp thuận | PENDING |
| AC-08 | Bàn giao có command/expected/actual/commit và thành viên khác chạy lại được; không đưa secret/output vào Git | Có báo cáo này, README và lệnh chạy; 238 file tracked giữ nguyên trong test, không có .env thật/node_modules/target/dist tracked, không khớp các mẫu secret đã rà soát. Chưa có xác nhận chạy lại của thành viên khác | PARTIAL |

Rà soát secret là kiểm tra tên đường dẫn và các mẫu private key/AWS access key/API key;
không phải kiểm toán bảo mật toàn diện. Không tự suy ra phê duyệt từ việc build/test PASS.

## 4. Lệnh đã chạy và bằng chứng

Các lệnh dưới chạy từ repository root, trừ lệnh npm chạy trong `team3_fullstack/frontend/`.
JDK kiểm tra: `D:\Java\jdk-25` (25.0.1); Node 24.21.0, npm 11.19.0; dùng lockfile hiện có.
Runner package dùng fixture riêng, không đọc hay ghi đè `.env` cá nhân.

| Kiểm tra | Lệnh / thao tác | Kết quả / evidence local |
| --- | --- | --- |
| Backend package | `run-local.ps1 -Task package -EnvFile target/week2-acceptance-20261012/build.env` trong Backend, JAVA_HOME JDK 25 | BUILD SUCCESS; 74 tests, 0 failure/error/skip; `backend-package.log` |
| Runner | `powershell -NoProfile -ExecutionPolicy Bypass -File team3_fullstack/backend/src/test/powershell/RunLocalConfigurationTests.ps1 -JavaHome D:\Java\jdk-25` | 37/37; `runner-tests.log` |
| T01 smoke | `powershell -File team3_fullstack/backend/target/week2-acceptance-20261012/t01/SmokeValidation.ps1` | 8 PASS records; `t01/config-smoke-results.json` |
| T02 HTTP | `powershell -File team3_fullstack/backend/target/week2-acceptance-20261012/t02/SmokeValidation.ps1` | 8/8; `t02/http-smoke-results.json` |
| FE install/build/test | `npm ci --prefer-offline --no-audit --no-fund`, `npm run build`, `npm test` | 20/20 tests; `frontend-install.log`, `frontend-build.log`, `frontend-tests.log` |
| Browser | `node team3_fullstack/backend/target/week2-acceptance-20261012/browser-audit.mjs <mode>`; core + insufficient_context + internal_error + service_unavailable + upstream_timeout | 27 PASS, 0 uncaught exceptions; `browser-*.json` |
| Retry body timeout | `node team3_fullstack/backend/target/week2-acceptance-20261012/slow-json-audit.mjs` | PASS: cùng request ID, history trước/sau 2; `slow-json-retry.json` |
| GT Team 3 | `python -B -X utf8 team3_fullstack/ground_truth/validate_ground_truth.py` | 13 mẫu hợp lệ; `golden-team3.log` |
| GT Team 2 | Import `team2_rag.validate_golden`, đặt `GOLDEN_FILE` tới bộ Team 3 rồi gọi `validate_golden_dataset()` | PASS 13/13; `golden-team2.log`; cách chạy ở [README GT](../../team3_fullstack/ground_truth/README.md#kiểm-tra) |
| GT regression | Fixture kiểm tra hợp lệ, max, trùng ID/câu, thiếu field/chunk, answered rỗng, status sai, insufficient có chunk và corpus thiếu | 10/10 ca, exit code đúng; `golden-regression.json` |
| Team 2/shared contract | `python -B -m unittest discover -s tests -p test_team2_mock.py -v`; check 4 schema và 9 valid/reject cases | 6/6 tests và 9/9 checks; `team2-contract-tests.log`, `contract-review.json` |

Evidence nằm trong `team3_fullstack/backend/target/week2-acceptance-20261012/` và bị Git ignore.
Các helper smoke/browser là artifact local, không có trên máy mới; dùng các hướng dẫn và thao tác
ở mục 4 để chạy lại phần public. Báo cáo chỉ ghi kết quả của code hash ở đầu trang.

Trong lần chạy ban đầu có lỗi công cụ: PowerShell coi stderr warning của npm là lỗi,
JDK của terminal chưa đúng, selector browser cũ và race khi lấy PID trong smoke harness.
Đã chỉnh môi trường/helper local rồi chạy lại các phần bị ảnh hưởng; kết quả PASS ở trên là
kết quả lần chạy hoàn tất. Không sửa code ứng dụng/test trong repository để đạt PASS.
Đã dừng đúng các PID test do phiên kiểm chứng tạo; cổng 8080/18082–18085/5173/9236 được giải phóng.

## 5. Chạy lại và xác nhận bàn giao

Đọc [quickstart T01](001-t01-backend-foundation/quickstart.md),
[quickstart T02](002-t02-mock-api/quickstart.md),
[README Frontend](../../team3_fullstack/frontend/README.md) và [README GT](../../team3_fullstack/ground_truth/README.md).
Thay đường dẫn JDK theo máy; không ghi đè `.env` đã có.

Terminal Backend, từ repository root:

```powershell
$env:JAVA_HOME = 'D:\Java\jdk-25'
$env:SPRING_PROFILES_ACTIVE = 'mock'
$env:MOCK_ANSWER_STATUS = 'answered'
$env:MOCK_QUERY_SCENARIO = 'answered'
$env:MOCK_ARTICLE_SCENARIO = 'success'
.\team3_fullstack\backend\run-local.ps1 -Port 18085 -AllowedOrigins 'http://localhost:5173,http://127.0.0.1:5173'
```

Terminal Frontend, từ repository root:

```powershell
Set-Location .\team3_fullstack\frontend
$env:VITE_API_URL = 'http://localhost:18085'
$env:VITE_MOCK_MODE = 'true'
npm ci
npm test
npm run build
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Mở `http://localhost:5173`: kiểm tra chặn rỗng/loading/answer, hỏi tiếp và hội thoại mới;
click citation, đóng viewer, reload hội thoại/document, Search và mobile.
Đổi `MOCK_QUERY_SCENARIO` rồi restart Backend để thử insufficient_context/500/503/504;
503/504 có Thử lại, dùng ID mới khi lượt trước đã failed. Viewer 503 ở browser audit là
lỗi được chèn có kiểm soát, không làm mất Chat. Các test API trong repo kiểm tra body timeout,
body hỏng, mất kết nối, hủy chủ động và chính sách giữ ID.

Ghi nhận thành viên khác đã chạy lại với commit, thao tác và kết quả trước khi đóng AC-08.
Reviewer nhóm cần xác nhận nguồn/phiên bản/đáp án và bàn giao GT trước khi đóng AC-07.

## 6. Giới hạn và phối hợp

- Mock dùng memory; dữ liệu mất sau restart. Java `HttpAiClient` vẫn placeholder và Python
  `query` còn mock. Chưa nghiệm thu tích hợp RAG thật hoặc PostgreSQL persistence.
- Search là fixture, không thêm API Search. Chưa kiểm tra deployment, Docker/nginx route
  fallback, auth hoặc streaming; đây không phải điều kiện nghiệm thu local/mock tuần 2.
- Dataset chung trong hai file hiện có 18 câu không trùng (17 answered, 1 insufficient_context),
  chưa đạt 30–50. T05 của Team 3 cần review 12 câu có căn cứ và xác nhận đóng góp nội bộ;
  không ghi tên cá nhân trong tài liệu public. Mẫu `gt_t3_008` vẫn chờ thống nhất cách bàn giao.
- `contracts/v0.1/` Revision 2 bám schema Team 3 v1.2 hơn bản nháp cũ và đã qua kiểm tra cấu trúc;
  vẫn là proposal. README contract ghi corpus lao động, corpus/GT hiện là doanh nghiệp:
  cần nhóm phối hợp làm rõ khi bàn giao liên team. Không đổi API/schema ở phiên này.
- Các đối chiếu contract trong báo cáo T01/T02 cũ là snapshot lịch sử, không thay nhận định
  về Revision 2 hiện tại. Không sửa Q1–Q3 hoặc tự nâng hành vi code thành contract.

## 7. Snapshot triển khai sau T01/T02

Bảng dưới được chuyển từ phần mở đầu của `docs/team3_fullstack/team3.md` khi tách
kiến trúc và trạng thái triển khai. Nó mô tả thời điểm sau T01/T02, trước thay đổi Frontend
và kiểm chứng tuần 2 ngày 12/10/2026; hiện trạng dùng kết quả ở mục 1–2.


| Thành phần | Vai trò | Hiện trạng sau T01/T02 |
| --- | --- | --- |
| chat/ | Nhận query, điều phối lượt, trả response và ID | Mock đồng bộ; guard output trước complete, lỗi sau accept giữ conversation ID |
| conversation/ | Tạo/xem/xóa hội thoại, lưu và xem tin nhắn | Bộ nhớ tạm; Conversation/Message là snapshot, repository JPA là placeholder tắt trong mock |
| document/ | Mở điều luật theo document_id/article_id | Mock tuple, guard đúng ID/schema; không tải URL tùy ý |
| ai/ | Ranh giới Backend–RAG | AiClient hiện nhận question/lấy article; MockAiClient có scenario; HttpAiClient chưa triển khai |
| common/ | Parser/filter/trace/CORS/lỗi | Đã có validation, CORS theo origin và error envelope |
| application*.properties, run-local.ps1 | Runtime/profile/env/port/origin | Mock tắt datasource/JPA; .env do runner nạp, không do Spring tự đọc |
| Frontend | Chat/Search/Viewer theo thiết kế | Có trang thử /try-backend; các màn hình chính T03/T04 chưa được nghiệm thu |

PostgreSQL, history truyền sang AI và gọi Python thật là phần kiến trúc tích hợp phía sau;
T01/T02 chưa triển khai chúng. Mock mất dữ liệu sau restart, không hiểu ngữ cảnh bằng AI thật.
Các schema nội bộ ở mục 1.9 là căn cứ phối hợp tích hợp; chênh lệch Team 2 còn phải đồng bộ,
không suy ra upstream đã chạy.

