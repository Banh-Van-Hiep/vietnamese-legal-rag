# AGENTS.md — Team 3: Fullstack Backend & Frontend (`team3_fullstack`)

## 1. Phạm Vi Trách Nhiệm
- **Java Spring Boot Backend (`team3_fullstack/backend/`):** Quản lý hội thoại, định tuyến request sang Python AI Service (`/internal/v1/*`), áp dụng timeout `50.0s` cho truy vấn RAG và `<= 10.0s` cho Article Viewer.
- **React + Vite Frontend (`team3_fullstack/frontend/`):** Giao diện Chat Panel, render Markdown (danh sách, bảng biểu GFM), parse marker `[C1]`, `[C2]` để mở Document Viewer (`<= 15.0s`), xử lý nút dừng stream và retry khi lỗi có `retryable: true`.

## 2. Hợp Đồng Tích Hợp Với Team 2
- Tài liệu hướng dẫn tích hợp UI chuẩn: `docs/team2_rag/ui-integration-guide.md`.
- Bảng mã lỗi wire code chuẩn: `INVALID_LLM_OUTPUT` (502), `CITATION_INVALID` (502), `LLM_UNAVAILABLE` (503), `LLM_TIMEOUT` (504), `RETRIEVAL_UNAVAILABLE` (503), `RETRIEVAL_TIMEOUT` (504), `DOCUMENT_NOT_FOUND` (404), `ARTICLE_NOT_FOUND` (404), `INVALID_REQUEST` (400).

## 3. Lệnh Kiểm Chứng Cục Bộ
```powershell
# Chạy test tích hợp phía Python của Team 3
.venv\Scripts\python.exe -m pytest team3_fullstack/tests -q
```
