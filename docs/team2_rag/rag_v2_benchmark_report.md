# Báo Cáo Đánh Giá Benchmark RAG v2 — Tuần 9 (VLRA-T2-26, VLRA-68)
**Thực hiện bởi:** Người 2 (Verification Engine & Benchmark Suite)  
**Người nhận bàn giao:** Người 1 (Đạt — Core Pipeline & Prompting)  
**Thời điểm thực thi:** 05/11/2026 10:22:44  
**Nhãn đánh giá:** `EXPLORATORY` *(Do tập Dev Set 70/110 câu của Team 1 chưa đóng băng)*  

---

## 1. Thông Tin Môi Trường & Cấu Hình Thử Nghiệm

| Thông số cấu hình | Giá trị thiết lập | Ghi chú |
| :--- | :--- | :--- |
| **Git Commit SHA** | `0a7c3520a8` | Nhánh `feature/team2-rag` |
| **Tập dữ liệu Golden** | `team2_rag\data\golden\golden_phase1_30cai.json` | Hash SHA-256: `298ae763fed0...` |
| **Mô hình LLM Benchmark** | `gemini-3.1-flash-lite` | Chạy thật qua Google API v1beta |
| **Tham số Retrieval** | `RAG_TOP_K=5`, `weights=(0.5, 1.0)` | BM25 + Qdrant Dense |
| **Cấu hình Reranker** | `enabled=False`, `timeout=4.0s` | BGE-Reranker-v2-m3 |
| **Cơ chế Claims & Verifier** | `include_claims=True`, `verifier=verify_response` | Kích hoạt bộ kiểm định 2 tầng Người 2 |

---

## 2. Kết Quả 3 Chỉ Số Cốt Lõi

| Chỉ số đánh giá | Giá trị thực tế | Mốc mục tiêu | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Citation Correctness** | **chưa đo (0 citation)** | >= 90.00% | ❌ CHƯA ĐẠT |
| **Citation Coverage** | **chưa đo (0 claim)** | >= 85.00% | ❌ CHƯA ĐẠT |
| **Query-level Hallucination Rate** | **chưa đo (0 câu answered)** | <= 5.00% | ❌ CHƯA ĐẠT |
| **Claim-level Hallucination Rate** | **chưa đo (0 claim)** | Tham chiếu | Bổ sung theo yêu cầu Người 1 |

*Ghi chú:* Các trường hợp không có mẫu số (0 citation / 0 claim / 0 answered) được ghi rõ `"chưa đo"`, tuyệt đối không tính 100% giả định.

---

## 3. Thống Kê Tổng Quan Theo Nhóm Câu

- **Tổng số câu hỏi đánh giá:** 3
- **Số câu trả lời được (Answered):** 0
- **Số câu hệ thống từ chối (Insufficient Context):** 2
- **Số câu gặp lỗi kỹ thuật (Error):** 1
- **Tổng số nhận định (Claims) phân tích:** 0 (Hợp lệ: 0, Nghi vấn: 0)
- **Tổng số trích dẫn (Citations) thẩm định:** 0 (Hợp lệ: 0, Bất thường: 0)

---

## 4. Phân Tích Ca Thất Bại Bàn Giao Cho Người 1 (VLRA-T2-27)

Tổng số ca thất bại / cần tinh chỉnh: **1**

### Phân loại nguyên nhân lỗi:
- **Prompt (lỗi sinh phản hồi từ llm)**: 1 ca

### Chi tiết từng ca lỗi:
#### Ca 1: `gold_002`
- **Câu hỏi:** Những ai thuộc đối tượng áp dụng của Luật Doanh nghiệp?
- **Nhóm lỗi:** `prompt (lỗi sinh phản hồi từ LLM)`
- **Lý do chi tiết:** Trạng thái: error
- **Trích xuất câu trả lời:** _Exception: LLMTimeoutError: Hết thời gian chờ phản hồi từ LLM provider._

