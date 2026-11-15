# Shared Contracts (Contract-First SSOT)

Thư mục `contracts/v0.1/` là nơi lưu trữ tập trung toàn bộ JSON Schema (Single Source of Truth) định nghĩa hợp đồng giao tiếp giữa Team 1, Team 2 và Team 3.

[Danh mục và mapping chi tiết từng file](v0.1/CONTRACT.md) là điểm đọc chính.
Giữ nguyên đường dẫn `contracts/v0.1/` để các bên tiếp tục tìm đúng file theo kiến trúc [ARCHITECTURE](../docs/ARCHITECTURE.md).

| File Schema | Ranh giới giao tiếp | Chức năng chính |
| :--- | :--- | :--- |
| [retrieval_output.schema.json](v0.1/retrieval_output.schema.json) | Team 1 → Team 2 | Cấu trúc danh sách candidate chunks trả về sau Retrieval |
| [chunk_metadata.schema.json](v0.1/chunk_metadata.schema.json) | Team 1 → Team 2 | Định nghĩa đầy đủ metadata 12 trường của từng chunk |
| [rerank_output.schema.json](v0.1/rerank_output.schema.json) | Team 2 Nội bộ | Candidate chunks sau khi chấm điểm và xếp hạng qua Reranker |
| [context.schema.json](v0.1/context.schema.json) | Team 2 Nội bộ | Ngữ cảnh nén và format nhãn [C1]..[Cn] đưa vào Prompt |
| [llm_input.schema.json](v0.1/llm_input.schema.json) | Team 2 Nội bộ | Định dạng tham số và prompt hoàn chỉnh gửi tới LLM Provider |
| [llm_output.schema.json](v0.1/llm_output.schema.json) | Team 2 Nội bộ | Cấu trúc JSON bắt buộc mà LLM phản hồi |
| [rag_response.schema.json](v0.1/rag_response.schema.json) | Team 2 → Java Backend | Định dạng phản hồi cuối cùng của RAG Pipeline |
| [internal_article.schema.json](v0.1/internal_article.schema.json) | Python → Java Backend | Endpoint xem chi tiết Điều luật (`/internal/v1/documents/...`) |
| [error_response.schema.json](v0.1/error_response.schema.json) | Dùng chung toàn hệ thống | Chuẩn hóa cấu trúc lỗi wire code và cờ `retryable` |
| [query_request.schema.json](v0.1/query_request.schema.json) | Frontend → Java Backend | Request gửi câu hỏi và lịch sử hội thoại |
| [chat_stream.schema.json](v0.1/chat_stream.schema.json) | Java Backend → Frontend | Sự kiện Server-Sent Events (SSE) stream câu trả lời về UI |
