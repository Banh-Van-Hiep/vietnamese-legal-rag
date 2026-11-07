# Báo Cáo Rà Soát Ngữ Nghĩa Thủ Công (Manual Audit) Mẫu Claims Đạt Chuẩn — Blocker 7

**Thực hiện bởi:** Người 2 (Verification Engine & Benchmark Suite)  
**Người nhận:** Người 1 (Đạt — Core Pipeline & Prompting)  
**Thời điểm thực hiện:** 08/11/2026  
**Mục đích:** Khảo sát thực tế tỷ lệ bỏ sót mâu thuẫn (False Negative) của bộ kiểm định đối chiếu từ vựng (`rubric.py`) trên các nhận định được gán nhãn `SUPPORTED`, giải quyết Blocker 7 trong kế hoạch Tuần 9.

---

## 1. Phương Pháp Lấy Mẫu & Tiêu Chí Đánh Giá

- **Kích thước mẫu:** 20 claims được trích xuất phân tầng từ 25 câu hỏi được trả lời (`status = answered`) trong đợt chạy Benchmark 30 câu (Golden Phase 1, `gemini-3.1-flash-lite`).
- **Quy trình thẩm định:**
  1. Đọc nội dung nhận định pháp lý (`claim_text`).
  2. Đối chiếu trực tiếp với từng chunk văn bản luật nguồn được trích dẫn (`cited_citations`).
  3. Kiểm tra xem có hiện tượng: đảo phủ định, mâu thuẫn điều kiện/ngoại lệ, thêm thắt nội dung không có trong luật hay không.

---

## 2. Bảng Kết Quả Thẩm Định Chi Tiết (20 Claims)

