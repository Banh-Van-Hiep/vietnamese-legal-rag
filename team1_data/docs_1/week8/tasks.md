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

---

## 6. Kết Quả Thực Hiện (31/10/2026)

Ghi nhận tự động các task Team 1 thuộc phạm vi tuần 8 (đánh giá Retrieval và chốt Retrieval v2). Chuyển từ `docs/weekly-changes/2026-10-31.md`.

### VLRA-48. Pipeline đánh giá Retrieval
- **Đã đổi gì:** Gói `team1_data/evaluation` + CLI `python -m team1_data.evaluation check|run`:
  - `check`: kiểm tra Dev Set (`team1_data/golden/golden_phase1.json`) và corpus (schema, gold có trong corpus, không bị lọc `legal_status`), in sha256.
  - `run --config <json>`: chạy nhiều cấu hình (BM25 / Dense / Hybrid RRF; tham số BM25, embedder, `rrf_k`, chunk size/overlap) trên cùng Dev Set; lưu `<cấu hình>.json`, `run.json` (commit, sha256, môi trường), `run.log`, `summary.md` vào `evaluation/retrieval/runs/<run-id>/`. Mỗi đầu ra được kiểm tra theo contract v0.1.
  - Chỉ số Recall@5/10/20, MRR@20 tính theo Khoản + gộp Khoản trùng nguyên văn giữa Luật 59/2020 và VBHN 67 (860 Khoản); kèm chỉ số strict theo chunk_id.
  - Embedder offline `lsa` (TF-IDF + SVD) và `hash`; `sentence_transformers` dùng khi có mạng tới HuggingFace (môi trường này bị chặn 403).
- **File:** `team1_data/evaluation/{__init__,__main__,core}.py`, `evaluation/retrieval/README.md` (hướng dẫn chạy + kiểm tra đầu vào), `evaluation/retrieval/configs/vlra49_methods.json`, `tests/test_retrieval_evaluation.py`
- **Test chứng minh:** `tests/test_retrieval_evaluation.py` (5 test: chỉ số, gộp Khoản, cắt chunk, chạy 4 cấu hình ghi đủ file, từ chối gold lạ).
- **Kết quả test toàn bộ:** 461 → 466 passed, 0 failed.

### VLRA-49. Đánh giá BM25 / Dense / Hybrid RRF
- **Lệnh tái lập:** `python -m team1_data.evaluation run --config evaluation/retrieval/configs/vlra49_methods.json --run-id vlra49` (~45 s, CPU 4 nhân). Kết quả: `evaluation/retrieval/runs/vlra49/`.
- **Dev Set:** `team1_data/golden/golden_phase1.json` (sha256 `f89956d5d61b…`), 110 câu đều có gold, 203 gold chunk; corpus 2.576 chunk (sha256 `042bd7f1696e…`), top-20.
- **Cấu hình:** BM25 Lucene k1=1.2, b=0.75, tokenizer underthesea · Dense: **LSA offline** (TF-IDF âm tiết 1–2 gram + SVD 256 chiều, học trên corpus) trong Qdrant in-memory, cosine — thay cho `AITeamVN/Vietnamese_Embedding` vì HuggingFace bị chặn (403) · Hybrid RRF k=60, trọng số 1:1, mỗi nhánh 100 ứng viên.

| Phương pháp | Recall@5 | Recall@10 | Recall@20 | MRR@20 | Recall@5 strict | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|
| BM25 | 0.863 | 0.912 | 0.929 | 0.814 | 0.781 | 1.3 | 2.2 |
| Dense (LSA-256, offline) | 0.852 | 0.920 | 0.929 | 0.757 | 0.760 | 37.3 | 46.3 |
| Hybrid RRF k=60 | **0.876** | 0.915 | **0.933** | **0.829** | 0.802 | 43.3 | 56.3 |

- **Nhận xét:** Hybrid tốt nhất ở R@5/R@20/MRR. Có **thiên lệch theo nguồn câu hỏi**: 40 câu Team 2 R@5 ≈ 0.65–0.68, 70 câu Team 1 soạn từ nội dung chunk R@5 ≈ 0.96–0.99 (trùng từ với chunk nhiều) → số tổng hợp lạc quan hơn thực tế; xem phân tích ở VLRA-53. "strict" thấp hơn vì retriever thường trả bản VBHN 67 thay vì Luật 59 (nội dung giống hệt).
- **Giới hạn:** Dense chưa phải model thật; cần chạy lại với `{"type": "sentence_transformers", "name": "AITeamVN/Vietnamese_Embedding", "revision": …}` khi có mạng.

