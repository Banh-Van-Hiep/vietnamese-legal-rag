# Shared Contract — public API và giao tiếp nội bộ

**Nguồn:** [ARCHITECTURE](../../docs/ARCHITECTURE.md), [CODING_CONVENTIONS](../../docs/CODING_CONVENTIONS.md).
**Cập nhật public:** 29/10/2026, theo quyết định sửa trực tiếp file gốc của đại diện Team 3.
Tên thư mục v0.1 được giữ để không đổi đường dẫn đang dùng; nó không có nghĩa toàn bộ
schema vẫn theo API JSON cũ. Public hiện theo baseline SSE; các schema nội bộ giữ nguyên.
Không ghi tên/tài khoản cá nhân và không suy cập nhật local đã được merge/review.

**Tác động chuyển đổi:** query_request.schema.json được sửa tại đúng tên/vị trí cũ,
không còn kiểm request snake_case/UUID của POST /api/v1/query legacy. Code legacy
profile mock vẫn tồn tại và không bị đổi; công cụ bên ngoài dùng schema cũ phải chuyển
sang payload public hiện hành. Không tạo schema lai cho cả hai loại request.

## 1. Luồng và ranh giới

`Frontend → Team 3 Backend → Python AI layer (Team 1 retrieval → Team 2 rerank/context/LLM/citation) → Backend → Frontend`

Team 1 cung cấp thư viện retrieval/article store cho AI Service Team 2. Team 3 sở hữu
public API, hội thoại, persistence và HTTP status; Team 2 sở hữu kết quả RAG nội bộ.
Tài liệu contract không tự chứng minh dịch vụ live đã sẵn sàng.

| Boundary | Schema | Vai trò / thay đổi |
| --- | --- | --- |
| FE → Java POST /api/v1/chat/stream | [query_request.schema.json](query_request.schema.json) | Sửa đúng file public request cũ: camelCase, ID hội thoại số; owner Team 3 |
| Java → FE SSE payload | [chat_stream.schema.json](chat_stream.schema.json) | Bổ sung vì bộ cũ chưa có SSE: meta, delta, complete, public error/citation; owner Team 3 |
| Team 1 → Team 2 retrieval | [retrieval_output.schema.json](retrieval_output.schema.json) | Giữ nguyên; snake_case, candidate chunks |
| Team 2 → Java RAG result | [rag_response.schema.json](rag_response.schema.json) | Giữ nguyên; status/answer/citations, không phải public complete8 |
| Python → Java Article | [internal_article.schema.json](internal_article.schema.json) | Giữ nguyên; 6 field snake_case |
| Lỗi nội bộ/dùng chung hiện có | [error_response.schema.json](error_response.schema.json) | Giữ nguyên; public payload error dùng definition ErrorResponse trong chat_stream để không đổi giới hạn nội bộ |

**Mapping rõ ràng:** query_request mới thay nội dung public request ngay tại file cũ;
chat_stream là phần SSE bổ sung, **không thay rag_response**. Java ánh xạ snake_case
của RAG result sang camelCase public citation và thêm 5 trường meta vào complete.
Các file runtime Team 2 đang đọc như rag_response không bị thay đổi trong lượt này.

Các schema dùng JSON Schema Draft 2020-12 và `additionalProperties: false` ở boundary. Những quy tắc liên quan nhiều field phải kiểm tra bằng code.

## 2. Quy ước tối thiểu

- Public query_request: question sau strip dài1–2000 Unicode code point; clientRequestId UUIDv4; conversationId bỏ/null hoặc integer1..9007199254740991. Không history/model/scenario; JSON UTF-8/camelCase. Schema kiểm payload đã chuẩn hóa; code point/NFC và integer token có kiểm bổ sung.
- chat_stream root chấp nhận một payload Meta/Delta/Complete/ErrorResponse; $defs/PublicCitation cho nguồn. ID/UUID tham chiếu query_request, không chép bộ request thứ hai. Meta5, complete8, citation9 field; clause/point nullable nhưng key bắt buộc. Heartbeat là comment, không có JSON schema riêng.
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

