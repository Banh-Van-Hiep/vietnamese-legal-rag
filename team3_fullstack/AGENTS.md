# AGENTS.md — Team 3: Fullstack Backend & Frontend (`team3_fullstack`)

## 1. Phạm Vi Trách Nhiệm
- **Java Spring Boot Backend (`team3_fullstack/backend/`):** Quản lý hội thoại, gọi Python AI Service (`/internal/v1/*`) qua `HttpAiClient` duy nhất, không retry. Timeout: truy vấn RAG `app.rag.timeout-ms=50000`, Article Viewer `app.rag.article-timeout-ms=10000` (NFR-08, NFR-09; giá trị viewer không được vượt 10000).
- **React + Vite Frontend (`team3_fullstack/frontend/`):** Chat Panel, render câu trả lời qua `src/utils/answerFormat.ts` (chỉ heading, in đậm, danh sách, đoạn văn và marker `[C1]`…`[Cn]`; chưa hỗ trợ bảng GFM), bấm marker để mở Document Viewer (timeout 15 s ở `src/api/publicApi.ts`), nút dừng stream và retry khi lỗi có `retryable: true` (`src/api/errorText.ts`).

## 2. Hợp Đồng Tích Hợp Với Team 2
- Hướng dẫn tích hợp UI: `docs/team2_rag/ui-integration-guide.md`. Contract: `contracts/v0.1/`.
- **Mã nội bộ** Python trả cho Java: `INVALID_LLM_OUTPUT`, `CITATION_INVALID` (502); `LLM_UNAVAILABLE`, `RETRIEVAL_UNAVAILABLE` (503); `LLM_TIMEOUT`, `RETRIEVAL_TIMEOUT` (504); `DOCUMENT_NOT_FOUND`, `ARTICLE_NOT_FOUND` (404); `INVALID_REQUEST` (400).
- **Mã public** frontend nhận: Java đổi theo `docs/ARCHITECTURE.md` mục 7.1 thành `UPSTREAM_INVALID_RESPONSE`, `SERVICE_UNAVAILABLE`, `UPSTREAM_TIMEOUT`, `UPSTREAM_CONTRACT_ERROR`, `UPSTREAM_ERROR` (404 giữ nguyên). Mã nội bộ không bao giờ hiện ra frontend; lỗi kỹ thuật không bao giờ thành `insufficient_context` (BIZ-02).

## 3. Lệnh Kiểm Chứng Cục Bộ
CI (`.github/workflows/verify.yml`) chạy đủ các lệnh dưới; chạy hết trước khi mở PR.
```powershell
# Backend (JDK 25)
cd team3_fullstack/backend; .\mvnw.cmd test; cd ../..
# Frontend (Node 22)
cd team3_fullstack/frontend; npm ci; npm test; npm run build; cd ../..
# Python harness của Team 3
.venv\Scripts\python.exe -m pytest team3_fullstack/tests -q
```
