# Ground Truth của Team 3

Bộ 8 mẫu hỏi đáp về Luật Doanh nghiệp, theo định dạng golden của Team 2
(`team2_rag/data/golden/golden_phase1_30cai.json`): `id`, `question`, `expected_status`,
`ground_truth`, `gold_chunk_ids`, `citation`, `category`, `author`.

**Trạng thái: bản nháp, chưa có người review.** Spec tuần 2 yêu cầu nguồn, phiên bản luật và đáp án
được reviewer nhóm chỉ định xác nhận trước khi nghiệm thu (AC-07). Chưa có xác nhận đó.

## Nội dung

| ID | Chủ đề | Trạng thái kỳ vọng | Căn cứ |
| --- | --- | --- | --- |
| gt_t3_001 | Số thành viên công ty TNHH hai thành viên trở lên | answered | Khoản 1 Điều 46 |
| gt_t3_002 | Trách nhiệm của chủ sở hữu công ty TNHH một thành viên | answered | Khoản 1 Điều 74 |
| gt_t3_003 | Số cổ đông tối thiểu của công ty cổ phần | answered | Điểm b khoản 1 Điều 111 |
| gt_t3_004 | Một cá nhân thành lập nhiều doanh nghiệp tư nhân | answered | Khoản 3 Điều 188 |
| gt_t3_005 | Thành viên hợp danh là cá nhân hay tổ chức | answered | Điểm b khoản 1 Điều 177 |
| gt_t3_006 | Cách viết loại hình công ty cổ phần trong tên | answered | Khoản 2 Điều 37 |
| gt_t3_007 | Quyết định số lượng và hình thức con dấu | answered | Khoản 1, 2 Điều 43 |
| gt_t3_008 | Thuế suất thuế thu nhập doanh nghiệp | insufficient_context | Không có trong corpus |

Mẫu 008 kiểm tra đường "thiếu căn cứ": corpus chỉ nhắc "theo pháp luật về thuế thu nhập doanh nghiệp"
(8 chunk), không có mức thuế suất, nên hệ thống không được nêu con số.

## Cách soạn

- Đáp án lấy từ nội dung chunk trong `data/doanh-nghiep/processed/chunks.jsonl` của Team 1
  (nhánh `develop`), không lấy từ response mock và không tự đặt `chunk_id`.
- Chỉ chọn các điều có nội dung **giống hệt** giữa Luật 59/2020/QH14 (`legal_status`:
  `het_hieu_luc_mot_phan`) và Văn bản hợp nhất 67/VBHN-VPQH (bản hiện hành, 15/8/2025), để đáp án
  không lỗi thời do các lần sửa đổi. Đã so sánh bằng cách đối chiếu văn bản từng điều.
- Không trùng câu hỏi hoặc ID với 5 mẫu của Team 2.
- Bản nháp do AI hỗ trợ soạn; người review cần tự đối chiếu với văn bản gốc tại `source_url` của chunk.

## Kiểm tra

```bash
python team3_fullstack/ground_truth/validate_ground_truth.py
# hoặc chỉ định nơi có chunks.jsonl:
python team3_fullstack/ground_truth/validate_ground_truth.py --chunks đường/dẫn/chunks.jsonl
```

Script kiểm tra: đủ field, 5–10 mẫu, ID và câu hỏi không trùng (kể cả với golden Team 2), `expected_status`
hợp lệ, mọi `gold_chunk_id` có trong corpus. Nó **không** kiểm tra đáp án đúng về pháp lý; việc đó thuộc
về reviewer.

## Việc còn lại

- Reviewer nhóm chỉ định xác nhận từng mẫu, rồi đổi `author` sang người chịu trách nhiệm.
- Team 2 xác nhận có nhận `expected_status = insufficient_context` và `gold_chunk_ids` rỗng trong định dạng golden
  (hiện bộ của họ chỉ có mẫu `answered`).
