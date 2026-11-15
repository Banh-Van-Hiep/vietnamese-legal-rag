# AGENTS.md — Team 1: Data Processing & Hybrid Retrieval (`team1_data`)

## 1. Phạm Vi Trách Nhiệm
- Tiền xử lý văn bản pháp luật (Luật Doanh nghiệp và văn bản liên quan) thành định dạng chuẩn `chunks.jsonl`.
- Cung cấp bộ truy xuất `BM25Retriever`, `DenseRetriever` (Qdrant + SentenceTransformer) và `HybridRetriever` (RRF).

## 2. Hợp Đồng Dữ Liệu Đầu Ra (Retrieval Contract)
- Mỗi candidate chunk trả về cho Team 2 bắt buộc tuân thủ schema `contracts/v0.1/retrieval_output.schema.json` và `contracts/v0.1/chunk_metadata.schema.json` (đầy đủ 12 trường: `chunk_id`, `document_id`, `article_id`, `document_title`, `article`, `content`, `source_url`, `score`, `rank`, `retrieval_method`...).

## 3. Lệnh Kiểm Chứng Cục Bộ
```powershell
.venv\Scripts\python.exe -m pytest tests/test_bm25_retrieval.py tests/test_hybrid_retrieval.py tests/test_retrieval_reranker_contract.py -q
```
