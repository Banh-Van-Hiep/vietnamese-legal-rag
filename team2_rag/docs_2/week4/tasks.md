# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 4
## Phân Hệ: RAG & LLM (Team 2)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 4 (Quy đổi học phần: Tuần 1 cũ + 3 = Tuần 4 mới).
- **Mục tiêu trọng tâm:**
  - Thiết kế kiến trúc phân hệ AI Service và luồng xử lý RAG trực tuyến toàn trình (Online RAG Flow): `Query Processing -> Hybrid Retrieval -> Cross-Encoder Reranker -> Context Builder -> Prompt Engineering -> LLM Generation -> Output & Citation Verification`.
  - Thiết lập và quản lý nghiêm ngặt ngân sách token prompt (Prompt Token Budget): `LEGAL_CONTEXT <= 3000 tokens`, `output reserve = 1500 tokens`, `safety margin = 256 tokens`.
  - Thiết kế cấu trúc package `team2_rag` tách biệt rõ ranh giới giữa thư viện lõi (Core Domain) và giao tiếp mạng (FastAPI HTTP Adapter).
  - Ban hành hợp đồng dữ liệu nội bộ (Internal Contract JSON Schema) cho endpoint `POST /internal/v1/query` và `GET /internal/v1/documents/{document_id}/articles/{article_id}`.
  - Đạt điều kiện nghiệm thu cổng **Gate G1 (Document Baseline)**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T2-01** | **Thiết kế RAG Pipeline Flow & Sơ đồ tương tác phân hệ**<br>- Thiết kế luồng xử lý truy vấn trực tuyến từ lúc nhận request đến khi trả kết quả.<br>- Định nghĩa cơ chế xử lý câu hỏi độc lập và giải tham chiếu lịch sử (Query Coreference Resolution).<br>- Thiết kế chuỗi thẩm tra output (Validation Chain): Parse JSON $\rightarrow$ Schema check $\rightarrow$ Marker check $\rightarrow$ Context membership check. | - Sơ đồ kiến trúc RAG Flow hoàn chỉnh được ghi nhận vào `docs/ARCHITECTURE.md`.<br>- Quy trình xử lý lỗi kỹ thuật (5xx) vs thiếu dữ kiện nghiệp vụ (`insufficient_context`) được thống nhất. |
| **VLRA-T2-02** | **Quản trị ngân sách Token & Cấu trúc Prompt Context Builder**<br>- Thiết lập giới hạn token chặt chẽ theo tokenizer của LLM mục tiêu.<br>- Phân bổ ngân sách: System Prompt + History ($\le 1200$ tokens), Legal Context ($\le 3000$ tokens), Output Reserve (1500 tokens), Safety Margin (256 tokens).<br>- Thiết kế cấu trúc Context Injection gán nhãn tạm `[C1]`, `[C2]`... cô lập metadata. | - Tài liệu đặc tả ngân sách token (Token Budget Spec) được ban hành.<br>- Bộ khung template Context Injection bảo vệ hệ thống khỏi Prompt Injection từ văn bản luật được hoàn thành. |
| **VLRA-T2-03** | **Đặc tả Contract nội bộ `POST /internal/v1/query` qua Pydantic Schema**<br>- Xây dựng Pydantic Schema cho `QueryRequest` (nhận `question` và `history` gồm tối đa 5 cặp completed+answered).<br>- Xây dựng Pydantic Schema cho `RagResponse` (gồm `status`, `answer`, `citations` với 9 trường `snake_case`).<br>- Định nghĩa cấu trúc lỗi chuẩn `ErrorResponse` (code, message, retryable). | - File schema Pydantic được viết và validate bằng Pytest.<br>- Đồng bộ 100% với file JSON Schema trong thư mục `contracts/v0.1/`. |
| **VLRA-T2-04** | **Khởi tạo Skeleton thư viện `team2_rag` & Cấu hình môi trường**<br>- Khởi tạo cấu trúc package Python theo chuẩn: `team2_rag/api/`, `team2_rag/core/`, `team2_rag/prompts/`, `team2_rag/clients/`.<br>- Thiết lập file `pyproject.toml`, cố định phiên bản thư viện (lockfile), tạo file `.env.example`.<br>- Thiết kế CLI test cục bộ cho phép chạy thử nghiệm độc lập. | - Chạy được lệnh `python -m team2_rag --help`.<br>- Cấu trúc package được commit và merge vào nhánh `develop` qua PR chuẩn. |
| **VLRA-T2-05** | **Khảo sát & Đề xuất LLM Adapter cùng Cross-Encoder Baseline**<br>- Đề xuất baseline Cross-Encoder: `BAAI/bge-reranker-v2-m3` chấm điểm lại top 20 candidates.<br>- Thiết kế giao diện Adapter đa nhà cung cấp LLM (Google Gemini, OpenAI, Qwen) qua biến môi trường. | - Tài liệu đánh giá và lựa chọn model baseline được thông qua.<br>- Interface LLM Client bọc ngoài SDK của nhà cung cấp được định nghĩa. |

