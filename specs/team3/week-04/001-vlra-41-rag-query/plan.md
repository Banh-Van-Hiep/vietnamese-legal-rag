# Plan — VLRA-41, v2.0

**Date**: 2026-10-23. **Branch**: nhánh bàn giao được người dùng chỉ định (người dùng yêu cầu commit; chưa push).
**Scope**: Java backend và tài liệu Team 3. Không FE, retrieval/LLM hoặc server Python.

## Technical Context

Kế thừa Java 25, Spring Boot 4.1.1 MVC, Maven Wrapper, PostgreSQL driver và JDBC/transactions
đã có qua starter-data-jpa. Dùng SseEmitter, bounded executor và scheduler. Profile `rag`
cho contract v2.0; profile `mock` giữ test/evidence JSON v1.2 lịch sử, không phải route
chat chính của v2.0. Không bật cả hai profile. Không đổi mặc định local một cách âm thầm.
H2 2.5.250 chỉ dependency test (tránh lỗi CHECK(IN) 2.4.240 theo research), PostgreSQL vẫn runtime đích. SQL init idempotent; không sửa DB cũ.

## Constitution Check

- Contract thay đổi được người dùng chốt v2.0; giữ internal RagResponse và provenance.
- Chỉ ai/ gọi Python; AiClient được mở rộng history/trace, mock cũ vẫn dùng được.
- Giữ kiến trúc controller → service → repository, không giữ transaction khi gọi AI.
- Tests phân biệt HTTP stub/H2 với PostgreSQL và live RAG; không chấm SC-001 từ stub.

## Hiện trạng và tác động

Đã có validator RagAnswer, filter giới hạn 16 KiB, CORS, ApiError, mock/v1.2 tests.
Cần bổ sung HttpAiClient strict JSON, DTO public camelCase, JDBC turn store, SSE service,
controller và conversation endpoints tối thiểu để quan sát/retry/delete lượt đã nhận.
Placeholder JPA repositories cũ không dùng cho profile rag. Không dựng lại backend.

File: ai/AiClient.java, ai/HttpAiClient.java, ai/dto/HistoryMessage.java;
chat/stream/{StreamController,StreamService,StreamConfiguration,StreamDtos}.java;
conversation/persistence/ChatStore.java; conversation/StreamConversationController.java;
common/exception/ApiException.java, GlobalExceptionHandler.java;
resources/application-rag.properties, resources/db/chat-schema.sql; .env.example;
src/test/java/com/legalai/backend/{HttpAiClientTests,StreamApiTests,ChatStoreTests,PostgresChatStoreTests}.java;
src/test/resources/application-rag-test.properties; pom.xml (H2 test only).

## Thiết kế

- JDBC transactions nhận lượt, complete/fail/delete; unique UUID receipt chống trùng giữa
  instance. Insert receipt trước tạo conv; race unique rollback rồi đọc binding cũ.
  SELECT FOR UPDATE conv trước ghi messages/delete, unique pending_conv bảo vệ pending.
- Hai message + receipt pending commit trước meta. Hoàn tất ghi citation rows + assistant
  + receipt snapshot cùng transaction. Fingerprint SHA256 question đã trim, binding conv.
- Recovery startup/trước accept/read, pending >60s fail PROCESSING_INTERRUPTED; chốt bằng
  conditional state dưới cùng lock; late output bị bỏ, transport disconnect không hủy AI.
- Worker bounded, heartbeat 10s, HTTP connect ≤2s/chờ 50s, async 55s; không retry AI.
- JSON parser strict duplicate/trailing/unknown/missing/type; không coerce field, không sửa
  citation. Map upstream code/status cố định và thông báo an toàn; X-Request-ID mỗi attempt.
- HTTP stub test dùng JDK HttpServer trong test, không tạo endpoint công khai hoặc Python server.

## Kiểm chứng

FR001/008: real-port HTTP SSE event order/shape, validation, no delta for insufficient.
FR002–005: HTTP upstream success/invalid/error/status/timeout/trace/history, safe errors.
FR006/009/010: history 5 cặp/20k; replay/pending/conflict/new conv race/busy/delete/tombstone;
recovery/late output, persistence rollback và transport disconnect. H2 test là kiểm chứng
logic SQL portable, không tự chứng minh lock trên PostgreSQL. Chạy PostgreSQL nếu môi trường
cho phép; ghi riêng chưa chạy. FR007/SC004: verification.md command/expected/actual/limits.
Maven Wrapper test + package và PowerShell tests cũ nếu sửa script. Live SC001 cần Team2.

Schema contract `contracts/chat-v2.schema.json` và `contracts/validate-examples.py` đối chiếu payload wire được xuất trong StreamApiTests, dùng jsonschema test extra đã có.
