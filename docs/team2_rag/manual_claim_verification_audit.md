# Báo Cáo Rà Soát Ngữ Nghĩa Thủ Công (Manual Audit) Mẫu Claims Đạt Chuẩn — Blocker 7

**Thực hiện bởi:** Người 2 (Verification Engine & Benchmark Suite)  
**Người nhận:** Người 1 (Đạt — Core Pipeline & Prompting)  
**Thời điểm thực hiện:** 08/11/2026  
**Mục đích:** Khảo sát thực tế tỷ lệ bỏ sót mâu thuẫn (False Negative) của bộ kiểm định đối chiếu từ vựng (`rubric.py`) trên các nhận định được gán nhãn `SUPPORTED`, giải quyết Blocker 7 trong kế hoạch Tuần 9.

---

## 1. Phương Pháp Lấy Mẫu & Tiêu Chí Đánh Giá

- **Kích thước mẫu (đợt 1, Người 2):** 20 claims thuộc gold_004 đến gold_016 (11/25 câu được trả lời; 27 claims trong nhóm này). Không phân tầng. Đợt 2 (Người 1, mục 4) bổ sung 39 claims của 13 câu còn lại (gold_017 đến gold_030). Nguồn: đợt chạy 30 câu (Golden Phase 1, `gemini-3.1-flash-lite`).
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

## 3. Kết Luận Đợt 1 (20 claims)

- Trong 20 claims, không thấy mâu thuẫn hay thêm thắt. Lưu ý gold_012 K1 có nhãn `PARTIAL` trong kết quả gốc nhưng bảng trên ghi "ĐÚNG": nội dung đúng nhưng chưa nêu đủ thành phần hồ sơ.
- 0/20 không chứng minh tỷ lệ bỏ sót bằng 0%: với 20 mẫu, tỷ lệ thật vẫn có thể đến khoảng 14%.
- Đợt 1 chỉ gồm 11 câu đầu. Kết luận chung phải dựa trên mục 4.

---

## 4. Đợt 2 (Người 1 làm thay Người 2, 08/11/2026): 39 claims của gold_017 đến gold_030

**Cách làm.** Với mỗi claim, đối chiếu với nội dung các chunk trong `gold_chunk_ids` của câu đó (đọc từ `data/doanh-nghiep/processed/chunks.jsonl`) và tìm cụm từ chính trong toàn corpus khi claim không nằm trong gold chunk. Kết quả chạy không lưu chunk đã được trích dẫn, nên đây là đối chiếu với điều luật đúng, không phải với context mà LLM thực sự nhận. Runner đã sửa để lần chạy sau lưu `retrieved_chunk_ids`, `context_chunk_ids`.

| Câu | Số claim | Khớp điều luật | Chưa đối chiếu được | Nhãn SUPPORTED nhưng claim chỉ nói "nguồn không quy định" |
| :--- | :---: | :---: | :---: | :---: |
| gold_017 | 3 | 3 | 0 | 0 |
| gold_018 | 3 | 3 | 0 | 0 |
| gold_020 | 3 | 3 | 0 | 0 |
| gold_021 | 4 | 2 | 2 (K2, K4) | 0 |
| gold_022 | 2 | 2 | 0 | 0 |
| gold_023 | 2 | 2 | 0 | 0 |
| gold_024 | 2 | 2 | 0 | 0 |
| gold_025 | 4 | 3 | 1 (K4) | 0 |
| gold_026 | 4 | 3 | 0 | 1 (K4) |
| gold_027 | 2 | 1 | 0 | 1 (K2) |
| gold_028 | 4 | 3 | 1 (K4) | 0 |
| gold_029 | 4 | 2 | 2 (K3, K4) | 0 |
| gold_030 | 2 | 0 | 2 (K1, K2) | 0 |
| **Tổng** | **39** | **29** | **8** | **2** |

**Phát hiện chính.** Không thấy claim đảo phủ định hay mâu thuẫn trực tiếp với điều luật. Nhưng có 2 claim dạng "nguồn không quy định…" được gán `SUPPORTED`:
- gold_026 K4: "LEGAL CONTEXT hiện tại không quy định về biện pháp khắc phục hậu quả". Điều 58 khoản 2 Nghị định 122/2021/NĐ-CP quy định "Buộc thực hiện thủ tục giải thể", và câu hỏi gốc hỏi đúng biện pháp này.
- gold_027 K2: "Nghị định 288/2026/NĐ-CP không quy định cụ thể về xử phạt hành vi chậm đăng ký thay đổi nội dung". Điều 2 của Nghị định 288/2026/NĐ-CP (các khoản 1 đến 7) chứa nội dung "Điều 44. Vi phạm về thời hạn đăng ký thay đổi nội dung…", tức là có quy định đúng nội dung đó.

Cả hai có thể đúng với context LLM nhận (nếu Điều 58 khoản 2 Nghị định 122/2021 và Điều 2 Nghị định 288/2026 không lọt vào context), nhưng bộ kiểm không thể biết, và nhãn `SUPPORTED` lại xuất phát từ độ trùng từ vựng với một chunk không nói điều đó (62,5% và 70,6%). Đây là điểm yếu thật: claim "không có quy định" không kiểm chứng được bằng đối chiếu từ vựng, và nó cũng cho thấy câu trả lời thiếu ý do retrieval.

## 5. Kết Luận Chung (59 claims đã rà: 20 của đợt 1, 39 của đợt 2)

1. Không thấy đảo phủ định hay thêm thắt sai luật. Điểm yếu đã biết (bỏ sót đảo phủ định) chưa xuất hiện trong mẫu này, nhưng mẫu chỉ có 59/67 claims và đối chiếu thủ công bởi một người.
2. Có 2/59 claim (khoảng 3,4%) gán `SUPPORTED` sai bản chất: đều là claim về việc nguồn không có quy định.
3. 8 claim còn lại chưa tìm được điều luật tương ứng trong phần đã đọc (không có nghĩa là sai).
4. Đề xuất cho bộ kiểm (chờ hai người chốt công thức T2-25, chưa sửa code): gắn nhãn riêng (ví dụ `UNVERIFIABLE`) cho claim "nguồn không quy định…" và loại khỏi mẫu số Coverage. Nếu loại hai claim này, Coverage đổi từ 98,51% (66/67) sang khoảng 98,46% (64/65); Hallucination mức câu không đổi.
5. Mốc Hallucination 4,00% giữ nhãn **`EXPLORATORY`**.
