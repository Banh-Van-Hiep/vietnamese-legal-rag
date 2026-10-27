# Tasks — VLRA-43

Ngày 24/10/2026. Đường dẫn tính từ `team3_fullstack/frontend/`. Không push, không sửa Team 1/2 hoặc contract.

- [x] T001 Đối chiếu Docs v2.0 §2.5/§8.6–8.7/§9.9–9.12, file phân công và team3.md §2.4; chốt FR-01…FR-11 trong `spec.md`.
- [x] T002 `src/utils/answerFormat.ts` + test: phân tích câu trả lời thành khối/inline, không HTML (FR-01).
- [x] T003 `src/utils/legalCitation.ts` + test: nhãn vị trí, tìm khoản/điểm duy nhất, bản sao chép kèm nguồn, link trang riêng (FR-02, FR-05, FR-08, FR-10).
- [x] T004 `src/components/chat/AnswerContent.tsx`, `MessageBubble.tsx`, `ChatWindow.tsx`, `pages/ChatPage.tsx`: render câu trả lời, căn cứ đang mở theo từng tin nhắn (FR-01, FR-03, FR-10).
- [x] T005 `src/components/citation/{CitationCard,CitationList}.tsx`: thẻ căn cứ có link nguồn và trạng thái đang mở (FR-02, FR-03).
- [x] T006 `src/components/document/{DocumentViewer,DocumentDrawer}.tsx`, `pages/DocumentPage.tsx`: tô sáng, 404 có nguồn dự phòng, modal bàn phím, trang riêng (FR-04…FR-08).
- [x] T007 `src/components/common/ScopeNote.tsx`, `.env.example`: phạm vi dữ liệu (FR-09).
- [x] T008 `tests/browser/vlra42-smoke.mjs`: cập nhật ca 404 theo nội dung mới và kiểm link nguồn dự phòng.
- [x] T009 Kiểm tra kiểu, unit test và trình duyệt desktop/360px với API giả lập; ghi `verification.md`, cập nhật `README.md`.
- [x] T010 Chạy `npm test` (72/72) và `npm run build` trên Windows; PASS (verification §3).
- [ ] T010b Chạy `node tests/browser/vlra42-smoke.mjs` với Java profile `rag` + PostgreSQL test riêng.
- [ ] T011 Kiểm lại với nguyên văn thật khi Team 2 có `/internal/v1/documents/.../articles/...` (gắn VLRA-44/47).