### VLRA-50. Chunk size (384, 512) × overlap (32, 64)
- **Lệnh tái lập:** `python -m team1_data.evaluation run --config evaluation/retrieval/configs/vlra50_chunking.json --run-id vlra50` (~1 phút 50 s). Kết quả: `evaluation/retrieval/runs/vlra50/`.
- **Cách cắt:** chunk gốc = 1 Khoản/chunk (không giới hạn độ dài, tối đa 968 token). Thử nghiệm cắt Khoản dài hơn `size` token (token = cụm không khoảng trắng, như `token_count` của chunker) bằng cửa sổ trượt `size`, bước `size − overlap`; metadata giữ nguyên, chunk_id `…__k<N>__<i>`. Chỉ số tính theo Khoản nên so được giữa các cách cắt. Cùng Dev Set 110 câu, cùng chỉ số với VLRA-49.

| Chunk | Số chunk | BM25 R@5 / R@10 / R@20 / MRR@20 | Hybrid k60 R@5 / R@10 / R@20 / MRR@20 | Hybrid p50 ms | build BM25 + Dense ms |
|---|---|---|---|---|---|
| gốc (theo Khoản) | 2576 | .863 / .912 / .929 / .814 | **.876** / .915 / .933 / .829 | 51.0 | 14121 |
| 384 / 32 | 2592 | .863 / .912 / .929 / .814 | .874 / .916 / .933 / .834 | 43.6 | 15187 |
| 384 / 64 | 2593 | .863 / .912 / .927 / .814 | **.876** / .916 / .933 / **.834** | 45.4 | 15055 |
| 512 / 32 | 2585 | .863 / .912 / .927 / .814 | .874 / .916 / .933 / .817 | 45.6 | 16292 |
| 512 / 64 | 2585 | .863 / .912 / .929 / .814 | .874 / .916 / .933 / .823 | 46.5 | 15781 |

- **Nhận xét chất lượng:** chênh lệch ≤ 0.002 Recall, ≤ 0.017 MRR — trong mức nhiễu của 110 câu. Lý do: chunk theo Khoản đã ngắn (90% ≤ 223 token), chỉ 14 Khoản > 384 và 9 Khoản > 512 token bị cắt.
- **Nhận xét chi phí:** thêm 9–17 chunk (+0,3–0,7%), thời gian build tăng ~1–2 s (do tokenize lại), latency truy vấn không đổi đáng kể (dao động do máy).
- **Đề xuất:** giữ chunk theo Khoản; nếu model embedding thật giới hạn 512 token subword (tiếng Việt ≈ 1,3 subword/âm tiết) thì bật cắt **384 / 64** — không giảm chỉ số nào, MRR Hybrid cao nhất.
- **Giới hạn:** Dense dùng LSA offline (HF bị chặn).

### VLRA-51. Hybrid RRF — thử giá trị k (cơ sở k = 60)
- **Lệnh tái lập:** `python -m team1_data.evaluation run --config evaluation/retrieval/configs/vlra51_rrf_k.json --run-id vlra51` (~1 phút). Kết quả: `evaluation/retrieval/runs/vlra51/`. Cùng Dev Set 110 câu, chunk gốc, trọng số 1:1, Dense = LSA-256 offline.

| Cấu hình | R@5 | R@10 | R@20 | MRR@20 | R@5 (40 câu Team 2) | MRR@20 (40 câu Team 2) |
|---|---|---|---|---|---|---|
| BM25 | .863 | .912 | .929 | .814 | .648 | .790 |
| Dense LSA-256 | .852 | .920 | .929 | .757 | .667 | .806 |
| Hybrid k=1 | .860 | .917 | .933 | .803 | .691 | .807 |
| Hybrid k=5 | **.876** | .914 | **.936** | .822 | .684 | .836 |
| Hybrid k=10 | .874 | .914 | **.936** | .826 | .678 | .836 |
| Hybrid k=20 | .874 | .914 | **.936** | **.829** | .678 | .836 |
| Hybrid k=30 | .874 | .914 | .933 | **.829** | .678 | .836 |
| **Hybrid k=60 (cơ sở)** | **.876** | .915 | .933 | **.829** | .683 | .836 |
| Hybrid k=100 | **.876** | .915 | .933 | **.829** | .683 | .836 |
| Hybrid k=200 | **.876** | .915 | .935 | **.829** | .683 | .836 |