---

## 3. Ý Tưởng Giải Thuật, Quản Trị Token & Prompt Design

### 3.1. Sơ Đồ Khối Xử Lý RAG Trực Tuyến (Online RAG Architecture)
```
      Backend Java (T3)
             │
             ▼ POST /internal/v1/query (Header: X-Request-ID)
┌────────────────────────────────────────────────────────────────────────┐
│                   Python FastAPI Adapter (T2)                          │
│  - Validate input payload bằng InternalQueryRequest Schema             │
│  - Trích xuất question & tối đa 5 cặp history gần nhất                 │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Query Processing Engine (T2)                         │
│  - Chuẩn hóa khoảng trắng, ký tự Unicode NFC                           │
│  - Coreference Resolution: giải tham chiếu đại từ (VD: "người đó")      │
│  - Sinh rewritten standalone query (<= 4.000 code points)              │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼ Direct Library Call
┌────────────────────────────────────────────────────────────────────────┐
│              Thư viện Retrieval của Team 1 (T1)                        │
│  - Gọi retrieve(question, top_k=20)                                    │
│  - Trả về 20 ứng viên (BM25 + Qdrant Dense qua RRF k=60)               │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼ Top 20 Candidates
┌────────────────────────────────────────────────────────────────────────┐
│                   Cross-Encoder Reranker (T2)                          │
│  - Model: BAAI/bge-reranker-v2-m3                                      │
│  - Tính điểm tương quan câu hỏi - ngữ cảnh                             │
│  - Lọc và chọn tối đa 5 chunk có điểm cao nhất                         │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼ Top <= 5 Best Chunks
┌────────────────────────────────────────────────────────────────────────┐
│                   Context Builder & Token Manager (T2)                 │
│  - Gán nhãn tạm [C1], [C2]... cho từng chunk                           │
│  - Đóng gói System Prompt, Context và History                          │
│  - Kiểm soát nghiêm ngặt ngân sách token <= 3000 tokens                │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼ Formatted Messages
┌────────────────────────────────────────────────────────────────────────┐
│                   LLM Provider Adapter (T2)                            │
│  - Gemini 1.5 Pro / GPT-4o-mini / Qwen qua API Key                     │
│  - Temperature = 0.0 (giảm tối đa ảo giác), JSON output                │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼ Raw LLM Output JSON
┌────────────────────────────────────────────────────────────────────────┐
│             Output Parser & Citation Verification (T2)                 │
│  - Parse JSON & Kiểm tra tính toàn vẹn                                 │
│  - Remap nhãn [Cn] trong bài viết sang mảng 9 trường citation metadata │
│  - Phân định nhánh: 'answered' vs 'insufficient_context'               │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼ InternalRagResponse (HTTP 200)
                               Backend Java (T3)
```

### 3.2. Quản Trị Ngân Sách Token (Token Budget Allocation)
Tổng ngân sách context của một lượt gọi LLM được chốt cố định như sau:
- **System Prompt & Hướng dẫn suy luận:** $\le 500$ tokens.
- **Lịch sử hội thoại (History - tối đa 5 cặp):** $\le 700$ tokens (bỏ bớt lượt cũ nhất nếu vượt quá).
- **Câu hỏi hiện tại (Question):** $\le 300$ tokens.
- **Ngữ cảnh pháp luật (`LEGAL_CONTEXT` - tối đa 5 chunks):** $\le 3000$ tokens.
- **Ngân sách dự phòng cho câu trả lời (Output Reserve):** $1500$ tokens.
- **Ngưỡng an toàn chống tràn context (Safety Margin):** $256$ tokens.
$$\text{Total Prompt Budget} \le 500 + 700 + 300 + 3000 = 4500 \text{ tokens}$$

