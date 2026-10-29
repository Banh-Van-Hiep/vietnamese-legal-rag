# Biên bản nghiệm thu lại Team 3 — Tuần 5

**Ngày:** 29/10/2026 (Asia/Saigon), thay kết quả tổng hợp ngày28/10.
**Căn cứ:** [tasks.md](tasks.md), [ARCHITECTURE](../../../docs/ARCHITECTURE.md) §3/§8.2.A,
[CODING_CONVENTIONS](../../../docs/CODING_CONVENTIONS.md) §5/§7,
[contract hiện hành](../../../contracts/v0.1/CONTRACT.md).
**Source chạy:** 2b7ccd3b6cb25b5599870416241b9f38a3511075.
**Develop đã fetch:** eea5604251afd4d8605fed510d6bf4de31d629bb, đã chứa các commit Team3.
Diff HEAD↔develop không đổi Backend/Frontend/contract/Golden/HTTP mock liên quan.
Ba file khác nằm ở chunk_documents, BM25 và một test reranker, không dùng trong luồng mock này.
Không checkout/merge vào worktree để làm audit. Sau audit, theo yêu cầu người dùng,
đóng góp Team3 được rút còn10 rồi hợp nhất vào file Phase1 chung tại Team2. Đã thay4
câu trùng ý và thu hẹp2 câu tổng hợp; xóa thư mục Golden riêng Team3. Code, corpus
và validator không đổi. Số liệu Golden mới được kiểm riêng, không sửa log audit cũ.
Hồ sơ công khai dùng vai trò, không ghi danh tính cá nhân.

## 1. Kết luận

**Tích hợp mock G2 đạt kiểm chứng kỹ thuật; Golden đã hợp nhất50 mẫu và rà trùng ý.
Phần đóng góp/hợp nhất VLRA24 của Team3 đã bàn giao; Team2 phụ trách kiểm chứng
và kết luận dataset chung theo phân công người dùng xác nhận ngày29/10/2026.** VLRA22, VLRA23 và VLRA-T3-06 đạt trong cấu hình kiểm thử
được mô tả dưới đây. Không tự đổi trạng thái Jira hoặc xác nhận nhóm đã duyệt G2.

**VLRA22, VLRA23 và VLRA-T3-06 đủ điều kiện chốt kỹ thuật trong phạm vi tuần5.**
Không còn blocker kỹ thuật đã ghi nhận đối với3 task này từ lần kiểm thử29/10.
Việc Team2 chưa nghiệm thu Golden không làm đổi kết quả của3 task độc lập.
Kết luận này dựa trên evidence đã chạy, không phải một lần chạy lại test trong lượt
xác nhận phân công. Chốt trạng thái Jira/gate chung vẫn theo quy trình duyệt của nhóm.

Đây là React → Java profile rag → PostgreSQL → FastAPI HTTP mock Team2, không gọi
retrieval/reranker/model/provider. Không dùng API JSON của profile mock cũ làm bằng
chứng SSE. Không đòi RAG live hoặc dataset v1 100–150 câu để thay điều kiện tuần5.

## 2. Expected / Actual theo task

