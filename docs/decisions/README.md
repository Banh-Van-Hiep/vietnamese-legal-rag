# Architecture Decision Records (ADR)

Mỗi file ghi **một** quyết định kỹ thuật: bối cảnh, quyết định, lý do, phương án đã loại và hệ quả.
`docs/ARCHITECTURE.md` mô tả hệ thống trông thế nào; ADR giải thích vì sao nhóm chọn như vậy.

Quy tắc:
- Đặt tên `NNNN-ten-ngan.md`, đánh số tăng dần, không đánh số lại.
- Trạng thái: `Proposed` (chờ nhóm chốt), `Accepted`, `Superseded by NNNN`.
- Muốn đổi một quyết định đã `Accepted`: viết ADR mới và ghi `Superseded by` vào ADR cũ, không sửa nội dung cũ.
- Khi nêu commit, ghi kèm người commit.

| ADR | Quyết định | Trạng thái |
| :--- | :--- | :--- |
| [0001](0001-baseline-v2-decisions.md) | Tám quyết định baseline v2.0 (DEC-01..08) | Accepted |
| [0002](0002-edit-contract-v0-1-in-place.md) | Sửa contract public ngay trong `contracts/v0.1/`, không tạo v0.2 | Accepted |
| [0003](0003-retrieval-v2-hybrid-aiteamvn.md) | Retrieval v2: Hybrid RRF k=60, BM25:Dense 0.5:1, AITeamVN embedding | Accepted, cần đo lại |
| [0004](0004-single-llm-slot.md) | Mỗi lúc chỉ một lượt gọi LLM trong AI service | Proposed |
| [0005](0005-article-store-articles-jsonl.md) | Viewer đọc Article Store `articles.jsonl` thay vì dựng Điều từ chunk | Accepted |

Mẫu cho ADR mới:

```markdown
# NNNN. Tên quyết định
- Ngày: YYYY-MM-DD · Trạng thái: Proposed · Người đề xuất: …
## Bối cảnh
## Quyết định
## Lý do
## Phương án đã loại
## Hệ quả
```
