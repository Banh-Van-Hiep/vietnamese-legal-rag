# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 5
## Phân Hệ: RAG & LLM (Team 2)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 5 (Quy đổi học phần: Tuần 2 cũ + 3 = Tuần 5 mới).
- **Mục tiêu trọng tâm:**
  - Xây dựng hoàn chỉnh bộ System Prompt và Context Injection Templates chuyên biệt cho bài toán hỏi đáp pháp luật doanh nghiệp Việt Nam.
  - Xây dựng **RAG Mock Service** độc lập, cung cấp đầy đủ 2 kịch bản nghiệp vụ: `answered` (kèm citation fixture trỏ về `mock_v1/art1` của Article Store) và `insufficient_context` (mảng citations rỗng, không có marker trích dẫn).
  - Triển khai bộ khung Adapter kết nối LLM thật (Google Gemini / OpenAI) và cơ chế đọc cấu hình từ biến môi trường (`.env`).
  - Hỗ trợ Team 3 tích hợp luồng giao tiếp Backend $\leftrightarrow$ AI Service mà không cần API Key LLM và không cần chờ dữ liệu thật của Team 1.
  - Đóng góp 5–10 câu hỏi kiểm thử doanh nghiệp vào bộ Golden Dataset ban đầu (30–50 câu).
  - Hoàn thành các nhiệm vụ Jira: **VLRA19**, **VLRA20**, **VLRA21** và đạt điều kiện nghiệm thu cổng **Gate G2 (Mock Integration)**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA19** | **Xây dựng Package `team2_rag`, CLI Mock & Bộ Unit Test cơ sở**<br>- Tổ chức mã nguồn package `team2_rag` hoàn chỉnh, định nghĩa các kiểu dữ liệu tại `types.py`.<br>- Lập trình giao diện CLI `__main__.py` hỗ trợ lệnh `python -m team2_rag --mock --scenario answered`.<br>- Thiết lập cấu hình `.env.example` và tài liệu hướng dẫn cài đặt `README.md`. | - Cài đặt package thành công qua `pip install -e .`.<br>- CLI chạy mượt mà, trả về JSON mẫu đúng contract.<br>- 100% Unit test cơ bản pass qua pytest. |
| **VLRA20** | **Thiết kế Prompt Templates pháp luật doanh nghiệp & LLM Adapter**<br>- Viết System Prompt chuyên gia pháp chế doanh nghiệp: bắt buộc tiếng Việt, suy diễn căn cứ từ context, nêu điều kiện/ngoại lệ, cấm bịa đặt.<br>- Xây dựng module `llm_adapter.py` tích hợp SDK Gemini / OpenAI với tham số `temperature = 0.0`.<br>- Xây dựng Context Injection Template định dạng nhãn `[C1]`, `[C2]`... | - File `prompts/system_prompt.py` và `prompts/context_template.py` được hoàn thiện.<br>- Test adapter với LLM thật bằng câu hỏi test cô lập, kiểm tra khả năng trả về JSON có cấu trúc. |
| **VLRA21** | **Xây dựng RAG Mock Service hoàn chỉnh phục vụ tích hợp độc lập**<br>- Lập trình module `mock_service.py` trả về 2 kịch bản định sẵn:<br>  + Kịch bản 1 (`answered`): Câu trả lời có nhãn `[C1]`, mảng `citations` chứa 1 phần tử trỏ đúng `document_id = "mock_v1"`, `article_id = "art1"`.<br>  + Kịch bản 2 (`insufficient_context`): Câu trả lời từ chối lịch sự, `citations = []`.<br>- Tích hợp Mock Engine vào FastAPI Adapter để phục vụ HTTP POST `/internal/v1/query`. | - Endpoint `/internal/v1/query` ở chế độ Mock trả về đúng 2 kịch bản qua cờ cấu hình `MOCK_MODE=true`.<br>- Dữ liệu trả về pass 100% validator của `rag_response.schema.json`.<br>- Backend Team 3 gọi sang nhận kết quả thành công mà không cần cấu hình API key. |
| **VLRA24-T2** | **Đóng góp câu hỏi kiểm thử Golden Dataset Phase 1 của Team 2**<br>- Đóng góp 5–10 câu hỏi tình huống thực tế về thẩm quyền ký kết hợp đồng, quyền cổ đông, giải thể công ty.<br>- Kiểm tra và thẩm định tính `answerability` (khả năng trả lời được từ ngữ cảnh). | - 5–10 câu hỏi chuẩn được bàn giao cho Team 3 tổng hợp vào file `golden_phase1_30cai.json`.<br>- Đạt tiêu chí phân loại rõ ràng giữa câu trả lời được và câu cần từ chối do thiếu dữ kiện. |

---

## 3. Ý Tưởng Giải Thuật, Quản Trị Token & Prompt Design