- **Nhận xét:** Hybrid hơn cả hai nhánh riêng lẻ ở R@5/R@20/MRR với mọi k ≥ 5. Từ k ≥ 20 kết quả gần như bằng nhau (chênh ≤ 0.003); k quá nhỏ (k=1) giảm MRR (.803) vì xếp hạng bị một nhánh chi phối.
- **Đề xuất:** giữ **k = 60** (mặc định hiện tại, thuộc vùng ổn định, không đổi code/API). Không có bằng chứng k khác tốt hơn vượt mức nhiễu của 110 câu. Cần đo lại khi có Dense model thật (độ lệch giữa hai nhánh sẽ khác LSA).

### VLRA-52. Đánh giá mô hình Embedding — [!] làm một phần
- **Lệnh tái lập:** `python -m team1_data.evaluation run --config evaluation/retrieval/configs/vlra52_embeddings.json --run-id vlra52` (~1 phút 50 s). Kết quả: `evaluation/retrieval/runs/vlra52/`. Cùng Dev Set 110 câu, chunk gốc, Hybrid k=60.
- **Chỉ thử được embedder offline** (học/tính trên corpus, không cần tải model). Model thật (`AITeamVN/Vietnamese_Embedding` mặc định trong `embedding.py`, các ứng viên khác) **không chạy được**: HuggingFace trả 403 và môi trường không cho kiểm tra host model khác.

| Embedder | Dense R@5 / R@10 / R@20 / MRR@20 | Hybrid k60 R@5 / R@10 / R@20 / MRR@20 | Dense p50 ms | build Dense ms |
|---|---|---|---|---|
| hash-bow 512 | .716 / .811 / .852 / .669 | .836 / .914 / .920 / .805 | 33.1 | 705 |
| hash-bow 1024 | .727 / .825 / .862 / .681 | .853 / .910 / .922 / .794 | 35.4 | 1012 |
| LSA 128 | .774 / .888 / .924 / .731 | .874 / .917 / .931 / .827 | 33.7 | 2728 |
| LSA 256 | .852 / .920 / .929 / .757 | .876 / .915 / .933 / .829 | 41.4 | 3186 |
| LSA 384 | .864 / .920 / .929 / .784 | .876 / .917 / .935 / .839 | 49.4 | 4878 |
| LSA 768 | .864 / .908 / .929 / .835 | **.886** / .916 / **.938** / **.859** | 69.4 | 10632 |

- **Nhận xét:** Dense tốt hơn khi số chiều tăng (LSA 768 MRR .835), Hybrid cải thiện theo; chi phí build ×3 và latency p95 Hybrid tăng mạnh (273 ms) với 768 chiều. Trong nhóm offline, **LSA 384** cân bằng nhất (Hybrid R@5 .876, MRR .839, p50 57 ms).
- **Chưa làm được (lý do không Done):** mục tiêu của task là chọn **mô hình embedding cho hệ thống** — cần chạy model thật. Khi có mạng: thêm cấu hình `{"type": "sentence_transformers", "name": "AITeamVN/Vietnamese_Embedding", "revision": "<commit>"}` (và ứng viên khác, vd `BAAI/bge-m3`, `intfloat/multilingual-e5-base` với `query_prefix`/`passage_prefix` "query: "/"passage: ") vào `vlra52_embeddings.json` rồi chạy lại lệnh trên.

### VLRA-53. Chọn cấu hình Retrieval v2 — [!] làm một phần
- **Bảng tổng hợp** (Dev Set 110 câu, top-20; nguồn `evaluation/retrieval/runs/vlra49..52`):

| Ứng viên | R@5 | R@10 | R@20 | MRR@20 | p50 ms | Ghi chú |
|---|---|---|---|---|---|---|
| BM25 (k1 1.2, b 0.75) | .863 | .912 | .929 | .814 | 1.3 | nhanh nhất |
| Dense LSA-256 | .852 | .920 | .929 | .757 | 37 | offline |
| Hybrid k60 + LSA-256 | .876 | .915 | .933 | .829 | 43 | VLRA-49/51 |
| Hybrid k60 + LSA-384 | .876 | .917 | .935 | .839 | 57 | cân bằng nhất (VLRA-52) |
| Hybrid k60 + LSA-768 | .886 | .916 | .938 | .859 | 86 (p95 273) | tốt nhất nhưng chậm |
| Chunk 384/64 (Hybrid k60) | .876 | .916 | .933 | .834 | 45 | không khác chunk gốc (VLRA-50) |