| Task | Expected / DoD | Actual ngày29/10 | Kết luận |
| --- | --- | --- | --- |
| **VLRA22** | Public SSE đúng frame/no-store/55s, REST hội thoại, curl -N, disconnect an toàn | Maven125/125 gồm12 StreamApiTests; curl -N trả200, UTF-8 đúng, meta→delta→complete và header đúng. REST list/messages/delete đạt. HTTP test kiểm heartbeat, disconnect và replay không gọi AI lại; source có callback completion/error/timeout. | **Đạt kiểm chứng mock**; Java cần PostgreSQL và Python mock, không cần AI/index thật. |
| **VLRA23** | Chat/sidebar/parser; gửi tới mock backend, nối delta, bấm C1 mở Viewer đúng mẫu | FE72/72 và tsc/Vite build đạt; E2E10/10 qua Java thật và FastAPI mock. E02 hỏi đầu, E03 mở C1/đúng nguyên văn, E04 tiếp nối, E05 reload history, E07 thiếu căn cứ, E08–E09 lỗi/thử lại. Không uncaught JS exception. | **Đạt kỹ thuật mock**. Không coi một delta chứa answer là streaming token từ model. |
| **VLRA24** | Bộ chung30–50 câu, validation/dedup; P0 thành lập10, vốn/cổ đông8, quản trị8, giải thể4, thiếu dữ kiện10 | File chung Team2 có50 câu:49 answered/1 insufficient; validator50/50, không trùng ID/câu hỏi sau chuẩn hóa. Đã thay4 câu trùng ý và thu hẹp2 câu tổng hợp; không còn bản riêng Team3. Chưa có mapping xác nhận cơ cấu10/8/8/4/10. | **Team3 hoàn tất phần đóng góp/hợp nhất, chuyển Team2 kiểm chứng**. Chưa có kết luận nghiệm thu dataset từ Team2; cơ cấu49/1 còn khác DoD. |
| **VLRA-T3-06** | CORS/trace header, cấu hình môi trường, integration mock100% | 37/37 harness cấu hình; HTTP test/CORS và curl/REST7/7 đạt. Allowed origin localhost:5173 preflight200, origin ngoài danh sách403 không ACAO; request FE thực15173 tới BE18043 thành công. Meta/complete/UUID được kiểm contract76/76 +4 wire payload. | **Đạt local**; runner dùng Maven stub, không phải37 lần Spring startup thật. |

Các tên hook/controller trong task là phân rã trách nhiệm, không bắt buộc tạo class
trùng. Parser ở api/sse.ts và chatStream.ts, lifecycle ở hooks/useChat.ts; dùng project
hiện có. Callback onTimeout và cấu hình55s đã đối chiếu source; không chờ riêng đủ55s
để đo async timeout thực trong lượt này. HTTP test có nhánh timeout/lỗi/disconnect liên quan.

## 3. Dataset Phase1: kết quả hợp nhất và phần chưa đạt

| Tập dữ liệu hiện hành | Tổng | answered | insufficient_context | ID/câu hỏi trùng sau chuẩn hóa |
| --- | ---: | ---: | ---: | ---: |
| team2_rag/data/golden/golden_phase1_30cai.json |50|49|1|0/0 |

- Hợp nhất10 mẫu đóng góp vào nguồn chung; xóa3 file ground_truth riêng Team3.
- Không trùng nguyên văn không đủ chứng minh độc lập: đã thay4 cặp trùng ý và thu
  hẹp gold_016/021. Bảng50 ý định/record sửa/giữ và chunk nguồn tại
  [validation hợp nhất](vlra24-team3-golden/validation.md).
- Validator Team2 mặc định exit0; field/type/NFC/chunk/hash corpus/validator đạt.
  Giữ nguyên38/40 nội dung record chung (không tính author) và6/10 đóng góp;4 câu mới có căn cứ snapshot thật.
- Hiện1/10 mẫu insufficient theo DoD, **thiếu9**. Đã đạt trần50 nên cần thay/bố trí
  lại bộ chung nếu giữ cơ cấu nghiệm thu; không tiếp tục cộng thêm9 câu.
- Chưa có mapping xác nhận cho các nhóm P0 thành lập/vốn/quản trị/giải thể.
  Không tự đổi nhãn hoặc sửa yêu cầu nguồn để hợp thức hóa.
- VLRA24 là nhiệm vụ chung3 team; Team3 có2 thành viên ×5 câu. Phần10 mẫu đã tích
  hợp không đồng nghĩa Team3 phải tự hoàn thiện cả bộ. Không ghi danh tính.
- PASS format/rà trùng không thay review pháp lý/hiệu lực; không dùng fixture mock.
- Team2 phụ trách kiểm chứng dataset chung theo xác nhận mới của người dùng. Các
  kết quả validator tại đây là pre-handoff của Team3; phần cơ cấu/review được bàn
  giao rõ cho Team2, không coi là blocker còn phải triển khai của3 task khác.

