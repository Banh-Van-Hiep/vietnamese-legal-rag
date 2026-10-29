# Đặc tả hợp nhất Golden Dataset — VLRA24

**Đối chiếu:**29/10/2026. Nguồn: quyết định người dùng,
[task tuần5](../tasks.md), [ARCHITECTURE](../../../../docs/ARCHITECTURE.md) §8.2.

## Mục tiêu và phạm vi

Hợp nhất40 mẫu chung và10 đóng góp Team3 vào một nguồn duy nhất:
`team2_rag/data/golden/golden_phase1_30cai.json`. Xóa thư mục ground_truth riêng của
Team3 sau kiểm chứng. Giữ schema8 field, UTF-8/NFC và căn cứ snapshot thật.

## Clarify — quyết định 29/10/2026

- Người dùng cho phép sửa dữ liệu chung tại Team2 và xóa bản riêng Team3.
- Người dùng xác nhận Team2 phụ trách kiểm chứng Golden chung; Team3 thực hiện
  đóng góp/hợp nhất và kiểm tra trước bàn giao, không thay kết luận nghiệm thu Team2.
- Độc lập nghĩa là các câu kiểm tra ý chính khác nhau, không chỉ đổi cách diễn đạt.
  Cùng lĩnh vực/chunk không tự động là trùng.
- Thay gt_t3_001/003/011/013 bằng4 chủ đề mới, cấp gold_041–044. Giữ nguyên6 câu
  gt_t3_004/005/008/009/010/012, không đánh lại số ID.
- Thu hẹp gold_016 vào trách nhiệm chủ sở hữu TNHH một thành viên; thu hẹp gold_021
  vào thời hạn lưu thông tin sau giải thể/phá sản. Ghi rõ đây là sửa nội dung record.
- Kết quả49 answered/1 insufficient; không đổi nhãn cho đủ quota10 insufficient.

## Hành vi và tiêu chí nghiệm thu

- AC01: Đúng50 record, đủ8 field; ID/câu hỏi không trùng sau NFC/casefold/gộp khoảng trắng.
- AC02:49 answered có chunk thật;1 insufficient có lý do và gold_chunk_ids rỗng.
  Các câu mới dựa vào snapshot, không tự xác minh luật hiện hành ngoài corpus.
- AC03: Rà câu hỏi/đáp án của cả50 câu, ghi bảng ý định; xử lý4 cặp trùng và2 câu
  tổng hợp chồng lặp. Không dùng validator cú pháp để khẳng định độc lập ngữ nghĩa.
- AC04: Validator Team2 mặc định exit0; kiểm type/NFC/ID/chunk và record bảo toàn.
- AC05: Xóa3 file ground_truth Team3, cập nhật lệnh/tham chiếu và báo cáo tuần.
  Không sửa corpus/validator/app/schema hoặc tự thay quota/duyệt pháp lý.

## Phụ thuộc, lỗi và ngoài phạm vi

Phụ thuộc corpus Team1 và validator Team2 hiện hữu. Lỗi field/status/chunk hoặc
trùng ý chặn hoàn thành việc hợp nhất. Review pháp lý/hiệu lực và mapping P0 còn chờ
nhóm; không benchmark retrieval/LLM, freeze Dev/Test, sửa dịch vụ hoặc push.