- **Lựa chọn Retrieval v2** (`team1_data/retrieval/retrieval_v2.json`): Hybrid RRF **k = 60**, trọng số 1:1, 100 ứng viên/nhánh, BM25 Lucene k1 = 1.2, b = 0.75 (underthesea), chunk theo **Khoản** (bật 384/64 nếu model embedding giới hạn 512 subword), top_k 20, lọc `con_hieu_luc` + `het_hieu_luc_mot_phan`. Lý do: Hybrid hơn từng nhánh ở R@5/R@20/MRR với mọi embedder đã thử; k và chunk size không tạo khác biệt vượt nhiễu nên giữ mặc định hiện tại → **tương thích hoàn toàn với API/runtime hiện tại** (không đổi code, `team2_rag.runtime` dùng được ngay). Test `tests/test_retrieval_v2_config.py` khóa cấu hình này với giá trị mặc định trong code và kiểm tra đầu ra đúng contract v0.1.
- **Mục tiêu Recall@5 ≥ 85%:** đạt trên toàn Dev Set (**0.876**, Hybrid k60 + LSA-384), nhưng **chưa đạt trên 40 câu Team 2 (0.684)**. Phân tích (Hybrid k60 + LSA-384, 23 câu có R@5 < 1, 22 câu thuộc nhóm Team 2):
  1. **Câu có nhiều gold (≥ 3 Khoản, 21 câu):** R@5 = 0.565 nhưng hit@5 (có ít nhất 1 gold trong top-5) = 0.952. Câu kiểu "Điều 7 có những quyền gì" có 6–11 gold Khoản nên R@5 tối đa chỉ 5/11; trần R@5 của cả Dev Set = 0.977. Câu 1 gold (88 câu): R@5 = 0.955.
  2. **Trả đúng Điều nhưng khác Khoản** (gold_012/014/015/088): R@5 theo Điều = 0.928 toàn bộ, 0.802 nhóm Team 2.
  3. **Câu định nghĩa/phạm vi chung** (gold_001 "Luật Doanh nghiệp quy định về những vấn đề gì?", gold_003 "cổ đông là ai?", gold_004 "vốn điều lệ …"): không có gold trong top-20; Khoản định nghĩa ở Điều 4 bị lấn bởi Khoản dùng cùng từ. Cần embedding ngữ nghĩa thật hoặc tăng trọng số `article_title`.
  4. **Câu ghép nhiều văn bản** (gold_019, 020, 027, 030: Luật + Nghị định, nhiều vế): mỗi vế cần truy vấn riêng.
  5. **Thiên lệch Dev Set:** 70 câu Team 1 soạn từ nội dung chunk có R@5 = 0.986 (trùng từ cao) → con số tổng lạc quan; nên dùng nhóm Team 2 làm mốc khó.
- **Chưa làm được (lý do không Done):** embedding cho v2 chưa chốt — chỉ thử được embedder offline (VLRA-52 [!]); `retrieval_v2.json` giữ model hiện tại `AITeamVN/Vietnamese_Embedding` với `status` "chờ chốt embedding". Cần chạy lại VLRA-52/53 với model thật rồi cập nhật số liệu/độ trễ.
- **File:** `team1_data/retrieval/retrieval_v2.json`, `tests/test_retrieval_v2_config.py`.
- **Kết quả test toàn bộ:** 466 → 468 passed, 0 failed.

#### VLRA-53 (bổ sung theo yêu cầu chủ repo): báo cáo 2 tầng + chỉ số nới
- **Đã đổi gì:** pipeline thêm `hit_at_5`, `article_recall_at_5` (Recall@5 theo Điều) và `metrics_by_group` theo `review_status`; `summary.md` có thêm bảng theo nhóm. Chạy lại 5 cấu hình ứng viên: `python -m team1_data.evaluation run --config evaluation/retrieval/configs/vlra53_candidates.json --run-id vlra53` (~1,5 phút).

