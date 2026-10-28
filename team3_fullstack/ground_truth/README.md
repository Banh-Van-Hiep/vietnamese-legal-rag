# Ground Truth của Team 3

Bộ hỏi đáp về Luật Doanh nghiệp, theo định dạng golden của Team 2
(`team2_rag/data/golden/golden_phase1_30cai.json`): `id`, `question`, `expected_status`,
`ground_truth`, `gold_chunk_ids`, `citation`, `category`, `author`.

**Trạng thái: bản nháp, chưa có người review.** Spec tuần 2 yêu cầu nguồn, phiên bản luật và đáp án
được reviewer nhóm chỉ định xác nhận trước khi nghiệm thu (AC-07). Chưa có xác nhận đó.

## Nội dung

`team3_ground_truth.json` chứa 13 mẫu: 8 mẫu nháp ban đầu và 5 mẫu bổ sung.
Có 12 mẫu `answered` với căn cứ và 1 mẫu `insufficient_context` không có chunk.
VLRA-24 yêu cầu 5–10 câu mỗi thành viên, 30–50 câu cho dataset chung.
File công khai dùng tác giả Team 3; bộ dữ liệu chưa được reviewer nhóm nghiệm thu.

### Bộ nháp ban đầu — `team3_ground_truth.json`

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

### Mẫu bổ sung — trong `team3_ground_truth.json`

| ID | Chủ đề | Căn cứ |
| --- | --- | --- |
| gt_t3_009 | Đặt trụ sở chính ở nước ngoài | Điều 42 |
| gt_t3_010 | Văn phòng đại diện thực hiện kinh doanh | Khoản 2 Điều 44 |
| gt_t3_011 | Thời hạn góp vốn và thời gian nhập khẩu tài sản | Khoản 2 Điều 47 |
| gt_t3_012 | Chuyển nhượng vốn dẫn đến chỉ còn một thành viên | Khoản 3 Điều 52 |
| gt_t3_013 | Doanh nghiệp tư nhân phát hành chứng khoán | Khoản 2 Điều 188 |

