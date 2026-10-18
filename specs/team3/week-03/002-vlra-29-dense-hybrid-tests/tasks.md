# Tasks: VLRA-29

Nguồn: spec.md, plan.md và hướng dẫn tester. Chỉ đánh dấu khi đã có bằng chứng.

## Phase 1: Setup

- [x] T001 Đối chiếu baseline/environment .local/team3/retrieval-audit-20261019/ và tests/test_dense_retrieval.py (FR-001/010/012).

## Phase 2: Foundational

- [x] T002 Tái dùng tests/retriever_contract.py và scripts/eval_retrieval.py từ VLRA-28 (FR-004/013).

## Phase 3: US1 — Dense embedding/vector (P1)

- [x] T003 [US1] Tích hợp mixin trong tests/test_dense_retrieval.py, giữ guard/cosine/nearest-neighbour/persistence riêng (FR-001/003/004).
- [x] T004 [US1] Bổ sung/chạy tests/test_retrieval_edge_cases.py: normalize/NFC/prefix/shape/manifest/integrity; bàn giao3 FAIL, không sửa production (FR-002/003/008/012).
- [ ] T005 [US1] Chạy benchmark model thật + Qdrant server bằng scripts/eval_retrieval.py; lưu specs/team3/week-03/evidence/dense-real.json (FR-005/009/013). BLOCKED vì RAM/server, chưa chạy model.

## Phase 4: US2 — Hybrid/RRF (P1)

- [x] T006 [US2] Chuẩn bị specs/team3/week-03/002-vlra-29-dense-hybrid-tests/hybrid-handoff.md và ../evidence/rrf-oracle.json, ghi candidate100/publicK50 (FR-006/007/008/011/014).
- [ ] T007 [US2] Chạy runtime Hybrid, timeout/error/version/dedup/RRF và benchmark bằng scripts/eval_retrieval.py; specs/team3/week-03/evidence/hybrid.json (FR-006/007/008/009/011/013/014). BLOCKED: chưa có runtime VLRA-27.

## Phase 5: US3 — Results/report (P2)

- [x] T008 [US3] Chạy regression tests/ và ghi lớp giả/thật/server/Hybrid tại specs/team3/week-03/002-vlra-29-dense-hybrid-tests/issues.md (FR-001/009/010).

## Final Phase

- [x] T009 Hoàn tất specs/team3/week-03/002-vlra-29-dense-hybrid-tests/verification.md và ../verification.md; map FR/SC, giữ task chưa thực thi (FR-001..014).

## Dependencies and implementation strategy

T001→T002→T003→T004; T005 phụ thuộc tài nguyên/model/server, T007 phụ thuộc runtime owner. T006 không chờ model; T008/T009 bàn giao partial khi T005/T007 còn mở.
Không đánh [P]: shared mixin/edge file được chỉnh tuần tự, không ghi chung index/alias đồng thời. Không commit/push. Task kiểm thử DONE không tự kết luận module PASS hoặc Jira DONE.
