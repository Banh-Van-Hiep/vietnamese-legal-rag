# Quickstart — chạy từ repository root

Môi trường đã dùng: .local/team3/retrieval-audit-20261019/venv/Scripts/python.exe (Python 3.12.15).
Cài theo pyproject extras retrieval/test, numpy và qdrant-client. Dense thật cần extra dense.

```powershell
$py = '.local/team3/retrieval-audit-20261019/venv/Scripts/python.exe'
& $py -m unittest discover -s tests -v
& $py scripts/run_retrieval_tests.py --output-dir .local/team3/retrieval-audit-20261019/final-unit
& $py -m team1_data.retrieval build --out .local/team3/retrieval-audit-20261019/bm25
& $py -m team1_data.retrieval query --index .local/team3/retrieval-audit-20261019/bm25 'Điều 17 Luật Doanh nghiệp'
& $py scripts/eval_retrieval.py --method bm25 --index .local/team3/retrieval-audit-20261019/bm25 --golden team2_rag/data/golden/golden_phase1_30cai.json --groups specs/team3/week-03/data/query_groups.json --output .local/team3/retrieval-audit-20261019/bm25-baseline.json
```

Chạy supplement riêng với --golden specs/team3/week-03/data/golden_retrieval_additions.json.
Validator T2: import team2_rag.validate_golden, đặt GOLDEN_FILE và CHUNKS_FILE cho lần gọi;
thu stdout, kiểm marker thành công và validate cấu trúc độc lập, không tin exit 0 đơn lẻ.
Windows sandbox có thể chặn TemporaryDirectory; chạy ngoài sandbox có kiểm soát, không sửa test để né lỗi.
Dense: pin model revision trong manifest, Qdrant version cố định được owner thống nhất,
build index cô lập, chạy cùng evaluator. FakeEmbedder/memory không là model/server PASS.
Hybrid: nhận runtime và --factory từ owner, không dùng oracle thay module; xem hybrid-handoff.md
trong bộ VLRA-29. Xem verification.md để biết lệnh thực tế, kết quả và bước còn mở.
