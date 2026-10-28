# Team 3 — Điểm đọc thiết kế theo chức năng

Nội dung chi tiết được duy trì tại từng file dưới đây. Tài liệu này là mục lục,
không lặp schema/thiết kế hoặc chứa nhiệm vụ tuần. Xem [README](README.md) cho ranh giới nguồn.

## 1. Nguồn áp dụng và nguyên tắc

[ARCHITECTURE](../ARCHITECTURE.md) là đặc tả chính;
[CODING_CONVENTIONS](../CODING_CONVENTIONS.md) quy định triển khai và nghiệm thu.
Mô tả code hiện tại không tự thay contract hoặc chứng minh hoàn thành.

## 2. Kiến trúc và ranh giới trách nhiệm

[Kiến trúc Fullstack](fullstack-architecture.md): luồng, phân lớp, owner và runtime/profile.

## 3. Public API theo baseline hiện hành

[API public và SSE](public-api-specification.md): DTO, validation, headers và lỗi.

## 4. Internal JSON và mapping nguồn

[Tích hợp RAG](rag-integration-specification.md): Python boundary, history/citation/article mapping.

## 5. Hội thoại, lỗi và retry

[ERD và persistence](persistence-design.md) · [State/idempotency](conversation-design.md).

## 6. Frontend và kiểm chứng

[Thiết kế UI](frontend-design.md): wireframe, routes, states, Viewer và an toàn render.
Phê duyệt/validation theo từng nhiệm vụ quản lý ở hồ sơ tuần, không ở các file thiết kế chung.
