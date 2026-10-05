# Đặc tả I/O của RAG

## Nguồn cấu trúc

Theo [Team 3 v1.2, mục 1.6–1.10](../team3_fullstack/team3.md) và [retrieval Team 1](../team1_data/retrieval-design.md). Tài liệu này mô tả cách Team 2 sử dụng các interface đã được đề xuất trong docs hai team; không đặt ra form liên team khác.

Các JSON Schema trong [schemas/](schemas/) là bản nháp cũ, được giữ nguyên. Ví dụ: retrieval cũ có 7 trường, citation cũ có 6 trường, RAG response cũ không có `status`. Không coi những schema này là bộ kiểm tra v1.2; chưa bổ sung adapter hay schema mới trong Week 1.

## 1. Team 3 → Team 2

| Ranh giới | Payload và trách nhiệm |
| --- | --- |
| Public `POST /api/v1/query` | FE gửi `question`, `client_request_id` UUID v4, `conversation_id` tùy chọn/null. Backend kiểm tra, lưu và chống gửi trùng. |
| Internal `POST /internal/v1/query` | Backend gửi `question`, `history` và header `X-Request-ID`. Không gửi ID hội thoại/request công khai sang Python. |

`question` công khai dài 1–2000 code point sau trim. Hội thoại mới gửi `history=[]`; hội thoại cũ gửi tối đa 5 cặp user/assistant đã hoàn tất với `answer_status=answered`, từ cũ đến mới. Mỗi item chỉ có `role` (`user|assistant`) và `content` không rỗng. Tổng content ≤20000 code point; body nội bộ ≤256 KiB. Backend bỏ nguyên cặp cũ nhất nếu vượt giới hạn, không gửi lượt hiện tại, pending, failed hoặc insufficient_context.

```json
{
  "question": "Câu hỏi dùng để kiểm thử",
  "history": []
}
```

Team 2 diễn giải tham chiếu bằng history thành câu hỏi độc lập, tối đa 4000 code point để gọi retrieval. Không dùng history làm bằng chứng; nếu mơ hồ thì yêu cầu làm rõ, không tự đoán.

## 2. Team 1 → Team 2

Gọi `retrieve(question, top_k=20)` qua thư viện Python Team 1; `top_k` hợp lệ 1–50. Output có `question` đúng câu hỏi đã truy xuất và `results` tối đa `top_k` candidate.

| Field candidate | Ràng buộc theo Team 1/3 |
| --- | --- |
| `chunk_id` | String 1–200 ký tự; định danh chunk gốc |
| `document_id`, `article_id` | String 1–200 / 1–100; ASCII chữ, số, `_`, `-`; định danh phiên bản nguồn |
| `content` | String không rỗng, tối đa 20000 code point |
| `document_title`, `article` | String 1–500 / 1–100 |
| `clause`, `point` | Mỗi field có key; string 1–100 hoặc null |
| `source_url` | URL HTTPS tuyệt đối, tối đa 2048 ký tự |
| `score` | Number hữu hạn; không phải xác suất đúng |
| `rank` | Integer 1..N liên tục, duy nhất; results xếp rank tăng dần |
| `retrieval_method` | `bm25|dense|hybrid_rrf` |

Cả 12 trường đều bắt buộc. Team 2 giữ nguyên candidate và metadata, lưu điểm rerank riêng trong bộ nhớ nội bộ; không đổi `score` thành field khác trong output Team 1. Retrieval thành công không có kết quả trả `results=[]`; index lỗi/timeout phải phát sinh lỗi.

Ví dụ mock, không phải văn bản pháp luật:

```json
{
  "question": "Câu hỏi dùng để kiểm thử",
  "results": [{
    "chunk_id": "mock_v1_art1_clause1",
    "document_id": "mock_v1",
    "article_id": "art1",
    "content": "Đoạn mẫu chỉ dùng để kiểm thử cấu trúc.",
    "document_title": "Văn bản kiểm thử",
    "article": "Điều 1",
    "clause": "Khoản 1",
    "point": null,
    "source_url": "https://example.com/mock-law",
    "score": 0.03,
    "rank": 1,
    "retrieval_method": "hybrid_rrf"
  }]
}
```

## 3. Team 2 → Team 3

Internal RagResponse chỉ có `status`, `answer`, `citations`. `answer` không rỗng, tối đa 12000 code point. Citation có 9 trường theo [citation-specification.md](citation-specification.md).

```json
{
  "status": "answered",
  "answer": "Nội dung trả lời kiểm thử dựa trên đoạn mẫu [C1].",
  "citations": [{
    "citation_id": "C1",
    "chunk_id": "mock_v1_art1_clause1",
    "document_id": "mock_v1",
    "article_id": "art1",
    "document_title": "Văn bản kiểm thử",
    "article": "Điều 1",
    "clause": "Khoản 1",
    "point": null,
    "source_url": "https://example.com/mock-law"
  }]
}
```

```json
{
  "status": "insufficient_context",
  "answer": "Tài liệu được truy xuất chưa đủ căn cứ để trả lời.",
  "citations": []
}
```

Backend bổ sung `conversation_id`, `client_request_id`, `user_message_id`, `assistant_message_id`, `created_at` UTC vào public response. Team 2 không sinh các trường đó. `insufficient_context` vẫn là HTTP 200; không có marker citation trong answer.

## 4. Lỗi và timeout

ErrorResponse là `{"error":{"code":"...","message":"...","retryable":false}}`. Không kèm `answer` hoặc `status` nghiệp vụ; message tiếng Việt an toàn.

| Lỗi nội bộ | HTTP | Public code do Backend ánh xạ |
| --- | --- | --- |
| `INVALID_LLM_OUTPUT`, `CITATION_INVALID` | 502 | `UPSTREAM_INVALID_RESPONSE` |
| `RETRIEVAL_UNAVAILABLE`, `LLM_UNAVAILABLE` | 503 | `SERVICE_UNAVAILABLE` |
| `RETRIEVAL_TIMEOUT`, `LLM_TIMEOUT` | 504 | `UPSTREAM_TIMEOUT` |

Theo Team 3: output sai không retry; unavailable/timeout có `retryable=true`. Input nội bộ sai trả 400, Backend ánh xạ 4xx query thành 502 `UPSTREAM_CONTRACT_ERROR`; lỗi nội bộ ngoài dự kiến trả 500. Ngân sách AI layer 45 giây, Backend chờ 50 giây, FE 60 giây. Retry, nếu có, phải nằm trong ngân sách còn lại.

Rerank/context/LLM input là xử lý nội bộ Team 2, không tạo endpoint hoặc đổi payload liên team trong Week 1. Trước implementation, các team cần chốt schema kiểm tra tương ứng đặc tả v1.2; bản nháp JSON hiện tại chưa đáp ứng việc này.
