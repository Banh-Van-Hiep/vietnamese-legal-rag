# Báo Cáo Đánh Giá Benchmark RAG v2 — Tuần 9 (VLRA-T2-26, VLRA-68)
**Thực hiện bởi:** Người 2 (Verification Engine & Benchmark Suite)  
**Người nhận bàn giao:** Người 1 (Đạt — Core Pipeline & Prompting)  
**Thời điểm thực thi:** 06/11/2026 20:19:23  
**Nhãn đánh giá:** `EXPLORATORY` *(Do tập Dev Set 70/110 câu của Team 1 chưa đóng băng)*  

---

## 1. Thông Tin Môi Trường & Cấu Hình Thử Nghiệm

| Thông số cấu hình | Giá trị thiết lập | Ghi chú |
| :--- | :--- | :--- |
| **Git Commit SHA** | `0799e076de` | Nhánh `feature/team2-rag` |
| **Tập dữ liệu Golden** | `team2_rag/data/golden/golden_phase1_30cai.json` | Hash SHA-256: `a9da43c9dd1c...` |
| **Mô hình LLM Benchmark** | `gemini-3.1-flash-lite` | Chạy thật qua Google API v1beta |
| **Trạng thái Fallback Model** | `TẮT (LLM_ALLOW_FALLBACK=false)` | Bảo đảm 100% câu hỏi do đúng model cấu hình xử lý |
| **Ngân sách thời gian Pipeline** | `45.0s` trần toàn luồng | Trần chỉ kiểm tra giữa các bước trong `RAGPipeline.query`; runner gọi từng bước riêng nên không áp dụng khi benchmark. Giới hạn từng bước: LLM <= 30s, Retrieval <= 10s, Rerank <= 4s |
| **Tham số Retrieval** | `RAG_TOP_K=5`, `weights=(0.5, 1.0)` | BM25 + Qdrant Dense |
| **Cấu hình Reranker** | `enabled=False`, `timeout=4.0s` | Tắt rerank (không chạy BGE-Reranker) |
| **Cơ chế Claims & Verifier** | `include_claims=True`, `verifier=verify_response` | Kích hoạt bộ kiểm định 2 tầng Người 2 |

---

## 2. Kết Quả 3 Chỉ Số Cốt Lõi

| Chỉ số đánh giá | Giá trị thực tế | Mốc mục tiêu | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Citation Correctness** | **100.00%** | >= 90.00% | ✅ ĐẠT |
| **Citation Coverage** | **98.51%** | >= 85.00% | ✅ ĐẠT |
| **Query-level Hallucination Rate** | **4.00%** | <= 5.00% | ✅ ĐẠT |
| **Claim-level Hallucination Rate** | **1.49%** | Tham chiếu | Bổ sung theo yêu cầu Người 1 |

> [!NOTE]
> **Ghi chú về mẫu số và giới hạn của bộ kiểm định (Lexical Heuristic):**
> - Mốc Hallucination 4.00% (1/25 câu answered) được đo trên **25 câu trả lời thực tế** (5 câu `insufficient_context` bị loại khỏi mẫu số theo đúng định nghĩa chuẩn). Toàn bộ kết quả mang nhãn **`EXPLORATORY`** do tập Dev Set 70/110 câu của Team 1 chưa đóng băng.
> - Con số 4.00% phản ánh khả năng phát hiện của bộ kiểm định đối chiếu từ vựng (Lexical Overlap) kết hợp nhận diện phân cực quyền hạn/cấm đoán. Đây là bộ lọc kỹ thuật rule-based nhanh, có thể bỏ sót các dạng mâu thuẫn ngữ nghĩa phức tạp (như đảo phủ định tinh vi mà không chứa từ khóa phân cực rõ ràng). Tỷ lệ này chưa phải tỷ lệ ảo giác ngữ nghĩa tuyệt đối của mô hình NLI sâu.
> - Mọi trường hợp không có mẫu số (0 citation / 0 claim / 0 answered) được ghi rõ `"chưa đo"`, tuyệt đối không tính 100% giả định.
> - Có **2 claim** khẳng định nguồn "không quy định": đối chiếu từ vựng không kiểm chứng được sự vắng mặt, nhưng các claim này vẫn nằm trong mẫu số Coverage.

---

## 3. Thống Kê Tổng Quan Theo Nhóm Câu

