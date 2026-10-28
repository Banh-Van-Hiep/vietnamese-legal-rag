# Báo cáo kiểm thử tuần3 — VLRA-28 và VLRA-29

**Kết luận19/10/2026:** đã bàn giao đủ công việc kiểm thử BM25 và công cụ chung;
VLRA-29 còn mở vì3 lỗi Dense, chưa benchmark model thật và chưa có runtime Hybrid.
Chưa nghiệm thu toàn tuần hoặc tự đổi trạng thái Jira.

| Lớp kiểm chứng | Kết quả | Evidence |
| --- | --- | --- |
| Baseline trước sửa test | BM25 18/18, Dense 22/22 PASS | Raw logs local, snapshot summary bên dưới |
| Retrieval sau bổ sung/refactor | 56 tests:53 PASS,3 FAIL,0 ERROR,0 SKIP | [JSON](evidence/unit-results.json), [JUnit](evidence/junit.xml) |
| Discovery toàn tests/ | 81 tests:76 PASS,3 FAIL,2 ERROR,0 SKIP | [JSON](evidence/regression-results.json), [JUnit](evidence/regression-junit.xml) |
| Preprocess riêng để kiểm tra2 ERROR | 3 tests:1 PASS,2 ERROR | [Isolated](evidence/preprocess-isolated.json) |
| BM25 corpus | Build/load/query/evaluate thành công, chưa là mọi câu hỏi đạt | [Baseline](evidence/bm25-baseline.json), [Supplement](evidence/bm25-supplement.json), [CSV từng câu](evidence/bm25-cases.csv) |
| Golden cấu trúc/ID | Baseline 30 + supplement 8 đều đạt validator và kiểm độc lập | [Validation](evidence/golden-validation.json), [Manifest](data/manifest.json) |
| Dense vector có kiểm soát | Cosine expected1.0/0.96 khớp số thực; model giả | [Diagnostics](evidence/dense-diagnostics.json) |
| Dense model thật / server | BLOCKED do RAM/server, chưa chạy weights | [Preconditions](evidence/dense-real.json) |
| Hybrid runtime | BLOCKED, chưa có implementation | [Status](evidence/hybrid.json), [Handoff](002-vlra-29-dense-hybrid-tests/hybrid-handoff.md) |

## Kết quả BM25 corpus thật

| Dataset | Scored/total | Recall5 | Recall20 | MRR10 | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline Team 2 | 30/30 | 0.496842 | 0.738160 | 0.666667 | 2.220 | 4.635 |
| Supplement draft | 6/8 | 0.833333 | 0.833333 | 0.833333 | 1.655 | 138.707 |

Baseline 30 đều scored; supplement 8 có6 answered tính metric,2 insufficient_context chỉ quan sát.
Baseline 12 câu legal_reference/18everyday; supplement4reference/2everyday/2out_of_corpus.
Metric từng nhóm và tất cả actual IDs/rank/score nằm trong JSON. CSV gán MATCH/PARTIAL/MISS
so với nhãn exact IDs, NOT_SCORED cho gold rỗng. Có14/30 baseline chưa lấy đủ gold ở top 20
(trong đó4 mẫu miss hoàn toàn), và1/6 supplement answered miss. Đây là nội dung cần review relevance/nhãn,
không che bằng kết luận unit PASS hoặc tự sửa gold theo output.

Số0.738160 khác0.805 minh họa; chưa có hash/protocol của lần cũ để coi là regression.
Không áp ngưỡng Hybrid 0.90 cho BM25; Hybrid phải đo khi có runtime trên cùng bộ dữ liệu.

## Vấn đề và việc còn mở

- D-01 MEDIUM: Dense connect không đối chiếu query prefix; test guard FAIL.
- D-02 HIGH: point UUID khác nhưng cùng chunk_id vẫn qua connect; query trả5 rows/4 IDs.
- D-03 LOW: norm float32 overflow với vector cực trị[3e38,3e38] tạo[0,0].
- R-P01 MEDIUM, ngoài phạm vi retrieval: preprocess gọi chunk_document không có trong chunker;
  cả discovery và isolated đều2 ERROR. Pipeline/source này không đổi trong lượt kiểm thử.
- Dense thật: model revision dea33aa1ab339f38d66ae0a40e6c40e0a9249568 đã xác minh metadata;
  weights FP32 tối thiểu2,12 GiB, máy cònkhoảng 1,1 GB RAM; Docker API lỗi500 sau khi thử start.
  Không tải/load weights; đã dừng Docker helper. Cần máy đủ RAM và Qdrant version thống nhất.
- Hybrid: owner VLRA-27 bàn giao runtime/factory/candidate100 interface. Oracle RRF chỉ là reference,
  chưa có runtime test cho timeout/version/dedup/error hay metric Hybrid.

Chi tiết expected/actual/repro/severity/owner và ma trận FR/SC nằm tại:
[VLRA-28 verification](001-vlra-28-bm25-tests/verification.md),
[VLRA-28 issues](001-vlra-28-bm25-tests/issues.md),
[VLRA-29 verification](002-vlra-29-dense-hybrid-tests/verification.md),
[VLRA-29 issues](002-vlra-29-dense-hybrid-tests/issues.md).

## Phạm vi, nguồn và môi trường