### 3.1. Kỹ Thuật Thiết Kế System Prompt (Prompt Engineering)
System prompt được xây dựng dựa trên nguyên tắc **Chỉ thị Tối cao (System Primacy)** nhằm vô hiệu hóa các nỗ lực Prompt Injection ẩn giấu trong văn bản luật:
```
Bạn là Trợ lý AI chuyên gia tra cứu pháp luật doanh nghiệp Việt Nam (Vietnamese Legal RAG Assistant).
Nhiệm vụ của bạn là giải đáp câu hỏi của người dùng một cách chính xác, khách quan và minh bạch dựa HOÀN TOÀN vào các tài liệu pháp luật được cung cấp trong phần LEGAL_CONTEXT.

CÁC NGUYÊN TẮC BẮT BUỘC:
1. Tính Căn cứ (Grounding): Mọi nhận định, kết luận pháp lý phải được suy diễn trực tiếp từ LEGAL_CONTEXT. Tuyệt đối không dùng kiến thức bên ngoài hoặc suy đoán.
2. Quy tắc Trích dẫn:
   - Khi đưa ra một nhận định có căn cứ từ tài liệu [Cn], bạn PHẢI gắn nhãn [Cn] ngay sau nhận định đó (ví dụ: "Doanh nghiệp có quyền tự do kinh doanh [C1].").
   - Chỉ sử dụng các nhãn [C1], [C2]... có sẵn trong danh sách tài liệu. KHÔNG TỰ BỊA ĐẶT nhãn mới, không tự sinh tên văn bản hay đường link URL trong câu trả lời.
3. Điều kiện và Ngoại lệ: Luôn nêu rõ các điều kiện đi kèm hoặc các trường hợp ngoại lệ ảnh hưởng đến kết luận pháp lý.
4. Xử lý Thiếu Căn cứ (Insufficient Context):
   - Nếu trong LEGAL_CONTEXT không có điều khoản điều chỉnh hoặc thông tin tình huống người dùng cung cấp chưa đủ để khẳng định, bạn PHẢI trả về trạng thái "insufficient_context", giải thích rõ phần thông tin còn thiếu và hướng dẫn người dùng bổ sung.
5. Ngôn ngữ & Định dạng: Trả lời bằng tiếng Việt chuẩn mực, chuyên nghiệp, định dạng JSON theo đúng schema quy định.
```

### 3.2. Context Injection Template
```jinja2
=== LỊCH SỬ HỘI THOẠI GẦN NHẤT ===
{% for item in history %}
{{ item.role }}: {{ item.content }}
{% endfor %}

=== TÀI LIỆU PHÁP LUẬT LÀM CĂN CỨ (LEGAL_CONTEXT) ===
{% for doc in context_documents %}
[{{ doc.label }}]
Văn bản: {{ doc.document_title }}
Điều khoản: {{ doc.article }} {% if doc.clause %}- {{ doc.clause }}{% endif %}
Nội dung:
{{ doc.content }}
----------------------------------------
{% endfor %}

=== CÂU HỎI HIỆN TẠI ===
Người dùng: {{ question }}

Hãy phân tích và trả về kết quả theo định dạng JSON hợp lệ.
```

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Cơ Chế Mock Service Phục Vụ Tích Hợp
Chế độ Mock được điều khiển thông qua biến môi trường:
- `MOCK_MODE=true`: Bật chế độ giả lập phản hồi, không nạp model Cross-Encoder và không gọi API LLM tốn phí.
- Phục vụ linh hoạt theo tham số hoặc nội dung câu hỏi để Team 3 kiểm thử:
  - Nếu câu hỏi chứa từ khóa `thiếu dữ liệu` hoặc `từ chối` $\rightarrow$ Trả về kịch bản `insufficient_context`.
  - Mặc định $\rightarrow$ Trả về kịch bản `answered`.

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

### 4.3. Fixture Chi Tiết — Kịch Bản 1: `answered`
```json
{
  "status": "answered",
  "answer": "Dữ liệu giả lập để kiểm thử tích hợp. Theo quy định tại Điều 1, doanh nghiệp có các quyền và nghĩa vụ theo quy định pháp luật [C1].",
  "citations": [
    {
      "citation_id": "C1",
      "chunk_id": "mock_v1_art1_clause1",
      "document_id": "mock_v1",
      "article_id": "art1",
      "document_title": "Văn bản thử nghiệm tích hợp Mock",
      "article": "Điều 1",
      "clause": "Khoản 1",
      "point": null,
      "source_url": "https://example.com/mock-law"
    }
  ]
}
```
*Lưu ý khớp nối:* Giá trị `document_id = "mock_v1"` và `article_id = "art1"` trong citation fixture này trỏ chính xác tới dữ liệu trả về của hàm `get_article(..., is_mock=True)` do Team 1 cung cấp trong tuần 5, đảm bảo luồng click citation mở Document Viewer trên UI chạy thông suốt 100%.

### 4.4. Fixture Chi Tiết — Kịch Bản 2: `insufficient_context`
```json
{
  "status": "insufficient_context",
  "answer": "Tài liệu hiện có trong hệ thống chưa đủ căn cứ để kết luận tình huống này. Bạn vui lòng bổ sung thông tin cụ thể về loại hình doanh nghiệp (công ty TNHH hay công ty cổ phần) để hệ thống tra cứu chính xác.",
  "citations": []
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 2 $\rightarrow$ Team 3 (Backend)** | - Dịch vụ FastAPI Mock Server chạy tại cổng local `http://localhost:8001`.<br>- Hướng dẫn test mock curl cho cả 2 kịch bản `answered` và `insufficient_context`. | Team 3 kết nối `HttpAiClient` và hoàn thiện SSE Controller, kiểm thử toàn bộ các frame `meta`, `delta`, `complete`. | Endpoint `POST /internal/v1/query` & file `team2_rag/README.md`. |
| **Team 1 $\rightarrow$ Team 2 (Retrieval)** | - Fixture metadata mẫu của chunk và nguyên văn Điều luật `mock_v1/art1`. | Team 2 đồng bộ trường dữ liệu citation trong RAG Mock khớp 100% với Article Store của Team 1. | Trao đổi qua contract schema và họp kỹ thuật. |
| **Team 2 $\rightarrow$ Cả nhóm (Evaluation)** | - 5–10 câu hỏi đóng góp Golden Dataset đã qua review tính khả thi nghiệp vụ. | Team 3 tổng hợp thành bộ câu hỏi chuẩn 30–50 câu của tuần 5. | File PR vào nhánh `develop`. |
