# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 8
## Phân Hệ: RAG & LLM (Team 2)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 8 (Quy đổi học phần: Tuần 5 cũ + 3 = Tuần 8 mới).
- **Mục tiêu trọng tâm:**
  - Thực hiện đánh giá thực nghiệm tác động định lượng của Cross-Encoder Reranker (`bge-reranker-v2-m3`) trên tập **Dev Set** (chiếm 60% Golden Dataset v1 đã đóng băng) thông qua báo cáo **Reranker Impact Analysis**.
  - Phân tích chi tiết các trường hợp trượt ngữ cảnh (Context Drop/Drift): Reranker đẩy chunk đúng xuống ngoài top 5 hoặc cắt nhầm điều kiện pháp lý quan trọng.
  - Tinh chỉnh số lượng candidates đầu vào ($K_{\text{in}} \in \{15, 20, 30\}$) và số lượng chunk đầu ra đưa vào context ($K_{\text{out}} \in \{3, 5, 7\}$) để tối ưu hóa mối quan hệ giữa độ bao phủ pháp lý và ngân sách token.
  - Phối hợp chặt chẽ với Team 1 (đang tối ưu hóa Retrieval v2) để xác lập cấu hình kết hợp `Hybrid Fusion (RRF k=60) + Cross-Encoder` tối ưu nhất cho toàn hệ thống.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T2-14** | **Thực nghiệm phân tích tác động của Reranker (Reranker Impact Analysis)**<br>- Thiết lập pipeline đo đạc so sánh hai nhánh xử lý trên tập Dev Set:<br>  + Nhánh không Rerank: Lấy trực tiếp top 5 từ kết quả Hybrid RRF của Team 1.<br>  + Nhánh có Rerank: Lấy top 20 từ Hybrid RRF $\rightarrow$ Reranker $\rightarrow$ Lọc lấy top 5.<br>- Đo lường tỷ lệ các câu hỏi mà Reranker giúp đưa `gold_chunk` lên thứ hạng 1–3 và tỷ lệ bị tụt hạng. | - Báo cáo `reranker_impact_analysis.md` hoàn thành với bảng số liệu so sánh định lượng.<br>- Chứng minh được Reranker cải thiện rõ rệt vị trí của chunk đúng (tăng MRR@5 và giảm nhiễu ngữ cảnh). |
| **VLRA-T2-15** | **Phân tích lỗi trượt ngữ cảnh & Tinh chỉnh Ngân sách Token (Error Analysis)**<br>- Rà soát các câu hỏi trong Dev Set mà Reranker không giữ được `gold_chunk` trong top 5.<br>- Phân loại nguyên nhân: do câu hỏi quá ngắn, do thuật ngữ kỹ thuật trong nghị định, hay do giới hạn độ dài của Cross-Encoder.<br>- Thử nghiệm tăng/giảm số lượng chunk đưa vào `LEGAL_CONTEXT` ($K_{\text{out}} = 3, 5, 7$) và đánh giá thời gian suy luận của LLM. | - Tài liệu phân tích lỗi (Error Taxonomy) chỉ ra các điểm mù của Reranker.<br>- Chốt cấu hình tối ưu: $K_{\text{in}} = 20$, $K_{\text{out}} = 5$ đảm bảo giữ nguyên ngân sách token $\le 3000$ tokens. |
| **VLRA-T2-16** | **Xây dựng cơ chế Giáng cấp An toàn (Graceful Degradation)**<br>- Lập trình cơ chế phòng vệ khi module Reranker gặp sự cố (quá tải GPU/CPU hoặc timeout $> 4.0$s):<br>  + Tự động fallback sử dụng trực tiếp thứ hạng của Hybrid RRF từ Team 1.<br>  + Bật cờ cảnh báo `degraded: true` trong log truy vết nội bộ.<br>- Đảm bảo hệ thống không bao giờ bị sập hoàn toàn chỉ vì lỗi của một bước rerank. | - Test suite mô phỏng Reranker lỗi, hệ thống tự động fallback về retrieval rank mà không làm gián đoạn phản hồi tới Backend.<br>- Ghi nhận đầy đủ log cảnh báo phân tích độ trễ. |
| **VLRA-T2-17** | **Phối hợp chốt cấu hình Pipeline v2 với Team 1 & Team 3**<br>- Họp kỹ thuật đối soát giữa kết quả Retrieval v2 (Team 1) và Reranker Impact (Team 2).<br>- Đảm bảo thời gian toàn trình của tầng AI: Retrieval $\le 5$s, Rerank $\le 5$s, LLM $\le 30$s, tổng thời gian xử lý AI $\le 45$ giây theo đúng chỉ tiêu NFR-07. | - Biên bản thống nhất cấu hình Pipeline v2 được cả 3 team ký duyệt.<br>- AI Service sẵn sàng bước vào giai đoạn tối ưu sâu prompt và thẩm định citation ở tuần 9. |

---

## 3. Ý Tưởng Giải Thuật, Quản Trị Token & Prompt Design

### 3.1. Phương Pháp Luận Phân Tích Tác Động Của Reranker (Impact Methodology)
Để chứng minh việc bổ sung Cross-Encoder là thực sự cần thiết theo đề bài Project 1, Team 2 đo đạc 3 chỉ số chuyển dịch thứ hạng:
1. **Promoted Rate (Tỷ lệ nâng hạng):** Tỷ lệ câu hỏi mà chunk đúng được Reranker đẩy từ vị trí sâu (rank 6–20) lên top 5 (giúp LLM nhìn thấy căn cứ mà trước đó bị khuất).
2. **Demoted Rate (Tỷ lệ hạ hạng sai):** Tỷ lệ câu hỏi mà chunk đúng ban đầu nằm trong top 5 của retrieval nhưng bị Reranker đánh tụt ra ngoài top 5 (cần giảm thiểu tối đa).
3. **Top-1 Precision:** Tỷ lệ câu hỏi mà chunk xếp hạng 1 chính là căn cứ cốt lõi của câu trả lời.

