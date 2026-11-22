# Golden Dataset Phase 1 (Team 1, VLRA-36)

`golden_phase1.json` — 110 câu hỏi–đáp án, dùng làm **Dev Set cố định** cho đánh giá Retrieval (VLRA-48..53).

| Nguồn | Số câu | `review_status` |
|---|---|---|
| `team2_rag/data/golden/golden_phase1_30cai.json` (giữ nguyên, thêm `source`, `review_status`) | 40 | `team2_reviewed` |
| Team 1 soạn mới từ chunk trong `data/doanh-nghiep/processed/chunks.jsonl` | 70 | `draft_needs_legal_review` |

Quy tắc cho câu mới (`gold_041`–`gold_110`):
- Mỗi câu gắn đúng 1 `gold_chunk_ids` (cấp Khoản); `ground_truth` là **nguyên văn** `content` của chunk đó; `citation` = Khoản · Điều · tên + số văn bản.
- Chỉ lấy văn bản còn hiệu lực/hiệu lực một phần: Luật Doanh nghiệp hợp nhất 67/VBHN-VPQH (48 câu) và Nghị định 168/2025/NĐ-CP (22 câu); không trùng Điều với 40 câu có sẵn.
- Câu hỏi do Claude viết từ nội dung chunk → **cần người có chuyên môn pháp lý rà soát** cách hỏi trước khi dùng làm tập test chính thức.

## Đóng băng Dev Set (10/11/2026)

- Cả 110 câu có `split: "dev"` và `relevant_unit_groups` (định dạng của `scripts/eval_reranker.py`). Không gold chunk nào có subchunk anh em cùng Khoản trong `data/doanh-nghiep/processed/chunks.jsonl`, nên mỗi gold chunk là một nhóm riêng (`[[id]]`), không gộp Khoản khác nhau.
- Hash: `golden_phase1.manifest.json` ghi `sha256` của `NFC(json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(",", ":")))` (UTF-8). Sửa bất kỳ câu nào phải cập nhật hash và báo Team 2.
- 40 câu `team2_reviewed` đồng bộ với bản Team 2 hiện hành (gold_016, gold_021–025 đã được Team 2 sửa ngày 03/11 trong #49).
- 70 câu `draft_needs_legal_review` **vẫn cần người có chuyên môn pháp lý rà soát**; đóng băng chỉ cố định nội dung để đo, không thay việc rà soát.
- Không tự chia lại Dev Set thành Test Set; Test Set riêng ở mục dưới.

Kiểm tra: `python3 -m pytest tests/test_golden_phase1.py` (đủ 100–150 câu, schema `scripts/eval_retrieval.py::validate_cases`, gold ID có trong corpus, đáp án trích nguyên văn).

## Test Set v1 (20/11/2026)

`test_set_v1.json`: 77 câu, `split: "test"`, đóng băng ngày 20/11/2026 để đo G5 (VLRA-77 Team 1, VLRA-78/79 Team 2). Không dùng để tối ưu cấu hình.

| Loại (`complexity`) | Số câu | Ghi chú |
|---|---|---|
| `single_clause` | 47 | 1 gold chunk cấp Khoản; `ground_truth` là nguyên văn `content` |
| `multi_clause` | 15 | 2 Khoản cùng Điều; `ground_truth` là nguyên văn hai chunk nối bằng dòng trống |
| `refusal` | 15 | `insufficient_context`: 7 `out_of_domain`, 4 `missing_information`, 4 `trap` |

- Độc lập với Dev Set: không câu nào dùng Điều đã có trong `golden_phase1.json` hoặc `out_of_scope_v1.json` (Luật 59/2020 và VBHN 67 tính là cùng Điều), không trùng câu hỏi.
- Nguồn: VBHN 67/VBHN-VPQH, Nghị định 168/2025/NĐ-CP, VBHN 7566/VBHN-BKHĐT, Nghị định 122/2021/NĐ-CP (chỉ các Điều không bị Nghị định 288/2026 sửa) và Nghị định 288/2026/NĐ-CP. Không lấy Luật 59/2020 gốc và Luật 76/2025 làm gold, vì nội dung hiện hành nằm trong VBHN 67.
- Chọn Khoản ngẫu nhiên có seed (20261120), bỏ Khoản chỉ dẫn chiếu hoặc điều khoản thi hành; câu hỏi do Claude viết.
- `relevant_unit_groups`: mỗi gold chunk một nhóm; chunk VBHN 67 nhận thêm chunk Luật 59/2020 cùng Điều/Khoản khi nội dung giống hệt (bỏ qua khoảng trắng và chú thích `[n]`).
- Hash: `test_set_v1.manifest.json`, cùng cách tính như Dev Set. Sửa câu nào thì cập nhật hash và báo Team 2.
- Cả 77 câu `draft_needs_legal_review`: **cần người có chuyên môn pháp lý rà soát** trước khi coi là kết quả nghiệm thu.
- Chạy Retrieval trên Test Set: `python -m team1_data.evaluation run --dev-set team1_data/golden/test_set_v1.json --config <file> --run-id <id>`. `scripts/eval_reranker.py` chủ động từ chối `split: "test"`.

Kiểm tra: `python3 -m pytest tests/test_test_set_v1.py`.
