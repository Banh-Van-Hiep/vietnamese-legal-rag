# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 6
## Phân Hệ: Data & Retrieval (Team 1)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 6 (Quy đổi học phần: Tuần 3 cũ + 3 = Tuần 6 mới).
- **Mục tiêu trọng tâm:**
  - Hoàn thiện nhánh tìm kiếm từ khóa Lexical: BM25 Retriever sử dụng thư viện `bm25s` kết hợp bộ tách từ tiếng Việt `Underthesea`.
  - Hoàn thiện nhánh tìm kiếm ngữ nghĩa Dense: Dense Retriever sử dụng vector database `Qdrant` và mô hình embedding tiếng Việt (`AITeamVN/Vietnamese_Embedding`).
  - Xây dựng thuật toán hợp nhất Hybrid Fusion sử dụng phương pháp Reciprocal Rank Fusion (RRF, tham số $k = 60$).
  - Đóng gói thư viện Python nội bộ, bàn giao chữ ký hàm `retrieve(question: str, top_k: int = 20) -> dict` tuân thủ nghiêm ngặt schema `retrieval_output.schema.json` (đúng 12 trường `snake_case`).
  - Hoàn thành bộ chỉ mục thực tế trên toàn bộ corpus snapshot và đạt nghiệm thu **Gate G3 (Real Data Ready)**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T1-06** | **Xây dựng Lexical Retriever bằng BM25s & Underthesea**<br>- Tiền xử lý tách từ tiếng Việt (word segmentation) trên `Search Text` bằng `underthesea.word_tokenize`.<br>- Xây dựng chỉ mục BM25 bằng `bm25s` (biến thể `lucene`, lưu mmap matrix).<br>- Lưu trữ và nạp chỉ mục nhanh từ `data/indexes/{snapshot_id}/bm25/`. | - Module `bm25_retriever.py` chạy độc lập, thời gian tìm kiếm p95 $\le 100$ms.<br>- Tìm kiếm chính xác các từ khóa số hiệu văn bản (VD: "59/2020", "Nghị định 168") và số Điều luật. |
| **VLRA-T1-07** | **Xây dựng Dense Retriever bằng Qdrant & Embedding Model**<br>- Tích hợp mô hình embedding tiếng Việt (`AITeamVN/Vietnamese_Embedding` hoặc cấu hình tương đương).<br>- Sinh vector embedding cho toàn bộ chunk trong `chunks.jsonl`.<br>- Đẩy vector và payload metadata vào collection trên Qdrant.<br>- Lập trình module `dense_retriever.py` thực hiện tìm kiếm tương đồng cosine. | - Toàn bộ chunk hợp lệ được đánh chỉ mục trong Qdrant.<br>- Module `dense_retriever.py` hỗ trợ filter theo snapshot và trạng thái `verified_current`.<br>- Độ trễ truy vấn vector p95 $\le 300$ms (sau warm-up). |
| **VLRA-T1-08** | **Lập trình Reciprocal Rank Fusion (RRF, k=60) & Eligibility Filter**<br>- Lấy tối đa 100 ứng viên từ mỗi nhánh (BM25 và Dense).<br>- Tính toán điểm hợp nhất theo công thức RRF với hằng số $k = 60$.<br>- Deduplicate theo `chunk_id`, áp dụng tie-break xác định và sắp xếp lại kết quả.<br>- Áp dụng bộ lọc hiệu lực (loại bỏ các chunk không thuộc diện `verified_current`). | - Module `hybrid_fusion.py` sinh danh sách ứng viên có thứ hạng `rank` liên tục từ 1 đến N.<br>- Bắt buộc có cờ `retrieval_method = "hybrid_rrf"`.<br>- Không bị crash hoặc trả kết quả rỗng khi một nhánh có ít ứng viên. |
| **VLRA-T1-09** | **Đóng gói Interface `retrieve()` & Kiểm thử Unit Test đạt chuẩn**<br>- Đóng gói hàm gọi trực tiếp `retrieve(question, top_k=20)` làm cổng giao tiếp duy nhất cho Team 2 AI Service.<br>- Đảm bảo mỗi candidate trong `results` có đủ 12 trường `snake_case`.<br>- Viết test suite `test_retrieval.py` kiểm thử các trường hợp: câu hỏi thông thường, câu hỏi không có kết quả, câu hỏi biên, kiểm tra timeout 5s. | - Hàm `retrieve()` pass 100% các bài test schema `retrieval_output.schema.json`.<br>- Thời gian toàn trình `retrieve()` p95 $\le 1.0$ giây trên phần cứng tiêu chuẩn.<br>- Xử lý ngoại lệ rõ ràng: ném exception khi mất kết nối Qdrant/Index, trả `results = []` khi không có căn cứ. |