| Cấu hình | Toàn bộ 110: R@5 / hit@5 / R@5 theo Điều / MRR@20 | **Bộ khó 40 câu Team 2**: R@5 / hit@5 / R@5 theo Điều / MRR@20 | 70 câu Team 1: R@5 |
|---|---|---|---|
| BM25 | .863 / .946 / .914 / .814 | .648 / .875 / .789 / .790 | .986 |
| Dense LSA-384 | .864 / .946 / .929 / .784 | .677 / .900 / .806 / .791 | .971 |
| Hybrid k60 + LSA-256 | .876 / .955 / .928 / .829 | .683 / .900 / .802 / .836 | .986 |
| **Hybrid k60 + LSA-384** (v2 offline) | .876 / .955 / .928 / .839 | .684 / .900 / .802 / **.840** | .986 |
| Hybrid k60 + LSA-768 | .886 / .964 / .928 / .859 | .686 / .900 / .802 / .829 | 1.000 |

- **Đọc kết quả:** trên bộ khó, 90% câu có ít nhất một đáp án đúng trong top-5 và 80% Điều đúng nằm trong top-5, nhưng Recall@5 cấp Khoản chỉ ~0.68. Phần lớn khoảng cách là do câu có nhiều Khoản đáp án và trả đúng Điều nhưng khác Khoản, không phải do không tìm ra văn bản. Mục tiêu R@5 ≥ 85% **chưa đạt** trên bộ khó với mọi cấu hình offline.
- **Đính chính:** đề xuất trước "đưa `article_title` vào văn bản tìm kiếm" không cần — `search_text` đã gồm `context_header` có sẵn "Điều N. <tên Điều>". Câu định nghĩa (gold_001/003/004) trượt dù đã có tên Điều, nên hướng xử lý còn lại là embedding ngữ nghĩa thật hoặc gom Khoản cùng Điều.
- **Vẫn [!]:** chưa chốt embedding (cần model thật, VLRA-52). Chưa có câu hỏi do người viết thêm (bước 4) — cần người.
- **File:** `team1_data/evaluation/core.py`, `evaluation/retrieval/README.md`, `evaluation/retrieval/configs/vlra53_candidates.json`, `evaluation/retrieval/runs/vlra53/`, `tests/test_retrieval_evaluation.py`.
- **Kết quả test toàn bộ:** 468 → 469 passed, 0 failed.

### VLRA-52 (hoàn tất). Đánh giá mô hình Embedding thật
- **Môi trường:** CPU 4 nhân, torch 2.15 (PyPI), sentence-transformers 6.2; HuggingFace + CDN đã được mở. Model ghim theo commit trong `evaluation/retrieval/configs/vlra52_real_*.json`.
- **Lệnh tái lập:** `python -m team1_data.evaluation run --config evaluation/retrieval/configs/vlra52_real_<model>.json --run-id vlra52-<model>`. Kết quả: `evaluation/retrieval/runs/vlra52-{e5small,aiteamvn,bgem3}/`. Cùng Dev Set 110 câu (sha256 `f89956d5d61b…`), chunk theo Khoản, Hybrid k=60, 1:1.

| Model (số tham số, chiều) | Dense R@5 / R@20 / MRR@20 / hit@5 | Hybrid 1:1 R@5 / R@20 / MRR@20 | Bộ khó (40) Dense R@5 / hit@5 / MRR | Encode 2.576 chunk | Dense p50 |
|---|---|---|---|---|---|
| LSA-384 offline (mốc cũ) | .864 / .929 / .784 / .946 | .876 / .935 / .839 | .677 / .900 / .791 | 5 s | 49 ms |
| intfloat/multilingual-e5-small (118M, 384) | .908 / .951 / .868 / .973 | .896 / .954 / .889 | .772 / .950 / .894 | 2,3 phút | 121 ms |
| **AITeamVN/Vietnamese_Embedding** (568M, 1024) | .902 / .964 / **.950** / .982 | .908 / .960 / .919 | .754 / **.975** / **.966** | 16–23 phút | 290 ms |
| BAAI/bge-m3 (568M, 1024) | .910 / .964 / .866 / .982 | .899 / .957 / .910 | .778 / .975 / .829 | 19 phút | 295 ms |