Kết quả RAG nội bộ giữ hai status answered/insufficient_context; không tự thêm out_of_scope.
Public complete giữ hai status này nhưng dùng field camelCase và thêm metadata của Java.

Trong `answered`, answer dùng marker `[C1]`, `[C2]`… Mỗi marker phải có đúng một citation tương ứng; không có citation thừa hoặc `chunk_id` trùng. Citation phải trỏ tới chunk đã dùng trong context và giữ nguyên metadata từ retrieval. Các quy tắc marker/provenance kiểm tra bằng code, không chỉ bằng JSON Schema.

**Ví dụ cấu trúc (mock, không phải nội dung tư vấn pháp luật):**

```json
{
  "status": "answered",
  "answer": "Câu trả lời minh họa về pháp luật doanh nghiệp [C1].",
  "citations": [{
    "citation_id": "C1",
    "chunk_id": "luat-59-2020-qh14-v1__dieu-47__k2__0",
    "document_id": "luat-59-2020-qh14-v1",
    "article_id": "dieu-47",
    "document_title": "Luật Doanh nghiệp",
    "article": "Điều 47",
    "clause": "Khoản 2",
    "point": null,
    "source_url": "https://example.com/mock-enterprise-law"
  }]
}
```

## 4. Error và quy tắc SSE

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

Team 3 ánh xạ lỗi nội bộ theo ARCHITECTURE §7. Không trả raw provider error, stack trace/API key.
ErrorResponse trong chat_stream mô tả payload public; error_response.schema.json giữ
nguyên cấu trúc/giới hạn nội bộ đang dùng, không tự sửa để đồng nhất implementation.

- Sau acceptance commit: meta trước delta/terminal. Khi chờ phát heartbeat khoảng10s.
- answered có delta0..N, complete canonical8 field; insufficient không delta/citation/marker.
- Đúng một terminal complete/error; complete giữ nguyên 5 trường meta. UUID thuộc request,
  trace HTTP mỗi attempt là riêng. Replay không gọi AI lại.
- Schema không chứng minh thứ tự raw frame, tổng buffer, heartbeat timing hoặc grounding.
  Validator kiểm marker C1..Cn theo lần xuất hiện đầu, chunk không trùng, ID/time binding,
  NFC và token integer (không nhận float1.0 dù schema coi là integer toán học).
- Legal ID public theo lowercase baseline; runtime còn rộng hơn và chưa normalize NFC
  tường minh, là backlog implementation, không được hợp thức hóa bằng cách nới schema.
- Request nội bộ question/history theo ARCHITECTURE §3.2; schema public không áp vào nó.

## 5. Kiểm chứng và bàn giao

[public_examples.json](public_examples.json) là mock kỹ thuật, không dùng làm Golden.
Dùng Python đã có jsonschema, từ gốc repository:

```powershell
python -X utf8 contracts/v0.1/validate_public_contract.py
python -X utf8 contracts/v0.1/validate_public_contract.py --wire-file team3_fullstack/backend/target/vlra41-contract-examples.json
```

--wire-file cần chạy StreamApiTests trước để có export mới. Lệnh kiểm4 payload/binding,
không phải raw SSE transcript. HTTP/FE tests kiểm heartbeat/framing/retry/disconnect.
Exit0 khi đạt; exit1 khi expected/actual lệch; exit2 khi thiếu file/schema/wire không hợp lệ.
Registry giải các $ref qua hai file local, không tải schema từ mạng. Khi dùng validator
khác phải cung cấp base URI/resolver để query_request.schema.json được resolve đúng.

Các schema nội bộ Team 1/2 giữ nguyên và tiếp tục cần kiểm chứng theo owner của chúng.
[Validation Team 3](../../team3_fullstack/docs_3/week4/vlra-t3-02-public-sse-contract/validation.md)
ghi hash preservation, ca hợp lệ/sai, wire thực và giới hạn. Schema PASS không xác nhận
đáp án đúng luật hoặc RAG live. Bàn giao theo PR/review; chưa tự commit/push vào develop/main.
