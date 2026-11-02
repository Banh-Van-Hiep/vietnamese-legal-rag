# Đề xuất cấu hình RAG Pipeline v2 — chờ kiểm chứng
## Phân Hệ: RAG & LLM (Team 2) — Nhiệm vụ VLRA-58 (Cả hai: Người 1 + Người 2)

---

## 1. Cơ Sở Thực Nghiệm & Tổng Hợp Dữ Liệu

Báo cáo này tổng hợp kết quả thực nghiệm định lượng từ **Người 1** (chạy ngày 31/10/2026 trên Colab GPU Tesla T4, dữ liệu `team2_rag/data/evaluation/colab-20261031/`) và các cải tiến kỹ thuật, phân tích lỗi từ **Người 2** (nhiệm vụ VLRA-56 và VLRA-57) để đề xuất cấu hình RAG Pipeline v2. Lượt 02/11 đã kiểm chứng riêng tùy chọn truncate trên 110 câu; chưa kiểm chứng toàn bộ pipeline v2 hoặc SLA.

### Kiểm chứng truncate ngày 02/11/2026

[Raw output](../../team2_rag/data/evaluation/colab-20261102/) tại commit
`1f51f66`: BGE gốc hoàn tất 97/110 câu; BGE truncate hoàn tất 110/110, không
lỗi retrieval và không dùng fallback. Trên cùng 97 câu, cả hai chính sách
BGE cho đúng cùng thứ tự; Recall@5 Hybrid 87,66%, BGE 83,70%.

Trên **đủ 110 câu**: Hybrid Recall@5 88,39%, BGE truncate 83,08%; MRR@20
0,6465 → 0,5968. Rerank truncate p50/p95 = 866,86/1.253,82 ms; tổng
retrieval/kiểm tra + rerank p50/p95 = 1.009,03/1.371,46 ms trên T4.

Truncate xử lý 13 ca quá dài trong lượt này nhưng chưa cho lợi ích chất
lượng xếp hạng. **Chưa chọn nó làm cấu hình tối ưu; giữ Hybrid làm mốc.**
Bộ 110 câu còn 70 câu draft, chưa có split/gold groups; các số trên là
khảo sát, chưa thay nghiệm thu. Xem [phân tích và từng nhóm dữ liệu](reranker_impact_analysis.md).
Không suy số liệu này thành kết quả toàn bộ pipeline v2 hoặc CPU/E2E.

### Bằng chứng hiện có trên bộ khảo sát 40 câu

Chất lượng hai cột đầu tính trên cùng **38 cặp thành công**, không phải đủ
40 câu. Cột v2 chưa có bằng chứng chạy model; không dùng số ước lượng làm
kết quả thực nghiệm. Runner `--compare-truncation` đo riêng tác động của
truncate, chưa kiểm chứng toàn bộ pipeline v2 hoặc SLA.

| Chỉ Số / Tiêu Chí | Phương án 1: Hybrid RRF (Không Rerank) | Phương án 2: Hybrid + Reranker (Nguyên bản) | Phương án 3: Hybrid + Reranker v2 (Người 2 tối ưu) |
| :--- | :---: | :---: | :---: |
| **Recall@5** | **73,77%** | 66,29% (−7,48%) | **Chưa đo** |
| **Recall@10** | **85,15%** | 77,34% (−7,80%) | **Chưa đo** |
| **Recall@20** | **87,42%** | **87,42%** | **Chưa đo** |
| **MRR@20** | **0,6871** | 0,6037 (−0,0834) | **Chưa đo** |
| **Tỷ lệ lỗi (Failure Rate)** | **0% (0/40)** | 5% (2/40 crash $> 512$ token) | **Chưa đo** |
| **Độ trễ p50 (Retrieval + Rerank)** | **~ 106 ms** | ~ 849 ms | **Chưa đo** |
| **Tính sẵn sàng (Availability)** | Rất cao | Rủi ro sập khi gặp nghị định dài | **Chưa đo** |

---

## 2. Nhận Xét & Phân Tích Đánh Đổi (Trade-off Analysis)

1. **Về chất lượng xếp hạng (Retrieval Quality):**
   - **Hybrid RRF ($k=60$)** của Team 1 hoạt động cực kỳ mạnh mẽ: kết hợp chính xác từ khóa số hiệu Điều/Khoản của BM25 với khả năng bắt ngữ nghĩa tổng thể của Dense Embedding.
   - Cross-Encoder `bge-reranker-v2-m3` nguyên bản có nhược điểm cố hữu: chấm điểm tương quan câu chữ chung chung, dễ dìm các số hiệu quy phạm quan trọng (như phân tích trong [Báo cáo VLRA-56](retrieval_error_analysis.md)).
   - Do đó, việc phụ thuộc 100% vào điểm BGE để ghi đè thứ tự là không an toàn cho bài toán tra cứu văn bản pháp luật.

