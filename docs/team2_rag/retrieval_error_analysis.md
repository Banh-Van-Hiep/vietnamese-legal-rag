# Báo Cáo Phân Tích Lỗi Retrieval & Reranker (Error Analysis)
## Phân Hệ: RAG & LLM (Team 2) — Nhiệm vụ VLRA-56 (Người 2)

---

## 1. Mục Tiêu & Dữ Liệu Khảo Sát

Báo cáo này thực hiện phân loại chi tiết các lỗi truy xuất và trượt ngữ cảnh phát sinh từ đợt chạy thực nghiệm của Người 1 (ngày 31/10/2026 trên Colab GPU T4, dữ liệu `team2_rag/data/evaluation/colab-20261031/` và báo cáo `docs/team2_rag/reranker_impact_analysis.md`).

### Dữ liệu đầu vào:
- **Tập mẫu:** 40 câu hỏi Golden Phase 1 (`team2_rag/data/golden/golden_phase1_30cai.json`).
- **Tập ứng viên:** Top 20 candidates sinh ra từ Hybrid Retrieval (BM25 Lucene + Dense LSA/Embedding, RRF $k=60$).
- **Mô hình Cross-Encoder:** `BAAI/bge-reranker-v2-m3` (revision `953dc6f6f85a`).
- **Thống kê tổng quan:**
  - 38/40 câu chạy thành công cả 2 nhánh (95%).
  - 2/40 câu lỗi sập hoàn toàn do vượt ngưỡng token (5%).
  - Recall@5 của nhánh có Rerank giảm **7,48 điểm %** (từ 73,77% xuống 66,29%).
  - MRR@20 giảm **0,0834** (từ 0,6871 xuống 0,6037).
  - Có **7 câu** bị Reranker đánh mất hoàn toàn nhóm đúng khỏi top 5 (Demoted cases).

---

## 2. Bảng Phân Loại Các Nhóm Lỗi Chính (Error Taxonomy)

Qua rà soát từng câu trong raw log `reranker-exploratory.json`, các lỗi được phân loại thành 4 nhóm chính:

| Mã Lỗi | Loại Lỗi | Số Ca | Tỷ Lệ | Các Câu Tiêu Biểu | Nguyên Nhân Cốt Lõi |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **ERR-01** | **Vượt giới hạn Token (Length Overflow Crash)** | 2 | 5,0% | `gold_027`, `gold_032` | Cặp `(query, passage)` vượt quá context 512 token của BGE; cấu hình `truncation=False` ném exception làm sập truy vấn. |
| **ERR-02** | **Trượt từ khóa định danh (Lexical Keyword Drift)** | 4 | 10,0% | `gold_002`, `gold_008`, `gold_014`, `gold_021` | Câu hỏi chứa số Điều/Khoản hoặc thuật ngữ thủ tục chính xác; BM25 xếp top 1–2, nhưng Cross-Encoder ưu tiên đoạn văn ngữ nghĩa chung chung và đẩy căn cứ đúng ra khỏi top 5. |
| **ERR-03** | **Loãng căn cứ đa điều khoản (Multi-part Coverage Dilution)** | 3 | 7,5% | `gold_005`, `gold_012`, `gold_039` | Câu hỏi nghiệp vụ phức tạp đòi hỏi nhiều Khoản đồng thời; Reranker chỉ đẩy 1 Khoản lên và đánh tụt 3–4 Khoản còn lại xuống ngoài top 10. |
| **ERR-04** | **Bất đối xứng độ dài (Length Bias Artifact)** | 5 | 12,5% | `gold_007`, `gold_016`, `gold_024`, `gold_029`, `gold_035` | Mô hình Cross-Encoder có xu hướng chấm điểm cao hơn cho các chunk dài, nhiều từ vựng giải thích, làm chìm các chunk ngắn nhưng chứa quy định cấm/thời hạn then chốt. |

---

## 3. Phân Tích Chi Tiết Từng Nhóm Lỗi & Bằng Chứng

### 3.1. Nhóm ERR-01: Lỗi Vượt Ngưỡng 512 Token (Crash)
- **Hiện tượng:** Truy vấn sập hoàn toàn với `RerankModelError("A question/content pair exceeds the model token limit.")`.
- **Dẫn chứng thực tế từ `reranker-length-check.json`:**
  - `gold_027`: Hỏi về trình tự, thủ tục đăng ký doanh nghiệp theo Nghị định 168/2025/NĐ-CP.
    - Cặp chứa `nd-168-2025-nd-cp-v1__dieu-63__k2__0`: **975 tokens** (vượt gần gấp đôi giới hạn 512).
    - Cặp chứa `nd-168-2025-nd-cp-v1__dieu-71__k2__0`: **913 tokens**.
    - Cặp chứa `nd-168-2025-nd-cp-v1__dieu-69__k1__0`: **715 tokens**.
  - `gold_032`: Cặp chứa `nd-168-2025-nd-cp-v1__dieu-43__k2__0` dài **532 tokens**.
