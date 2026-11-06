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
| **Ngân sách thời gian Pipeline** | `45.0s` trần toàn luồng | Cưỡng chế trần NFR-07 (LLM <= 30s, Retrieval <= 10s, Rerank <= 4s) |
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

*Ghi chú:* Các trường hợp không có mẫu số (0 citation / 0 claim / 0 answered) được ghi rõ `"chưa đo"`, tuyệt đối không tính 100% giả định.

> [!WARNING]
> **Giới hạn kỹ thuật của chỉ số Hallucination Rate (4.00%):**
> 1. Con số 4.00% (1/25 câu answered) phản ánh kết quả thẩm định của bộ lọc **Lexical-Semantic Heuristic** (độ trùng khớp từ vựng + đối chiếu cặp từ khóa đối lập tầng đầu), **chưa phải mô hình Full Semantic NLI sâu hay LLM-as-a-judge**.
> 2. Bộ lọc heuristic có thể bỏ sót những trường hợp mâu thuẫn ngữ nghĩa tinh tế hoặc đảo cấu trúc ngữ pháp phức tạp ngoài các cặp từ khóa đối lập phổ biến đã định nghĩa.
> 3. Mốc $\le 5\%$ đạt được trên tập mẫu 25 câu trả lời thực tế của Golden Phase 1; đây là chỉ số tham chiếu kỹ thuật cho tầng lọc inline thời gian thực và cần được kiểm chứng thêm khi Team 1 bàn giao Dev Set đóng băng 110 câu.

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