---

## 3. Ý Tưởng Giải Thuật & Thiết Kế Kỹ Thuật Chi Tiết

### 3.1. Sơ Đồ Kiến Trúc Hybrid Retrieval (BM25 + Dense + RRF)
```
                  ┌────────────────────────────────────────┐
                  │          Query từ Team 2 RAG           │
                  │   question (1 - 4.000 code points)     │
                  └───────────────────┬────────────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 │                                         │
                 ▼                                         ▼
   ┌───────────────────────────┐             ┌───────────────────────────┐
   │      Nhánh BM25 Lexical   │             │     Nhánh Dense Vector    │
   │  Underthesea Tokenizer    │             │  Embedding Model (768d)   │
   │  bm25s Index Search       │             │  Qdrant Cosine Similarity │
   └─────────────┬─────────────┘             └─────────────┬─────────────┘
                 │ Top 100 Candidates                      │ Top 100 Candidates
                 │ (rank_bm25: 1..100)                     │ (rank_dense: 1..100)
                 └────────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │      Reciprocal Rank Fusion (RRF)      │
                  │              k = 60                    │
                  │  RRF_Score = Sum( 1 / (60 + rank_i) )  │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │       Unit Applicability Filter        │
                  │ (Chỉ giữ chunk "verified_current")     │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  Sort theo RRF Score DESC & Truncate   │
                  │            Top-K (mặc định 20)         │
                  │      Gán rank mới liên tục 1..K        │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │   Output 12 trường RetrievalOutput     │
                  └────────────────────────────────────────┘
```

### 3.2. Công Thức Tính Điểm RRF (Reciprocal Rank Fusion)
Với mỗi tài liệu $d$ xuất hiện trong tập kết quả của BM25 hoặc Dense:
$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{bm25}, \text{dense}\}} \frac{1}{k + \text{rank}_m(d)}$$
- Hằng số làm mịn $k = 60$ (chuẩn thực nghiệm đề tài).
- Nếu tài liệu $d$ không xuất hiện trong top 100 của một nhánh thì $\text{rank}_m(d) = \infty$ (đóng góp bằng 0).
- **Tie-break xác định:** Khi hai chunk có cùng `RRF_Score`, ưu tiên chunk có điểm Dense cao hơn, sau đó so sánh theo thứ tự từ điển của `chunk_id`.

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Chữ Ký Hàm Thư Viện Python (Python Interface)
```python
from typing import Dict, Any, List

class RetrievalError(Exception):
    """Lỗi khi phân hệ truy hồi gặp sự cố kỹ thuật."""
    pass

class RetrievalUnavailableError(RetrievalError):
    """Index chưa sẵn sàng hoặc Vector DB mất kết nối."""
    pass

class RetrievalTimeoutError(RetrievalError):
    """Thời gian truy hồi vượt quá ngân sách deadline (5 giây)."""
    pass

def retrieve(question: str, top_k: int = 20) -> Dict[str, Any]:
    """
    Truy hồi các đoạn văn bản pháp luật phù hợp nhất với câu hỏi bằng cơ chế Hybrid Retrieval.
    
    Args:
        question: Câu hỏi độc lập của người dùng (1 - 4.000 code points sau trim).
        top_k: Số lượng ứng viên tối đa cần lấy (1 đến 50, mặc định 20).
        
    Returns:
        Dict tuân thủ contracts/v0.1/retrieval_output.schema.json:
        {
            "question": str,
            "results": List[Candidate]  # Mỗi candidate có đúng 12 trường snake_case
        }
        
    Raises:
        ValueError: Nếu question rỗng hoặc top_k không nằm trong khoảng 1-50.
        RetrievalUnavailableError: Khi Qdrant hoặc BM25 index không phản hồi.
        RetrievalTimeoutError: Khi truy vấn vượt quá 5.0 giây.
    """
    pass
```