2. **Về độ ổn định & rủi ro tràn độ dài:**
   - Các điều luật về thủ tục hành chính (Nghị định 168/2025/NĐ-CP) thường dài từ 500 đến 1.000 token.
   - Bản **VLRA-57** bổ sung tùy chọn xử lý passage dài; cần chạy lại model để xác nhận tác động:
     - `truncate=True` (`truncation="only_second"`): Giữ nguyên 100% câu hỏi, cắt phần đuôi văn bản luật nếu vượt 512 token trước khi chấm điểm. Vẫn có thể lỗi nếu riêng câu hỏi đã vượt giới hạn; cắt đuôi cũng có thể mất căn cứ.
     - `strict_rerank=False`: Khi scorer báo lỗi, pipeline có thể giữ nguyên thứ hạng Hybrid RRF và ghi log fallback. Code hiện chưa có timer cưỡng chế dừng rerank sau 4 giây; không coi mốc này là hành vi đã triển khai.

---

## 3. Cấu hình đề xuất, chưa nghiệm thu

Các tham số dưới đây là mục tiêu cần kiểm chứng, chưa phải toàn bộ giá trị mặc định đang chạy trong `runtime.py`:

### 3.1. Tầng 1 — Hybrid Retrieval (Team 1)
- **Phương pháp hợp nhất:** Reciprocal Rank Fusion (RRF) với hằng số $k = 60$, tỷ lệ trọng số BM25 : Dense là $1 : 1$.
- **Bộ lọc hiệu lực pháp lý:** Chỉ nạp các chunk có `legal_status` $\in$ {`con_hieu_luc`, `het_hieu_luc_mot_phan`}.
- **Kích thước ứng viên đầu ra ($K_{\text{in}}$):** Lấy đúng **$K_{\text{in}} = 20$ candidates** gửi sang Team 2.

### 3.2. Tầng 2 — Reranker & Context Builder (Team 2)
- **Mô hình Reranker:** `BAAI/bge-reranker-v2-m3` (revision `953dc6f6f85a`).
- **Chế độ suy luận:**
  - `truncate: True` (chế độ cắt đuôi an toàn văn bản dài).
  - `strict_rerank: False` (chế độ Graceful Degradation tự động fallback về thứ tự Hybrid RRF khi xảy ra sự cố).
  - Timeout tối đa của bước Rerank: $\le 4.0$ giây.
- **Số lượng chunks chọn lọc vào Context ($K_{\text{out}}$):** Lấy tối đa **$K_{\text{out}} = 5$ chunks** có điểm cao nhất.
- **Ngân sách Prompt Token:** Giới hạn `LEGAL_CONTEXT` $\le 3000$ tokens, bảo đảm bảo tồn toàn bộ tên văn bản, Điều, Khoản, Điểm và liên kết URL nguồn.

### 3.3. Tầng 3 — LLM Generation & Output Verification
- **Mô hình triển khai:**
  - *Môi trường Local / Miễn phí:* **Ollama `qwen2.5:3b`** (Context window: 8192 tokens, timeout: 120s, temperature: 0.0).
  - *Môi trường Cloud / Production:* **Google Gemini 1.5 Flash** (Context window: 128K tokens, timeout: 30s).
- **Thẩm định trích dẫn:**
  - Kiểm tra 100% nhãn trích dẫn `[C1]` ... `[Cn]` phải xuất hiện trong ngữ cảnh `LEGAL_CONTEXT`.
  - Tự động remapping nhãn theo đúng thứ tự xuất hiện đầu tiên trong câu trả lời.

---

## 4. Ngân Sách Thời Gian Toàn Trình (Latency Budget SLA)

Đây là **ngân sách mục tiêu**, chưa có lượt đo E2E chứng minh các percentile. Không cộng p95 từng bước để suy ra p95 tổng đã đo. Đối chiếu với chỉ tiêu thời gian phản hồi NFR-07 (ngân sách tầng AI $\le 45$ giây do Team 3 thiết lập):

```text
Request từ Java BE (POST /internal/v1/query)
   │
   ├─ [1] Hybrid Retrieval (BM25 + Dense) :  p95 <= 0.8 giây
   ├─ [2] Cross-Encoder Rerank (Top 20 -> 5) : p95 <= 3.0 giây (hoặc fallback tức thì)
   ├─ [3] Context Builder & Prompt Assembly:  p95 <= 0.1 giây
   ├─ [4] LLM Generation (Ollama / Gemini):  p95 <= 25.0 giây
   ├─ [5] Citation Validation & Remapping:   p95 <= 0.1 giây
   ▼
Tổng thời gian toàn trình AI Layer: p95 <= 29.0 giây (Dư an toàn 16 giây so với ngưỡng 45s)
```

---

## 5. Kết Luận Bàn Giao

1. **Mã nguồn:** `BGEScorer` đã có tùy chọn `truncate=True`, nhưng `runtime.py` vẫn gọi `BGEScorer()` với mặc định `truncate=False`, mặc định `RAG_TOP_K=10`. Cần Người 2 xác nhận cấu hình triển khai; runner khảo sát vẫn giữ top 20 để so sánh. Không tự đổi runtime bằng kết quả chưa đo.
2. **Kế hoạch kiểm chứng lại:** Khi Team 1 đóng băng bộ Dev Set chuẩn 110 câu (`team1_data/golden/golden_phase1.json`), nhóm sẽ tái chạy bộ runner đo đạc chính thức để đối chiếu lần cuối trước buổi nghiệm thu Gate G4.
