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

Nguyên tắc phối hợp và contract đề xuất cho Week 1 được mô tả tại [`team2_rag/rag-io-specification.md`](../docs/team2_rag/rag-io-specification.md); các JSON Schema tương ứng nằm tại [`team2_rag/schemas/`](../docs/team2_rag/schemas/). Team 1, Team 2 và Team 3 cần review các interface trước khi triển khai. Các tài liệu này là proposal thiết kế, chưa phải implementation contract đã được phê duyệt.