# Báo Cáo Đánh Giá Benchmark RAG v2 — Tuần 9 (VLRA-T2-26, VLRA-68)
**Thực hiện bởi:** Người 2 (Verification Engine & Benchmark Suite)  
**Người nhận bàn giao:** Người 1 (Đạt — Core Pipeline & Prompting)  
**Thời điểm thực thi:** 06/11/2026 18:02:32  
**Nhãn đánh giá:** `EXPLORATORY` *(Do tập Dev Set 70/110 câu của Team 1 chưa đóng băng)*  

---

## 1. Thông Tin Môi Trường & Cấu Hình Thử Nghiệm

| Thông số cấu hình | Giá trị thiết lập | Ghi chú |
| :--- | :--- | :--- |
| **Git Commit SHA** | `ddfda129be` | Nhánh `feature/team2-rag` |
| **Tập dữ liệu Golden** | `team2_rag\data\golden\golden_phase1_30cai.json` | Hash SHA-256: `298ae763fed0...` |
| **Mô hình LLM Benchmark** | `gemini-3.1-flash-lite` | Chạy thật qua Google API v1beta |
| **Trạng thái Fallback Model** | `TẮT (LLM_ALLOW_FALLBACK=false)` | Bảo đảm 100% câu hỏi do đúng model cấu hình xử lý |
| **Ngân sách thời gian Pipeline** | `45.0s` trần toàn luồng | Cưỡng chế trần NFR-07 (LLM <= 30s, Retrieval <= 10s, Rerank <= 4s) |
| **Tham số Retrieval** | `RAG_TOP_K=5`, `weights=(0.5, 1.0)` | BM25 + Qdrant Dense |
| **Cấu hình Reranker** | `enabled=False`, `timeout=4.0s` | BGE-Reranker-v2-m3 |
| **Cơ chế Claims & Verifier** | `include_claims=True`, `verifier=verify_response` | Kích hoạt bộ kiểm định 2 tầng Người 2 |

---

## 2. Kết Quả 3 Chỉ Số Cốt Lõi

| Chỉ số đánh giá | Giá trị thực tế | Mốc mục tiêu | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Citation Correctness** | **100.00%** | >= 90.00% | ✅ ĐẠT |
| **Citation Coverage** | **92.54%** | >= 85.00% | ✅ ĐẠT |
| **Query-level Hallucination Rate** | **20.00%** | <= 5.00% | ❌ CHƯA ĐẠT |
| **Claim-level Hallucination Rate** | **7.46%** | Tham chiếu | Bổ sung theo yêu cầu Người 1 |

*Ghi chú:* Các trường hợp không có mẫu số (0 citation / 0 claim / 0 answered) được ghi rõ `"chưa đo"`, tuyệt đối không tính 100% giả định.

---

## 3. Thống Kê Tổng Quan Theo Nhóm Câu

- **Tổng số câu hỏi đánh giá:** 30
- **Số câu trả lời được (Answered):** 25
- **Số câu hệ thống từ chối (Insufficient Context):** 5
- **Số câu gặp lỗi kỹ thuật (Error):** 0
- **Tổng số nhận định (Claims) phân tích:** 67 (Hợp lệ: 62, Nghi vấn: 5)
- **Tổng số trích dẫn (Citations) thẩm định:** 72 (Hợp lệ: 72, Bất thường: 0)

---

## 4. Phân Tích Ca Thất Bại Bàn Giao Cho Người 1 (VLRA-T2-27)

Tổng số ca thất bại / cần tinh chỉnh: **5**

### Phân loại nguyên nhân lỗi:
- **Claim không có nguồn (nội dung khẳng định không có trong điều luật)**: 5 ca

### Chi tiết từng ca lỗi:
#### Ca 1: `gold_002`
- **Câu hỏi:** Những ai thuộc đối tượng áp dụng của Luật Doanh nghiệp?
- **Nhóm lỗi:** `claim không có nguồn (nội dung khẳng định không có trong điều luật)`
- **Lý do chi tiết:** [C1]: Nội dung claim không tìm thấy căn cứ xác thực trong chunk được trích dẫn (Độ bao phủ chỉ đạt 20.0%). Nguy cơ Hallucination.
- **Trích xuất câu trả lời:** _Đối tượng áp dụng của Luật Doanh nghiệp bao gồm doanh nghiệp [C1]._

