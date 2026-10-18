# Implementation Plan: VLRA-29

**Ngày:** 19/10/2026. **Spec:** [spec.md](spec.md). Nhánh hiện tại feature/team3/*, không đổi.

## Summary
Tái sử dụng code và test hiện có; bổ sung ca còn thiếu và đo theo hướng dẫn tester.
Dense tái dùng evaluator/mixin/golden VLRA-28; Hybrid runtime do owner bàn giao.

## Technical Context
Python >=3.10 theo pyproject; dùng venv Python 3.12.15 để kiểm thử, không đổi pin project.
unittest/jsonschema; BM25 bm25s/underthesea; Dense numpy/qdrant-client; model thật thêm
sentence-transformers và torch CPU. Không đổi framework hoặc model mặc định.
Venv/cache/index/raw log: .local/team3/retrieval-audit-20261019/ (ignored).
Docker CLI có; daemon/model/Hybrid phải kiểm tra runtime, chưa sẵn sàng không phải PASS.

## Constitution Check
I: giữ nguyên contract v0.1 và public top_k<=50. II: phân công tester T1 được user giao,
không sửa production, corpus, golden gốc hoặc docs T1/T2. III: kế thừa unittest/retrievers.
IV: expected độc lập, bằng chứng và lỗi tái hiện; skip không là PASS. C1–C5 giữ nguyên.
Gate trước/sau thiết kế PASS cho phần độc lập; dependency runtime báo riêng.

## Project Structure
Dự kiến tác động: tests/test_dense_retrieval.py; tests/test_retrieval_edge_cases.py; hybrid-handoff.md.
Evidence/verification/issues đặt trong specs/team3/week-03/; production team1_data/retrieval chỉ đọc.
Scripts/run_retrieval_tests.py xuất JSON/JUnit XML/log để review và sử dụng CI sau này;
không tự thêm workflow CI hoặc comment PR.

## Phases
0: inventory/research. 1: evidence model/contracts/quickstart. 2: tasks theo user story,
analyze read-only và sửa vấn đề. 3: baseline → bổ sung test/tool → regression → corpus → report.
Dense và BM25 dùng chung file edge/mixin nên chỉnh tuần tự; không gắn [P] sai dependency.

## Validation and reporting
Recall@K macro = |gold ∩ topK|/|gold|; MRR@10 = nghịch đảo rank relevant đầu tiên,
miss=0; gold rỗng loại khỏi denominator và báo riêng. Đo top_k=20, lấy cutoffs 5/20/10.
Query lỗi có status/error/elapsed, không âm thầm bỏ hoặc chấm PASS; run partial/error.
p50/p95 nội suy tuyến tính trên wall time retrieve thành công, không gồm model load/build;
không warmup trong lần đo này và không coi mẫu nhỏ là chứng minh SLA.
Baseline 30 và supplement báo riêng, lưu case ID/question/group/expected/actual/rank/score,
hash corpus/golden/schema/source, index_version, model/revision, Python/packages/HEAD/dirty.
Mục tiêu Hybrid theo T1 §5: Recall20>=0.90 và không kém nhánh tốt nhất; không áp vào unit BM25/Dense.
Markdown report gồm scope/environment/commands/AC matrix/results/issues/dependencies/verdict;
JSON + JUnit XML làm bằng chứng, không chứa tên tài khoản cá nhân.

## Analyze remediation
I1: readiness đã cập nhật. U1: CLI setup failure phải ghi JSON BLOCKED và exit 2;
query/schema error ghi ERROR và exit 1; complete exit 0. Không sửa production để đổi FAIL thành PASS.
Không có ngoại lệ constitution hoặc CRITICAL/HIGH còn chặn phần độc lập.
