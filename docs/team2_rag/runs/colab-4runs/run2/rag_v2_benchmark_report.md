# Báo Cáo Đánh Giá Benchmark RAG v2 — Tuần 9 (VLRA-T2-26, VLRA-68)
**Thực hiện bởi:** Người 2 (Verification Engine & Benchmark Suite)  
**Người nhận bàn giao:** Người 1 (Đạt — Core Pipeline & Prompting)  
**Thời điểm thực thi:** 10/11/2026 08:48:14  
**Nhãn đánh giá:** `EXPLORATORY` *(Do tập Dev Set 70/110 câu của Team 1 chưa đóng băng)*  

---

## 1. Thông Tin Môi Trường & Cấu Hình Thử Nghiệm

| Thông số cấu hình | Giá trị thiết lập | Ghi chú |
| :--- | :--- | :--- |
| **Git Commit SHA** | `3b307fa835` | Nhánh `feature/team2-rag` |
| **Tập dữ liệu Golden** | `/content/vietnamese-legal-rag/team2_rag/data/golden/golden_phase1_30cai.json` | Hash SHA-256: `a9da43c9dd1c...` |
| **Mô hình LLM Benchmark** | `gemini-3.1-flash-lite` | Chạy thật qua Google API v1beta |
| **Trạng thái Fallback Model** | `TẮT (LLM_ALLOW_FALLBACK=false)` | Bảo đảm 100% câu hỏi do đúng model cấu hình xử lý |
| **Ngân sách thời gian Pipeline** | `45.0s` trần toàn luồng | Trần chỉ kiểm tra giữa các bước trong `RAGPipeline.query`; runner gọi từng bước riêng nên không áp dụng khi benchmark. Giới hạn từng bước: LLM <= 30s, Retrieval <= 10s, Rerank <= 4s |
| **Tham số Retrieval** | `RAG_TOP_K=10`, `weights=(0.5, 1.0)` | BM25 + Qdrant Dense |
| **Cấu hình Reranker** | `enabled=False`, `timeout=4.0s` | Tắt rerank (không chạy BGE-Reranker) |
| **Cơ chế Claims & Verifier** | `include_claims=True`, `verifier=verify_response` | Kích hoạt bộ kiểm định 2 tầng Người 2 |

---

## 2. Kết Quả 3 Chỉ Số Cốt Lõi

| Chỉ số đánh giá | Giá trị thực tế | Mốc mục tiêu | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Citation Correctness** | **100.00%** | >= 90.00% | ✅ ĐẠT |
| **Citation Coverage** | **96.67%** | >= 85.00% | ✅ ĐẠT |
| **Query-level Hallucination Rate** | **11.11%** | <= 5.00% | ❌ CHƯA ĐẠT |
| **Claim-level Hallucination Rate** | **3.33%** | Tham chiếu | Bổ sung theo yêu cầu Người 1 |

> [!NOTE]
> **Ghi chú về mẫu số và giới hạn của bộ kiểm định (Lexical Heuristic):**
> - Mốc Hallucination 11.11% (3/27 câu answered) được đo trên **27 câu trả lời thực tế** (3 câu `insufficient_context` hoặc lỗi bị loại khỏi mẫu số theo đúng định nghĩa). Toàn bộ kết quả mang nhãn **`EXPLORATORY`** do tập Dev Set 70/110 câu của Team 1 chưa đóng băng.
> - Con số 11.11% phản ánh khả năng phát hiện của bộ kiểm định đối chiếu từ vựng (Lexical Overlap) kết hợp nhận diện phân cực quyền hạn/cấm đoán. Đây là bộ lọc kỹ thuật rule-based nhanh, có thể bỏ sót các dạng mâu thuẫn ngữ nghĩa phức tạp (như đảo phủ định tinh vi mà không chứa từ khóa phân cực rõ ràng). Tỷ lệ này chưa phải tỷ lệ ảo giác ngữ nghĩa tuyệt đối của mô hình NLI sâu.
> - Mọi trường hợp không có mẫu số (0 citation / 0 claim / 0 answered) được ghi rõ `"chưa đo"`, tuyệt đối không tính 100% giả định.
> - Có **0 claim** khẳng định nguồn "không quy định": đối chiếu từ vựng không kiểm chứng được sự vắng mặt, nhưng các claim này vẫn nằm trong mẫu số Coverage.

---

## 3. Thống Kê Tổng Quan Theo Nhóm Câu

- **Tổng số câu hỏi đánh giá:** 30
- **Số câu trả lời được (Answered):** 27
- **Số câu hệ thống từ chối (Insufficient Context):** 0
- **Số câu gặp lỗi kỹ thuật (Error):** 3
- **Tổng số nhận định (Claims) phân tích:** 90 (Hợp lệ: 87, Nghi vấn: 3)
- **Tổng số trích dẫn (Citations) thẩm định:** 125 (Hợp lệ: 125, Bất thường: 0)

---

## 4. Phân Tích Ca Thất Bại Bàn Giao Cho Người 1 (VLRA-T2-27)

Tổng số ca thất bại / cần tinh chỉnh: **6**

### Phân loại nguyên nhân lỗi:
- **Claim không có nguồn (nội dung khẳng định không có trong điều luật)**: 3 ca
- **Hạ tầng llm (timeout, quá tải hoặc cấu hình; không phải lỗi prompt)**: 3 ca