- **Nguyên nhân:** Các điều luật quy định về hồ sơ, biểu mẫu và trình tự thường có danh sách liệt kê rất dài. Khi Team 1 cắt chunk theo nguyên vẹn Khoản, độ dài chunk vượt ngưỡng 512 token của tokenizer BGE. Adapter của Team 2 cấu hình nghiêm ngặt không cho cắt chuỗi (`truncation=False`) dẫn tới exception.
- **Tác động:** Làm hỏng hoàn toàn độ sẵn sàng của hệ thống (5% failure rate), vi phạm yêu cầu không được làm gián đoạn luồng người dùng.

### 3.2. Nhóm ERR-02: Trượt Từ Khóa Định Danh (Keyword Drift)
- **Hiện tượng:** Căn cứ đúng nằm ở Top 1–2 của Hybrid RRF, nhưng sau khi Rerank bị rơi xuống Top 10–20.
- **Dẫn chứng thực tế:**
  - `gold_002`: Câu hỏi tra cứu trực tiếp về đối tượng áp dụng.
    - Ban đầu (Hybrid RRF): Hai chunk của Điều 2 xếp ở **hạng 1 và hạng 2**.
    - Sau khi Rerank: Bị đánh tụt xuống **hạng 8 và hạng 12** $\rightarrow$ Rơi hoàn toàn khỏi Top 5! Recall@5 giảm từ 100% xuống 0%.
  - Thay vào đó, Reranker đẩy các chunk thuộc chương Điều khoản chung (nói về giải thích từ ngữ) lên Top 1–3 vì chúng chứa nhiều câu văn giải nghĩa bóng bẩy.
- **Nguyên nhân:** `bge-reranker-v2-m3` là mô hình đa ngôn ngữ tổng quát, không được huấn luyện riêng trên tập văn bản pháp luật tiếng Việt. Nó chấm điểm dựa trên độ tương đồng ngữ nghĩa mờ (semantic similarity), nên đánh giá thấp các số hiệu quy phạm ("Điều 2", "Khoản 1") so với BM25.

### 3.3. Nhóm ERR-03: Loãng Căn Cứ Đa Điều Khoản (Multi-part Coverage Dilution)
- **Hiện tượng:** Câu hỏi cần $\ge 3$ căn cứ; Reranker chỉ giữ được 1 căn cứ, các căn cứ còn lại bị đẩy ra ngoài.
- **Dẫn chứng thực tế:**
  - `gold_012`: Câu hỏi nghiệp vụ cần 4 gold chunks.
    - Ban đầu (Hybrid RRF): Cả 4 chunk đều nằm gọn trong Top 5 (xếp hạng 1, 3, 4, 5).
    - Sau khi Rerank: Cả 4 chunk bị đẩy xuống **hạng 10, 13, 17, 19**.
  - `gold_005`: Cần các Khoản của Điều 7. Reranker đẩy 1 Khoản từ 12 lên 3, nhưng lại dìm 3 Khoản khác từ hạng 1, 4, 5 xuống 12, 15, 19.
- **Nguyên nhân:** Cross-Encoder chấm điểm độc lập từng cặp $(q, c_i)$, hoàn toàn không có cơ chế nhận biết tính bổ trợ giữa các Khoản trong cùng một Điều luật. Do đó, các chunk bổ trợ bị đẩy dạt ra ngoài bởi các chunk từ văn bản khác có từ ngữ na ná câu hỏi.

---

## 4. Đề Xuất Hướng Xử Lý & Tinh Chỉnh (Actionable Mitigations)

Dựa trên phân tích 4 nhóm lỗi trên, Người 2 đề xuất 3 giải pháp kỹ thuật cần lập trình trong nhiệm vụ **VLRA-57**:

1. **Xử lý An toàn Giới hạn Độ Dài (Safe Truncation):**
   - Không cho phép Reranker ném exception khi độ dài $> 512$ token.
   - Áp dụng cơ chế cắt chuỗi thông minh: `truncation="only_second"` (bảo toàn 100% câu hỏi của người dùng, chỉ cắt bớt phần đuôi của văn bản luật nếu vượt 512 token). Vì câu dẫn và điều kiện áp dụng quan trọng nhất luôn nằm ở phần đầu của Điều/Khoản luật, việc giữ nguyên 512 token đầu là hoàn toàn đủ để Reranker đánh giá chính xác.

2. **Cơ chế Giáng Cấp An Toàn (Graceful Degradation & Hybrid Fallback):**
   - Khi Reranker gặp sự cố (quá tải, timeout $> 4.0$s hoặc lỗi tính toán), tự động giữ nguyên thứ hạng ban đầu của **Hybrid RRF** từ Team 1, không ngắt quãng luồng xử lý.
   - Ghi log cảnh báo `reranker_fallback` phục vụ giám sát vận hành.

3. **Cân Bằng Điểm Số (Score Blending / Rank Preservation):**
   - Đối với các ứng viên xếp hạng 1–2 trong kết quả Hybrid RRF có điểm số vượt trội từ BM25, áp dụng ngưỡng bảo vệ (Rank Preservation) để tránh việc Reranker đẩy trượt khỏi top 5 các điều khoản chỉ định rõ đích danh.
   - Giữ nguyên ngân sách Context Builder: $K_{\text{in}} = 20$, $K_{\text{out}} = 5$, bảo đảm $\le 3000$ tokens.