## 4. Kiểm chứng mới, lệnh và evidence

### 4.1. Tổng hợp

| Kiểm tra | Kết quả |
| --- | --- |
| Maven Wrapper package |125/125, 0 fail/error/skip; gồm16 H2 +16 PostgreSQL,12 HTTP/SSE |
| Frontend unit |72/72, 0 fail |
| Frontend build |tsc -b + Vite production build PASS |
| Config runner |37/37; khôi phục env/location |
| Browser E2E |10/10; 0 uncaught JS exception; chính FastAPI mock Team2 |
| curl/CORS/REST |7/7: stream UTF-8, allowed/denied origin, list, messages, delete, deleted history |
| Public schema/semantic |76/76 (15 positive,61 negative),4 payload thật và binding PASS |
| Golden validators |Sau hợp nhất50/50 exit0; kiểm field/type/NFC/dedup/chunk, rà50 ý định; corpus/validator giữ nguyên |

Không cộng các nhóm con16/16/12 vào tổng125. Kết quả28/10 không tính là chạy mới;
mobile/latency/benchmark live không chạy lại và không gán PASS từ báo cáo cũ.

### 4.2. Môi trường và lệnh

Windows, JDK25/Spring Boot4.1.1/Maven Wrapper, Node24.21/React18/Vite,
Python3.12 với FastAPI/httpx/jsonschema, PostgreSQL18 cluster test riêng, Edge headless
profile riêng. Database: legal_rag_week5_20261029 tại127.0.0.1:55442.
FE15173/Java18043/FastAPI mock18044/CDP19242 để tránh cổng dịch vụ dùng chung.
CORS cấu hình riêng có cả localhost:5173 như task yêu cầu; không sửa .env thật.

Từ backend với JAVA_HOME trỏ JDK25:

```powershell
.\mvnw.cmd -B -ntp "-Dtest.postgres.url=jdbc:postgresql://127.0.0.1:55442/postgres" "-Dtest.postgres.user=vlra42" package
```

Từ frontend:

```powershell
npm.cmd test -- --reporter=json --outputFile=../backend/target/week5-acceptance-20261029/frontend-unit.json
npm.cmd run build
```

Từ gốc repository, Python kiểm thử đã có dependency:

```powershell
.\team3_fullstack\backend\src\test\powershell\RunLocalConfigurationTests.ps1 -JavaHome D:/Java/jdk-25
python -X utf8 team2_rag/validate_golden.py
python -X utf8 contracts/v0.1/validate_public_contract.py --wire-file team3_fullstack/backend/target/week5-acceptance-20261029/curl-wire.json
```

JAR được chạy profile rag với DB test/RAG_BASE_URL trỏ mock, không giữ transaction
trong lúc HTTP. Vite/Edge chạy ẩn rồi gọi frontend/tests/browser/vlra44-e2e.mjs với
FE_URL/BE_URL/RAG_PORT/CDP_URL/PYTHON/REPO_ROOT/EVIDENCE_DIR của môi trường test.
Harness tự bật/tắt FastAPI cho ca E01–E10, chưa phải provider thật.
Có runner [run-vlra44-e2e.ps1](../../run-vlra44-e2e.ps1) để tái lập;
port DB tùy chỉnh dùng database tạo trước, không dùng CreateDb của runner vốn giả định5432.

Ca curl dùng đúng curl.exe -N, request UTF-8 lưu file, Content-Type application/json,
Accept text/event-stream, Origin http://localhost:5173; dump header/body ra evidence.
Không in câu trả lời mock như lời tư vấn pháp luật hoặc đưa vào Golden.

### 4.3. Evidence và dọn môi trường

