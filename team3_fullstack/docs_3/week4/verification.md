# Biên bản nghiệm thu lại Team 3 — Tuần 4

**Ngày kiểm tra:** 29/10/2026 (Asia/Saigon), thay kết luận ngày 28/10.
**Căn cứ:** [ARCHITECTURE](../../../docs/ARCHITECTURE.md) §2/§3/§6;
[CODING_CONVENTIONS](../../../docs/CODING_CONVENTIONS.md) §1/§2/§6/§7;
[nhiệm vụ tuần 4](tasks.md). G1 là mốc Document Baseline trong nhiệm vụ tuần,
không phải các cổng chất lượng Recall/Citation của ARCHITECTURE §8.2.B.
**Source:** `62c3556bab16e106e2e6ff29b0280a96fb738146`, cùng tài liệu chưa commit.
Không sửa code ứng dụng/test hoặc dataset; public contract được sửa theo quyết định.
Commit local được yêu cầu, chưa push/PR hoặc merge develop.

> Cập nhật đường dẫn ngày29/10/2026: Golden hiện hợp nhất50 mẫu tại
> `team2_rag/data/golden/golden_phase1_30cai.json`; thư mục riêng Team3 đã xóa.
> Số liệu13/40 bên dưới là evidence tuần4, không phải kiểm chứng bộ50.
> Kết quả hiện hành: [tuần5](../week5/vlra24-team3-golden/validation.md).

## 1. Kết luận

**Đủ điều kiện nghiệm thu G1 nội bộ theo phần kỹ thuật và xác nhận nhóm.** Sơ đồ DB
đã đồng bộ; schema public SSE bổ sung tại contracts/v0.1/ đã kiểm chứng. Đại diện
Team 3 xác nhận dùng ERD theo baseline và GitHub đã cưỡng chế giới hạn push main.
Bộ thay đổi được bàn giao bằng commit local theo yêu cầu; **chưa push/PR/merge develop**.
Kết luận này không là release, nghiệm thu các tuần sau hoặc tuyên bố đã merge develop.

Đại diện Team 3 xác nhận trực tiếp ngày 29/10: wireframe đã duyệt, không cần nguồn
hoặc danh tính bổ sung; UI có thể tiếp tục điều chỉnh. Phần đóng góp Golden đã làm
trước đó trong ground_truth. Trưởng nhóm duyệt, thành viên không được push trực tiếp
main; hoàn tất tuần thì tự nghiệm thu trong team rồi merge develop. Giữ quy trình PR
trong CODING_CONVENTIONS; không suy cho phép bỏ review hoặc tự thay quyền repository.

Không cần RAG/LLM thật hoặc dataset 100–150 câu để nghiệm thu riêng tuần 4. Xác nhận
đóng góp/validator không tự là review pháp lý của dataset hoặc nghiệm thu tuần 5/7.
Toàn bộ hồ sơ mới dùng vai trò/ngày, không tên, tài khoản hoặc danh tính cá nhân.

## 2. Đối chiếu từng task và DoD

| Task | Expected / DoD | Actual và bằng chứng | Kết luận |
| --- | --- | --- | --- |
| **VLRA-T3-01** | ERD/DDL và thiết kế phù hợp ARCHITECTURE | ERD chung 4 bảng/36 cột, tasks §3.1 dẫn đúng DDL; 16 ca H2 +16 ca PostgreSQL đạt. Người dùng xác nhận dùng bản ERD này theo baseline ngày29/10. | Đạt kỹ thuật/tài liệu và xác nhận thiết kế. |
| **VLRA-T3-02** | Public SSE/camelCase/ID số; wireframe được nhóm duyệt | [Public schema hiện hành](../../../contracts/v0.1/CONTRACT.md) có đủ payload; 76 ca contract đạt, 4 payload thực/binding đạt; chạy lại 12 test HTTP/SSE đạt. Wireframe được đại diện Team 3 xác nhận duyệt ngày 29/10. | Đạt kỹ thuật và xác nhận wireframe; contract mới chờ bàn giao review. |
| **VLRA-T3-03** | State transition, IDEM-01–12, khóa/recovery tránh race | [Thiết kế hội thoại](../../../docs/team3_fullstack/conversation-design.md) có state/12 ca/row lock/tombstone/recovery; test lưu trữ đã đạt. | Đạt DoD thiết kế; job recovery định kỳ là khoảng thiếu triển khai, không tự coi đã có. |
| **VLRA-T3-04** | FE/BE build, skeleton develop, Git/PR/protection | Backend125/125, FE72/72 và build đạt; refs main/develop, origin/develop 3c8ec8c có skeleton, PR #42 đã merge; PR template có. Người dùng xác nhận quy trình trưởng nhóm review/nghiệm thu team/merge develop và giới hạn push main. Người dùng xác nhận GitHub đã chặn bằng cấu hình quyền/quy tắc; không phải kết quả đọc rules API. | Đạt build/skeleton, quy trình và enforcement theo xác nhận người dùng; không tự đổi quyền. |
| **VLRA-T3-05** | Format/validator và tổ chức đóng góp P0 5–10 câu/người | ground_truth có 13 mẫu, validator đạt; Team 2 có40 mẫu đạt. Người dùng xác nhận phần đóng góp này đã làm trước đó tại ground_truth. Không tạo lại phân công có danh tính hoặc suy công việc từ author. | Đạt theo xác nhận trực tiếp và evidence format hiện có; không tự xác nhận pháp lý/cơ cấu Phase1 tuần5. |

