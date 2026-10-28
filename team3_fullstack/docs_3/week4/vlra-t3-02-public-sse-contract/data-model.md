# Data model — public payload

Không thêm DB entity. Field/giới hạn chi tiết duy trì ở schema chung và
[public API](../../../../docs/team3_fullstack/public-api-specification.md).

| Entity | Shape / quan hệ |
| --- | --- |
| ChatRequest | question, clientRequestId; conversationId optional/null; không history/model |
| Meta | conversationId, clientRequestId, userMessageId, assistantMessageId, createdAt |
| Delta | text; chỉ nối buffer khi answered, không phải kết quả canonical |
| Complete | Meta5 + status/answer/citations, đúng8 field; status quyết định cardinality |
| ErrorResponse | error object đúng code/message/retryable, không stack trace |
| PublicCitation | citationId/chunkId/documentId/articleId/documentTitle/article/clause/point/sourceUrl; nullable clause/point nhưng key bắt buộc |

SSE comment heartbeat không có entity JSON. Một terminal mỗi stream; completed/failed
và receipt được mô tả tại conversation-design, task này không đổi transition.
