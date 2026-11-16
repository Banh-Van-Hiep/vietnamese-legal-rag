# 0005. Viewer đọc Article Store `articles.jsonl` thay vì dựng Điều từ chunk

- Ngày: 2026-11-10 · Trạng thái: Accepted
- Nguồn: commit `cc111a8` và `f9883fe` (người commit: Claude), `team1_data/docs_1/week10/tasks.md` mục 3.3 và 6 (VLRA-71/72).

## Bối cảnh
Trước đây Viewer dựng nguyên văn Điều bằng cách nối các chunk. Cách này lặp câu dẫn ở 48 Điều, mất tên Điều, và mất chú thích sửa đổi ở 46 Điều.

## Quyết định
`data/doanh-nghiep/chunk_documents.py` xuất thêm `processed/articles.jsonl`: 635 Điều, mỗi dòng đúng 6 trường của `contracts/v0.1/internal_article.schema.json`, khóa `(document_id, article_id)`. `get_article` nạp file này vào bộ nhớ một lần.

## Lý do
- Nguyên văn đúng: 2.576/2.576 chunk mở đúng Điều; 46 Điều giữ đủ marker và định nghĩa chú thích (`tests/test_article_store.py`).
- Đủ nhanh: file 1,5 MB, nạp nguội 10,7 ms, `get_article` p95 1,2 µs, rất xa mốc 200 ms.
- Chunk và Article Store sinh từ cùng một lần tách, nên luôn cùng snapshot.

## Phương án đã loại
- Dựng Điều từ chunk: sai nguyên văn như nêu ở trên.
- SQLite hoặc dịch vụ riêng: không cần cho 635 Điều; thêm một thành phần phải vận hành.

## Hệ quả
- `team2_rag/articles.py` vẫn âm thầm quay về dựng Điều từ chunk khi thiếu `articles.jsonl`. Theo `ARCHITECTURE.md` mục 7.1, trường hợp này phải trả 503 `RETRIEVAL_UNAVAILABLE`. Việc sửa thuộc VLRA-71 (A2), Team 2 duyệt.
- Khi bật corpus mở rộng, cần sinh Article Store cho cả corpus đó.
