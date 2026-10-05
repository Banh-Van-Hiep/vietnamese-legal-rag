# VLRA-9 — Đặc tả I/O theo Contract v0.1

[Contract Revision 2](../../contracts/v0.1/README.md) và bốn schema là nguồn chuẩn.
Tài liệu này giải thích contract, không thay đổi interface liên team.

## Boundary

| Luồng | Payload/schema | Owner |
| --- | --- | --- |
| FE → BE: POST /api/v1/query | [query_request](../../contracts/v0.1/query_request.schema.json) | Team 3 |
| BE → Python | question; history là mở rộng nội bộ cần review | Team 3/2 |
| Team 1 → Team 2 | [retrieval_output](../../contracts/v0.1/retrieval_output.schema.json) | Team 1 |
| Team 2 → BE | [rag_response](../../contracts/v0.1/rag_response.schema.json) | Team 2 |
| Lỗi | [error_response](../../contracts/v0.1/error_response.schema.json) | Team 3 ánh xạ HTTP |

RagResponse không phải toàn bộ public response: Backend bổ sung conversation_id,
client_request_id, user_message_id, assistant_message_id theo đặc tả Team 3.
Không đưa ID hội thoại vào RagResponse hoặc để Python sinh chúng.

## 1. Public request

```json
{
  "client_request_id": "44444444-4444-4444-8444-444444444444",
  "conversation_id": null,
  "question": "Câu hỏi minh họa về pháp luật lao động?"
}
```

- client_request_id: UUID v4 bắt buộc; FE sinh, BE chống gửi trùng.
- conversation_id: bỏ/null ở lượt đầu hoặc UUID hội thoại có sẵn.
- question: 1–2000 Unicode code point sau trim, không toàn khoảng trắng.
- Không nhận top_k, history, provider hoặc debug trong public request.

Backend truyền X-Request-ID để truy vết, không chuyển hai ID public vào retrieval.
Week 1 thiết kế single-turn. Team 3 đề xuất POST /internal/v1/query với question + history;
v0.1 chưa có schema nội bộ đó. Không âm thầm bỏ history khác rỗng hoặc tuyên bố
multi-turn đã có. Khi tích hợp: history chỉ giúp giải nghĩa, cần retrieval lại,
không phải bằng chứng pháp luật.

## 2. Retrieval

retrieve(question, top_k=20): question 1–4000 code point, top_k 1–50.
Trả {"question": "...", "results": [...]} với tối đa top_k candidate (schema tối đa 50).

| Field | Kiểu/quy ước |
| --- | --- |
| chunk_id | string không rỗng, giữ nguyên |
| document_id, article_id | ID string hợp lệ, dùng cho viewer |
| content | nguyên văn chunk, 1–20000 code point |
| document_title, article | nhãn hiển thị từ nguồn |
| clause, point | có key; string không rỗng hoặc null |
| source_url | HTTPS URL từ nguồn, không tự sinh |
| score | số hữu hạn, không là confidence pháp lý |
| rank | 1…N liên tục, duy nhất; results sắp rank tăng |
| retrieval_method | bm25 / dense / hybrid_rrf |

Đúng 12 field ở mỗi candidate. Retrieval thành công không tìm được nguồn → results=[];
index hỏng/unavailable/timeout → lỗi. ID là opaque: giữ kiểu Team 1
bl-45-2019-qh14-v1 / dieu-113; không ép sang ID minh họa trong README contract.
Không nhận thêm field registry vào boundary strict. Metadata v0.2 xem [review](cross-team-review.md).

## 3. Nội bộ Team 2

Reranker giữ nguyên candidate và thêm rerank_score trong bộ nhớ, không ghi đè score/rank.
Context giữ bảng C1…C5 → chunk. Không cần schema liên team cho mỗi bước nội bộ.
Xem [reranker](reranker-design.md), [context](context-builder.md), [prompt](prompt-design.md).

## 4. RAG result

```json
{
  "status": "insufficient_context",
  "answer": "Chưa đủ căn cứ trong dữ liệu được cung cấp để trả lời.",
  "citations": []
}
```

| status | answer | citations |
| --- | --- | --- |
| answered | Tiếng Việt, 1–12000 code point, marker [C1]…[C10] | 1–10 nguồn hợp lệ |
| insufficient_context | Giới hạn dữ liệu/yêu cầu làm rõ; không kết luận pháp lý | Rỗng, không marker |

Không thêm out_of_scope. Ngoài corpus cũng dùng insufficient_context.
Schema tối đa 10 citation; builder tối đa 5 chunk nên thiết kế này tối đa 5 nguồn.
Citation có đúng citation_id, chunk_id, document_id, article_id,
document_title, article, clause, point, source_url. Không thêm claim/quote/snippet.
[Fixture answered](examples/rag_answered.json); [quy tắc citation](citation-specification.md).

## 5. Error

```json
{
  "error": {
    "code": "LLM_TIMEOUT",
    "message": "Dịch vụ xử lý chưa phản hồi trong thời hạn.",
    "retryable": true
  }
}
```

| Mã nội bộ | Mapping theo đặc tả Team 3 v1.2 |
| --- | --- |
| LLM_TIMEOUT / RETRIEVAL_TIMEOUT | 504 UPSTREAM_TIMEOUT |
| LLM_UNAVAILABLE / RETRIEVAL_UNAVAILABLE | 503 SERVICE_UNAVAILABLE |
| INVALID_LLM_OUTPUT / CITATION_INVALID | 502 UPSTREAM_INVALID_RESPONSE |

Đây là mô tả thiết kế, không triển khai HTTP mapping. AI deadline 45 giây,
Backend 50 giây, FE 60 giây. Không dùng insufficient_context để che lỗi hệ thống.
Không lộ API key/stack trace/raw provider error.

## 6. Validation ngoài JSON Schema

Trim, rank liên tục, score hữu hạn, chunk_id duy nhất, marker/citation khớp,
metadata khớp context phải kiểm tra riêng.
Schema chỉ kiểm tra hình dạng, không chứng minh nguồn hỗ trợ câu trả lời.
[Validator tài liệu](README.md#kiểm-tra-tài-liệu) không thay thế benchmark.
