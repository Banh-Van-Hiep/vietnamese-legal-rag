# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 6
## Phân Hệ: RAG & LLM (Team 2)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 6 (Quy đổi học phần: Tuần 3 cũ + 3 = Tuần 6 mới).
- **Mục tiêu trọng tâm:**
  - Xây dựng module **Cross-Encoder Reranker prototype** tích hợp mô hình `BAAI/bge-reranker-v2-m3` để chấm lại điểm top 20 candidates từ Team 1 và lọc lấy tối đa 5 chunk chất lượng cao nhất.
  - Hoàn thiện module **Context Builder** đóng gói thông minh các chunk vào prompt trong giới hạn ngân sách token ($\le 3000$ tokens).
  - Kết nối luồng sinh câu trả lời thật (Live RAG) với LLM thông qua Adapter (Gemini / OpenAI), áp dụng cấu hình chống ảo giác.
  - Vận hành dịch vụ **FastAPI Internal Server** (Port `8001`), hỗ trợ tiếp nhận header truy vết phân tán `X-Request-ID` từ Java Backend.
  - Chuyển tiếp yêu cầu tra cứu Điều luật sang Article Store của Team 1 qua route `GET /internal/v1/documents/{document_id}/articles/{article_id}`.
  - Đạt điều kiện nghiệm thu cổng **Gate G3 (Real Data Ready)** cho tầng xử lý RAG.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T2-06** | **Tích hợp Thư viện Retrieval Team 1 & Gọi tìm kiếm trực tiếp**<br>- Nhúng gói thư viện `team1_data` vào môi trường Python của AI Service.<br>- Lập trình module `retrieval_adapter.py` gọi hàm `retrieve(question, top_k=20)`.<br>- Xử lý an toàn các ngoại lệ: trả `insufficient_context` nếu `results = []`, ném lỗi 503 nếu mất kết nối Qdrant/Index. | - Gọi được dữ liệu thật từ chỉ mục Qdrant và BM25 của Team 1.<br>- Bắt trọn vẹn ngoại lệ, không để AI Service bị crash khi thư viện tầng dưới lỗi. |
| **VLRA-T2-07** | **Xây dựng Cross-Encoder Reranker Prototype (`bge-reranker-v2-m3`)**<br>- Nạp mô hình `BAAI/bge-reranker-v2-m3` qua thư viện `sentence-transformers` / `transformers`.<br>- Tính điểm tương quan ngữ nghĩa trực tiếp giữa `(question, candidate_content)` cho toàn bộ 20 ứng viên.<br>- Sắp xếp lại theo điểm Rerank Score giảm dần, cắt lấy tối đa 5 chunk tốt nhất.<br>- Đo đạc thời gian xử lý của Reranker (ngân sách $\le 5.0$ giây). | - Module `reranker.py` hoạt động ổn định trên CPU/GPU.<br>- Thời gian chấm điểm 20 candidates p95 $\le 3.0$ giây.<br>- Lưu điểm `rerank_score` nội bộ, không ghi đè metadata của Team 1. |
| **VLRA-T2-08** | **Xây dựng Context Builder & Quản trị Token tự động**<br>- Đóng gói tối đa 5 chunk sau Rerank vào template `LEGAL_CONTEXT`.<br>- Lập trình bộ đếm token bằng tokenizer LLM chuẩn, tự động loại bỏ chunk thứ 5, 4 nếu vượt quá ngưỡng 3000 tokens.<br>- Đảm bảo bảo toàn trọn vẹn từng chunk, không cắt vụn làm mất câu dẫn hoặc ngoại lệ pháp luật. | - Tổng số token của Legal Context luôn $\le 3000$ tokens.<br>- Gán nhãn `[C1]` đến `[Cn]` chuẩn xác theo thứ tự ưu tiên của Reranker. |
| **VLRA-T2-09** | **Kết nối Live LLM & Khởi chạy FastAPI Internal Server (Port 8001)**<br>- Hoàn thiện hàm gọi LLM thật sinh câu trả lời dựa trên context.<br>- Khởi chạy server FastAPI phục vụ endpoint `POST /internal/v1/query`.<br>- Tiếp nhận và ghi log header `X-Request-ID` xuyên suốt các pha xử lý.<br>- Mở endpoint proxy xem Điều: `GET /internal/v1/documents/{document_id}/articles/{article_id}` gọi hàm `get_article()` của Team 1. | - Server FastAPI chạy tại port 8001, xử lý thành công request từ curl hoặc Postman.<br>- Header `X-Request-ID` xuất hiện trong toàn bộ log xử lý.<br>- Sinh câu trả lời Live thành công kèm trích dẫn thật từ văn bản luật. |

---

## 3. Ý Tưởng Giải Thuật, Quản Trị Token & Prompt Design

