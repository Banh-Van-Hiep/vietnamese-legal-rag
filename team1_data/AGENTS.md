# AGENTS.md — Team 1: Data Processing & Hybrid Retrieval (`team1_data`)

## 1. Phạm Vi Trách Nhiệm
- Tiền xử lý văn bản pháp luật (Luật Doanh nghiệp và văn bản liên quan) thành định dạng chuẩn `chunks.jsonl`.
- Cung cấp bộ truy xuất `BM25Retriever`, `DenseRetriever` (Qdrant + SentenceTransformer) và `HybridRetriever` (RRF).

## 2. Hợp Đồng Dữ Liệu Đầu Ra (Retrieval Contract)
- Mỗi candidate chunk trả về cho Team 2 tuân thủ `contracts/v0.1/retrieval_output.schema.json`: đúng 12 trường `chunk_id`, `document_id`, `article_id`, `content`, `document_title`, `article`, `clause`, `point`, `source_url`, `score`, `rank`, `retrieval_method`.
- Dữ liệu chunk nội bộ (`chunks.jsonl`, 31 trường bắt buộc) theo `docs/team1_data/schemas/chunk_metadata.schema.json`. Schema này là của Team 1, không phải contract giữa các team.
- Article Store (`data/doanh-nghiep/processed/articles.jsonl`) trả cho Viewer đúng 6 trường của `contracts/v0.1/internal_article.schema.json`. Mã lỗi khi store không đọc được: xem `docs/ARCHITECTURE.md` mục 7.1.

## 3. Lệnh Kiểm Chứng Cục Bộ
```powershell
# Retrieval
.venv\Scripts\python.exe -m pytest tests/test_bm25_retrieval.py tests/test_hybrid_retrieval.py tests/test_retrieval_reranker_contract.py -q
# Article Store và Viewer
.venv\Scripts\python.exe -m pytest tests/test_article_store.py team2_rag/tests/test_article_api.py -q
# Golden Dev Set
.venv\Scripts\python.exe -m pytest tests/test_golden_phase1.py tests/test_out_of_scope_v1.py -q
```
