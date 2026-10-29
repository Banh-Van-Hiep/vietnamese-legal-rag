# Validation — Golden Dataset Phase1

**Ngày kiểm chứng:**30/10/2026. **Kết quả:** validator Phase1 đạt; chưa chốt do ID gold_041 xung đột fixture và cơ cấu/chứng thực còn thiếu.

## Expected / Actual

| Tiêu chí | Kết quả |
| --- | --- |
| Số lượng/định dạng | 50 record theo8 field hiện hành |
| Phân loại | 49 answered/1 insufficient_context |
| ID/câu hỏi sau chuẩn hóa | Không trùng trong Phase1; gold_041 xung đột nội dung với fixture5 câu |
| Nội dung câu hỏi | Đã rà ý chính và xử lý các cặp trùng |
| UTF-8/NFC/chunk ID | Đạt; căn cứ tham chiếu tồn tại trong corpus |
| Validator | 50/50, exit0 |

## Nội dung đã hoàn tất

- Hợp nhất các đóng góp vào một file chung.
- Hoàn thiện câu hỏi độc lập về ý chính, đáp án và căn cứ tương ứng.
- Phân biệt answered và insufficient_context theo dữ liệu nguồn.

## Kết quả và bằng chứng

Validator50/50. Bộ test mở rộng:388 đạt,1 lỗi,147 subtest đạt.
Lỗi: `test_sample_ids_do_not_collide_with_full_golden`, do gold_041 chỉ hai câu hỏi khác nhau.
Bằng chứng tại `backend/target/final-acceptance-20261030/`: golden-validator.log, extra-checks.json, internal-regression-rerun.log và internal-regression.xml.

## Bảng rà ý định toàn bộ50 câu

| ID | Ý định kiểm tra |
| --- | --- |
| gold_001 | Phạm vi vấn đề điều chỉnh |
| gold_002 | Đối tượng áp dụng |
| gold_003 | Định nghĩa cổ đông |
| gold_004 | Định nghĩa vốn điều lệ TNHH |
| gold_005 | Các quyền của doanh nghiệp |
| gold_006 | Số lượng/tư cách thành viên TNHH |
| gold_007 | Thời hạn góp vốn TNHH và thời gian loại trừ |
| gold_008 | Lệ phí trước bạ khi chuyển tài sản góp vốn |
| gold_009 | Số lượng cổ đông công ty cổ phần |
| gold_010 | DNTN phát hành chứng khoán |
| gold_011 | Nhóm hành vi bị nghiêm cấm |
| gold_012 | Thành phần hồ sơ thành lập hợp danh |
| gold_013 | Nội dung giấy đề nghị đăng ký |
| gold_014 | Nội dung Điều lệ |
| gold_015 | Nội dung giấy chứng nhận đăng ký |
| gold_016 | Giới hạn trách nhiệm chủ sở hữu TNHH một thành viên |
| gold_017 | Trách nhiệm và nghĩa vụ cổ đông |
| gold_018 | Số lượng/trách nhiệm đại diện theo pháp luật |
| gold_019 | Căn cứ/điều kiện/thủ tục giải thể |
| gold_020 | Tiêu chí/kê khai/danh sách chủ sở hữu hưởng lợi |
| gold_021 | Thời hạn lưu thông tin sau giải thể/phá sản |
| gold_022 | Hiệu lực/chuyển tiếp Luật76 |
| gold_023 | Điều kiện/cam kết doanh nghiệp xã hội |
| gold_024 | Phương tiện/thời gian công bố thông tin DNNN |
| gold_025 | Nguyên tắc xử phạt đăng ký doanh nghiệp theo NĐ122 |
| gold_026 | Xử phạt không giải thể khi hết hạn hoạt động |
| gold_027 | Xử phạt kê khai/chậm đăng ký thay đổi theo NĐ288 |
| gold_028 | Hiệu lực/bãi bỏ NĐ288 |
| gold_029 | Phạm vi/hiệu lực biểu mẫu Thông tư68 |
| gold_030 | Thông báo/thủ tục/xử phạt tạm ngừng |
| gold_031 | Số người đại diện theo ủy quyền theo tỷ lệ vốn |
| gold_032 | Thời điểm có hiệu lực văn bản cử đại diện |
| gold_033 | Định giá tài sản góp vốn phi tiền/vàng |
| gold_034 | Dấu dưới hình thức chữ ký số |
| gold_035 | Điều kiện hoàn trả vốn TNHH một thành viên |
| gold_036 | Bắt buộc cổ phần phổ thông và tên người sở hữu |
| gold_037 | Cổ tức cố định độc lập kết quả kinh doanh |
| gold_038 | Tỷ lệ cổ phần phổ thông sáng lập đăng ký mua |
| gold_039 | Hình thức chi trả cổ tức/đồng tiền |
| gold_040 | Người nhận cổ tức khi chuyển nhượng sau chốt danh sách |
| gt_t3_004 | Số DNTN mỗi cá nhân được thành lập |
| gt_t3_005 | Tư cách/trách nhiệm thành viên hợp danh |
| gt_t3_008 | Không xác định được thuế suất từ snapshot |
| gt_t3_009 | Trụ sở chính phải tại Việt Nam |
| gt_t3_010 | Văn phòng đại diện không kinh doanh |
| gt_t3_012 | Chuyển đổi TNHH khi còn một thành viên |
| gold_041 | Hạn chế/ngoại lệ chuyển nhượng cổ phần ưu đãi biểu quyết |
| gold_042 | Cấp lại cổ phiếu bị mất và nội dung đề nghị |
| gold_043 | Phương tiện/nội dung thông báo mời họp HĐTV |
| gold_044 | Cỡ chữ tên doanh nghiệp tiếng nước ngoài |

## Điều kiện nghiệm thu còn lại

Theo DoD10 mẫu insufficient hiện có1, còn thiếu9; nhóm P0/căn cứ bộ chung cần được
Team2 xác nhận. Cần thống nhất ID gold_041 giữa Phase1 và fixture5 câu rồi chạy lại test lỗi.

## Kiểm tra bàn giao

- [x] File chung50 câu, validator đạt.
- [x] ID/câu hỏi không trùng sau chuẩn hóa; ý chính đã rà.
- [x] Chunk tham chiếu tồn tại.
- [ ] Team3/Team2 thống nhất ID gold_041 và test không xung đột đạt.
- [ ] Team2 xác nhận nội dung/căn cứ và cơ cấu bộ chung.

## Trách nhiệm kiểm chứng

Team3 hoàn tất đóng góp/hợp nhất và phối hợp xử lý ID. Team2 kiểm chứng nội dung, căn cứ, cơ cấu và fixture liên quan.

[Spec](spec.md) · [Tasks](tasks.md) · [Nghiệm thu tuần5](../verification.md).
