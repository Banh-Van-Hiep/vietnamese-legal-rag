# Contract — VLRA-42

Nguồn gốc Docs v2.0 §9; tái sử dụng [schema chat VLRA-41](../../001-vlra-41-rag-query/contracts/chat-v2.schema.json).
POST /api/v1/chat/stream JSON question/clientRequestId/conversationId optional/null;
Accept text/event-stream. meta đúng1lần trước delta/terminal; heartbeat comment bị bỏ;
complete full answer/citation là bản chuẩn, error là terminal. Reconnect POST cùng UUID,
không Last-Event-ID. Public errors envelope error/code/message/retryable.
GET conversations và messages trả arrays. Viewer GET /api/v1/documents/{documentId}?articleId=...
trả documentId/documentTitle/articleId/article/content/sourceUrl, IDs phải khớp request.
Không đổi internal snake_case hoặc tạo API Python trong task này.
