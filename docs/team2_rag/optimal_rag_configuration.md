# Đề Xuất Cấu Hình RAG Pipeline v2 Tối Ưu
## Phân Hệ: RAG & LLM (Team 2) — Nhiệm vụ VLRA-58 (Cả hai: Người 1 + Người 2)

---

## 1. Cơ Sở Thực Nghiệm & Tổng Hợp Dữ Liệu

Báo cáo này tổng hợp kết quả thực nghiệm định lượng từ **Người 1** (chạy ngày 31/10/2026 trên Colab GPU Tesla T4, dữ liệu `team2_rag/data/evaluation/colab-20261031/`) và các cải tiến kỹ thuật, phân tích lỗi từ **Người 2** (nhiệm vụ VLRA-56 và VLRA-57) để chốt cấu hình chính thức cho phiên bản RAG Pipeline v2.

### Bảng so sánh hiệu năng các phương án (trên tập mẫu 40 câu):

| Chỉ Số / Tiêu Chí | Phương án 1: Hybrid RRF (Không Rerank) | Phương án 2: Hybrid + Reranker (Nguyên bản) | Phương án 3: Hybrid + Reranker v2 (Người 2 tối ưu) |
| :--- | :---: | :---: | :---: |
| **Recall@5** | **73,77%** | 66,29% (−7,48%) | **71,45%** (giữ căn cứ khóa) |
| **Recall@10** | **85,15%** | 77,34% (−7,80%) | **83,20%** |
| **Recall@20** | **87,42%** | **87,42%** | **87,42%** |
| **MRR@20** | **0,6871** | 0,6037 (−0,0834) | **0,6650** |
| **Tỷ lệ lỗi (Failure Rate)** | **0% (0/40)** | 5% (2/40 crash $> 512$ token) | **0% (0/40 — Safe Truncation)** |
| **Độ trễ p50 (Retrieval + Rerank)** | **~ 106 ms** | ~ 849 ms | ~ 850 ms (GPU) / ~ 2.5s (CPU) |
| **Tính sẵn sàng (Availability)** | Rất cao | Rủi ro sập khi gặp nghị định dài | **Rất cao (Graceful Fallback)** |

---

## 2. Nhận Xét & Phân Tích Đánh Đổi (Trade-off Analysis)

1. **Về chất lượng xếp hạng (Retrieval Quality):**
   - **Hybrid RRF ($k=60$)** của Team 1 hoạt động cực kỳ mạnh mẽ: kết hợp chính xác từ khóa số hiệu Điều/Khoản của BM25 với khả năng bắt ngữ nghĩa tổng thể của Dense Embedding.
   - Cross-Encoder `bge-reranker-v2-m3` nguyên bản có nhược điểm cố hữu: chấm điểm tương quan câu chữ chung chung, dễ dìm các số hiệu quy phạm quan trọng (như phân tích trong [Báo cáo VLRA-56](retrieval_error_analysis.md)).
   - Do đó, việc phụ thuộc 100% vào điểm BGE để ghi đè thứ tự là không an toàn cho bài toán tra cứu văn bản pháp luật.

2. **Về độ ổn định & rủi ro tràn độ dài:**
   - Các điều luật về thủ tục hành chính (Nghị định 168/2025/NĐ-CP) thường dài từ 500 đến 1.000 token.
   - Bản cải tiến **VLRA-57** đã giải quyết triệt để vấn đề này nhờ cơ chế:
     - `truncate=True` (`truncation="only_second"`): Giữ nguyên 100% câu hỏi, cắt phần đuôi văn bản luật nếu vượt 512 token để mô hình luôn chấm điểm được.
     - `strict_rerank=False`: Khi module Reranker quá tải hoặc timeout $> 4.0$s, hệ thống tự động fallback giữ nguyên thứ hạng Hybrid RRF, phát log `reranker_degraded_fallback degraded=true` mà không làm gián đoạn người dùng.

---

## 3. Đề Xuất Cấu Hình RAG Pipeline v2 Chính Thức

Nhóm thống nhất đề xuất cấu hình tiêu chuẩn cho toàn hệ thống gồm các tham số chi tiết sau:

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

Đối chiếu với chỉ tiêu thời gian phản hồi NFR-07 (ngân sách tầng AI $\le 45$ giây do Team 3 thiết lập):

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

1. **Mã nguồn:** Cấu hình đã được cập nhật trực tiếp vào [`team2_rag/reranker.py`](../../team2_rag/reranker.py) và [`team2_rag/runtime.py`](../../team2_rag/runtime.py).
2. **Kế hoạch kiểm chứng lại:** Khi Team 1 đóng băng bộ Dev Set chuẩn 110 câu (`team1_data/golden/golden_phase1.json`), nhóm sẽ tái chạy bộ runner đo đạc chính thức để đối chiếu lần cuối trước buổi nghiệm thu Gate G4.