Cả 5 mẫu dùng `expected_status = answered`, có chunk thật thuộc
`vbhn-67-vbhn-vpqh-v1` (67/VBHN-VPQH ngày 15/08/2025). Đã đối chiếu nội dung
các chunk tương ứng với bản Luật 59/2020/QH14 trong corpus: giống nhau ở các
đoạn được chọn. Đây là kiểm tra theo corpus, chưa chứng minh không có thay đổi luật sau
phiên bản này. Nguồn gốc: [Công báo](https://congbao.chinhphu.vn/van-ban/van-ban-hop-nhat-so-67-vbhn-vpqh-45865.htm).
Trang thông tin truy cập được; tải PDF để đối chiếu độc lập ngày 12/10/2026 trả HTTP 502.
Reviewer vẫn cần xác nhận đáp án, phiên bản áp dụng và nội dung văn bản gốc.

## Cách soạn

- Đáp án lấy từ nội dung chunk trong `data/doanh-nghiep/processed/chunks.jsonl` của Team 1
  (nhánh `develop`), không lấy từ response mock và không tự đặt `chunk_id`.
- Chỉ chọn các điều có nội dung **giống hệt** giữa Luật 59/2020/QH14 (`legal_status`:
  `het_hieu_luc_mot_phan`) và Văn bản hợp nhất 67/VBHN-VPQH (bản hiện hành, 15/8/2025), để đáp án
  không lỗi thời do các lần sửa đổi. Đã so sánh bằng cách đối chiếu văn bản từng điều.
- Không trùng câu hỏi hoặc ID với 5 mẫu của Team 2.
- Bản nháp do AI hỗ trợ soạn; người review cần tự đối chiếu với văn bản gốc tại `source_url` của chunk.

## Kiểm tra

Chạy **validator của Team 2** trên bộ Team 3 đã gộp, từ thư mục gốc repository:

```powershell
python -X utf8 -c "from pathlib import Path; import team2_rag.validate_golden as validator; validator.GOLDEN_FILE = Path('team3_fullstack/ground_truth/team3_ground_truth.json'); validator.validate_golden_dataset()"
```

`validate_golden.py` chưa có tham số CLI để chọn file: lệnh trên chỉ đổi đường dẫn
trong tiến trình Python, không sửa script hay dữ liệu Team 2. Chạy trực tiếp
`python team2_rag/validate_golden.py` sẽ kiểm tra bộ Team 2, không phải bộ Team 3.

Validator Team 3 mặc định chỉ yêu cầu **tối thiểu 5 mẫu và không giới hạn tối đa** (chỉ tiêu 5–10 câu
tính theo từng thành viên trong VLRA-24, còn file này gộp nhiều người). Muốn ép giới hạn theo file thì
truyền `--min` / `--max`:

```powershell
python -X utf8 team3_fullstack/ground_truth/validate_ground_truth.py
python -X utf8 team3_fullstack/ground_truth/validate_ground_truth.py --max 10   # ép giới hạn: bộ 13 mẫu sẽ báo lỗi
```

Validator Team 2 kiểm tra field bắt buộc, ID trùng trong file và chunk tồn tại, nhưng
điều kiện chunk không rỗng đang kiểm tra trạng thái `answerable`, trong khi dataset dùng
`answered`. Script cũng chưa trả exit code khác 0 khi phát hiện lỗi; phải đọc kết quả
in ra. Validator Team 3 bổ sung kiểm tra trạng thái và chunk không rỗng cho `answered`,
trả exit code 1 khi có lỗi, và bắt trùng ID/câu hỏi (kể cả với 5 mẫu Team 2) sau khi chuẩn hóa
Unicode NFC, khoảng trắng và chữ hoa/thường.
Cả hai không kiểm chứng tính đúng pháp lý của đáp án hoặc việc luật còn áp dụng hiện nay.

Kết quả ngày **12/10/2026** cho `team3_ground_truth.json` sau khi gộp:

- Validator Team 2: **PASS 13/13** theo thông báo kết quả, đủ field và mọi chunk ID tồn tại.
- Validator Team 3 (sau khi bỏ giới hạn tối đa): **PASS**, exit code 0, 13 mẫu (12 `answered`,
  1 `insufficient_context`). Với `--max 10` vẫn báo lỗi số lượng đúng như mong đợi. Đã thử với dữ liệu cố ý sai
  (trùng ID, trùng câu hỏi khác Unicode/hoa thường, chunk không tồn tại, `answered` thiếu chunk, trạng thái sai,
  thiếu field): cả 6 lỗi đều bị bắt và exit code là 1.
- Nội dung 8 mẫu ban đầu giữ nguyên; 5 mẫu bổ sung đã đối chiếu từng đáp án với chunk nguồn.
- **Chưa nghiệm thu pháp lý**; kết quả trên không đánh dấu T05 hoàn thành.

## Nhiệm vụ và nghiệm thu hiện hành

- [Tuần 5](../docs_3/week5/tasks.md): Phase 1 và đóng góp; [kết quả kiểm tra](../docs_3/week5/verification.md).
- [Tuần 7](../docs_3/week7/tasks.md): bộ v1 100–150 câu, stratified split và freeze manifest;
  [phần còn thiếu](../docs_3/week7/verification.md).
- Validator chỉ kiểm tra format/trùng/chunk ID, không xác nhận đáp án đúng về pháp lý.
  Mẫu `answered` cần chunk ID; mẫu `insufficient_context` dùng danh sách rỗng theo quy chuẩn.
- Bộ riêng Team 3 không tự là bản gộp chính thức của dự án; cần thống nhất review, phân chia
  và phiên bản dữ liệu trước khi dùng cho benchmark hoặc tuyên bố nghiệm thu.
