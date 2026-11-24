# Báo Cáo Tổng Hợp Đánh Giá Tầng AI / RAG (Team 2) — Nghiệm Thu G5 (VLRA-81)

- **Phân hệ phụ trách:** Core RAG, Reranker & LLM Engine (`team2_rag`)
- **Ticket liên quan:** `VLRA-78` (Định lượng B0 vs T0 & Phân tích lỗi), `VLRA-79` (Chấm mù Rubric 5 tiêu chí), bàn giao cho `VLRA-81` (Final Evaluation Report).
- **Tập kiểm thử độc lập:** `team1_data/golden/test_set_v1.json` (**77 câu hỏi**, `split: "test"`, gồm `62` câu `answered` và `15` câu `insufficient_context`, SHA-256 `2d4b1f4db19e0c798518b4145f2a3f41d31676d2ddd1d1350fb69bd0b06de0a5`).

---

## 1. Bảng Đối Chiếu Mục Tiêu Nghiệm Thu G5 (`docs/REQUIREMENTS.md`)

| Mã NFR | Chỉ số đánh giá | Ngưỡng yêu cầu | Kết quả **B0 (`BM25-only`)** | Kết quả **T0 (`Hybrid + BGE Rerank`)** | Trạng thái |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **NFR-02** | **Citation correctness** *(tính từ `raw_results`)* | `≥ 90,0%` | **`100,00%`** (`120/120`) | **`100,00%`** (`132/132`) | **ĐẠT** |
| **NFR-03** | **Điểm chất lượng câu trả lời chấm mù** *(40 câu, Rubric 5 tiêu chí, thang 10)* | `T0 ≥ B0` | **`8,80 / 10`** | **`9,04 / 10`** *(9,27/10 nếu loại 1 ca timeout)* | **ĐẠT** |
| — | **Citation coverage** | — | `99,17%` (`119/120`) | **`100,00%`** (`131/131`) | Tốt |
| — | **Query Hallucination Rate** *(ước lượng từ vựng `rubric.py`)* | Càng thấp càng tốt | `1,67%` (`1/60`) | **`0,00%`** (`0/61`) | Tốt |
| — | **Claim Hallucination Rate** *(ước lượng từ vựng `rubric.py`)* | Càng thấp càng tốt | `0,83%` (`1/120`) | **`0,00%`** (`0/131`) | Tốt |
| — | **Từ chối (`insufficient_context`): Precision / Recall** | — | `87,50%` / `93,33%` | **`93,33%`** / **`93,33%`** | Tốt |
| — | **Số ca lỗi dịch vụ (`error` / `timeout`)** | Đếm riêng | `1` (`CITATION_INVALID`) | `1` (`LLM_TIMEOUT`) | Đã ghi nhận |

---

## 2. Tóm Tắt Đánh Giá Định Tính (Chấm Mù 2 Giám Khảo — VLRA-79)

- **Thiết kế thực nghiệm:** Chọn 40 câu phức tạp (toàn bộ 15 câu `multi_clause` và 25 câu `single_clause` trọng tâm), ẩn danh ngẫu nhiên thành `Hệ thống A` và `Hệ thống B`, chấm độc lập bởi **2 giám khảo** theo Rubric 5 tiêu chí (`0–2` điểm/tiêu chí).
- **Kết quả điểm trung bình (2 giám khảo):**
  - **Target T0 (`Hybrid + BGE Rerank`):** **`9,04 / 10`** (`Đúng pháp lý: 1,83`, `Đầy đủ: 1,83`, `Trích dẫn: 1,75`, `Mạch lạc: 1,95`, `An toàn: 1,68`).
  - **Baseline B0 (`BM25-only`):** **`8,80 / 10`** (`Đúng pháp lý: 1,73`, `Đầy đủ: 1,73`, `Trích dẫn: 1,75`, `Mạch lạc: 1,95`, `An toàn: 1,65`).
- **Độ đồng thuận liên giám khảo:** Chênh lệch tuyệt đối trung bình `MAD = 0,088` điểm; `100%` (80/80 cặp) có chênh lệch `≤ 2` điểm; hệ số tương quan Spearman $\rho = 0,9994$ (không có ca nào lệch `> 3` điểm).

---

## 3. Giới Hạn Phương Pháp & Các Hạng Mục Chưa Đo Tại Team 2

1. **Giới hạn phương pháp đo Hallucination tự động:** Chỉ số Hallucination Rate (`1,67%` ở B0 và `0,00%` ở T0) được tính bằng bộ lọc đối chiếu từ vựng và phân cực phủ định (`team2_rag/verification/rubric.py`), **chưa phải mô hình suy luận ngữ nghĩa sâu (Full Semantic NLI)**. Vì vậy, kết quả chấm mù 40 câu của 2 giám khảo được dùng làm nguồn đối chiếu chất lượng ngữ nghĩa chính thức.
2. **Các chỉ số thuộc phạm vi team khác (chưa đo trong báo cáo Team 2):**
   - `Recall@5 / 10 / 20` và `MRR@20` của tầng Retrieval do **Team 1** báo cáo tại `VLRA-77`.
   - Độ trễ E2E đồng thời 5 người dùng qua cổng Public API (`NFR-07`) và luồng mở Điều luật trên UI (`NFR-09`) do **Team 3** tổng hợp tại `VLRA-80` / `VLRA-81`.
3. **Danh mục tài liệu bằng chứng trong `docs/team2_rag/`:**
   - Báo cáo định lượng G5 (Người 1): `docs/team2_rag/g5_b0_vs_t0_report.json` và `docs/team2_rag/g5_b0_vs_t0_report.md`
   - Báo cáo chấm mù & phiếu điểm 2 giám khảo (Người 2): `docs/team2_rag/g5_blind_evaluation_report.md`, `docs/team2_rag/g5_blind_scores_judge1.csv`, `docs/team2_rag/g5_blind_scores_judge2.csv`, `docs/team2_rag/g5_blind_eval_package.json`, `docs/team2_rag/g5_blind_eval_key.json`
   - Báo cáo phân tích lỗi sinh câu trả lời (Người 2): `docs/team2_rag/g5_error_analysis.md`
