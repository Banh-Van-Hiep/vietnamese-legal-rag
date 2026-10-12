# Data Model — T02
Không DTO field mới hoặc entity/migration. Source team3.md v1.2 1.1/1.6–1.8/1.10.
- Query request: question string 1–2000 code point sau trim; client_request_id UUIDv4
  bắt buộc; conversation_id UUID/null/tùy chọn; unknown/duplicate/coercion/malformed reject.
- Public query: 8 field ID/status/answer/citations/time đúng nguồn; Backend sở hữu ID/time.
- RagAnswer: status answered hoặc insufficient_context; answer nonblank 1–12000 code point,
  citations không null. answered 1–10; insufficient_context rỗng và không marker.
- Citation: đủ 9 key; citation_id C1..C10 duy nhất; chunk_id/document_id 1–200,
  article_id 1–100, document_title 1–500, article 1–100, clause/point null hoặc 1–100,
  source_url HTTPS tuyệt đối 1–2048. Document/article ID chỉ ASCII chữ/số/_/-.
  First distinct marker theo C1..Cn, ID set đúng marker set, không chunk trùng. Array order
  không bị ràng buộc thêm; repeated marker hợp lệ. C0/C11/C01 không hợp lệ.
- ArticleResponse: đủ 6 field, ID đúng request, title/article/source như citation,
  content nonblank 1–200000 code point plain text giữ xuống dòng.
- Scenario: query 5 enum, article 4 enum theo plan; giá trị cấu hình blank/invalid fail,
  không field JSON. Legacy status chỉ answered/insufficient_context.
- Lifecycle: request hợp lệ → accept → fixture → guard → complete; fixture/guard failure
  → fail giữ conversation ID/failed state; không trạng thái thành công cho error.
- Evidence: command/environment/working-tree/input/config/expected/actual/status/log/limitations.
