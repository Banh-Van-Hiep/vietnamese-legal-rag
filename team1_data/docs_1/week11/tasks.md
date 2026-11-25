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

### 6.1. VLRA-77 — Đánh giá Retrieval trên Test Set v1 (25/11/2026)
Trạng thái: Đã chạy đánh giá, xuất raw results và phân tích offline; chờ soát pháp lý chuyên môn và bàn giao Team 3.
Thiết lập và khả năng tái lập
- Test Set độc lập: team1_data/golden/test_set_v1.json, 77 câu (47 single_clause, 15 multi_clause, 15 refusal); 62 câu có gold, 77 gold chunk IDs. 15 câu refusal không tính Recall/MRR.
- Kiểm tra đầu vào: 6 tests, 293 subtests PASS; 2.576 chunks được index.
- Hybrid RRF k=60, BM25:Dense = 0.5:1; AITeamVN/Vietnamese_Embedding revision dea33aa1ab339f38d66ae0a40e6c40e0a9249568; giữ chunk gốc, không tối ưu theo Test Set.
- Config: evaluation/retrieval/configs/vlra77_test.json.
- Commit gốc theo raw export: d71128be59e33df4db4a0f3f48ab6b385c4c747b.
- SHA256 byte file Test Set: 7fbd2cc19d79aff332eefa7e264be9551614a6db91e2bf84b63e63354e8cd9f0; hash chuẩn hóa trong manifest: 1edaf4f14426bb52cc58620b14eea71d6bdd8393dd0b7040e4e5da4d59882001 (hai cách tính khác nhau).
- SHA256 byte file corpus: 37aa6dea2b33a94f9ecc5020796d150f43f8a1dc5ef4d3e797fa9cb1d1707d66.
- Lệnh chạy: python -m team1_data.evaluation run --dev-set team1_data/golden/test_set_v1.json --config evaluation/retrieval/configs/vlra77_test.json --run-id vlra77.
- Raw export là lần chạy riêng cùng config và hash đầu vào; 77 × 20 = 1.540 kết quả; 0/77 câu thay đổi top-5 đơn vị chuẩn hóa. Đối chiếu lại strict Recall@5/10/20 và RR từng câu cho thấy 62/62 câu khớp lần chạy gốc. Không khẳng định toàn bộ thứ tự raw của lần gốc giống hệt, vì lần gốc không lưu raw. Không sửa pipeline chung.
Kết quả định lượng
Chỉ số	Pipeline chuẩn hóa theo Khoản	Raw + relevant_unit_groups (bổ sung)	Strict chunk ID
Recall@5	1.0000	0.9758	0.9274
Recall@10	1.0000	1.0000	0.9919
Recall@20	1.0000	1.0000	1.0000
MRR@20	0.9570	0.9710	0.6976


- Hit@5 và Recall@5 theo Điều của pipeline: 1.0000; p50/p95 = 136.40/148.58 ms (truy hồi, không phải end-to-end).
- Build BM25 10.706 ms; Dense 1.052.977 ms (tổng khoảng 17,73 phút).
- Pipeline gộp các đơn vị tương đương trước khi lấy 5 đơn vị đầu; chỉ số raw + relevant_unit_groups cắt 5 chunk vật lý đầu rồi kiểm tra mỗi nhóm có ít nhất một ID được chấp nhận. MRR raw dùng hạng vật lý đầu tiên của ID được chấp nhận. Đây là phép đo bổ sung, không thay chỉ số pipeline.
- 59/62 câu có đủ nhóm căn cứ trong raw top-5; 3/62 câu thiếu một trong hai Khoản. 54/62 câu đủ strict gold trong raw top-5; 61/62 trong raw top-10; 62/62 trong raw top-20.
Phân tích 8 câu sai lệch strict
ID	Khoản gold bị thiếu trong raw top-5 (Điều/Khoản)	Hạng bản Luật 59/2020	Hạng gold VBHN 67	Recall@5 strict	Recall@5 raw theo nhóm
test_020	80/5	5	6	0.00	1.00
test_048	82/2	6	7	0.50	0.50
test_051	106/2	4	7	0.50	1.00
test_053	83/2	6	12	0.50	0.50
test_054	39/1	4	6	0.50	1.00
test_056	155/1	6	8	0.50	0.50
test_057	81/2	5	9	0.50	1.00
test_058	65/3	3	6	0.50	1.00


15/15 cặp gold và bản tương đương của 8 câu trên có nội dung content giống hệt trong raw export. 5 câu chỉ sai lệch ID khi nhóm tương đương đã có đủ trong raw top-5; 3 câu (test_048, test_053, test_056) thiếu căn cứ thực sự nếu context chỉ lấy 5 chunk vật lý. Không có câu nào thiếu căn cứ trong top-5 đơn vị chuẩn hóa.
Phân loại lỗi theo tokenizer / embedding / chunking
Nhóm	Bằng chứng quan sát	Kết luận
Tokenizer	test_020: Điều 58 Khoản 1–2 xếp trên Điều 80 Khoản 5; các điều dùng thuật ngữ họp Hội đồng thành viên nhưng khác loại công ty.	Nhiễu từ khóa/phạm vi pháp lý có thể xảy ra; raw Hybrid không có token hoặc điểm BM25 riêng, chưa xác định lỗi tokenizer.
Embedding	test_053: Điều 165 Khoản 1 ở hạng 2–3 và Điều 71 Khoản 1 ở hạng 5 cạnh tranh với Điều 83 Khoản 2 (hạng 6/12).	Có hiện tượng cạnh tranh ngữ nghĩa, chưa chứng minh do embedding vì chỉ có điểm Hybrid RRF.
Chunking / trùng phiên bản trong context	test_048: hai bản Điều 82 Khoản 3 ở hạng 1–2 và hai bản Điều 64 Khoản 3 ở hạng 3–4; Điều 82 Khoản 2 đến hạng 6/7. test_056: Điều 155 Khoản 3 trùng ở hạng 1–2, Khoản 2 trùng ở hạng 4–5; Khoản 1 đến hạng 6/8.	Xác nhận trùng nội dung chiếm vị trí context; không có bằng chứng chunker cắt mất nội dung gold. Cả ba lỗi raw top-5 đều có hiện tượng trùng phiên bản và cạnh tranh thứ hạng. Không ép gán nguyên nhân gốc vào một trong ba nhóm khi chưa có phép đo từng nhánh.


