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
- Không có Test Set riêng: không tự chia lại tập đã dùng để tối ưu.

Kiểm tra: `python3 -m pytest tests/test_golden_phase1.py` (đủ 100–150 câu, schema `scripts/eval_retrieval.py::validate_cases`, gold ID có trong corpus, đáp án trích nguyên văn).