- **Đề xuất:** dùng **AITeamVN/Vietnamese_Embedding@dea33aa** (đã là model mặc định của hệ thống): MRR@20 cao nhất rõ rệt (.950 toàn bộ, .966 bộ khó — đáp án đúng thường đứng hạng 1), hit@5 bộ khó .975. bge-m3 có R@5 ngang nhưng MRR thấp hơn nhiều (.866). e5-small là phương án dự phòng rẻ (encode nhanh ~8×, p50 121 ms) khi không có GPU, chất lượng thấp hơn ~0.08 MRR.
- **Chi phí:** model 568M encode toàn corpus ~20 phút CPU — khi lên 600 văn bản cần GPU hoặc encode offline một lần; truy vấn ~0,3 s/câu trên CPU.

### VLRA-53 (hoàn tất). Cấu hình Retrieval v2 cuối
- **Thử thêm trọng số Hybrid với AITeamVN** (`configs/vlra53_aiteamvn_weights.json`, `runs/vlra53-aiteamvn-weights/`, ~19 phút):

| Cấu hình (BM25 : Dense) | R@5 | R@20 | MRR@20 | hit@5 | R@5 theo Điều | Bộ khó R@5 / R@20 / MRR / hit@5 / R@5 Điều | p50 ms |
|---|---|---|---|---|---|---|---|
| Dense riêng | .902 | .964 | .950 | .982 | .935 | .754 / .925 / .966 / .975 / .848 | 292 |
| Hybrid k60 1 : 1 | .908 | .960 | .919 | .973 | .951 | .773 / .889 / .891 / .950 / .865 | 346 |
| **Hybrid k60 0,5 : 1** | **.912** | .966 | .946 | .982 | **.956** | **.783** / .905 / .911 / .975 / **.902** | 331 |
| Hybrid k60 0,3 : 1 | .903 | .972 | .950 | .982 | .949 | .758 / .922 / .941 / .975 / .886 | 326 |

- **Chốt Retrieval v2** (`team1_data/retrieval/retrieval_v2.json`, `status = đã chốt`): Hybrid RRF k = 60, **trọng số BM25 0,5 : Dense 1,0**, 100 ứng viên/nhánh, BM25 Lucene k1 1.2 / b 0.75, embedding **AITeamVN/Vietnamese_Embedding@dea33aa**, chunk theo Khoản, top_k 20. Lý do: R@5 và R@5 theo Điều cao nhất (toàn bộ và bộ khó), hit@5 bằng Dense riêng, MRR gần Dense riêng (.946 vs .950), hơn 1:1 ở mọi chỉ số bộ khó; vẫn giữ nhánh BM25 cho truy vấn chứa số hiệu/Điều cụ thể. Lưu ý: bộ khó chỉ 40 câu, chênh 0,5:1 với 1:1 cỡ 1 câu — chọn vì đồng thuận trên mọi chỉ số, không vì một con số đơn lẻ.
- **Tương thích API:** đổi mặc định `HybridRetriever(weights=...)` thành `DEFAULT_WEIGHTS = (0.5, 1.0)` nên `team2_rag.runtime` (gọi `HybridRetriever(adapter, dense)` không truyền weights) dùng v2 ngay, không cần Team 2 sửa code; contract `retrieval_output` không đổi. Model và revision lấy từ manifest index Dense như cũ — cần build index Dense bằng AITeamVN@dea33aa.
- **Mục tiêu Recall@5 ≥ 85%:** **đạt trên toàn Dev Set (0,912)**; **chưa đạt trên bộ khó 40 câu Team 2 (0,783)**. Nguyên nhân (có số liệu ở VLRA-53 phần trước): câu nhiều Khoản đáp án làm trần R@5 < 1; bộ khó hit@5 = 0,975 và R@5 theo Điều = 0,902 → hầu hết câu đều có đáp án đúng trong top-5, phần thiếu là Khoản phụ cùng Điều. Hướng tiếp: gom Khoản cùng Điều trong context (Team 2) hoặc đánh giá theo Điều.
- **File:** `team1_data/retrieval/hybrid.py` (`DEFAULT_WEIGHTS`), `team1_data/retrieval/retrieval_v2.json`, `docs/team1_data/hybrid-retrieval-proposal.md`, `tests/test_hybrid_retrieval.py` (test cũ truyền 1:1 tường minh + test mới cho mặc định 0,5:1), `evaluation/retrieval/runs/vlra53-aiteamvn-weights/`.
- **Kết quả test toàn bộ:** 469 → 470 passed, 0 failed.