| STT | Query ID | Claim ID | Nội dung Claim | Căn cứ Chunk trích dẫn | Kết quả thẩm định thủ công | Ghi chú ngữ nghĩa |
| :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| 1 | `gold_004` | K1 | TNHH 1TV tăng vốn điều lệ do chủ sở hữu góp thêm hoặc huy động thêm. | Khoản 1 Điều 87 Luật DN | ✅ **ĐÚNG** | Khớp ngữ nghĩa quy định pháp luật. |
| 2 | `gold_004` | K2 | Chủ sở hữu quyết định hình thức và mức tăng vốn điều lệ. | Khoản 2 Điều 87 Luật DN | ✅ **ĐÚNG** | Khớp hoàn toàn thẩm quyền chủ sở hữu. |
| 3 | `gold_005` | K1 | Quyền tuyển dụng, thuê và sử dụng lao động theo pháp luật lao động. | Khoản 4 Điều 7 Luật DN | ✅ **ĐÚNG** | Đúng nguyên văn tinh thần Điều 7. |
| 4 | `gold_005` | K2 | Quyền khiếu nại, tham gia tố tụng theo quy định pháp luật. | Khoản 7 Điều 7 Luật DN | ✅ **ĐÚNG** | Đúng quyền tố tụng của doanh nghiệp. |
| 5 | `gold_007` | K1 | Thành viên TNHH 2TV góp vốn trong thời hạn 90 ngày kể từ ngày cấp ĐKDN. | Khoản 2 Điều 47 Luật DN | ✅ **ĐÚNG** | Đúng thời hạn luật định. |
| 6 | `gold_007` | K2 | Thời gian vận chuyển, nhập khẩu, thủ tục hành chính không tính vào thời hạn góp vốn. | Khoản 2 Điều 47 Luật DN | ✅ **ĐÚNG** | Đúng ngoại lệ loại trừ của luật ("không kể thời gian..."). |
| 7 | `gold_008` | K1 | Chuyển quyền sở hữu tài sản góp vốn không phải chịu lệ phí trước bạ. | Khoản 2 Điều 35 Luật DN | ✅ **ĐÚNG** | Đúng miễn lệ phí trước bạ khi góp vốn. |
| 8 | `gold_009` | K1 | Công ty cổ phần có số lượng cổ đông tối thiểu là 03. | Điểm b Khoản 1 Điều 111 | ✅ **ĐÚNG** | Đúng số lượng tối thiểu. |
| 9 | `gold_009` | K2 | Không hạn chế số lượng cổ đông tối đa của công ty cổ phần. | Điểm b Khoản 1 Điều 111 | ✅ **ĐÚNG** | Khớp quy định không giới hạn trần cổ đông. |
| 10 | `gold_010` | K1 | Doanh nghiệp tư nhân không được phát hành bất kỳ loại chứng khoán nào. | Khoản 2 Điều 188 Luật DN | ✅ **ĐÚNG** | Đúng quy định cấm phát hành chứng khoán DNTN. |
| 11 | `gold_011` | K1 | Cấm hành vi gây chậm trễ, phiền hà, cản trở, sách nhiễu người thành lập DN. | Khoản 3 Điều 16 Luật DN | ✅ **ĐÚNG** | Đúng hành vi bị nghiêm cấm của cơ quan ĐKKD. |
| 12 | `gold_011` | K2 | Cấm hoạt động dưới hình thức DN mà không đăng ký. | Khoản 1 Điều 16 Luật DN | ✅ **ĐÚNG** | Đúng hành vi kinh doanh không phép. |
| 13 | `gold_012` | K1 | Hồ sơ ĐKDN công ty hợp danh gồm Điều lệ, Danh sách thành viên, giấy tờ pháp lý. | Điều 20 Luật DN | ✅ **ĐÚNG** | Đúng thành phần hồ sơ cơ bản. |
| 14 | `gold_012` | K2 | Đã kê khai số định danh cá nhân thì không cần bản sao giấy tờ pháp lý cá nhân. | Khoản 1 Điều 11 NĐ 168/2025 | ✅ **ĐÚNG** | Cập nhật chính xác quy định liên kết văn bản mới. |
| 15 | `gold_013` | K1 | Giấy đề nghị ĐKDN bao gồm nội dung về tên doanh nghiệp. | Khoản 1 Điều 23 Luật DN | ✅ **ĐÚNG** | Đúng nội dung bắt buộc. |
| 16 | `gold_013` | K2 | Giấy đề nghị ĐKDN bao gồm nội dung về ngành, nghề kinh doanh. | Khoản 3 Điều 23 Luật DN | ✅ **ĐÚNG** | Đúng nội dung bắt buộc. |
| 17 | `gold_015` | K1 | Giấy chứng nhận ĐKDN gồm tên và mã số doanh nghiệp. | Khoản 1, 2 Điều 28 Luật DN | ✅ **ĐÚNG** | Đúng nội dung cốt lõi của Giấy chứng nhận. |
| 18 | `gold_015` | K2 | Giấy chứng nhận ĐKDN gồm địa chỉ trụ sở chính. | Khoản 3 Điều 28 Luật DN | ✅ **ĐÚNG** | Đúng thông tin trụ sở chính. |
| 19 | `gold_016` | K1 | Công ty TNHH 2TV trở lên có từ 02 đến 50 thành viên. | Khoản 1 Điều 46 Luật DN | ✅ **ĐÚNG** | Đúng biên độ số lượng thành viên. |
| 20 | `gold_016` | K2 | Thành viên TNHH 2TV chịu trách nhiệm về các khoản nợ trong phạm vi số vốn đã góp. | Điểm b Khoản 1 Điều 46 | ✅ **ĐÚNG** | Đúng nguyên tắc trách nhiệm hữu hạn. |

---

## 3. Kết Luận & Đánh Giá Tác Động (Blocker 7)

1. **Tỷ lệ bỏ sót mâu thuẫn (False Negative Rate) trên mẫu kiểm tra:** **0.00% (0/20 claims)**.
   - Toàn bộ 20/20 claims được `rubric.py` đánh giá SUPPORTED khi kiểm tra thủ công đều là khẳng định pháp lý chuẩn xác, không có hiện tượng mâu thuẫn đối lập hoặc suy diễn sai lệch so với văn bản gốc.
   - Lý do: Bản thân mô hình `gemini-3.1-flash-lite` tuân thủ rất nghiêm ngặt System Prompt v3 (chỉ trích xuất từ LEGAL CONTEXT và giữ nguyên điều kiện/ngoại lệ).
2. **Khẳng định về giá trị của chỉ số Hallucination 4.00%:**
   - Bộ lọc Lexical Heuristic hiện tại hoàn thành tốt nhiệm vụ lọc thô trong môi trường thời gian thực (inline verification < 10ms).
   - Con số **4.00%** (1/25 câu) phản ánh đúng nguy cơ hallucination do trích dẫn chunk không đủ thông tin (`gold_002`).
   - Mặc dù vậy, nhóm vẫn giữ nguyên nhãn **`EXPLORATORY`** cho mốc này theo đúng thỏa thuận với Người 1, vì phương pháp rule-based về mặt lý thuyết vẫn có thể bỏ sót mâu thuẫn đảo phủ định tinh vi nếu LLM sinh câu với cấu trúc ngữ pháp phức tạp.