- **Tổng số câu hỏi đánh giá:** 30
- **Số câu trả lời được (Answered):** 25
- **Số câu hệ thống từ chối (Insufficient Context):** 5
- **Số câu gặp lỗi kỹ thuật (Error):** 0
- **Tổng số nhận định (Claims) phân tích:** 67 (Hợp lệ: 66, Nghi vấn: 1)
- **Tổng số trích dẫn (Citations) thẩm định:** 72 (Hợp lệ: 72, Bất thường: 0)

---

## 4. Phân Tích Ca Thất Bại Bàn Giao Cho Người 1 (VLRA-T2-27)

Tổng số ca thất bại / cần tinh chỉnh: **1**

### Phân loại nguyên nhân lỗi:
- **Claim không có nguồn (nội dung khẳng định không có trong điều luật)**: 1 ca

### Chi tiết từng ca lỗi:
#### Ca 1: `gold_002`
- **Câu hỏi:** Những ai thuộc đối tượng áp dụng của Luật Doanh nghiệp?
- **Nhóm lỗi:** `claim không có nguồn (nội dung khẳng định không có trong điều luật)`
- **Lý do chi tiết:** [C1]: Nội dung claim không tìm thấy căn cứ xác thực trong chunk được trích dẫn (Độ bao phủ chỉ đạt 20.0%). Nguy cơ Hallucination.
- **Trích xuất câu trả lời:** _Đối tượng áp dụng của Luật Doanh nghiệp bao gồm doanh nghiệp [C1]._
---

## 5. Phân Tích 5 Ca Hệ Thống Từ Chối Trả Lời (Insufficient Context)

Trong 30 câu của tập Golden, có **5 câu hỏi có đáp án pháp lý nhưng hệ thống trả lời `insufficient_context`** (tỷ lệ từ chối 16.67%).

> [!IMPORTANT]
> **Trạng thái kết luận (cập nhật 08/11):** Lượt chạy 06/11 không lưu danh sách chunk nên chưa kết luận được nguyên nhân từng ca. Đã có bằng chứng: gold_003 và gold_014 là lỗi retrieval (chunk then chốt không nằm trong context); gold_019 phù hợp lỗi retrieval ở `top_k=5`. Với gold_001 và gold_006, chunk đúng nằm trong top 5 của Hybrid ở lượt Colab 02/11, nên chưa thể quy cho `top_k=5`. Prompt v3 từ chối đúng khi context thiếu căn cứ; chưa có bằng chứng prompt gây từ chối nhầm. Cần chạy lại ở cấu hình mặc định (runner nay lưu chunk) rồi dùng "Chẩn đoán từ chunk" để kết luận.

### Chi tiết 5 ca từ chối:

#### 1. `gold_001`
- **Câu hỏi:** *Luật Doanh nghiệp quy định về những vấn đề gì?*
- **Căn cứ pháp lý mục tiêu:** Điều 1 Luật Doanh nghiệp 2020 (Phạm vi điều chỉnh).
- **Giả thuyết ban đầu (chưa kiểm chứng):** Câu hỏi rộng, BM25 bị nhiễu do từ khóa "Luật Doanh nghiệp" xuất hiện ở hàng trăm chunk, khiến chunk Điều 1 bị trôi khỏi Top 5.
- **Bằng chứng bổ sung:** Colab 02/11 (Hybrid 1:1): chunk Điều 1 hạng 2, tức trong top 5. Chẩn đoán BM25-only top_k=10: câu được trả lời dù chunk Điều 1 không nằm trong context (chưa kiểm tra nội dung). Chưa kết luận được cho Hybrid 0,5:1.
- **Phản hồi của hệ thống:** _"Dữ liệu cung cấp không chứa thông tin tổng quát về phạm vi điều chỉnh hoặc các vấn đề mà Luật Doanh nghiệp quy định, mà chỉ cung cấp định nghĩa về vốn có quyền biểu quyết và quy định về chế độ làm việc của Hội đồng thành viên."_