Mã VLRA-T3-* là phân rã nội bộ, không đổi thành ticket Jira mới. Quyết định trực tiếp
của người dùng là nguồn xác nhận trong lượt này; không đòi thêm nguồn duyệt wireframe
hoặc khôi phục danh tính cá nhân chỉ để đánh dấu checklist.

## 3. Kiểm chứng chạy mới ngày 29/10

### 3.1. Môi trường và kết quả

Windows; JDK 25 / Spring Boot 4.1.1 / Maven Wrapper; Node 24.21 / Vitest / TypeScript /
Vite; Python 3.12 với jsonschema; PostgreSQL 18 riêng tại 127.0.0.1:55442.
16 ca PostgreSQL dùng schema UUID riêng và tự xóa sau mỗi ca, không dùng DB nghiệp vụ.

Chọn review tài liệu/source, unit, HTTP integration và tích hợp DB đồng thời; không
thêm testcase trùng bộ hiện có. Không chạy lại E2E/mobile/LLM thật trong lượt này:
DoD thiết kế tuần 4 cần duyệt wireframe, test trình duyệt không thay phê duyệt đó.
E2E 10/10 ngày 28/10 **không tính** là kết quả chạy mới hôm nay.

| Kiểm tra | Expected | Actual | Kết quả |
| --- | --- | --- | --- |
| Maven package | Build thành công, không lỗi/bỏ qua | 125 test, 0 fail/error/skip; BUILD SUCCESS | PASS |
| Lưu trữ/concurrency | DDL/transaction/khóa/replay đúng assertions | H2 16/16, PostgreSQL thật 16/16 | PASS |
| Public HTTP/SSE | Frame, ID/casing, heartbeat, replay, lỗi an toàn/CORS đúng | StreamApiTests 12/12; gồm meta sau commit, heartbeat, insufficient không delta/citation, RuntimeException an toàn HTTP 500/replay | PASS |
| Frontend unit/build | Không test lỗi; TypeScript/Vite build được | 72/72; tsc -b và Vite build thành công | PASS |
| Script cấu hình local | Ưu tiên cấu hình/giá trị lỗi/khôi phục môi trường đúng | 37/37 | PASS, Maven được stub; không phải 37 lần Spring startup |
| Golden format/chunk ID | Đủ field, trạng thái/ID/chunk hợp lệ | Team 2: 40/40; Team 3: 13/13 (12 answered, 1 insufficient_context) | PASS format; không xác nhận pháp lý |
| Schema syntax | Schema Draft 2020-12 hợp lệ | 6/6 schema trong contracts/v0.1 qua check_schema | PASS cú pháp; framing/semantics kiểm bổ sung |
| Payload public hiện hành | Schema request đúng casing/ID của SSE | query_request gốc nhận camelCase/ID số; request snake_case legacy bị từ chối có chủ đích | PASS theo quyết định sửa trực tiếp file gốc |
| Tài liệu | Link local tồn tại, JSON parse, ERD đủ cột/IDEM đủ ca | 10 file; 3 ví dụ JSON; ERD 4 bảng/36 cột; IDEM-01–12 đủ; số link trong summary.json | PASS phần đã kiểm; chưa render Mermaid/kiểm anchor |

