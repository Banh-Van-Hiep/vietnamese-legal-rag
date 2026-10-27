# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 8
## Phân Hệ: Data & Retrieval (Team 1)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 8 (Quy đổi học phần: Tuần 5 cũ + 3 = Tuần 8 mới).
- **Mục tiêu trọng tâm:**
  - Thiết lập pipeline đánh giá tự động và đo đạc các chỉ số truy hồi trên tập **Dev Set** (chiếm 60% Golden Dataset v1 đã đóng băng).
  - Tiến hành thực nghiệm so sánh đa cấu hình: BM25-only, Dense-only, Hybrid RRF thuần túy và Weighted RRF với các giá trị làm mịn $k$ khác nhau.
  - Thử nghiệm các tham số tiền xử lý: `MAX_TOKENS` (384 vs 512), `OVERLAP_TOKENS` (32 vs 64), và đánh giá các biến thể mô hình embedding tiếng Việt.
  - Tối ưu hóa toàn diện để đạt mục tiêu kỹ thuật cốt lõi của đề tài Project 1: **Recall@5 $\ge 85\%$** trên các câu hỏi answerable; đồng thời báo cáo đầy đủ **Recall@10**, **Recall@20** (mục tiêu $\ge 90\%$) và **MRR@20**.
  - Đóng gói phiên bản **Retrieval Pipeline v2** và công bố **Báo cáo Thực nghiệm Retrieval Evaluation Report**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T1-14** | **Xây dựng Runner Đánh giá Tự động (Retrieval Evaluation Runner)**<br>- Lập trình script `evaluate_retrieval.py` tự động nạp Dev Set, gửi query vào hàm `retrieve()`, tính toán các chỉ số Top-K Recall và MRR.<br>- Triển khai thuật toán tính toán độ phủ nhóm đơn vị pháp lý tương đương (`relevant_unit_groups`) để tránh sai lệch điểm số do cách chia nhỏ chunk. | - Script `evaluate_retrieval.py` chạy tự động, xuất kết quả ra file JSON và bảng tổng hợp Markdown.<br>- Hỗ trợ macro-average trên toàn bộ tập câu hỏi answerable trong Dev Set.<br>- Tách biệt hoàn toàn, không sử dụng Test Set để tránh ô nhiễm dữ liệu. |
| **VLRA-T1-15** | **Thực nghiệm so sánh đa phương pháp (BM25 vs Dense vs Hybrid RRF)**<br>- Chạy benchmark cấu hình Baseline B0 (BM25-only).<br>- Chạy benchmark cấu hình Dense-only (Qdrant Cosine Similarity).<br>- Chạy benchmark Hybrid RRF với các giá trị $k \in \{20, 60, 100\}$ và Weighted RRF (tỷ lệ trọng số $0.3 / 0.7$, $0.5 / 0.5$, $0.7 / 0.3$). | - Có bảng dữ liệu đối đầu trực tiếp giữa các phương pháp trên cùng một Dev Set.<br>- Chứng minh định lượng Hybrid Fusion vượt trội hơn rõ rệt so với chạy đơn lẻ từng nhánh.<br>- Chọn ra tham số $k$ tối ưu nhất cho bài toán pháp luật doanh nghiệp. |
| **VLRA-T1-16** | **Thực nghiệm tham số Chunk Size, Overlap & Tinh chỉnh Index**<br>- Thử nghiệm tạo hai biến thể chunking: Biến thể A (`TARGET = 384`, `MAX = 512`, `OVERLAP = 64`) và Biến thể B (`TARGET = 256`, `MAX = 384`, `OVERLAP = 32`).<br>- Re-build chỉ mục trên tập dữ liệu thử nghiệm và đo lường độ dịch chuyển của Recall@5.<br>- Tinh chỉnh các tham số HNSW trên Qdrant (`ef_search`, `m`) để cân bằng giữa độ chính xác và độ trễ. | - Báo cáo phân tích tác động của kích thước đoạn cắt đối với khả năng truy hồi ngữ cảnh.<br>- Xác lập cấu hình chunking chuẩn cho phiên bản Retrieval v2.<br>- Đảm bảo thời gian truy hồi p95 vẫn duy trì $\le 1.0$ giây. |
| **VLRA-T1-17** | **Đóng gói Retrieval v2 & Ban hành Báo cáo Thực nghiệm**<br>- Cập nhật mã nguồn `team1_data` thành phiên bản chính thức Retrieval v2.<br>- Viết báo cáo chi tiết `docs/retrieval_evaluation_report.md` gồm: phương pháp luận, thông số phần cứng, các bảng so sánh, biểu đồ phân tích và phân loại các ca lỗi phổ biến (Error Analysis). | - Retrieval v2 được merge vào nhánh develop qua PR có đầy đủ test evidence.<br>- Chỉ số **Recall@5 đạt $\ge 85\%$** trên Dev Set.<br>- Báo cáo thực nghiệm được phê duyệt và lưu trữ làm bằng chứng cho Gate G5 sau này. |

