# Validation — hợp nhất Golden Dataset VLRA24

**Ngày:**29/10/2026. [Spec](spec.md), [plan](plan.md), [tasks](tasks.md),
[analyze](analysis.md). Thay kết quả chọn subset riêng trước đó.

## Expected / Actual

| Tiêu chí | Kết quả |
| --- | --- |
| AC01 | Đúng50 record tại file chung, không trùng ID/câu hỏi sau chuẩn hóa |
| AC02 |49 answered/1 insufficient, chunk tồn tại trong2576 chunk; field/type/NFC đạt |
| AC03 | Rà50 câu/đáp án, thay4 cặp trùng và thu hẹp2 câu tổng hợp; bảng dưới |
| AC04 | Validator Team2 exit0; giữ38/40 nội dung record chung (không tính author) và6/10 đóng góp; corpus/validator giữ nguyên hash |
| AC05 | Xóa3 file ground_truth Team3 sau PASS; sửa lệnh/tham chiếu; kiểm link/diff ở cuối |

## Thay đổi có chủ đích

- Bỏ gt_t3_001/003/011/013, lần lượt lặp gold_006/009/007/010.
- Bổ sung gold_041–044: chuyển nhượng cổ phần ưu đãi biểu quyết; cấp lại cổ phiếu;
  thông báo mời họp Hội đồng thành viên; cỡ chữ tên doanh nghiệp tiếng nước ngoài.
- Thu hẹp gold_016 về trách nhiệm chủ sở hữu TNHH một thành viên, dùng Điều74 khoản1
  bản vbhn-67-vbhn-vpqh-v1; gold_021 về thời hạn lưu thông tin sau giải thể/phá sản,
  dùng Điều1 khoản26 Luật76/2025. Không còn câu so sánh bao trùm các câu riêng.
- Giữ nguyên gt_t3_004/005/008/009/010/012. Không tái dùng ID câu bị loại cho câu mới.
  Không đổi answered thành insufficient để đạt tỷ lệ.
- Tác giả câu mới chỉ ghi vai trò; metadata record chung cũ được giữ.

## Lệnh, kết quả và evidence

Từ gốc repository:

```powershell
python -X utf8 team2_rag/validate_golden.py
```

Kết quả50/50, exit0. Kiểm bổ sung: đủ8 field/đúng type/không rỗng, NFC, ID/câu hỏi
không trùng sau casefold/gộp khoảng trắng, chunk thật,49/1,38+6 nội dung record nguyên bản (không tính author),
hash corpus/validator không đổi. Đã kiểm dấu tiếng Việt trên cả6 record sửa/tạo mới.
Validator không kiểm ngữ nghĩa; bảng dưới là rà soát thủ công, không tuyên bố có bộ
phát hiện ngữ nghĩa tự động hoặc xác nhận đáp án đúng luật hiện hành.

Evidence ignored: backend/target/week5-golden-merge-20261029/ chứa before-team2.json,
before-team3.json, preservation.json, checks.json, semantic-review.json,
validator-team2.log. Không ghi đè log audit cũ40/13/10 thành kết quả50.

## Bảng rà ý định toàn bộ50 câu

Cùng lĩnh vực/chunk không tự là trùng; đối chiếu câu hỏi và thông tin cần trả lời.

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

## Giới hạn và nghiệm thu

Hợp nhất, kiểm format và rà các ý định trên đạt. Cơ cấu Phase1 vẫn thiếu9 mẫu
insufficient so với DoD10; đã ở trần50 nên phải thay/bố trí lại trong bước điều phối,
không cộng thêm9 để vượt50. Mapping P0 và review pháp lý/hiệu lực vẫn chờ nhóm.
Không chạy lại FE/BE vì không sửa app/config/schema; commit theo yêu cầu bàn giao; không push.

## Kiểm tra bàn giao cuối

14 file Markdown,40 tham chiếu local và1 anchor: không lỗi. git diff --check PASS.
Thư mục ground_truth đã xóa đúng3 file được kiểm kê; không xóa file ngoài phạm vi.
T001–T004 hoàn thành theo kiểm chứng trên; chưa nghiệm thu pháp lý/cơ cấu Phase1.

## Trách nhiệm kiểm chứng đã chốt

Theo xác nhận người dùng ngày29/10/2026, Team2 phụ trách kiểm chứng/nghiệm thu bộ
Golden chung. Kết quả trên là kiểm tra trước bàn giao của Team3, không phải Team2
đã duyệt. Phần đóng góp/hợp nhất của Team3 hoàn tất; chờ Team2 kết luận dataset.

Đã thay author mang danh tính người dùng bằng vai trò Nhóm đóng góp theo yêu cầu
riêng tư đã chốt; không đổi nội dung pháp lý. Số liệu bảo toàn38/40 tính không gồm
metadata author; IDs điều chỉnh metadata được lưu trong checks.json ignored.