### 3.1. Luồng Giải Thuật Reranking & Context Selection
```python
# Pseudocode logic trong ContextBuilder & Reranker
def build_legal_context(question: str, candidates: List[RetrievalCandidate]) -> Tuple[str, List[CitationMetadata]]:
    # 1. Chấm điểm lại bằng Cross-Encoder
    pairs = [[question, cand.content] for cand in candidates]
    rerank_scores = cross_encoder_model.predict(pairs)
    
    # 2. Gán điểm và sắp xếp giảm dần
    for idx, cand in enumerate(candidates):
        cand.rerank_score = float(rerank_scores[idx])
    sorted_candidates = sorted(candidates, key=lambda x: x.rerank_score, reverse=True)
    
    # 3. Lọc chọn tối đa 5 chunks trong ngân sách token
    selected_chunks = []
    current_tokens = 0
    TOKEN_BUDGET = 3000
    
    for cand in sorted_candidates[:5]:
        chunk_token_count = count_llm_tokens(cand.content)
        if current_tokens + chunk_token_count <= TOKEN_BUDGET:
            selected_chunks.append(cand)
            current_tokens += chunk_token_count
        else:
            # Dừng nếu thêm chunk này sẽ làm tràn ngân sách
            continue
            
    # 4. Gán nhãn [C1], [C2]... và chuẩn bị metadata tương ứng
    context_text = ""
    citations_metadata = []
    for index, cand in enumerate(selected_chunks, start=1):
        label = f"C{index}"
        context_text += f"\n[{label}]\nVăn bản: {cand.document_title}\nĐiều khoản: {cand.article}\nNội dung: {cand.content}\n"
        citations_metadata.append(create_citation_object(label, cand))
        
    return context_text, citations_metadata
```

### 3.2. Cấu Hình Adapter Gọi LLM Trực Tuyến
- **Provider mặc định:** Google Gemini 1.5 Pro / Flash qua SDK `google-generativeai`.
- **Generation Config:**
  - `temperature = 0.0` (Khóa chặt tính sáng tạo để triệt tiêu bịa đặt).
  - `top_p = 1.0`
  - `response_mime_type = "application/json"` (Ép buộc LLM trả về JSON cấu trúc).
- **Ngân sách thời gian:** Timeout gọi LLM $\le 30.0$ giây.

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Pydantic Schema Cho Request Nội Bộ (`POST /internal/v1/query`)
```python
from pydantic import BaseModel, Field
from typing import List, Literal

class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=12000)

class InternalQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    history: List[HistoryItem] = Field(default_factory=list, max_items=10)
```

### 4.2. Pydantic Schema Cho Response Nội Bộ
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal

class CitationMetadata(BaseModel):
    citation_id: str = Field(..., regex=r"^C([1-9]|10)$")
    chunk_id: str = Field(..., min_length=1, max_length=200)
    document_id: str = Field(..., min_length=1, max_length=200)
    article_id: str = Field(..., min_length=1, max_length=100)
    document_title: str = Field(..., min_length=1, max_length=500)
    article: str = Field(..., min_length=1, max_length=100)
    clause: Optional[str] = Field(None, max_length=100)
    point: Optional[str] = Field(None, max_length=100)
    source_url: HttpUrl

class InternalRagResponse(BaseModel):
    status: Literal["answered", "insufficient_context"]
    answer: str = Field(..., min_length=1, max_length=12000)
    citations: List[CitationMetadata] = Field(default_factory=list, max_items=10)
```

### 4.3. Fixture Mẫu Cho Câu Trả Lời Live RAG (Tuần 6)
```json
{
  "status": "answered",
  "answer": "Theo quy định tại Luật Doanh nghiệp 2020, công ty trách nhiệm hữu hạn và công ty cổ phần có thể có một hoặc nhiều người đại diện theo pháp luật [C1]. Số lượng, chức danh quản lý cụ thể của người đại diện sẽ do Điều lệ công ty quy định [C1].",
  "citations": [
    {
      "citation_id": "C1",
      "chunk_id": "luat-59-2020-qh14-v1__dieu-12__k2__0",
      "document_id": "luat-59-2020-qh14-v1",
      "article_id": "dieu-12",
      "document_title": "Luật Doanh nghiệp số 59/2020/QH14",
      "article": "Điều 12",
      "clause": "Khoản 2",
      "point": null,
      "source_url": "https://vbpl.vn/bocongthuong/Pages/vbpq-toanvan.aspx?ItemID=143940"
    }
  ]
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 2 $\rightarrow$ Team 3 (Backend)** | - Dịch vụ FastAPI Live Server chạy tại cổng `8001`.<br>- Hỗ trợ đầy đủ endpoint `POST /internal/v1/query` và `GET /internal/v1/documents/{document_id}/articles/{article_id}`.<br>- Header `X-Request-ID` được bảo toàn trong response header. | Java Backend gọi sang để chuyển tiếp câu hỏi từ Public SSE và hiển thị nội dung trích dẫn Điều luật trên Document Viewer. | HTTP REST API / JSON UTF-8. |
| **Team 1 $\rightarrow$ Team 2 (Retrieval)** | - Thư viện `team1_data` với hàm `retrieve()` và `get_article()` đã được kiểm thử ổn định trên dữ liệu thật. | Team 2 tích hợp trực tiếp vào pipeline Reranker và proxy Article Store. | Python Package `import team1_data`. |
| **Team 3 $\rightarrow$ Team 2** | - Cấu hình mạng Docker Compose và thông số port 8001.<br>- Phản hồi về các trường hợp lỗi timeout hoặc format JSON không khớp. | Team 2 tối ưu hóa thời gian Rerank/LLM và tinh chỉnh error handling. | Log tập trung và trao đổi kỹ thuật. |