Đề xuất Team 2 kiểm tra khử trùng theo đơn vị tương đương trước khi lấy context, ưu tiên văn bản hợp nhất khi phù hợp hiệu lực; không gộp các Khoản đã sửa có nội dung khác. Muốn quy kết tokenizer hoặc embedding cần trace riêng BM25/Dense, token và hạng ứng viên. Không điều chỉnh cấu hình theo Test Set đã đóng băng; đề xuất thí nghiệm trên Dev Set hoặc tập mới.
Rà soát hiệu lực các câu phức tạp (offline)
Theo bảng E3 của VLRA-64 (team1_data/docs_1/week9/tasks.md), hai phiên bản giống hệt không tính E3. Đối chiếu chú thích trong data/doanh-nghiep/interim/vbhn-67-vbhn-vpqh-v1.txt đối với 10 Điều VBHN 67 dùng trong nhóm multi_clause không thấy marker sửa đổi tại các Điều này. Metadata 30/30 gold chunks của 15 câu multi_clause là con_hieu_luc trong snapshot.
ID	Văn bản gold	Điều/Khoản	Hạng raw gold theo thứ tự Khoản	Rà soát offline
test_048	VBHN 67	82/(2, 3)	7, 2	Không thấy chú thích sửa đổi trong Điều; metadata còn hiệu lực
test_049	VBHN 67	137/(1, 2)	3, 4	Không thấy chú thích sửa đổi trong Điều; metadata còn hiệu lực
test_050	NĐ 168/2025	16/(2, 4)	2, 1	Metadata còn hiệu lực; cần đối chiếu nguồn chính thức
test_051	VBHN 67	106/(1, 2)	2, 7	Không thấy chú thích sửa đổi trong Điều; metadata còn hiệu lực
test_052	VBHN 67	67/(1, 2)	2, 3	Không thấy chú thích sửa đổi trong Điều; metadata còn hiệu lực
test_053	VBHN 67	83/(2, 3)	12, 4	Không thấy chú thích sửa đổi trong Điều; metadata còn hiệu lực
test_054	VBHN 67	39/(1, 2)	6, 2	Không thấy chú thích sửa đổi trong Điều; metadata còn hiệu lực
test_055	NĐ 168/2025	72/(2, 4)	1, 3	Metadata còn hiệu lực; cần đối chiếu nguồn chính thức
test_056	VBHN 67	155/(1, 3)	8, 2	Không thấy chú thích sửa đổi trong Điều; metadata còn hiệu lực
test_057	VBHN 67	81/(1, 2)	2, 9	Không thấy chú thích sửa đổi trong Điều; metadata còn hiệu lực
test_058	VBHN 67	65/(1, 3)	2, 6	Không thấy chú thích sửa đổi trong Điều; metadata còn hiệu lực
test_059	NĐ 168/2025	103/(2, 3)	1, 2	Metadata còn hiệu lực; cần đối chiếu nguồn chính thức
test_060	VBHN 67	182/(2, 3)	1, 4	Không thấy chú thích sửa đổi trong Điều; metadata còn hiệu lực
test_061	NĐ 168/2025	10/(2, 3)	1, 2	Metadata còn hiệu lực; cần đối chiếu nguồn chính thức
test_062	NĐ 168/2025	84/(2, 4)	1, 2	Metadata còn hiệu lực; cần đối chiếu nguồn chính thức


- 8 câu strict sai lệch không có dấu hiệu E3 ở các cặp gold tương đương đã đối chiếu. Đây không phải đánh giá citation của câu trả lời LLM, cũng không loại trừ rủi ro E3 ở các chunk ngoài gold.
- VBHN 67 không có ngày hiệu lực riêng; effective_date = 2025-08-15 ở chunk là giá trị dự phòng từ ngày ban hành (L1, VLRA-64), không dùng để khẳng định ngày hiệu lực pháp lý. NĐ 168/2025 có metadata ngày hiệu lực 2025-07-01; cần kiểm tra văn bản sửa đổi mới nếu có.
- Chưa xác minh trực tuyến tình trạng hiện hành của từng Điều đến ngày chạy; toàn bộ 77 câu vẫn draft_needs_legal_review. Kết quả dùng cho đánh giá kỹ thuật, chưa thay thế soát pháp lý hoặc nghiệm thu chuyên môn.
Bàn giao và giới hạn
- Đường dẫn evaluation/retrieval/runs/vlra77/: run.json, run.log, summary.md, hybrid_k60_aiteamvn_w0.5-1.json, vlra77_raw_results.json.
- Team 3 (VLRA-81) sử dụng chỉ số pipeline chính thức; nêu rõ 62 câu có gold, ba trường hợp thiếu căn cứ raw top-5 và trạng thái chờ soát pháp lý. 15 câu refusal chỉ lưu truy hồi, chưa đo khả năng từ chối của hệ thống trả lời.
- Chưa xác nhận vị trí báo cáo Jira khác quy ước repo; giữ kết quả tại evaluation/retrieval/runs/vlra77/ và tóm tắt trong week11/tasks.md theo đề xuất thành viên A. Chưa gửi số liệu trực tiếp Team 3.