---

## 3. Ý Tưởng Giải Thuật & Thiết Kế Kỹ Thuật Chi Tiết

### 3.1. Phương Pháp Luận Đánh Giá (Evaluation Metrics)

#### A. Top-K Recall (Recall@K)
Với một câu hỏi $q$ có tập các nhóm đơn vị pháp lý chuẩn $G_q = \{g_1, g_2, \dots, g_m\}$ (mỗi nhóm đại diện cho một Khoản hoặc Điều luật cần thiết):
$$\text{Recall@K}(q) = \frac{|\{g \in G_q \mid \text{Top-K}(q) \cap g \neq \emptyset\}|}{|G_q|}$$
$$\text{Macro-Recall@K} = \frac{1}{|Q_{\text{answerable}}|} \sum_{q \in Q_{\text{answerable}}} \text{Recall@K}(q)$$
- **Mục tiêu bắt buộc:** $\text{Recall@5} \ge 0.85$ (Cổng kiểm soát chất lượng của MVP).
- **Mục tiêu mở rộng:** $\text{Recall@20} \ge 0.90$.

#### B. Mean Reciprocal Rank (MRR@K)
Đo lường vị trí xuất hiện đầu tiên của một đơn vị pháp lý đúng trong danh sách trả về:
$$\text{RR}(q) = \begin{cases} \frac{1}{\text{rank}_1(q)} & \text{nếu có ít nhất 1 chunk đúng trong Top-K} \\ 0 & \text{ngược lại} \end{cases}$$
$$\text{MRR@K} = \frac{1}{|Q_{\text{answerable}}|} \sum_{q \in Q_{\text{answerable}}} \text{RR}(q)$$

### 3.2. Bảng Thiết Kế Ma Trận Thực Nghiệm (Experiment Matrix)
| Mã Cấu hình | Phương pháp Truy hồi | Tham số Chunking | Tham số Fusion / Search | Mục tiêu kỳ vọng |
| :--- | :--- | :--- | :--- | :--- |
| **EXP-01 (Baseline B0)** | BM25-only | Target 384, Max 512 | `k1=1.5`, `b=0.75` | Đo mốc cơ sở (dự kiến Recall@5 ~ 65-70%) |
| **EXP-02** | Dense-only (Qdrant) | Target 384, Max 512 | Cosine, `ef_search=64` | Đánh giá độ phủ ngữ nghĩa đơn thuần |
| **EXP-03** | Hybrid RRF ($k=20$) | Target 384, Max 512 | RRF $k=20$, top 100/nhánh | Khảo sát mức độ ưu tiên thứ hạng đầu |
| **EXP-04 (Target v1)** | Hybrid RRF ($k=60$) | Target 384, Max 512 | RRF $k=60$, top 100/nhánh | Cấu hình chuẩn đề xuất |
| **EXP-05** | Hybrid RRF ($k=100$)| Target 384, Max 512 | RRF $k=100$, top 100/nhánh| Khảo sát mức độ san phẳng thứ hạng |
| **EXP-06 (Chunking v2)**| Hybrid RRF ($k=60$) | Target 256, Max 384 | Overlap 32 | Đo ảnh hưởng của việc cắt chunk nhỏ hơn |
| **EXP-07 (Weighted RRF)**| Weighted RRF | Target 384, Max 512 | $W_{\text{dense}}=0.6, W_{\text{bm25}}=0.4$ | Tối ưu hóa trọng số ngữ nghĩa |

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Chữ Ký Module Đánh Giá Tự Động (Python Interface)
```python
from typing import Dict, Any, List

def evaluate_retrieval_on_dataset(
    dataset_path: str,
    top_k_list: List[int] = [5, 10, 20],
    rrf_k: int = 60,
    is_dev_only: bool = True
) -> Dict[str, Any]:
    """
    Chạy đánh giá tự động trên tập câu hỏi và xuất các chỉ số truy hồi.
    
    Args:
        dataset_path: Đường dẫn tới file JSON Golden Dataset.
        top_k_list: Danh sách các mốc K cần đo lường (mặc định [5, 10, 20]).
        rrf_k: Tham số hằng số làm mịn của giải thuật RRF.
        is_dev_only: Cờ bảo vệ bắt buộc chỉ đọc các câu thuộc split 'dev'.
        
    Returns:
        Dict chứa báo cáo chi tiết:
        {
            "total_queries": int,
            "answerable_queries": int,
            "metrics": {
                "recall@5": float,
                "recall@10": float,
                "recall@20": float,
                "mrr@20": float
            },
            "latency_p95_ms": float,
            "failed_query_ids": List[str]
        }
    """
    pass
```

