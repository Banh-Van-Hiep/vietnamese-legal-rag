# 0002. Sửa contract public ngay trong `contracts/v0.1/`, không tạo v0.2

- Ngày: 2026-10-29 · Trạng thái: Accepted
- Nguồn: `contracts/v0.1/CONTRACT.md` và `contracts/README.md` (bảng "Trạng thái cập nhật 29/10/2026").

## Bối cảnh
Google Doc v2.0 (mục 9.12) dự định tạo `contracts/v0.2/` cho public SSE (chat request, stream meta/delta, public citation, public article) và giữ `query_request.schema.json` v0.1 làm contract cũ.

## Quyết định
Nhóm sửa trực tiếp `contracts/v0.1/query_request.schema.json` thành request public camelCase, ID số, có `clientRequestId`, và thêm `chat_stream.schema.json`, `internal_article.schema.json` ngay trong `v0.1/`.

## Lý do
- Frontend và backend đã dùng đường dẫn `contracts/v0.1/`; tạo bộ song song dễ khiến hai bên validate theo hai bộ khác nhau.
- Tên thư mục `v0.1` không gắn với URL `/api/v1`, nên đổi nội dung không làm đổi route.

## Phương án đã loại
- Tạo `contracts/v0.2/` như Google Doc mục 9.12: thêm một bộ schema song song trong lúc chưa có consumer nào cần bản cũ.

## Hệ quả
- `query_request.schema.json` không còn kiểm JSON của route cũ `/api/v1/query`.
- Schema nháp trong `docs/team2_rag/schemas/` không thuộc contract giữa các team. Ngày 2026-11-16 nhóm gỡ 7 bản chép nháp khỏi `contracts/v0.1/`; chúng được chép vào bởi commit `969d3da` (người commit: Banh-Van-Hiep).
