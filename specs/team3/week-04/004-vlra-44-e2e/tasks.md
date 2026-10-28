# Tasks — VLRA-44

Ngày 25/10/2026. Không push, không sửa code Team 1/2.

- [x] T001 Đối chiếu bàn giao Team 2 (PR #33/#35/#36) với `HttpAiClient`: route query/article, request `{question, history}`,
  response 3 trường, citation và article 9/6 trường snake_case, mã lỗi 404/502/503/504. Không cần sửa Java.
- [x] T002 Merge `develop` (`7a97fa3`) vào nhánh team 3, không xung đột (`8ed1b2e`).
- [x] T003 `frontend/tests/browser/vlra44-e2e.mjs`: 10 kịch bản với FastAPI `mock_app` thật, tự bật/tắt service Python.
- [x] T004 `run-vlra44-e2e.ps1`: kiểm tra máy, PostgreSQL test (Docker hoặc cài sẵn), Java `rag`, Vite, Edge headless, dọn tiến trình.
- [x] T005 Sửa lỗi môi trường: Java chạy với `user.timezone=UTC` vì PostgreSQL 16 từ chối `Asia/Saigon` (`f790276`).
- [x] T006 Chạy trên Windows: 10/10 PASS; ghi `verification.md`.
- [ ] T007 Live (G4): chạy lại cùng kịch bản với `create_app` khi có index BM25/Dense, `articles.jsonl` (Team 1) và LLM (Team 2);
  thay các assert nội dung mock bằng kiểm tra trích dẫn khớp nguyên văn thật.