Các nhóm 16 + 16 + 12 là **nhóm con của 125**, không cộng thêm vào tổng.
Bộ hiện hành có6 schema: query_request sửa trực tiếp, chat_stream bổ sung và4 schema
nội bộ giữ nguyên. **76/76 ca contract**,4 wire payload/binding đạt. Regression sau chuyển
file: **Java28/28** (SSE12 + JSON legacy16), **Team2 75 test +24 subtest đạt**. Đây là
chạy lại kiểm tra liên quan, không cộng thêm vào tổng125. Không cần model/provider live.

### 3.2. Lệnh đã chạy

Từ backend, đặt JAVA_HOME trỏ JDK 25 rồi chạy:

```powershell
.\mvnw.cmd -B -ntp "-Dtest.postgres.url=jdbc:postgresql://127.0.0.1:55442/postgres" "-Dtest.postgres.user=vlra42" package
```

Từ frontend:

```powershell
npm.cmd test -- --reporter=json --outputFile=../backend/target/week4-acceptance-20261029/frontend-unit.json
npm.cmd run build
```

Từ gốc repository, dùng Python đã cài dependency:

```powershell
.\team3_fullstack\backend\src\test\powershell\RunLocalConfigurationTests.ps1 -JavaHome D:/Java/jdk-25
python -X utf8 team2_rag/validate_golden.py
```

DB test phải sẵn sàng trước lệnh Maven; không trỏ vào dữ liệu thật.
Lượt Maven đầu bị PowerShell ErrorAction Stop ngắt khi nhận cảnh báo stderr Mockito.
Lượt quyết định chạy qua cmd, stdout/stderr ghi log và kiểm exit code 0; không sửa test.

### 3.3. Evidence và giới hạn

Evidence local ignored: `team3_fullstack/backend/target/week4-acceptance-20261029/`:
backend-package.log, frontend-unit.json/log, frontend-build.log, config-runner.log,
golden-team2.log, golden-team3.log, summary.json và check-evidence.py.
Chi tiết từng test: backend/target/surefire-reports/TEST-*.xml.
Harness cấu hình: backend/target/t01/runner-6f4fde6ddad94c198d7ee2c9275e1b4f/results.json.
Đây là file sinh local có thể bị clean/build ghi đè; biên bản giữ kết quả/lệnh/giới hạn,
không tự thêm cache, build hoặc browser profile vào Git.

GitHub connector xác nhận PR #42 merged, base develop, merge commit
`0aee92e7cbda5d21e46e767e4f0b8ec7cf89a40c`; timeline review trả về rỗng.
Connector hiện không có công cụ đọc branch protection; không suy protection từ CODEOWNERS.
Không fetch/merge code mới: snapshot origin/develop local vẫn là `3c8ec8c`.
PostgreSQL test được dừng sau kiểm tra; không để môi trường nghiệm thu chạy nền.

## 4. Xử lý sai lệch và điều kiện còn lại

| Mã | Kết quả hiện tại | Phần còn lại |
| --- | --- | --- |
| **W4-01** | tasks §3.1 dẫn ERD đúng DDL: không FK receipt, snapshot TEXT/JSON, tombstone, citation PK kép. | Đã xác nhận dùng bản thiết kế chi tiết theo baseline ngày29/10, không đổi DB. |
| **W4-02** | Đã sửa trực tiếp query_request tại đúng tên; chat_stream bổ sung SSE, fixture/validator cùng v0.1. Bỏ bộ trùng; schema nội bộ không đổi. | 76 ca contract, 28 Java API và75 test Team2/24 subtest đạt. Không đổi runtime; schema request không còn kiểm JSON legacy. |
| **W4-03** | Đại diện Team 3 xác nhận wireframe đã duyệt, không cần nguồn khác; UI được tiếp tục điều chỉnh phù hợp. | Không còn chặn phê duyệt wireframe; cập nhật tài liệu/kiểm tra phần UI khi thay đổi sau này. |
| **W4-04** | Quy trình trưởng nhóm review, nghiệm thu nội bộ rồi merge develop, thành viên không push trực tiếp main đã được xác nhận. | Người dùng xác nhận giới hạn push main đã được GitHub cưỡng chế, không đòi ảnh chụp hoặc danh tính. CODEOWNERS có đường dẫn /src/team3_fullstack/ không khớp /team3_fullstack/; đây là hỗ trợ review cần sửa riêng, không tự thêm thành DoD bắt buộc hoặc ghi owner cá nhân. Chưa sửa .github/quyền remote. |
| **W4-05** | Người dùng xác nhận phần đóng góp đã làm trong ground_truth; có file/validator thực tế. | Không yêu cầu lập bảng hồi tố chứa tên. Thẩm định pháp lý/cơ cấu release Phase1 theo nhiệm vụ tuần sau. |