#### 2. `gold_003`
- **Câu hỏi:** *Theo Luật Doanh nghiệp, cổ đông là ai?*
- **Căn cứ pháp lý mục tiêu:** Khoản 3 Điều 4 Luật Doanh nghiệp 2020 (Giải thích từ ngữ: Cổ đông).
- **Giả thuyết ban đầu (chưa kiểm chứng):** Retrieval trả về các chunk nói về cổ đông sáng lập và cổ đông ngoại, thiếu chunk định nghĩa chung tại Khoản 3 Điều 4.
- **Bằng chứng bổ sung:** Colab 02/11: chunk đúng không có trong Hybrid top 20. Chẩn đoán BM25-only top_k=10: vẫn từ chối, 0/1 chunk đúng trong context. Phù hợp lỗi retrieval.
- **Phản hồi của hệ thống:** _"Các tài liệu được cung cấp không chứa quy định định nghĩa cụ thể về việc cổ đông là ai, mà chỉ đề cập đến các loại cổ đông như cổ đông sáng lập, cổ đông là nhà đầu tư nước ngoài..."_

#### 3. `gold_006`
- **Câu hỏi:** *Công ty TNHH hai thành viên trở lên được có tối thiểu và tối đa bao nhiêu thành viên? Thành viên có thể là tổ chức không?*
- **Căn cứ pháp lý mục tiêu:** Khoản 1 Điều 46 Luật Doanh nghiệp 2020 (Từ 02 đến 50 thành viên, là cá nhân hoặc tổ chức).
- **Giả thuyết ban đầu (chưa kiểm chứng):** Retrieval bốc trúng Điều 47 (góp vốn), thiếu Điều 46 (định nghĩa và biên độ số lượng thành viên).
- **Bằng chứng bổ sung:** Colab 02/11: chunk Điều 46 hạng 2, tức trong top 5. Chẩn đoán BM25-only top_k=10: được trả lời, chunk đúng nằm trong context. Chưa quy được cho top_k=5 với Hybrid.
- **Phản hồi của hệ thống:** _"Các tài liệu pháp luật được cung cấp không chứa thông tin về số lượng thành viên tối thiểu và tối đa của công ty trách nhiệm hữu hạn hai thành viên trở lên..."_

#### 4. `gold_014`
- **Câu hỏi:** *Điều lệ công ty phải quy định những nội dung chủ yếu nào theo Điều 24 Luật Doanh nghiệp?*
- **Căn cứ pháp lý mục tiêu:** Khoản 2 Điều 24 Luật Doanh nghiệp 2020 (Nội dung chủ yếu của Điều lệ).
- **Giả thuyết ban đầu (chưa kiểm chứng):** Retrieval lấy trúng Khoản 1 & 3 (người ký Điều lệ), thiếu Khoản 2 (danh mục nội dung bắt buộc).
- **Bằng chứng bổ sung:** Colab 02/11: các chunk đúng ở hạng 1, 2, 4, 7. Chẩn đoán BM25-only top_k=10: vẫn từ chối vì Khoản 2 (danh mục nội dung chủ yếu) không có trong context dù Khoản 1, 3, 4 có; LLM từ chối đúng. Phù hợp lỗi retrieval.
- **Phản hồi của hệ thống:** _"Các văn bản pháp luật được cung cấp tại LEGAL CONTEXT chỉ quy định về thành phần ký tên trên Điều lệ công ty... không liệt kê các nội dung chủ yếu phải có trong Điều lệ công ty theo Điều 24..."_

#### 5. `gold_019`
- **Câu hỏi:** *Doanh nghiệp bị giải thể trong những trường hợp nào, phải đáp ứng điều kiện gì, và với trường hợp tự giải thể thì phải gửi hồ sơ cho cơ quan đăng ký kinh doanh theo các mốc thời hạn nào?*
- **Căn cứ pháp lý mục tiêu:** Điều 207 và Điều 208 Luật Doanh nghiệp 2020.
- **Giả thuyết ban đầu (chưa kiểm chứng):** Retrieval lấy trúng Điều 209 (giải thể cưỡng chế do thu hồi GCN), thiếu Điều 207 và 208.
- **Bằng chứng bổ sung:** Colab 02/11: chỉ 1/5 nhóm căn cứ nằm trong top 20, ở hạng 10. Chẩn đoán BM25-only top_k=10: được trả lời nhưng 0/5 chunk đúng trong context (chưa kiểm tra nội dung). Phù hợp lỗi retrieval ở top_k=5.
- **Phản hồi của hệ thống:** _"Dữ liệu cung cấp không chứa thông tin về các trường hợp doanh nghiệp bị giải thể nói chung, điều kiện giải thể... Nguồn hiện tại chỉ quy định về trình tự giải thể trong trường hợp bị thu hồi Giấy chứng nhận đăng ký doanh nghiệp hoặc theo quyết định của Tòa án."_
