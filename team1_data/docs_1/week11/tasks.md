# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 11
## Phân Hệ: Data & Retrieval (Team 1)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 11 (Sprint 8, hạn 23/11/2026), mốc G5 Evaluation.
- **Mục tiêu trọng tâm:**
  - Giao Test Set độc lập, đã đóng băng (Team 2 đang chặn ở VLRA-T2-37; Sprint 8 chưa có ticket cho việc này).
  - VLRA-77: đo Recall@5/10/20, MRR@20 trên Test Set và phân tích lỗi truy hồi cho Final Evaluation Report.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Người phụ trách | Tên công việc & Nội dung | Tiêu chí hoàn thành (DoD) |
| :--- | :--- | :--- | :--- |
| **T1-W11-1** | Thành viên A | **Tạo và đóng băng Test Set v1** (`team1_data/golden/test_set_v1.json`): câu trả lời được, câu ghép nhiều Khoản, câu cần từ chối. | `split: "test"`; không trùng câu, không trùng Điều với Dev Set; đáp án nguyên văn; hash trong manifest; có test. |
| **VLRA-77** | Thành viên B | **Đánh giá Retrieval & phân tích lỗi trên Test Set.** | Recall@5/10/20, MRR@20 kèm `raw_results` từng câu; lỗi chia theo tokenizer / embedding / chunking; kiểm hiệu lực đơn vị luật của câu phức tạp. |

---

## 3. Ý Tưởng Giải Thuật & Thiết Kế Kỹ Thuật Chi Tiết

### 3.1. Độc lập với Dev Set
Khóa so sánh là Điều: `(document_id, số Điều)`, riêng Luật 59/2020 và VBHN 67 dùng chung khóa `law`. Loại mọi Điều đã có gold trong `golden_phase1.json` hoặc `out_of_scope_v1.json`.

### 3.2. Chọn Khoản
- Chỉ văn bản còn hiệu lực hoặc hết hiệu lực một phần, nội dung hiện hành: VBHN 67, NĐ 168/2025, VBHN 7566, NĐ 122/2021 (bỏ Điều 43, 44, 46, 48, 49, 50, 52 đã bị NĐ 288/2026 sửa), NĐ 288/2026.
- Khoản dài 150–1.100 ký tự; bỏ điều khoản thi hành, chuyển tiếp, bãi bỏ; chọn ngẫu nhiên seed 20261120, mỗi Điều tối đa một câu; bỏ thủ công 2 Khoản chỉ dẫn chiếu (Điều 206 khoản 4 VBHN 67, Điều 39 khoản 5 NĐ 168).
- Câu ghép: 2 Khoản cùng Điều, câu hỏi gộp hai ý (phục vụ chấm mù câu phức tạp của Team 2).

### 3.3. `relevant_unit_groups`
Mỗi gold chunk một nhóm. Chunk VBHN 67 nhận thêm chunk Luật 59/2020 cùng Điều/Khoản khi nội dung giống hệt (bỏ qua khoảng trắng và chú thích `[n]`), để câu trả lời trích bản 59/2020 có cùng nội dung không bị tính sai. Khoản đã bị sửa (nội dung khác) không được thêm.

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Bản ghi Test Set
Cùng trường với Dev Set (`id`, `question`, `expected_status`, `ground_truth`, `gold_chunk_ids`, `citation`, `category`, `author`, `source`, `review_status`, `split`, `relevant_unit_groups`), thêm `complexity` ∈ {`single_clause`, `multi_clause`, `refusal`}; câu từ chối có `reason`.

### 4.2. Mẫu

```json
{"id": "test_048", "question": "Giám đốc công ty trách nhiệm hữu hạn một thành viên phải đáp ứng tiêu chuẩn gì và có những quyền, nghĩa vụ nào?",
 "expected_status": "answered", "complexity": "multi_clause", "split": "test",
 "gold_chunk_ids": ["vbhn-67-vbhn-vpqh-v1__dieu-82__k2__0", "vbhn-67-vbhn-vpqh-v1__dieu-82__k3__0"],
 "relevant_unit_groups": [["vbhn-67-vbhn-vpqh-v1__dieu-82__k2__0", "luat-59-2020-qh14-v1__dieu-82__k2__0"],
                          ["vbhn-67-vbhn-vpqh-v1__dieu-82__k3__0", "luat-59-2020-qh14-v1__dieu-82__k3__0"]],
 "citation": "Khoản 2, 3 Điều 82 - Hợp nhất Luật Doanh nghiệp 67/VBHN-VPQH"}
```

### 4.3. Lệnh chạy cho VLRA-77
`python -m team1_data.evaluation run --dev-set team1_data/golden/test_set_v1.json --config <file> --run-id vlra77`

---

## 5. Blockers & Risks

| Rủi ro | Ảnh hưởng | Phương án |
| :--- | :--- | :--- |
| 77 câu `draft_needs_legal_review` chưa được người có chuyên môn pháp lý soát | Test Set dùng để đo được, chưa phải tập đã duyệt chuyên môn | Người có chuyên môn rà; sửa câu nào thì cập nhật hash và báo Team 2 |
| DoD Jira VLRA-77 yêu cầu lưu kết quả "trong docs/team1_data/" | Trái `docs/CODING_CONVENTIONS.md` (docs/ chỉ chứa đặc tả) | Số liệu ở `evaluation/retrieval/runs/vlra77/`, tóm tắt ở mục 6 file này; chờ chủ repo xác nhận |
| Metadata `chapter` của một số chunk hộ kinh doanh trong NĐ 168 ghi Chương VII | Không ảnh hưởng gold; có thể gây nhầm khi hiển thị | Báo lại khi rà chunking |

---

## 6. Kết Quả Thực Hiện

| Task | Trạng thái | Kết quả |
| :--- | :--- | :--- |
| T1-W11-1 | Xong (chờ soát pháp lý) | `test_set_v1.json` 77 câu: 47 `single_clause`, 15 `multi_clause`, 15 `refusal` (7 out_of_domain, 4 missing_information, 4 trap). sha256 chuẩn hóa `1edaf4f14426bb52cc58620b14eea71d6bdd8393dd0b7040e4e5da4d59882001` (manifest). 47 nhóm có thêm chunk Luật 59/2020 giống hệt. `tests/test_test_set_v1.py` 6 test. Bàn giao Thành viên B và Team 2 (VLRA-T2-37). |
| VLRA-77 | Chưa làm | Thành viên B, dùng Test Set trên. |
