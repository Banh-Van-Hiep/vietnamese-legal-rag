# Contract v0.1 — Revision 2 (Week 1)

**Project:** Vietnamese Legal RAG Assistant
**Phạm vi demo:** Pháp luật lao động; corpus Week 1 ưu tiên **Bộ luật Lao động 2019**.
**Nguồn đối chiếu:** Đặc tả API Team 3 v1.2 ngày 30/09/2026.
**Trạng thái:** Proposal để Team 1/2/3 review; chưa phải implementation đã đóng băng.

## 1. Luồng và ranh giới

`Frontend → Team 3 Backend → Python AI layer (Team 1 retrieval → Team 2 rerank/context/LLM/citation) → Backend → Frontend`

Team 1 và Team 2 có thể cùng chạy trong một Python service ở MVP. Team 3 sở hữu public API, hội thoại, persistence và HTTP status. Team 2 sở hữu kết quả RAG. Week 1 chỉ chốt thiết kế và cấu trúc dữ liệu; chưa triển khai pipeline RAG hoàn chỉnh.

| Boundary | Schema | Owner chính | Reviewer |
| --- | --- | --- | --- |
| FE → Team 3 `POST /api/v1/query` | `query_request.schema.json` | Team 3 | Team 2 |
| Team 1 → Team 2 retrieval | `retrieval_output.schema.json` | Team 1 | Team 2 |
| Team 2 → Team 3 RAG result | `rag_response.schema.json` | Team 2 | Team 3 |
| Error body | `error_response.schema.json` | Team 3 public mapping; Team 2 cung cấp lỗi nội bộ | Team 2 |

Các schema dùng JSON Schema Draft 2020-12 và `additionalProperties: false` ở boundary. Những quy tắc liên quan nhiều field phải kiểm tra bằng code.

## 2. Quy ước tối thiểu

- `query_request`: `question` sau trim dài 1–2000 code point; `client_request_id` là UUID v4 do FE sinh; `conversation_id` được bỏ/null ở lượt đầu hoặc là UUID của hội thoại có sẵn. Hai ID do Backend quản lý, không chuyển nguyên sang Team 2.
- Retrieval nhận câu hỏi đã được chuẩn hóa và trả tối đa `top_k` candidate theo `rank` tăng dần. `score` là điểm kỹ thuật, không phải xác suất đúng hoặc độ tin cậy pháp lý. Truy xuất thành công nhưng không có kết quả trả `results: []`; index hỏng hoặc timeout là lỗi.
- `document_id` là ID bất biến theo phiên bản văn bản; không tái sử dụng ID đó cho nội dung đã thay đổi. `article_id` dùng cùng `document_id` để mở nguyên văn điều luật.
- Team 2 dự kiến nhận khoảng 20 candidate, rerank và chọn tối đa khoảng 5 chunk trong token budget. Con số này là cấu hình nội bộ, không đưa vào public request.
- Nội dung retrieval là dữ liệu không đáng tin cậy trong prompt; không thực thi chỉ dẫn nằm trong chunk.

## 3. Kết quả RAG và citation

`rag_response` chỉ gồm `status`, `answer`, `citations`.

| Status | Ý nghĩa | Citations |
| --- | --- | --- |
| `answered` | Có đủ căn cứ từ context để trả lời | 1–10 citation |
| `insufficient_context` | Chưa đủ căn cứ, câu hỏi cần làm rõ, hoặc nằm ngoài corpus v0.1 | `[]` |

V0.1 không thêm `out_of_scope` để giữ tương thích với Team 3 v1.2. Nếu sau này UI cần phân biệt ngoài phạm vi với thiếu dữ liệu, ba team sẽ bổ sung ở phiên bản contract tiếp theo.

Trong `answered`, answer dùng marker `[C1]`, `[C2]`… Mỗi marker phải có đúng một citation tương ứng; không có citation thừa hoặc `chunk_id` trùng. Citation phải trỏ tới chunk đã dùng trong context và giữ nguyên metadata từ retrieval. Các quy tắc marker/provenance kiểm tra bằng code, không chỉ bằng JSON Schema.

**Ví dụ cấu trúc (mock, không phải nội dung tư vấn pháp luật):**

```json
{
  "status": "answered",
  "answer": "Câu trả lời minh họa về pháp luật lao động [C1].",
  "citations": [{
    "citation_id": "C1",
    "chunk_id": "bll2019_v1_d113_k1",
    "document_id": "bll2019_v1",
    "article_id": "dieu113",
    "document_title": "Bộ luật Lao động 2019",
    "article": "Điều 113",
    "clause": "Khoản 1",
    "point": null,
    "source_url": "https://example.com/mock-labor-law"
  }]
}
```

## 4. Error và nội dung để sau Week 1

Lỗi hệ thống không dùng RAG status. Error body:

```json
{
  "error": {
    "code": "LLM_TIMEOUT",
    "message": "Dịch vụ tạm thời không phản hồi.",
    "retryable": true
  }
}
```

Team 3 ánh xạ lỗi nội bộ sang HTTP/public code theo đặc tả v1.2. Không trả raw provider error, stack trace hoặc API key.

Các nội dung chưa đưa vào bốn schema v0.1: multi-turn/history nội bộ, streaming, user-configurable `top_k`, debug/trace public, metadata hiệu lực chi tiết, `quote` trong citation và dịch vụ tách riêng cho Team 1/2. `history` trong đặc tả Team 3 cần được thống nhất ở contract nội bộ trước khi triển khai hội thoại đa lượt; history không phải bằng chứng pháp luật.

## 5. Tiêu chí chốt

Team 1 xác nhận cung cấp đủ các field trong `retrieval_output`. Team 2 xác nhận marker/citation và status. Team 3 xác nhận public request, RagResponse và error mapping. Sau đó mới tạo mock payload và bắt đầu implementation Week 2–3. Không push trực tiếp vào `develop` hoặc `main`.