#### Ca 2: `gold_007`
- **Câu hỏi:** Thành viên công ty TNHH hai thành viên trở lên phải góp đủ vốn đã cam kết trong bao lâu? Thời gian vận chuyển, nhập khẩu tài sản góp vốn và làm thủ tục chuyển quyền sở hữu có tính vào thời hạn này không?
- **Nhóm lỗi:** `claim không có nguồn (nội dung khẳng định không có trong điều luật)`
- **Lý do chi tiết:** [C1]: Phát hiện mâu thuẫn phân cực (phủ định/khẳng định) với điều luật. Độ trùng khớp từ vựng: 88.6% | [C2]: Phát hiện mâu thuẫn phân cực (phủ định/khẳng định) với điều luật. Độ trùng khớp từ vựng: 88.6%
- **Trích xuất câu trả lời:** _Thành viên công ty TNHH hai thành viên trở lên phải góp đủ và đúng loại tài sản đã cam kết trong thời hạn 90 ngày kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp [C1], [C2]. Thời gian vận chuyển, nhập khẩu tài sản góp vốn và thực hiện thủ tục hành chính để chuyển quyền sở hữu tài sản không _

#### Ca 3: `gold_017`
- **Câu hỏi:** Cổ đông công ty cổ phần chịu trách nhiệm về nợ của công ty trong phạm vi nào và có những nghĩa vụ gì?
- **Nhóm lỗi:** `claim không có nguồn (nội dung khẳng định không có trong điều luật)`
- **Lý do chi tiết:** [C2]: Phát hiện mâu thuẫn phân cực (phủ định/khẳng định) với điều luật. Độ trùng khớp từ vựng: 100.0% | [C3]: Phát hiện mâu thuẫn phân cực (phủ định/khẳng định) với điều luật. Độ trùng khớp từ vựng: 100.0%
- **Trích xuất câu trả lời:** _Cổ đông công ty cổ phần chỉ chịu trách nhiệm về các khoản nợ và nghĩa vụ tài sản khác của doanh nghiệp trong phạm vi số vốn đã góp vào doanh nghiệp [C1]. Cổ đông không được rút vốn đã góp bằng cổ phần phổ thông ra khỏi công ty dưới mọi hình thức, trừ trường hợp được công ty hoặc người khác mua lại c_

#### Ca 4: `gold_023`
- **Câu hỏi:** Theo văn bản hợp nhất Nghị định hướng dẫn Luật Doanh nghiệp (7566/VBHN-BKHĐT), doanh nghiệp xã hội được xác định theo quy định nào, phải duy trì những cam kết gì và ai phải chịu trách nhiệm liên đới khi doanh nghiệp xã hội vi phạm?
- **Nhóm lỗi:** `claim không có nguồn (nội dung khẳng định không có trong điều luật)`
- **Lý do chi tiết:** [C1]: Phát hiện mâu thuẫn phân cực (phủ định/khẳng định) với điều luật. Độ trùng khớp từ vựng: 100.0%
- **Trích xuất câu trả lời:** _Doanh nghiệp xã hội phải duy trì mục tiêu xã hội, môi trường, mức lợi nhuận giữ lại để tái đầu tư và các nội dung khác ghi tại Cam kết thực hiện mục tiêu xã hội, môi trường trong suốt quá trình hoạt động [C1]. Các đối tượng chịu trách nhiệm liên đới đối với các thiệt hại phát sinh khi doanh nghiệp x_

#### Ca 5: `gold_030`
- **Câu hỏi:** Doanh nghiệp tạm ngừng kinh doanh phải gửi thông báo trước ít nhất mấy ngày làm việc, hồ sơ gồm những giấy tờ nào, và hành vi không thông báo tạm ngừng kinh doanh bị xử phạt thế nào?
- **Nhóm lỗi:** `claim không có nguồn (nội dung khẳng định không có trong điều luật)`
- **Lý do chi tiết:** [C1]: Phát hiện mâu thuẫn phân cực (phủ định/khẳng định) với điều luật. Độ trùng khớp từ vựng: 100.0%
- **Trích xuất câu trả lời:** _Doanh nghiệp phải gửi hồ sơ thông báo tạm ngừng kinh doanh đến Cơ quan đăng ký kinh doanh cấp tỉnh chậm nhất 03 ngày làm việc trước ngày tạm ngừng kinh doanh [C1]. Thời hạn tạm ngừng của mỗi lần thông báo không được quá 12 tháng [C1]. LEGAL CONTEXT hiện tại không quy định về thành phần hồ sơ cụ thể _

