# Schema nháp cũ — không dùng cho giao tiếp liên team v1.2

Thư mục này giữ lại 9 JSON Schema của bản nháp thiết kế Team 2 trước đây để tham khảo. Các file JSON được giữ nguyên; chúng chưa mô tả đầy đủ đặc tả API Team 3 v1.2 và dữ liệu retrieval trong docs Team 1.

Không dùng bộ này để validate payload Team 1 → Team 2 hoặc Team 2 → Team 3. Ví dụ, schema cũ dùng `document/source`, citation có 6 trường và RAG response chưa có `status`.

## Contract chung đề xuất

Đọc [Contract v0.1 Revision 2](../../../contracts/v0.1/README.md) và dùng đúng schema theo ranh giới:

- [query_request.schema.json](../../../contracts/v0.1/query_request.schema.json): request công khai Frontend → Backend Team 3.
- [retrieval_output.schema.json](../../../contracts/v0.1/retrieval_output.schema.json): candidate Team 1 → Team 2.
- [rag_response.schema.json](../../../contracts/v0.1/rag_response.schema.json): kết quả RAG nội bộ Team 2 → Backend Team 3.
- [error_response.schema.json](../../../contracts/v0.1/error_response.schema.json): envelope lỗi; Team 3 ánh xạ HTTP và mã public.

Backend bổ sung ID hội thoại, ID message và thời gian vào public response; không validate toàn bộ public response bằng schema RAG nội bộ.

Các schema rerank/context/LLM trong thư mục này cũng chỉ là bản nháp, chưa phải hợp đồng nội bộ đã đóng băng. Xem [thiết kế I/O hiện tại](../rag-io-specification.md); rà soát schema nội bộ trước khi implementation cần đến chúng.

Bốn schema chung chưa bao gồm request nội bộ `question/history`. Phần này đang được mô tả trong docs và cần chốt riêng trước implementation. Contract chung vẫn là proposal cần các team review, không chứng minh đã có runtime tương thích.