Khoảng thiếu implementation đã biết, **tách khỏi DoD thiết kế tuần 4**: recovery hiện
chạy startup/đọc/accept/delete và xử lý stale >60s, chưa có scheduler định kỳ 30s.
RequestParser chưa chuẩn hóa NFC tường minh; validator legal ID vẫn chấp nhận chữ hoa
so với quy chuẩn chữ thường. Theo dõi ở nhiệm vụ triển khai liên quan, không nghiệm thu
chúng bằng test thiết kế/G1 và không sửa code trong lượt kiểm tra này.

## 5. Bổ sung contract và xác nhận ngày 29/10

Hồ sơ Spec Kit tại [vlra-t3-02-public-sse-contract](vlra-t3-02-public-sse-contract/spec.md):
specify → clarify → plan → tasks → analyze → làm rõ → implement → validate.
[Validation](vlra-t3-02-public-sse-contract/validation.md) ghi mapping yêu cầu/task,
kết quả test, bảo toàn checksum, kiểm tra privacy/link và giới hạn.

Evidence mới tại backend/target/week4-contract-20261029/: preservation.json,
pre-schema.log, stream-api.log, contract-cases.json, contract-wire.json,
cli-exit-codes.json. Payload thực từ backend/target/vlra41-contract-examples.json.
Trước khi thêm schema, validator thiếu schema exit2 đúng; fixture lỗi trên bản copy
trong target exit1, thiếu wire exit2, không sửa fixture public để làm test đạt.

Chỉ query_request, CONTRACT và contracts/README đổi trong bộ file được snapshot;
4 schema nội bộ, .github, code/test ứng dụng, dataset và tài liệu Team1/2 giữ nguyên.
Không thêm tên/tài khoản/danh tính vào schema, fixture, hồ sơ hoặc xác nhận duyệt.
Không chạy lại full Maven/FE chỉ vì thêm tài liệu/schema; dùng lại evidence125/72/37
của code không đổi và chạy riêng HTTP/contract bị ảnh hưởng.

## 6. Checklist khép nghiệm thu

- [x] Đồng bộ ERD/DDL trong nhiệm vụ, sửa link Article schema sai.
- [x] ERD chi tiết được đại diện Team 3 xác nhận dùng theo baseline ngày29/10.
- [x] Sửa query_request gốc; bổ sung chat_stream đúng vai trò trong v0.1, không giữ bộ public trùng; kiểm positive/negative và wire thực.
- [x] Ghi nhận wireframe đã duyệt theo xác nhận người dùng, không yêu cầu danh tính/nguồn khác.
- [x] Ghi nhận đóng góp Golden đã thực hiện trong ground_truth, không tự dựng bảng tác giả.
- [x] Ghi quy trình review/nghiệm thu nội bộ/merge develop và giới hạn push main theo xác nhận.
- [x] Giới hạn push main được GitHub cưỡng chế theo xác nhận ngày29/10; ghi nguồn xác nhận, không giả là đã đọc rules API.
- [x] Hash155/155 file ngoài phạm vi giữ nguyên; 3 file public request/tài liệu đổi có chủ đích;37 file Markdown/218 link/9 anchor không lỗi; privacy/cú pháp/diff đạt, task7/7 hoàn tất.
- [x] Chuẩn bị bộ tài liệu/schema để commit theo yêu cầu, chia theo phần công việc.
- [ ] Push/PR/review/merge develop: chưa thực hiện; commit local không đồng nghĩa publish.

Không dùng tên, tài khoản hoặc nguồn nhận diện cá nhân để chứng minh checklist.