```
       Hybrid Retrieval Top 20 Candidates
                      │
                      ▼
       ┌──────────────────────────────┐
       │   bge-reranker-v2-m3         │
       │ Chấm điểm tương quan Cross   │
       └──────────────┬───────────────┘
                      │
       ┌──────────────┴───────────────┐
       ▼                              ▼
[Promoted to Top 1-5]         [Demoted to Out of 5]
 (Thành công: cứu context)     (Lỗi: trượt context -> Cần tinh chỉnh)
```

### 3.2. Cân Bằng Ngân Sách Token & Số Lượng Chunks ($K_{\text{out}}$)
| Số lượng chunks ($K_{\text{out}}$) | Ước tính Tokens | Độ trễ LLM Generation (p95) | Khả năng bao phủ căn cứ | Đánh giá rủi ro |
| :---: | :---: | :---: | :---: | :--- |
| **$K_{\text{out}} = 3$** | ~ 1500 tokens | ~ 12s | Thiếu điều kiện đối với tình huống phức tạp | Rủi ro thiếu căn cứ cao |
| **$K_{\text{out}} = 5$ (Chọn)** | **~ 2400 tokens** | **~ 18s** | **Đầy đủ điều kiện và ngoại lệ chính** | **Cân bằng tối ưu nhất** |
| **$K_{\text{out}} = 7$** | ~ 3400 tokens (vượt budget) | ~ 28s | Rất đầy đủ nhưng có chunk loãng | Dễ làm LLM xao nhãng và tràn budget 3000 |

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Cấu Trúc Báo Cáo Phân Tích Thực Nghiệm Reranker
```python
from pydantic import BaseModel, Field

class RerankerEvaluationReport(BaseModel):
    experiment_id: str
    sample_size: int
    top1_precision_before: float
    top1_precision_after: float
    promoted_count: int
    demoted_count: int
    mrr_at_5_before: float
    mrr_at_5_after: float
    latency_rerank_p95_ms: float
    recommendation_summary: str
```

### 4.2. Fixture Dữ Liệu Báo Cáo Mẫu (Tuần 8 Target)
```json
{
  "experiment_id": "EXP-RERANK-BGE-M3-DEV",
  "sample_size": 60,
  "top1_precision_before": 0.583,
  "top1_precision_after": 0.767,
  "promoted_count": 14,
  "demoted_count": 2,
  "mrr_at_5_before": 0.685,
  "mrr_at_5_after": 0.821,
  "latency_rerank_p95_ms": 2450.0,
  "recommendation_summary": "Reranker bge-reranker-v2-m3 giúp tăng vọt MRR@5 từ 0.685 lên 0.821 trên Dev Set. Đề xuất chốt cấu hình K_in = 20, K_out = 5 cho phiên bản RAG Pipeline v2."
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 2 $\rightarrow$ Team 1 (Retrieval)** | - Báo cáo phân tích các ca bị Reranker đánh tụt hạng (Demoted cases).<br>- Yêu cầu về cấu trúc `Search Text` và tiêu đề văn bản để Cross-Encoder đọc hiểu tốt hơn. | Team 1 tinh chỉnh lại cách sinh `context_header` và thử nghiệm các tham số tiền xử lý trong Retrieval v2. | File báo cáo kỹ thuật & họp review tuần 8. |
| **Team 2 $\rightarrow$ Team 3 (Backend)** | - Thống kê thời gian xử lý thực tế của Reranker ($\sim 2.5$s) và LLM ($\sim 18$s).<br>- Xác nhận tổng thời gian AI luôn nằm trong ngưỡng an toàn 45 giây. | Team 3 điều chỉnh cấu hình async timeout trên Spring MVC (`50` giây) và frontend timeout (`60` giây) cho phù hợp. | Tài liệu tham số cấu hình `.env`. |
| **Team 1 $\rightarrow$ Team 2** | - Bộ ứng viên chất lượng cao từ bản cập nhật Retrieval v2 (Recall@5 $\ge 85\%$). | Team 2 nạp kết quả để chuẩn bị cho tuần 9: Tinh chỉnh Prompt và Module thẩm định trích dẫn chuyên sâu. | Gọi trực tiếp qua thư viện `team1_data`. |


## Cập nhật phần Người 1 — 30/10/2026

- VLRA-54/55: đã thêm `scripts/eval_reranker.py` để đo Hybrid và Hybrid +
  Reranker trên cùng pool top 20, xuất Recall@5/@10/@20, MRR@20, latency,
  ca tăng/mất nhóm đúng và lỗi từng câu.
- Hướng dẫn và giới hạn: [Đánh giá Hybrid và Reranker](../../../../docs/team2_rag/reranker-evaluation.md).
- Kiểm thử offline: 37 test liên quan đạt, có cả đường CLI dùng runtime giả.
- Chưa hoàn thành thực nghiệm thật: máy chưa có index/model, Golden hiện
  chưa có Dev split và gold group đã review. Các số liệu ở phần fixture và
  bảng ước tính phía trên không phải kết quả chạy của lần cập nhật này.
- VLRA-58: đã có runner để cung cấp bằng chứng; chưa chốt cấu hình tối ưu.
  Phần phân tích nguyên nhân và tối ưu của Người 2 không thay đổi.
