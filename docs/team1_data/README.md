# Team 1 — Data & Retrieval

## Responsibilities

- Legal data and data cleaning
- Chunking and metadata
- BM25 retrieval and dense retrieval
- Embedding and vector store/vector database
- Hybrid retrieval and Reciprocal Rank Fusion (RRF)
- Retrieval evaluation

Hybrid Retrieval và RRF thuộc Team 1, không thuộc Team 2.

## Scope

Team 1 tự thiết kế implementation bên trong thư mục này. Chỉ dữ liệu trao đổi với team khác cần được thống nhất tại `contracts/`. README này chỉ mô tả trách nhiệm; chưa có implementation.

## Tài liệu thiết kế

Đọc theo thứ tự dưới đây.

### Đặc tả dữ liệu và quy trình xử lý

| Tài liệu | Nội dung |
|---|---|
| [`legal-data-specification.md`](legal-data-specification.md) | Danh mục văn bản, nguồn và định dạng (HTML/DOCX/PDF), cấu trúc Phần/Chương/Mục/Điều/Khoản/Điểm, registry văn bản |
| [`data-processing-flow.md`](data-processing-flow.md) | Pipeline 8 bước, quy tắc làm sạch và chuẩn hóa, validation |
| [`chunk-format-spec.md`](chunk-format-spec.md) | Chunk theo Khoản, `MAX_TOKENS` = 512, overlap, câu dẫn, `context_header` |
| [`metadata-specification.md`](metadata-specification.md) | Trường metadata, quy tắc sinh ID, ánh xạ sang `retrieval_output` |
| [`schemas/chunk_metadata.schema.json`](schemas/chunk_metadata.schema.json) | JSON Schema của một chunk |

### Kiến trúc tìm kiếm và truy hồi

| Tài liệu | Nội dung |
|---|---|
| [`retrieval-design.md`](retrieval-design.md) | Luồng tổng thể, chọn Qdrant, interface `retrieve()`, lỗi, phiên bản index, đánh giá |
| [`bm25-proposal.md`](bm25-proposal.md) | `bm25s`, tách từ Underthesea, bảo vệ cụm pháp lý |
| [`dense-retrieval-proposal.md`](dense-retrieval-proposal.md) | Mô hình embedding tiếng Việt, collection Qdrant, quy trình build index |
| [`hybrid-retrieval-proposal.md`](hybrid-retrieval-proposal.md) | RRF (`k` = 60), so sánh với Weighted Score, tie-break |

### Phạm vi corpus

Đã chốt: **pháp luật lao động**, trọng tâm là Bộ luật Lao động 2019
(45/2019/QH14) và các văn bản hướng dẫn còn hiệu lực. Thống nhất với
`contracts/v0.1/README.md` của Team 2. Danh mục đầy đủ ở
[`legal-data-specification.md`](legal-data-specification.md) mục 2.1.

### Vấn đề mở cần thống nhất với Team 2 và Team 3

- Bổ sung `document_number`, `issued_date`, `legal_status` vào contract retrieval v0.2.
- Phiên bản image Qdrant trong `docker-compose.yml` chung.