### 4.2. Pydantic Schema Cho Candidate (Đúng 12 trường)
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal

class RetrievalCandidate(BaseModel):
    chunk_id: str = Field(..., min_length=1, max_length=200)
    document_id: str = Field(..., min_length=1, max_length=200)
    article_id: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=20000)
    document_title: str = Field(..., min_length=1, max_length=500)
    article: str = Field(..., min_length=1, max_length=100)
    clause: Optional[str] = Field(None, max_length=100)
    point: Optional[str] = Field(None, max_length=100)
    source_url: HttpUrl
    score: float = Field(..., description="Điểm số hữu hạn từ giải thuật hợp nhất RRF")
    rank: int = Field(..., ge=1, le=50, description="Thứ tự liên tục từ 1..N")
    retrieval_method: Literal["bm25", "dense", "hybrid_rrf"]

class RetrievalOutputSchema(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    results: List[RetrievalCandidate] = Field(..., max_items=50)
```

### 4.3. Mock Data Fixture Chuẩn (Đầu ra mẫu của hàm `retrieve`)
```json
{
  "question": "Công ty TNHH 2 thành viên ai là người đại diện theo pháp luật?",
  "results": [
    {
      "chunk_id": "luat-59-2020-qh14-v1__dieu-12__k2__0",
      "document_id": "luat-59-2020-qh14-v1",
      "article_id": "dieu-12",
      "content": "Công ty trách nhiệm hữu hạn và công ty cổ phần có thể có một hoặc nhiều người đại diện theo pháp luật. Điều lệ công ty quy định cụ thể số lượng, chức danh quản lý và quyền, nghĩa vụ của người đại diện theo pháp luật của doanh nghiệp.",
      "document_title": "Luật Doanh nghiệp số 59/2020/QH14",
      "article": "Điều 12",
      "clause": "Khoản 2",
      "point": null,
      "source_url": "https://vbpl.vn/bocongthuong/Pages/vbpq-toanvan.aspx?ItemID=143940",
      "score": 0.03278688524590164,
      "rank": 1,
      "retrieval_method": "hybrid_rrf"
    }
  ]
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 1 $\rightarrow$ Team 2 (RAG)** | - Thư viện Python `team1_data` tích hợp trực tiếp vào môi trường AI Service.<br>- Hàm `retrieve(question, top_k=20)` hoạt động với dữ liệu thật.<br>- Qdrant Collection và BM25 index snapshot sẵn sàng. | Team 2 gọi trực tiếp `retrieve()` trong luồng RAG thật, sau đó đưa danh sách candidate vào Cross-Encoder Reranker. | Python package call nội bộ & Docker container Qdrant (port 6333). |
| **Team 1 $\rightarrow$ Team 3 (Viewer)** | - Hoàn thiện hàm `get_article(document_id, article_id)` đọc dữ liệu thật từ `articles.jsonl`. | Backend Team 3 gọi sang AI Service (proxy qua Team 1) để lấy nguyên văn Điều hiển thị trên Document Viewer. | Internal HTTP Endpoint `GET /internal/v1/documents/.../articles/...`. |
| **Team 2, 3 $\rightarrow$ Team 1** | - Báo cáo lỗi format hoặc thiếu trường dữ liệu trong quá trình tích hợp thử nghiệm.<br>- Thống kê thời gian xử lý thực tế qua Backend. | Team 1 kiểm tra lại schema validation và tối ưu hiệu năng bộ truy hồi. | Log tập trung với `X-Request-ID` và họp kỹ thuật giữa tuần. |
