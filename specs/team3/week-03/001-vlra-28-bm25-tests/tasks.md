# Tasks: VLRA-28

Nguồn: spec.md, plan.md và hướng dẫn tester. Chỉ đánh dấu khi đã có bằng chứng.

## Phase 1: Setup

- [x] T001 Lưu baseline HEAD/status/hashes ở .local/team3/retrieval-audit-20261019/baseline.json (FR-009/010).
- [x] T002 Tạo venv Python 3.12.15, cài extras theo pyproject và ghi .local/team3/retrieval-audit-20261019/environment.json (FR-001/009).

## Phase 2: Foundational

- [x] T003 Chạy baseline tests/test_bm25_retrieval.py 18 tests và tests/test_dense_retrieval.py 22 tests; lưu baseline logs (FR-001).

## Phase 3: US1 — Index/query/contract (P1)

- [x] T004 [US1] Tạo tests/retriever_contract.py, tích hợp tests/test_bm25_retrieval.py; thay generic checks trùng, giữ cơ chế đặc thù (FR-002/003/004/005/006/008/012).
- [x] T005 [US1] Bổ sung/chạy tests/test_retrieval_edge_cases.py; kiểm Unicode/K/index integrity cùng tests/test_bm25_retrieval.py (FR-002/003/004/008).

## Phase 4: US2 — Corpus/evaluation (P1)

- [x] T006 [US2] Viết/chạy9 tests trong tests/test_eval_retrieval.py cho metric oracle/empty gold/error/schema/report (FR-011).
- [x] T007 [US2] Triển khai scripts/eval_retrieval.py và scripts/run_retrieval_tests.py; kiểm metric/JSON/JUnit/exit status (FR-007/009/011).
- [x] T008 [US2] Tạo specs/team3/week-03/data/golden_retrieval_additions.json, query_groups.json, manifest.json; giữ golden T2 (FR-007/013).
- [x] T009 [US2] Chạy validator team2_rag/validate_golden.py qua import cho30+8 mẫu; kiểm cấu trúc/IDs độc lập, lưu evidence/golden-validation.json (FR-013).
- [x] T010 [US2] Build/load/query BM25 CLI trên2576 chunks; xuất specs/team3/week-03/evidence/bm25-baseline.json, bm25-supplement.json, bm25-cases.csv (FR-002/007/011).

## Phase 5: US3 — Errors/report (P2)

- [x] T011 [US3] Chạy regression tests/, tái hiện và phân loại lỗi trong specs/team3/week-03/001-vlra-28-bm25-tests/issues.md (FR-008/009/010).

## Final Phase

- [x] T012 Hoàn tất specs/team3/week-03/001-vlra-28-bm25-tests/verification.md và ../verification.md; map FR/SC, kiểm links/diff/preservation (FR-001..013).

## Dependencies and implementation strategy

T001→T002→T003→US1; T006→T007 và T008→T009, sau đó T010→T011→T012. US1 là increment độc lập đầu tiên; tool/golden phục vụ US2.
Không đánh [P]: shared mixin/edge file được chỉnh tuần tự, không ghi chung index/alias đồng thời. Không commit/push. Task kiểm thử DONE không tự kết luận module PASS hoặc Jira DONE.
