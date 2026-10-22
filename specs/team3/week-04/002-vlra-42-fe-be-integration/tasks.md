# Tasks — VLRA-42

Ngày23/10/2026. Code paths tính từ `team3_fullstack/`. Commit từng phần theo yêu cầu;
không push hoặc sửa Team2. Checklist chất lượng16/16 đạt, không có hooks.

## Setup

- [x] T001 Chốt spec/checklist, lập `plan.md`, `research.md`, `data-model.md`, `contracts/README.md`, `quickstart.md` trong feature này; baseline FE20tests/build PASS; xác minh GitHub identity.

## US1 — transport và boundary

- [x] T002 [US1] Thêm `frontend/src/types/publicApi.ts`, `frontend/src/api/publicContract.ts`: safe integer ID, UUIDv4, meta5/complete8/citation9fields; validate không coerce và giữ provenance.
- [x] T003 [US1] Thêm `frontend/src/api/{sse,chatStream}.ts` và `chatStream.test.ts`: UTF8/frame/CRLF/multiline, meta→terminal, timeout60s, request JSON/camelCase, abort/replay không ghép JSON vào answer.
- [x] T004 [US1] Chạy npm test/build, commit1 chỉ thêm transport/tests và wire types; UI cũ vẫn build được.
- [x] T005 [US1] Thêm `frontend/src/api/publicApi.ts`, `publicApi.test.ts` cho conversation arrays/message mapping/document query route, kiểm IDs nguồn; giữ view model UI nội bộ riêng.
- [x] T006 [US1] Mở `backend/.../document/DocumentService.java` cho rag; bổ sung `PublicDocumentController.java` proxy6fields camelCase và test trong `backend/.../StreamApiTests.java` cho đúngIDs/404/lỗi.
- [x] T007 [US1] Chạy FE test/build và Maven tests liên quan; commit2 API adapters + proxy, chưa đổi UI callers.

## US2 — trạng thái hỏi đáp/retry

- [x] T008 [US2] Chuyển `frontend/src/api/{chatApi,conversationApi,documentApi}.ts` sang v2.0 và `hooks/useChat.ts`: meta binding, không create conv trước lượt đầu, complete canonical, unknown retry giữ UUID/reset buffer, known failed UUID mới.
- [x] T009 [US2] Thêm receipt session/retry helpers và tests tại `frontend/src/api/{pendingTurn,pendingTurn.test}.ts`; giữ UUID khi reload chưa biết kết quả, clear question khi terminal; guard gửi trong pending và thao tác Dừng nhận.

## US3 — reload/đổi lựa chọn/mở nguồn

- [x] T010 [US3] Hoàn thiện `frontend/src/{hooks/useArticle.ts,context/AppContext.tsx,pages/ChatPage.tsx,components/chat/MessageBubble.tsx}`: stale response guard, array mapping, lịch sử pending/failed, errors source không mất answer; thay thông báo sai về in-memory.
- [x] T011 [US3] Chạy browser thật bằng Edge/CDP với Vite + Java rag + PostgreSQL riêng + stub nội bộ; lưu kịch bản tại `frontend/tests/browser/vlra42-smoke.mjs`, evidence local và tóm tắt vào `verification.md`. Kiểm send/follow-up/reload/retry/abort/switch/citation/CORS.
- [x] T012 [US3] npm test/build, Maven regression phù hợp và kiểm scope; commit3 wiring/UI state đã kiểm chứng, giữ stub được nhận diện.

## Bàn giao

- [x] T013 Cập nhật spec/tasks/quickstart/verification/analysis feature này, `frontend/README.md`, `.env.example`; ghi hashes commit1–3 và thứ tự revert; commit4 tài liệu riêng VLRA42.
- [ ] T014 Khi Team2 bàn giao service, xác minh lại cấu hình và chạy live RAG/UI trong VLRA41/44; hiện để mở, không tạo Python service thay họ.

Thứ tự T001→T002→T003→T004→T005→T006→T007→T008→T009→T010→T011→T012→T013.
T014 là dependency live ngoài nghiệm thu cơ chế42. Không gắn[P] do cùng modules/API tests
và commit checkpoint. US1 kiểm transport độc lập; US2/3 phụ thuộc boundary đã có.

## Checkpoint

- Commit1 d561f7f: transport/validators, FE44test + build PASS.
- Commit2 b632265: adapters + Viewer proxy, FE50test/build + Backend32test PASS.
- Commit3 b695277: UI/state và browser harness, FE56test/build, Backend119test và browser11ca PASS.
- Commit4: hồ sơ bàn giao này; T014 live giữ mở theo chỉ định chờ Team2.