Thực hiện 19/10/2026 theo Jira VLRA-28/29 do người dùng cung cấp và
[hướng dẫn tester 17/10](https://velvetforest.github.io/minh-hoa-BTL/minh-hoa-cong-viec.html).
Thiết kế/contract: docs/team1_data/retrieval-design.md, BM25/Dense/Hybrid proposals,
contracts/v0.1/CONTRACT.md và retrieval_output.schema.json. Không đổi API/schema/production.
HEAD 5a9af42e734391e00dfc0f7ede304506fdd5a28f, working tree có thay đổi tài liệu từ trước,
được giữ nguyên. Chưa commit/push hoặc cập nhật Jira/comment PR.

Windows 11, venv Python 3.12.15 riêng trong .local/team3/retrieval-audit-20261019/.
bm25s 0.3.14, underthesea 9.5.0, numpy 2.5.4, qdrant-client 1.19.1,
jsonschema 4.26.0; torch 2.14.1+cpu và sentence-transformers 5.7.0 chỉ mới cài.
Không tải model weights/gọi LLM/API trả phí. Qdrant unit dùng memory, không là server.
Các dependency giữ phạm vi pyproject; không sửa pyproject/Compose/corpus.

Corpus 2.576 chunk / 8 văn bản, SHA256
37aa6dea2b33a94f9ecc5020796d150f43f8a1dc5ef4d3e797fa9cb1d1707d66.
Golden baseline 30 SHA256
383b57e9d63cf014e9adb7c25c61beb71bf4844efb6b7eb0a6662594ffac0740.
Index audit qa-20261019-01, hash tập ID và manifest trong evidence BM25.
Source hashes dùng để đối chiếu lần chạy, không chứng minh applicability pháp lý.

## Quy trình và lệnh thực tế

Đã thực hiện riêng clarify → plan → tasks → analyze → sửa I1/U1 → implement.
Checklist chất lượng mỗi spec16/16; không có hooks; đây không là test PASS.
Baseline trước chỉnh test: unittest discovery từng file BM25 18/18 và Dense 22/22 PASS.
Sau đó thay generic checks bằng mixin, bổ sung metric và edge tests.

```powershell
$py = '.local/team3/retrieval-audit-20261019/venv/Scripts/python.exe'
& $py -m unittest discover -s tests -p test_bm25_retrieval.py -v
& $py -m unittest discover -s tests -p test_dense_retrieval.py -v
& $py scripts/run_retrieval_tests.py --output-dir .local/team3/retrieval-audit-20261019/final-unit
& $py scripts/run_retrieval_tests.py --pattern 'test*.py' --output-dir .local/team3/retrieval-audit-20261019/full-regression
& $py scripts/run_retrieval_tests.py --pattern test_preprocess_legal_data.py --output-dir .local/team3/retrieval-audit-20261019/preprocess-isolated
```

CLI build/query/evaluate có exit0; lệnh/args trong evidence/commands.json.
Validator Team 2 chạy qua import với GOLDEN_FILE trỏ baseline/supplement riêng,
kiểm marker thành công + validate cấu trúc/IDs độc lập, không dựa exit0 đơn lẻ.
Sandbox Windows chặn TemporaryDirectory; chạy kiểm thử ngoài sandbox đã xử lý
lỗi môi trường đó. Không sửa test/production để né quyền hoặc chuyển FAIL thành PASS.

## Cách đọc kết quả

Count là số unittest methods, không cộng subtests tám input thành tám test mới.
Recall/MRR là macro exact gold chunk-ID trên answered, không là hit-rate hay unit-group recall.
Mẫu gold rỗng báo riêng, không cộng Recall=1. Score là kỹ thuật, không là confidence.
Query top 20 cùng lần chạy cung cấp Recall5/20 và MRR10. Latency chỉ retrieve thành công,
không gồm build/model load/validation. Không warmup; p95 bộ8 câu nhạy cold first call,
không coi số đo nhỏ là chứng minh SLA hoặc cải thiện hiệu năng.
Golden supplement là draft corpus-relative; validator không xác minh pháp lý hoặc
nhãn relevant đầy đủ. Bộ chẩn đoán này chưa là held-out evaluation; không tuning trên nó.

## Đối chiếu bàn giao task → Jira → tuần

VLRA-28: scope tester hoàn thành, gồm unit tests, Top-K/chunk_id, báo cáo pass/fail và
issue list. Unit test / contract cơ chế đạt; relevance giới hạn theo nhãn, chưa tuyên bố chất lượng
pháp lý hoặc toàn bộ câu hỏi đều đạt. Cần reviewer chấp nhận bàn giao, không tự cập nhật Jira.
VLRA-29: bàn giao partial, còn T005(model thật / server) và T007(runtime Hybrid),3 lỗi OPEN.
Toàn tuần chưa DONE; tuần2 và C1–C5 không bị thay đổi. Không sửa app/production/docs T1/T2,
không commit/push. Bằng chứng bảo toàn và link check: evidence/final-validation.json.

## Kiểm tra bàn giao cuối

69 liên kết nội bộ hợp lệ; JSON/JUnit count khớp, source hash test khớp bản bàn giao.
HEAD/index không đổi, không mất thay đổi có trước. VLRA-28 12/12 task kiểm thử/báo cáo;
VLRA-29 7/9 task, T005/T007 còn mở. Log BLOCKED của ca CLI thiếu file là negative test
được kỳ vọng, không phải lỗi mới của evaluator.