### Chi tiết từng ca lỗi:
#### Ca 1: `gold_002`
- **Câu hỏi:** Những ai thuộc đối tượng áp dụng của Luật Doanh nghiệp?
- **Nhóm lỗi:** `claim không có nguồn (nội dung khẳng định không có trong điều luật)`
- **Lý do chi tiết:** [C1]: Nội dung claim không tìm thấy căn cứ xác thực trong chunk được trích dẫn (Độ bao phủ chỉ đạt 20.0%). Nguy cơ Hallucination. | [C2]: Nội dung claim không tìm thấy căn cứ xác thực trong chunk được trích dẫn (Độ bao phủ chỉ đạt 20.0%). Nguy cơ Hallucination.
- **Trích xuất câu trả lời:** _Đối tượng áp dụng của Luật Doanh nghiệp bao gồm doanh nghiệp [C1], [C2] và các cơ quan, tổ chức, cá nhân có liên quan đến việc thành lập, tổ chức quản lý, tổ chức lại, giải thể và hoạt động có liên quan của doanh nghiệp [C3], [C4]. Trong trường hợp luật khác có quy định đặc thù về các vấn đề nêu trê_

#### Ca 2: `gold_008`
- **Câu hỏi:** Khi thành viên góp vốn vào công ty TNHH bằng tài sản có đăng ký quyền sở hữu, việc chuyển quyền sở hữu tài sản đó cho công ty có phải chịu lệ phí trước bạ không?
- **Nhóm lỗi:** `hạ tầng LLM (timeout, quá tải hoặc cấu hình; không phải lỗi prompt)`
- **Lý do chi tiết:** Trạng thái: error
- **Trích xuất câu trả lời:** _Exception: LLMProviderError: gemini: HTTP 503_

#### Ca 3: `gold_016`
- **Câu hỏi:** Chủ sở hữu công ty TNHH một thành viên chịu trách nhiệm về các khoản nợ và nghĩa vụ tài sản khác của công ty trong phạm vi nào?
- **Nhóm lỗi:** `claim không có nguồn (nội dung khẳng định không có trong điều luật)`
- **Lý do chi tiết:** [C4]: Phát hiện mâu thuẫn phân cực (phủ định/khẳng định) với điều luật. Độ trùng khớp từ vựng: 80.6% | [C5]: Phát hiện mâu thuẫn phân cực (phủ định/khẳng định) với điều luật. Độ trùng khớp từ vựng: 80.6%
- **Trích xuất câu trả lời:** _Chủ sở hữu công ty TNHH một thành viên chịu trách nhiệm về các khoản nợ và nghĩa vụ tài sản khác của công ty trong phạm vi số vốn điều lệ của công ty [C1], [C2]. Ngoài ra, chủ sở hữu công ty chịu trách nhiệm bằng toàn bộ tài sản của mình đối với các nghĩa vụ tài chính của công ty và thiệt hại xảy ra_

#### Ca 4: `gold_019`
- **Câu hỏi:** Doanh nghiệp bị giải thể trong những trường hợp nào, phải đáp ứng điều kiện gì, và với trường hợp tự giải thể thì phải gửi hồ sơ cho cơ quan đăng ký kinh doanh theo các mốc thời hạn nào?
- **Nhóm lỗi:** `hạ tầng LLM (timeout, quá tải hoặc cấu hình; không phải lỗi prompt)`
- **Lý do chi tiết:** Trạng thái: error
- **Trích xuất câu trả lời:** _Exception: LLMTimeoutError: Hết thời gian chờ phản hồi từ LLM provider._

#### Ca 5: `gold_023`
- **Câu hỏi:** Theo văn bản hợp nhất Nghị định hướng dẫn Luật Doanh nghiệp (7566/VBHN-BKHĐT), doanh nghiệp xã hội được xác định theo quy định nào, phải duy trì những cam kết gì và ai phải chịu trách nhiệm liên đới khi doanh nghiệp xã hội vi phạm?
- **Nhóm lỗi:** `hạ tầng LLM (timeout, quá tải hoặc cấu hình; không phải lỗi prompt)`
- **Lý do chi tiết:** Trạng thái: error
- **Trích xuất câu trả lời:** _Exception: LLMProviderError: gemini: HTTP 503_

#### Ca 6: `gold_026`
- **Câu hỏi:** Công ty hết thời hạn hoạt động ghi trong Điều lệ mà không thực hiện thủ tục giải thể thì bị phạt bao nhiêu, phải khắc phục hậu quả thế nào và mức phạt đó áp dụng cho tổ chức hay cá nhân?
- **Nhóm lỗi:** `claim không có nguồn (nội dung khẳng định không có trong điều luật)`
- **Lý do chi tiết:** [C1]: Nội dung claim không tìm thấy căn cứ xác thực trong chunk được trích dẫn (Độ bao phủ chỉ đạt 28.1%). Nguy cơ Hallucination. | [C2]: Nội dung claim không tìm thấy căn cứ xác thực trong chunk được trích dẫn (Độ bao phủ chỉ đạt 25.0%). Nguy cơ Hallucination.
- **Trích xuất câu trả lời:** _Công ty không thực hiện thủ tục giải thể khi kết thúc thời hạn hoạt động ghi trong Điều lệ mà không có quyết định gia hạn sẽ bị phạt tiền từ 20.000.000 đồng đến 30.000.000 đồng [C1]. Ngoài ra, công ty còn bị buộc phải thực hiện thủ tục giải thể doanh nghiệp [C2]. Các quy định về xử phạt vi phạm hành_