### 3.3. Thiết Kế Cấu Trúc Context Injection
```markdown
Dưới đây là các tài liệu pháp luật làm căn cứ tra cứu (LEGAL_CONTEXT). Mỗi tài liệu được đánh nhãn [C{index}]:

[C1]
Văn bản: Luật Doanh nghiệp số 59/2020/QH14
Điều khoản: Điều 12 (Người đại diện theo pháp luật của doanh nghiệp)
Nội dung: {content_chunk_1}

[C2]
Văn bản: Nghị định 168/2025/NĐ-CP
Điều khoản: Điều 15
Nội dung: {content_chunk_2}
```
**Quy tắc bất biến:** LLM chỉ được phép trích dẫn căn cứ bằng cách gắn nhãn `[C1]`, `[C2]` vào cuối mỗi nhận định pháp lý. Tuyệt đối không cho phép mô hình tự bịa đặt ID, URL hay tên văn bản trong bài viết.

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Pydantic Schema Cho Request Nội Bộ (`InternalQueryRequest`)
```python
from pydantic import BaseModel, Field
from typing import List, Literal

class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=12000)

class InternalQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Câu hỏi của người dùng đã trim")
    history: List[HistoryItem] = Field(default_factory=list, max_items=10, description="Tối đa 5 cặp completed + answered")
```

### 4.2. Pydantic Schema Cho Response Nội Bộ (`InternalRagResponse`)
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal

class CitationMetadata(BaseModel):
    citation_id: str = Field(..., regex=r"^C([1-9]|10)$", description="Nhãn trích dẫn từ C1 đến C10")
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

### 4.3. Mock Data Fixture — Nhánh `answered`
```json
{
  "status": "answered",
  "answer": "Người đại diện theo pháp luật của doanh nghiệp là cá nhân đại diện cho doanh nghiệp thực hiện các quyền và nghĩa vụ phát sinh từ giao dịch [C1].",
  "citations": [
    {
      "citation_id": "C1",
      "chunk_id": "mock_v1_art1_clause1",
      "document_id": "mock_v1",
      "article_id": "art1",
      "document_title": "Luật Doanh nghiệp (Thử nghiệm)",
      "article": "Điều 1",
      "clause": "Khoản 1",
      "point": null,
      "source_url": "https://example.com/mock-law"
    }
  ]
}
```

### 4.4. Mock Data Fixture — Nhánh `insufficient_context`
```json
{
  "status": "insufficient_context",
  "answer": "Dữ liệu pháp luật trong snapshot hiện tại chưa có quy định cụ thể về vấn đề bạn đang hỏi. Vui lòng cung cấp thêm thông tin về loại hình doanh nghiệp để hệ thống đối chiếu chính xác.",
  "citations": []
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 2 $\rightarrow$ Team 3 (Backend)** | - Đặc tả Schema JSON nội bộ `InternalQueryRequest` và `InternalRagResponse`.<br>- Quy ước lỗi HTTP và Error Envelope (`code`, `message`, `retryable`). | Team 3 xây dựng `HttpAiClient` trên Java Spring Boot để gọi sang AI Service và map sang Public SSE. | OpenAPI / JSON Schema trong `contracts/v0.1/` & tài liệu tuần `tasks.md`. |
| **Team 1 $\rightarrow$ Team 2 (Retrieval)** | - Chữ ký hàm thư viện `retrieve(question, top_k=20)`.<br>- Schema 12 trường của `RetrievalCandidate`. | Team 2 tích hợp hàm tìm kiếm trực tiếp vào pipeline xử lý ngữ cảnh trước khi rerank. | Thư viện Python `team1_data` import nội bộ. |
| **Cả 3 Team** | - Thống nhất mã lỗi hệ thống: 400 (Bad Request), 502 (Upstream Invalid), 503 (Unavailable), 504 (Timeout). | Đồng bộ xử lý lỗi toàn trình từ Frontend đến AI Service. | Bảng mã lỗi chuẩn trong `docs/CODING_CONVENTIONS.md`. |
