# Validation — đồng bộ public contract tại v0.1

**Ngày:** 29/10/2026. **Source kiểm thử:** 62c3556 và thay đổi tài liệu/schema local.
**Kết luận:** hoàn tất 7 task, đủ kiểm chứng local; commit cả đợt tài liệu đã được
người dùng yêu cầu, chưa push/PR. Không ghi danh tính cá nhân vào hồ sơ hoặc fixture.

## Quy trình và phạm vi

Thực hiện specify → clarify → plan → tasks → analyze chỉ đọc → làm rõ → implement
→ validate trong đúng thư mục tuần. Quyết định mới: sửa trực tiếp query_request.schema.json,
giữ tên/vị trí; thêm chat_stream.schema.json cho phần SSE chưa có. Bộ public trùng đã xóa.
Spec/plan/tasks được cập nhật trước sửa; không tạo một bộ spec khác. Checklist8/8.

Analyze sau thay phạm vi: FR001–006/SC001–003 đều có task, 7 task, coverage100%,
không CRITICAL/HIGH, không task ngoài yêu cầu. Làm rõ maxLength sau strip, schema không
kiểm raw SSE/cross-payload và integer token khác integer toán học1.0.
Người dùng cho phép schema request không còn kiểm JSON legacy. Runtime legacy giữ
nguyên; không tự tuyên bố tương thích schema với request cũ.

| Yêu cầu | Task | Evidence |
| --- | --- | --- |
| FR-001/002 | T002/T003/T004 | request schema, stream schema, 76 ca, 4 wire payload |
| FR-003 | T002/T003/T004 | semantic marker/citation/binding; HTTP/FE test riêng cho framing |
| FR-004 | T001/T003/T006 | Chỉ query_request/CONTRACT/index đổi trong snapshot; schema nội bộ/code giữ nguyên |
| FR-005 | T005/T006 | Xác nhận theo vai trò/ngày; privacy scan và review |
| FR-006 | T002/T004/T006 | expected/actual, exit0/1/2, lệnh tái lập |
| SC-001/002/003 | T001–T007 | Contract/API/Team2 regression, bảo toàn file và hồ sơ trung thực |

## Expected / actual

Môi trường kiểm thử riêng: JDK25/Maven Wrapper, Python3.12/jsonschema/FastAPI/httpx.
Bổ sung pytest theo requirements-dev đã có của Team2 vào venv riêng; không đổi dependency
repository. Lượt pytest đầu thiếu công cụ; sau cài đặt, chạy lại đạt.

| Kiểm tra | Expected | Actual |
| --- | --- | --- |
| Public contract | Schema hợp lệ, positive nhận/negative từ chối | 76/76: 15 positive, 61 negative; exit0 |
| Wire HTTP mới | Request/meta/delta/complete hợp schema và binding | 4 payload, binding PASS |
| Java API regression | SSE và JSON legacy vẫn chạy theo test hiện có | StreamApiTests12/12 + MockApiTests16/16 =28/28, 0 fail/error/skip |
| Team2 regression | API thực với fake pipeline/mock còn hợp schema nội bộ | 75 test +24 subtest đạt; không provider/model/network |
| CLI thất bại | Fixture lỗi/thiếu schema/thiếu wire không được PASS | Bản copy target: exit1/2/2 đúng |
| File ngoài phạm vi | Không sửa internal schema/code/test/dataset/Team1/2 | 155/155 hash giữ nguyên; 3 file query_request/CONTRACT/contracts README đổi có chủ đích |
| Resolver | Không truy cập mạng để resolve schema | Registry local cho request + stream, wire validation đạt |

28 test Java là chạy lại nhóm trong tổng125 đã đạt trước đó; không cộng thành153.
Không chạy lại FE/full PostgreSQL do code/config không đổi. Schema không xác nhận
RAG live, tính đúng pháp lý, source truy cập được hoặc chất lượng retrieval.

## Lệnh chạy lại

Từ gốc repository, dùng Python có jsonschema và pytest theo requirements-dev:

```powershell
python -X utf8 contracts/v0.1/validate_public_contract.py --wire-file team3_fullstack/backend/target/vlra41-contract-examples.json
python -X utf8 -m pytest -q team2_rag/tests/test_internal_query_api.py tests/test_team2_mock.py tests/test_team2_api.py
cd team3_fullstack/backend
.\mvnw.cmd -B -ntp -Dtest=StreamApiTests,MockApiTests test
```

Để có wire mới phải chạy Maven trước lệnh --wire-file. Maven dùng JDK25, thu log qua cmd
để stderr cảnh báo không làm PowerShell báo nhầm lỗi. Script --report-file lưu JSON local.

Evidence ignored: backend/target/week4-contract-20261029/: preservation.json,
contract-wire.json, cli-exit-codes.json, migration-api.log, migration-team2.log,
pytest-setup.log, final-checks.json. Payload: backend/target/vlra41-contract-examples.json.
Hash hai schema được ghi trong contract-wire.json, không dùng hash bộ file đã bỏ.

## Bàn giao và giới hạn

Wireframe/ERD và GitHub chặn push main được ghi theo xác nhận trực tiếp của đại diện
Team3, không giả thành kết quả đọc rules API; không ghi người/tài khoản và không sửa
CODEOWNERS theo một danh tính suy đoán. Golden theo xác nhận đã làm, không suy ra review luật.
NFC/legal ID runtime còn lệch mức chặt baseline là backlog implementation, không nới
schema để hợp thức hóa và không sửa code trong lần này.

Kiểm tra cuối: **37 file Markdown, 218 tham chiếu local, 9 anchor: không lỗi**;
6 schema hợp cú pháp, privacy scan/review đạt; không còn bộ public trùng.
Đánh dấu task theo evidence và commit theo nhóm:
contract, thiết kế chung, hồ sơ tuần/dọn tài liệu cũ. Commit local không đồng nghĩa
đã push, tạo PR hoặc merge develop. Phạm vi này không sửa code nghiệp vụ của team nào.
