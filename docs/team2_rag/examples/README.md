Mock chỉ kiểm tra schema/provenance, không phải nội dung pháp luật hay kết quả gọi model.
URL example.com không dùng cho sản phẩm. Runtime chỉ nhận nguồn thật từ Team 1.

query_request: public FE → Backend.
retrieval_output: Team 1 → Team 2.
rag_answered / rag_insufficient: Team 2 → Backend, chưa có ID Backend bổ sung.
error_response: lỗi nội bộ, Backend quyết định public HTTP/code.
