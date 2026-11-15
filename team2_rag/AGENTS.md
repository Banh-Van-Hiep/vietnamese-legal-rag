# AGENTS.md — Team 2: Core RAG, Reranker & LLM Engine (`team2_rag`)

## 1. Phạm Vi Trách Nhiệm
- Điều phối luồng `RAGPipeline.query` (`team2_rag/pipeline.py`): Retrieval -> Rerank (`BGEScorer`) -> Context Builder -> LLM Generation (`team2_rag/answer.py`, `team2_rag/llm/service.py`) -> Citation & Claim Verification (`team2_rag/verification/`).
- Cung cấp FastAPI nội bộ (`POST /internal/v1/query`, `GET /internal/v1/documents/{document_id}/articles/{article_id}`) và Mock App (`team2_rag/api/mock_app.py`) cho Team 3.

## 2. Quy Tắc Bất Biến Khi Sửa Code Team 2
1. **Lazy Reranker Loading (`runtime.py`):** Khi `RAG_RERANK=false`, tuyệt đối không khởi tạo hay warm-up `BGEScorer` để tránh chiếm dụng RAM/VRAM.
2. **Truyền Thời Gian Còn Lại (`VLRA-T2-33`):** Luôn tính `remaining = deadline - time.monotonic()` trong `RAGPipeline.query` và truyền `llm_timeout_seconds=max(0.1, remaining - 0.5)` xuống `generate_answer_detailed`.
3. **Nghiêm Cấm Tự Vá Citation:** Mọi vi phạm cú pháp marker `[C1]..[Cn]` hoặc trích dẫn ngoài context phải được xử lý qua `errors.py` / `output_parser.py`, không tự sửa chuỗi trả lời của LLM.
4. **Cập Nhật Sổ Cái Công Việc:** Mọi thay đổi trong tuần phải được đối chiếu với đặc tả trong `team2_rag/docs_2/week10/tasks.md`.

## 3. Lệnh Kiểm Chứng Cục Bộ
```powershell
# 1. Chạy toàn bộ Unit Test & Timeout/Concurrency Test của Team 2
.venv\Scripts\python.exe -m pytest team2_rag/tests -q

# 2. Chạy kiểm tra tương thích với test tích hợp ở gốc
.venv\Scripts\python.exe -m pytest tests/test_team2_api.py tests/test_team2_pipeline.py tests/test_team2_pipeline_v2.py tests/test_team2_mock_markdown.py -q

# 3. Chạy Benchmark E2E NFR-07/08/09 (chế độ local BM25-only)
.venv\Scripts\python.exe scripts/benchmark_e2e_nfr07.py
```
