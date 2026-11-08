# Báo Cáo Đánh Giá Benchmark RAG v2 — Tuần 9 (VLRA-T2-26, VLRA-68)
**Thực hiện bởi:** Người 2 (Verification Engine & Benchmark Suite)  
**Người nhận bàn giao:** Người 1 (Đạt — Core Pipeline & Prompting)  
**Thời điểm thực thi:** 08/11/2026, chạy trên Colab (file kết quả không ghi giờ chạy chính xác)  
**Nhãn đánh giá:** `EXPLORATORY` *(Do tập Dev Set 70/110 câu của Team 1 chưa đóng băng)*  

---

## 1. Thông Tin Môi Trường & Cấu Hình Thử Nghiệm

| Thông số cấu hình | Giá trị thiết lập | Ghi chú |
| :--- | :--- | :--- |
| **Git Commit SHA** | `d1b32c3266` | Nhánh `feature/team2-rag` |
| **Tập dữ liệu Golden** | `team2_rag/data/golden/golden_phase1_30cai.json` | Hash SHA-256: `a9da43c9dd1c...` |
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
| **Citation Coverage** | **98.67%** | >= 85.00% | ✅ ĐẠT |
| **Query-level Hallucination Rate** | **3.85%** | <= 5.00% | ✅ ĐẠT |
| **Claim-level Hallucination Rate** | **1.33%** | Tham chiếu | Bổ sung theo yêu cầu Người 1 |

> [!NOTE]
> **Ghi chú về mẫu số và giới hạn của bộ kiểm định (Lexical Heuristic):**
> - Mốc Hallucination 3.85% (1/26 câu answered) được đo trên **26 câu trả lời thực tế** (1 câu `insufficient_context` bị loại khỏi mẫu số theo đúng định nghĩa). Toàn bộ kết quả mang nhãn **`EXPLORATORY`** do tập Dev Set 70/110 câu của Team 1 chưa đóng băng.
> - Con số 3.85% phản ánh khả năng phát hiện của bộ kiểm định đối chiếu từ vựng (Lexical Overlap) kết hợp nhận diện phân cực quyền hạn/cấm đoán. Đây là bộ lọc kỹ thuật rule-based nhanh, có thể bỏ sót các dạng mâu thuẫn ngữ nghĩa phức tạp (như đảo phủ định tinh vi mà không chứa từ khóa phân cực rõ ràng). Tỷ lệ này chưa phải tỷ lệ ảo giác ngữ nghĩa tuyệt đối của mô hình NLI sâu.
> - Mọi trường hợp không có mẫu số (0 citation / 0 claim / 0 answered) được ghi rõ `"chưa đo"`, tuyệt đối không tính 100% giả định.
> - Có **1 claim** khẳng định nguồn "không quy định": đối chiếu từ vựng không kiểm chứng được sự vắng mặt, nhưng các claim này vẫn nằm trong mẫu số Coverage.

---

## 3. Thống Kê Tổng Quan Theo Nhóm Câu

- **Tổng số câu hỏi đánh giá:** 30
- **Số câu trả lời được (Answered):** 26
- **Số câu hệ thống từ chối (Insufficient Context):** 1
- **Số câu gặp lỗi kỹ thuật (Error):** 3
- **Tổng số nhận định (Claims) phân tích:** 75 (Hợp lệ: 74, Nghi vấn: 1)
- **Tổng số trích dẫn (Citations) thẩm định:** 89 (Hợp lệ: 89, Bất thường: 0)

---

## 4. Phân Tích Ca Thất Bại Bàn Giao Cho Người 1 (VLRA-T2-27)

Tổng số ca thất bại / cần tinh chỉnh: **4**

### Phân loại nguyên nhân lỗi:
- **Claim không có nguồn (nội dung khẳng định không có trong điều luật)**: 1 ca
- **Nguồn sai (verification không qua)**: 2 ca
- **Prompt (llm trả sai form hoặc bị chặn nội dung)**: 1 ca

### Chi tiết từng ca lỗi:
#### Ca 1: `gold_002`
- **Câu hỏi:** Những ai thuộc đối tượng áp dụng của Luật Doanh nghiệp?
- **Nhóm lỗi:** `claim không có nguồn (nội dung khẳng định không có trong điều luật)`
- **Lý do chi tiết:** [C1]: Nội dung claim không tìm thấy căn cứ xác thực trong chunk được trích dẫn (Độ bao phủ chỉ đạt 22.2%). Nguy cơ Hallucination.
- **Trích xuất câu trả lời:** _Đối tượng áp dụng của Luật Doanh nghiệp bao gồm doanh nghiệp [C1] và các cơ quan, tổ chức, cá nhân có liên quan đến việc thành lập, tổ chức quản lý, tổ chức lại, giải thể và hoạt động có liên quan của doanh nghiệp [C2]. Trong trường hợp luật khác có quy định đặc thù về các vấn đề nêu trên thì áp dụn_

#### Ca 2: `gold_003`
- **Câu hỏi:** Theo Luật Doanh nghiệp, cổ đông là ai?
- **Nhóm lỗi:** `nguồn sai (Verification không qua)`
- **Lý do chi tiết:** Trạng thái: error
- **Trích xuất câu trả lời:** _Exception: CitationInvalidError: C3: nhãn lạ hoặc metadata không khớp chunk đã gửi cho LLM._

#### Ca 3: `gold_008`
- **Câu hỏi:** Khi thành viên góp vốn vào công ty TNHH bằng tài sản có đăng ký quyền sở hữu, việc chuyển quyền sở hữu tài sản đó cho công ty có phải chịu lệ phí trước bạ không?
- **Nhóm lỗi:** `nguồn sai (Verification không qua)`
- **Lý do chi tiết:** Trạng thái: error
- **Trích xuất câu trả lời:** _Exception: CitationInvalidError: C1: nhãn lạ hoặc metadata không khớp chunk đã gửi cho LLM._

#### Ca 4: `gold_030`
- **Câu hỏi:** Doanh nghiệp tạm ngừng kinh doanh phải gửi thông báo trước ít nhất mấy ngày làm việc, hồ sơ gồm những giấy tờ nào, và hành vi không thông báo tạm ngừng kinh doanh bị xử phạt thế nào?
- **Nhóm lỗi:** `prompt (LLM trả sai form hoặc bị chặn nội dung)`
- **Lý do chi tiết:** Trạng thái: error
- **Trích xuất câu trả lời:** _Exception: LLMBadOutputError: claim.citation_ids phải là danh sách nhãn có trong citations, không trùng._


---

## 5. Phân Tích Các Ca Hệ Thống Từ Chối Trả Lời (Insufficient Context)

Có **1 câu hỏi** hệ thống trả lời `insufficient_context` do context không chứa điều luật trực tiếp.

#### 1. `gold_014`
- **Câu hỏi:** *Điều lệ công ty phải quy định những nội dung chủ yếu nào theo Điều 24 Luật Doanh nghiệp?*
- **Chẩn đoán từ chunk:** retrieval một phần: 3/4 chunk đúng nằm trong 5 chunk đầu (ước tính); thiếu dieu-24__k2__0 hạng 7
- **Phản hồi của hệ thống:** _Các văn bản pháp luật được cung cấp trong LEGAL CONTEXT chỉ quy định về thành phần Điều lệ công ty và yêu cầu về họ, tên, chữ ký của những người ký Điều lệ khi đăng ký hoặc sửa đổi, bổ sung, chứ không liệt kê các nội dung chủ yếu phải có trong Điều lệ công ty theo Điều 24 Luật Doanh nghiệp._