File sinh local ignored tại backend/target/week5-acceptance-20261029/:
summary.json, inventory.json, backend-package.log, frontend-unit.json/log,
frontend-build.log, config-runner.log, golden-team2.log, golden-team3.log,
e2e.log, e2e/results.json, e2e/browser.png, e2e/rag-mock.log,
curl-request.json, curl-headers.txt, curl-stream.txt, curl-wire.json,
http-smoke.json, contract-wire.json, cleanup.json và runtime logs.
Runner raw: backend/target/t01/runner-ebfde764655945e5af9eb29db1b3d8df/results.json.
XML chi tiết: backend/target/surefire-reports/TEST-*.xml.

Các file target có thể bị build/clean ghi đè; biên bản lưu expected/actual/lệnh/giới hạn
để review. Không đưa cache, .env, browser profile hoặc danh tính vào Git.
Đã dừng đúng PID dịch vụ đã mở và cluster test riêng, xác nhận cả5 cổng test đóng.
Không thay dịch vụ PostgreSQL khác; DB kiểm thử riêng còn để tái lập.

## 5. Kết luận nghiệm thu và bước tiếp theo

- **G2 về kỹ thuật mock: đạt kiểm chứng local.** Phê duyệt mốc/Jira vẫn thuộc nhóm.
- **VLRA22/VLRA23/VLRA-T3-06 đủ điều kiện chốt kỹ thuật tuần5 theo phạm vi mock.**
- **VLRA24: Team3 đã hoàn tất đóng góp/hợp nhất; Team2 kiểm chứng dataset chung.**
  Chưa có xác nhận nghiệm thu từ Team2, không tự đóng toàn bộ VLRA24 thay họ.
- Bộ chung đã hợp nhất50 mẫu,49 answered/1 insufficient. Cần điều phối cơ cấu để
  đủ10 insufficient, mapping P0 và review căn cứ/phiên bản. Không đổi nhãn khi nội
  dung vẫn có căn cứ; không cộng thêm mẫu vượt trần50.
- [Validation hợp nhất](vlra24-team3-golden/validation.md) lưu kết quả mới. Raw
  inventory/log audit cũ40/13 và evidence subset10 không bị ghi đè thành kết quả50.
  Evidence mới: backend/target/week5-golden-merge-20261029/. Không chạy lại FE/BE vì
  không đổi source/config; commit theo yêu cầu bàn giao, không push.

## 6. Nội dung báo người điều phối

Đã hợp nhất đóng góp10 câu Team3 vào Golden chung tại Team2, tổng50 câu
(49 answered/1 insufficient_context); xóa bản riêng. Rà nội dung và xử lý4 câu trùng
ý, thu hẹp2 câu tổng hợp; validator PASS50/50. Bộ chung vẫn thiếu9 mẫu insufficient
so với DoD tuần5, chưa có mapping P0/review pháp lý được xác nhận. Vì đã đạt trần50,
nhóm cần chốt các mẫu được thay để đủ cơ cấu, không đổi nhãn tùy ý hoặc cộng thêm9.
Đây là điều phối chung3 team; Team3 đã đóng góp10 theo chỉ tiêu2 thành viên ×5.

Phân công bàn giao đã xác nhận: Team2 kiểm chứng Golden và xử lý kết luận cơ cấu/
review chung; Team3 không tiếp tục tự nghiệm thu dataset thay Team2. Các task kỹ
thuật còn lại của tuần5 đủ điều kiện chốt trong phạm vi mock đã kiểm chứng.

**Chốt bàn giao tuần5:** Người dùng yêu cầu nghiệm thu và commit ngày29/10/2026.
VLRA22, VLRA23 và VLRA-T3-06 chốt kỹ thuật phạm vi mock theo evidence trên;
VLRA24 hoàn tất phần đóng góp/hợp nhất của Team3, chuyển Team2 kiểm chứng.
Không tự cập nhật Jira, xác nhận gate chung đã duyệt hoặc mở PR/push trong lượt này.
Metadata author chứa danh tính người dùng đã chuyển sang vai trò theo yêu cầu riêng tư.
