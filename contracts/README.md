# Shared Contracts

[Danh mục và mapping từng file](v0.1/CONTRACT.md) là điểm đọc chính.
Giữ đường dẫn contracts/v0.1/ để các bên tiếp tục tìm đúng file, không tạo bộ public
song song. Căn cứ yêu cầu: [ARCHITECTURE](../docs/ARCHITECTURE.md).

| File | Ranh giới | Trạng thái cập nhật 29/10/2026 |
| --- | --- | --- |
| [query_request.schema.json](v0.1/query_request.schema.json) | FE → Java /api/v1/chat/stream | Sửa trực tiếp request public theo baseline: camelCase/ID số |
| [chat_stream.schema.json](v0.1/chat_stream.schema.json) | Java → FE SSE | Bổ sung payload meta/delta/complete và public citation/error |
| [retrieval_output.schema.json](v0.1/retrieval_output.schema.json) | Team 1 → Team 2 | Giữ nguyên |
| [rag_response.schema.json](v0.1/rag_response.schema.json) | Team 2 → Java | Giữ nguyên, snake_case; không phải public complete |
| [internal_article.schema.json](v0.1/internal_article.schema.json) | Python → Java Viewer | Giữ nguyên |
| [error_response.schema.json](v0.1/error_response.schema.json) | Lỗi nội bộ/dùng chung hiện có | Giữ nguyên; public error có definition trong chat_stream |

query_request hiện không còn kiểm JSON legacy /api/v1/query. Tên thư mục v0.1 không
định nghĩa phiên bản URL; public chat vẫn /api/v1/chat/stream. Không sửa API runtime.
Request question/history nội bộ không dùng query_request public.

[Validator public](v0.1/validate_public_contract.py) và [fixture mock](v0.1/public_examples.json)
phục vụ kiểm payload. Các schema nháp tại docs/team2_rag/schemas không thay bộ này.
Không suy schema hợp lệ thành dịch vụ live đã hoàn thành hoặc đáp án đã đúng pháp lý.
