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

Đề xuất contract dùng chung cho Week 1 nằm tại [`v0.1/`](v0.1/), gồm tài liệu Revision 2 và bốn JSON Schema cho các ranh giới giữa Team 1, Team 2 và Team 3.

Các schema trong [`docs/team2_rag/schemas/`](../docs/team2_rag/schemas/) là bản nháp cũ, giữ để tham khảo; không dùng để validate giao tiếp liên team v1.2 hoặc coi là schema nội bộ đã được chốt. Bộ contract chung đề xuất nằm tại [`v0.1/`](v0.1/).

Team 1, Team 2 và Team 3 cần review các điểm chưa thống nhất trong [`v0.1/README.md`](v0.1/README.md) trước khi triển khai. Request nội bộ `question/history` hiện được mô tả trong docs, chưa có JSON Schema riêng trong bộ bốn schema chung.