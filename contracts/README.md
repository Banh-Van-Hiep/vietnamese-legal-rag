# Shared Contracts

Thư mục này mô tả interface/data contract giữa các team. Mỗi team được tự do thiết kế implementation bên trong phạm vi của mình; chỉ dữ liệu được trao đổi qua ranh giới team mới cần thống nhất.

## Communication Flow

```text
Team 1
  │ Retrieval Output (results / chunks)
  ▼
Team 2
  │ RAG Output (answer + citations)
  ▼
Team 3
```

Team 3 cũng gửi user question qua interface đã thống nhất để phục vụ luồng hỏi đáp.

README này chỉ ghi nguyên tắc phối hợp. Chưa tạo schema hoặc contract implementation.