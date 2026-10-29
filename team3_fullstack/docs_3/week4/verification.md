# Biên bản nghiệm thu Team 3 — Tuần 4

**Ngày kiểm tra:** 30/10/2026 (Asia/Saigon).
**Căn cứ:** [ARCHITECTURE](../../../docs/ARCHITECTURE.md) §2/§3/§6;
[CODING_CONVENTIONS](../../../docs/CODING_CONVENTIONS.md) §1/§2/§6/§7;
[nhiệm vụ tuần 4](tasks.md). G1 là mốc Document Baseline trong nhiệm vụ tuần,
không phải các cổng chất lượng Recall/Citation của ARCHITECTURE §8.2.B.
**Source:** `ac358283eb6bc7d95ec3ef589dd22639b10cebb6`.

## 1. Kết luận

**Đủ điều kiện nghiệm thu G1 nội bộ theo phần kỹ thuật và xác nhận nhóm.**

## 2. Đối chiếu từng task và DoD

| Task | Expected / DoD | Actual và bằng chứng | Kết luận |
| --- | --- | --- | --- |
| **VLRA-T3-01** | ERD/DDL và thiết kế phù hợp ARCHITECTURE | ERD chung 4 bảng/36 cột, tasks §3.1 dẫn đúng DDL; 16 ca H2 +16 ca PostgreSQL đạt. Người dùng xác nhận dùng bản ERD này theo baseline ngày29/10. | Đạt kỹ thuật/tài liệu và xác nhận thiết kế. |
| **VLRA-T3-02** | Public SSE/camelCase/ID số; wireframe được nhóm duyệt | [Public schema hiện hành](../../../contracts/v0.1/CONTRACT.md) có đủ payload; 76 ca contract đạt, 4 payload thực/binding đạt; chạy lại 12 test HTTP/SSE đạt. Wireframe được đại diện Team 3 xác nhận duyệt ngày 29/10. | Đạt kỹ thuật và xác nhận wireframe; contract mới chờ bàn giao review. |
| **VLRA-T3-03** | State transition, IDEM-01–12, khóa/recovery tránh race | [Thiết kế hội thoại](../../../docs/team3_fullstack/conversation-design.md) có state/12 ca/row lock/tombstone/recovery; test lưu trữ đã đạt. | Đạt DoD thiết kế; còn thiếu triển khai job recovery định kỳ. |
| **VLRA-T3-04** | FE/BE build, skeleton develop, Git/PR/protection | Backend125/125, FE72/72 và build đạt; skeleton có trên develop; quy trình review và bảo vệ main đã được xác nhận. | Đạt. |
| **VLRA-T3-05** | Format/validator và đóng góp P0 5–10 câu/người | Format/validator đã ban hành; Team3 hoàn tất10 câu đóng góp và hợp nhất vào bộ chung50 câu. | Đạt phạm vi đóng góp; Team2 kiểm chứng bộ chung. |

## 3. Kiểm chứng

### 3.1. Môi trường và kết quả

Windows; JDK 25 / Spring Boot 4.1.1 / Maven Wrapper; Node 24.21 / Vitest / TypeScript /
Vite; Python 3.12 với jsonschema; PostgreSQL 18 riêng tại 127.0.0.1:55442.
16 ca PostgreSQL dùng schema UUID riêng và tự xóa sau mỗi ca, không dùng DB nghiệp vụ.

| Kiểm tra | Expected | Actual | Kết quả |
| --- | --- | --- | --- |
| Maven package | Build thành công, không lỗi/bỏ qua | 125 test, 0 fail/error/skip; BUILD SUCCESS | PASS |
| Lưu trữ/concurrency | DDL/transaction/khóa/replay đúng assertions | H2 16/16, PostgreSQL thật 16/16 | PASS |
| Public HTTP/SSE | Frame, ID/casing, heartbeat, replay, lỗi an toàn/CORS đúng | StreamApiTests 12/12; gồm meta sau commit, heartbeat, insufficient không delta/citation, RuntimeException an toàn HTTP 500/replay | PASS |
| Frontend unit/build | Không test lỗi; TypeScript/Vite build được | 72/72; tsc -b và Vite build thành công | PASS |
| Script cấu hình local | Ưu tiên cấu hình/giá trị lỗi/khôi phục môi trường đúng | 37/37 | PASS, Maven được stub; không phải 37 lần Spring startup |
| Golden format/chunk ID | Đủ field, trạng thái/ID/chunk hợp lệ | Bộ chung50/50 đạt | PASS format; Team2 kiểm chứng nội dung |
| Schema syntax | Schema Draft 2020-12 hợp lệ | 6/6 schema trong contracts/v0.1 qua check_schema | PASS cú pháp; framing/semantics kiểm bổ sung |
| Payload public hiện hành | Schema request đúng casing/ID của SSE | query_request gốc nhận camelCase/ID số; request snake_case legacy bị từ chối có chủ đích | PASS theo quyết định sửa trực tiếp file gốc |
| Tài liệu/thiết kế | Link local, JSON, ERD đủ cột/IDEM đủ ca | ERD4 bảng/36 cột và IDEM-01–12 đủ; đường dẫn/anchor và JSON được kiểm | PASS phần đã kiểm; chưa render Mermaid |

