# Tasks: Public SSE contract tuần 4

**Input:** [spec](spec.md), [plan](plan.md). Mã task nội bộ T3-02, không tạo ticket Jira mới.
Chỉ đánh dấu sau có evidence. Commit theo yêu cầu người dùng; không push hoặc thêm danh tính.

## Phase 1 — Setup

- [x] T001 Lưu hash trước triển khai cho contracts/v0.1/, .github/, code FE/BE và ground_truth vào backend/target/week4-contract-20261029/preservation.json; đối chiếu ranh giới FR-004.

## Phase 2 — US1: Kiểm đúng phiên bản (P1)

- [x] T002 [US1] Tạo contracts/v0.1/public_examples.json và validate_public_contract.py; có positive/negative cho casing/field, UUIDv4, integer1..9007199254740991, question1–2000 code point, UTC, answered1–10 citation/insufficient rỗng và semantic marker/binding; dùng bản copy target để xác nhận thiếu schema không báo PASS (FR-001/002/003/006).
- [x] T003 [US1] Sửa contracts/v0.1/query_request.schema.json; thêm chat_stream.schema.json (Draft2020-12, request tách payload SSE Meta/Delta/Complete/ErrorResponse/PublicCitation), additionalProperties=false; complete8/citation9 field, nullable clause/point bắt buộc key; legal ID lowercase; cập nhật contracts/README.md và contracts/v0.1/CONTRACT.md với mapping/cảnh báo legacy; bỏ bộ public trùng vừa tạo sau kiểm đủ nội dung (FR-001/002/003/004).
- [x] T004 [US1] Chạy validate_public_contract.py và StreamApiTests/MockApiTests qua Maven Wrapper/JDK25 cùng regression API Team2; dùng --wire-file backend/target/vlra41-contract-examples.json mới, lưu expected/actual tại validation.md (FR-006, SC-001/002).

## Phase 3 — US2: Bàn giao trung thực (P2)

- [x] T005 [US2] Cập nhật docs/team3_fullstack/public-api-specification.md, frontend-design.md và docs_3/week4/verification.md với link schema, xác nhận duyệt/Golden/quy trình Git theo vai trò; không bịa reviewer hoặc cấu hình rules đã kiểm (FR-005, SC-003).
- [x] T006 [US2] So hash schema nội bộ/.github/source/dataset; query_request, CONTRACT và contracts/README đổi có chủ đích; kiểm link/anchor/privacy, lỗi validator trả exit khác0, ghi kết quả vào validation.md (FR-004/005/006, SC-002/003).

## Phase 4 — Tổng hợp

- [x] T007 Ghi kết quả analyze, những việc đã sửa/còn mở tại validation.md; cập nhật task checkbox và biên bản docs_3/week4/verification.md theo bằng chứng (SC-001/002/003).

## Dependencies & strategy

T001 → T002 → T003 → T004 → T005 → T006 → T007. Không đánh dấu [P]: schema và
validator/fixture đồng phụ thuộc, tài liệu cuối tham chiếu kết quả. US1 kiểm độc lập
bằng validator; US2 kiểm độc lập bằng hash/link/privacy và đối chiếu xác nhận người dùng.
MVP là US1; hoàn tất US2 trước bàn giao. Test cấu trúc/semantic mới cần thiết để kiểm
contract mới, không viết lại bộ test nghiệp vụ ứng dụng đã đạt.
