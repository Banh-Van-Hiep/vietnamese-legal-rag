# Team 2 RAG Flow

## End-to-End Flow

```text
User Question
  -> Team 3 Backend
  -> Team 1 Retrieval
  -> BM25 / Dense / Hybrid / RRF
  -> Team 2 Reranker
  -> Context Builder
  -> Prompt
  -> External LLM API
  -> Citation Verification
  -> Answer + Citation
  -> Team 3 Frontend
  -> User
```

Backend nhận request và điều phối các service/API. Team 1 thực hiện truy xuất ứng viên bằng BM25 và/hoặc dense retrieval; hybrid retrieval và Reciprocal Rank Fusion (RRF) là trách nhiệm của Team 1. Team 1 trả candidate chunks cùng điểm retrieval và metadata.

Team 2 xếp hạng lại ứng viên, chọn và sắp xếp context trong giới hạn ngân sách, dựng prompt, gọi external LLM API qua abstraction, rồi kiểm tra citation do model trả về có tham chiếu context hợp lệ hay không. Kết quả đã xác minh được trả dưới dạng answer + citations.

Team 3 sở hữu backend, REST API, frontend, UI/UX, document viewer, integration và deployment. Frontend hiển thị kết quả; frontend không gọi trực tiếp LLM provider.

## Ownership

| Stage | Owner | Boundary |
| --- | --- | --- |
| Legal data, cleaning, chunking, metadata | Team 1 | Cung cấp dữ liệu/chunks có metadata |
| BM25, dense, embedding, vector store, hybrid, RRF | Team 1 | Retrieval Output tới Team 2 |
| Reranker, context builder, prompt, LLM service, citations, RAG pipeline | Team 2 | RAG Output tới Team 3 |
| Backend, REST API, frontend, document viewer, integration, deployment | Team 3 | Nhận question, trình bày answer/citations |

## Week 1 Boundary

Week 1 chỉ phân tích và thiết kế. Sơ đồ, field, schema, provider abstraction và tham số trong tài liệu là proposal để các team review; không có RAG runtime, model integration, retrieval, API hay UI implementation trong deliverables này.