### 4.2. Pydantic Schema Cho Báo Cáo Thực Nghiệm
```python
from pydantic import BaseModel, Field
from typing import Dict, List

class RetrievalMetricsReport(BaseModel):
    experiment_id: str
    configuration_summary: str
    sample_count: int = Field(..., ge=1)
    recall_at_5: float = Field(..., ge=0.0, le=1.0)
    recall_at_10: float = Field(..., ge=0.0, le=1.0)
    recall_at_20: float = Field(..., ge=0.0, le=1.0)
    mrr_at_20: float = Field(..., ge=0.0, le=1.0)
    latency_p50_ms: float
    latency_p95_ms: float
    error_analysis_notes: str
```

### 4.3. Mock Data Fixture — Kết Quả Báo Cáo Mẫu (Tuần 8 Target)
```json
{
  "experiment_id": "EXP-04-RRF60-DEV",
  "configuration_summary": "Hybrid BM25s + Underthesea + Qdrant (AITeamVN Embedding) + RRF (k=60)",
  "sample_count": 60,
  "recall_at_5": 0.867,
  "recall_at_10": 0.917,
  "recall_at_20": 0.950,
  "mrr_at_20": 0.782,
  "latency_p50_ms": 420.5,
  "latency_p95_ms": 850.0,
  "error_analysis_notes": "Đạt chỉ tiêu Recall@5 >= 85% trên Dev Set. 8 trường hợp miss chủ yếu do từ khóa quá đặc thù trong biểu mẫu Thông tư 68."
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 1 $\rightarrow$ Team 2 (RAG)** | - Phiên bản **Retrieval Pipeline v2** có cấu hình tham số tối ưu nhất.<br>- Danh sách top 20 candidates chất lượng cao (Recall@5 $\ge 85\%$).<br>- Phân tích các trường hợp khó để Team 2 tinh chỉnh prompt và reranker. | Team 2 sử dụng để bước vào tuần 9: Tối ưu LLM Prompt, Context Builder và Citation Verification trên kết quả truy hồi chuẩn xác. | Package update `team1_data` & Báo cáo `docs/retrieval_evaluation_report.md`. |
| **Team 1 $\rightarrow$ Team 3 (Fullstack)** | - Chỉ số đo đạc độ trễ p95 của thư viện truy hồi sau tối ưu ($\le 850$ms).<br>- Xác nhận API contract `retrieve()` và `get_article()` không có bất kỳ thay đổi nào gây ảnh hưởng ngược dòng. | Team 3 tích hợp đo đạc thời gian toàn trình (End-to-End Latency) và kiểm thử khả năng chịu tải trên Backend Java. | Báo cáo hiệu năng và file cấu hình `.env`. |
| **Team 3 $\rightarrow$ Team 1** | - File Golden Dataset v1 đã phân chia rõ cờ `split: "dev"` (60%) và `split: "test"` (40%). | Team 1 nạp đúng tập Dev để chạy các vòng thực nghiệm tuần 8. | File `team2_rag/data/golden/golden_dataset_v1.json`. |