Các nhóm 16 + 16 + 12 là **nhóm con của 125**, không cộng thêm vào tổng.
Bộ hiện hành có6 schema: query_request sửa trực tiếp, chat_stream bổ sung và4 schema
nội bộ giữ nguyên. **76/76 ca contract**,4 wire payload/binding đạt. Hồi quy API Java **28/28** (SSE12 + JSON legacy16) nằm trong tổng125.
Nhóm API/mock/pipeline/reranker/Hybrid nội bộ: **48 test +81 subtest đạt**.
Bộ mở rộng Team2: **388 đạt,1 lỗi Golden,147 subtest đạt**; lỗi `gold_041`
được theo dõi tại [nghiệm thu tuần5](../week5/verification.md#3-dataset-phase1-kết-quả-hợp-nhất-và-phần-chưa-đạt).

### 3.2. Evidence và giới hạn

Bằng chứng tại `backend/target/final-acceptance-20261030/`: backend-package-rerun.log,
frontend-unit.json, frontend-build.log, config-runner.log, contract.json,
extra-checks.json, internal-regression-rerun.log và summary.json.
Chi tiết JUnit tại thư mục `junit/`. Kiểm tra local/mock và PostgreSQL thật;
chưa nghiệm thu chất lượng câu trả lời từ LLM hoặc render Mermaid.

## 4. Xử lý sai lệch và điều kiện còn lại

| Mã | Kết quả hiện tại | Phần còn lại |
| --- | --- | --- |
| **W4-01** | tasks §3.1 dẫn ERD đúng DDL: không FK receipt, snapshot TEXT/JSON, tombstone, citation PK kép. | ERD đã được xác nhận. |
| **W4-02** | query_request và chat_stream cùng fixture/validator tại v0.1 đạt kiểm chứng. | Contract cần bàn giao review; query_request hiện hành kiểm request SSE, không kiểm request JSON legacy. |
| **W4-03** | Wireframe đã được Team 3 duyệt. | Cập nhật tài liệu và kiểm tra UI khi thiết kế thay đổi. |
| **W4-04** | Quy trình review, nghiệm thu nội bộ, merge develop và bảo vệ main đã xác nhận. | CODEOWNERS cần khớp đường dẫn /team3_fullstack/. |
| **W4-05** | Format/validator và phần đóng góp Team3 đã hoàn tất. | Phối hợp Team2 thống nhất ID gold_041 giữa Phase1/fixture; Team2 kiểm chứng nội dung/cơ cấu. |

Backlog triển khai: recovery định kỳ, chuẩn hóa NFC tường minh và kiểm legal ID chữ thường.

## 5. Contract và xác nhận thiết kế

[Kiểm chứng contract](vlra-t3-02-public-sse-contract/validation.md).

76/76 ca schema/semantic,4 payload thực và3 đường lỗi CLI đạt.
ERD4 bảng/36 cột khớp DDL; thiết kế đủ12 ca IDEM; ERD và wireframe đã được xác nhận.
Bằng chứng: contract.json, extra-checks.json và junit/ trong thư mục nghiệm thu hiện hành.

## 6. Checklist khép nghiệm thu

- [x] ERD/DDL và tham chiếu Article schema khớp baseline.
- [x] ERD chi tiết được đại diện Team 3 xác nhận dùng theo baseline ngày29/10.
- [x] query_request/chat_stream tại v0.1 đạt kiểm tra positive/negative và payload thực.
- [x] Wireframe được Team 3 xác nhận duyệt.
- [x] Team3 đóng góp10 câu Golden, đã hợp nhất vào bộ chung50 câu.
- [x] Ghi quy trình review/nghiệm thu nội bộ/merge develop và giới hạn push main theo xác nhận.
- [x] Giới hạn push main được GitHub cưỡng chế theo xác nhận ngày29/10.
