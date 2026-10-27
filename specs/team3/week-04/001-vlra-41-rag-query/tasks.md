# Tasks — VLRA-41

Ngày 23/10/2026; commit bàn giao trên nhánh bàn giao được người dùng chỉ định theo yêu cầu người dùng; chưa push. Đường dẫn code dưới tính từ `team3_fullstack/backend/`.

## Phase 1 — Setup

- [x] T001 Chốt W4-Q1 theo trả lời người dùng, đối chiếu develop 3d64c4d và lập `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/README.md`, `quickstart.md` trong thư mục feature này.
- [x] T002 Bổ sung H2 test trong `pom.xml`, profile `src/main/resources/application-rag.properties` và cấu hình mẫu `.env.example`; giữ profile mock lịch sử riêng biệt.

## Phase 2 — Foundation

- [x] T003 Bổ sung DTO camelCase/ID integer 1..9007199254740991 trong `src/main/java/com/legalai/backend/chat/stream/StreamDtos.java`; mở rộng `ai/AiClient.java`, `ai/dto/HistoryMessage.java` giữ mock tương thích.
- [x] T004 Bổ sung `src/main/resources/db/chat-schema.sql`, `conversation/persistence/ChatStore.java`: receipt unique, message unique sequence/pending, transaction và snapshot; mỗi lượt một cặp message, conditional terminal, ID số an toàn.

## Phase 3 — US1, gọi RAG và SSE

- [x] T005 [US1] Viết `src/test/java/com/legalai/backend/HttpAiClientTests.java` và `StreamApiTests.java` cho request/history/trace, success, insufficient, SSE event shape/order và JSON camelCase.
- [x] T006 [US1] Triển khai `src/main/java/com/legalai/backend/ai/HttpAiClient.java`: POST internal JSON, strict parse/validator, connect≤2s, response≤50s, không retry; không tạo Python server.
- [x] T007 [US1] Triển khai `src/main/java/com/legalai/backend/chat/stream/{StreamController,StreamService,StreamConfiguration}.java`: bounded worker, commit→meta→heartbeat→validate/persist→delta/complete, async55s, disconnect không hủy AI.

## Phase 4 — US2, lỗi

- [x] T008 [US2] Mở rộng `src/test/java/com/legalai/backend/{HttpAiClientTests,StreamApiTests}.java`: input/media/CORS, malformed/unknown/null/coerced output, upstream4xx/502/503/504, timeout, safe messages, pre-stream HTTP/post-stream error/replay logical status.
- [x] T009 [US2] Hoàn thiện `src/main/java/com/legalai/backend/common/exception/{ApiException,GlobalExceptionHandler}.java` và SSE service: lỗi DB503, lỗi bất ngờ500; không complete trước persist, không đổi completed vì transport lỗi.

## Phase 5 — US3, persistence/history/replay

- [x] T010 [US3] Viết `src/test/java/com/legalai/backend/ChatStoreTests.java`: replay/failed/pending/conflict, race cùng UUID/hội thoại, history tối đa 5 cặp và ≤20000 code point bỏ nguyên cặp, recovery60s, delete/tombstone, rollback/late output.
- [x] T011 [US3] Hoàn thiện `src/main/java/com/legalai/backend/conversation/persistence/ChatStore.java` và `conversation/StreamConversationController.java`: arrays camelCase, read/recovery/delete, pending lock, tombstone xóa hash/content/snapshots.

## Phase 6 — Verification

- [x] T012 Chạy Maven Wrapper test/package và kiểm tra scope/diff; ghi lệnh, kết quả, giới hạn trong `verification.md` của feature. Đối chiếu FR001–010/SC001–004.
- [x] T013 Kiểm tra PostgreSQL thực với schema riêng cho test nếu môi trường cho phép; ghi kết quả/khả năng đa instance trong `verification.md`, không đồng nhất H2 với PostgreSQL.
- [ ] T014 [US1] Khi Team2 bàn giao service live, chạy API → retrieval/rerank/LLM thật và truy vết citation/snapshot; ghi evidence trong `verification.md` và đối chiếu SC001. Chưa có service thì giữ mở.

## Dependencies và cách thực hiện

T001→T002→T003→T004; T005→T006→T007; T008→T009; T010→T011→T012→T013.
T014 phụ thuộc T012 và W4-D1/D2 của Team2. Không gắn [P]: tests/store/service được dùng
chung và cần kết quả giai đoạn trước. Bắt đầu US1 trên HTTP stub, thêm US2/US3 rồi regression;
stub không hoàn thành SC001. Checklist đánh giá yêu cầu tách khỏi task implementation.

## Kết quả 23/10/2026

T001–T013 hoàn tất, kiểm chứng trong [verification.md](verification.md): full suite
117/117 PASS, package PASS; schema payload thực và runtime PostgreSQL/restart PASS.
T014 vẫn mở: develop chưa có service HTTP RAG thật; không dùng stub thay SC001.
Commit phần Java và hồ sơ VLRA-41 theo yêu cầu người dùng; chưa push, chưa chốt nghiệm thu toàn ticket.
