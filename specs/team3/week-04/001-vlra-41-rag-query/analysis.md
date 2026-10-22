# Analysis — VLRA-41

**Ngày:** 23/10/2026. Đối chiếu spec/plan/tasks theo constitution và Docs v2.0.
W4-Q1 đã có quyết định người dùng; không tạo câu hỏi giả JSON/SSE. Không có extension hook.

| Yêu cầu | Tasks | Kiểm chứng |
| --- | --- | --- |
| FR001 | T001/003/005/007 | SSE route, camelCase, numeric IDs; legacy route absent trong rag |
| FR002 | T005/006/008 | HTTP stub body/history/trace, invalid input không tạo turn |
| FR003/004 | T003/005/006/008 | strict JSON + AiResponseValidator, answered/insufficient |
| FR005 | T008/009 | upstream classes, safe errors, logical status replay |
| FR006 | T004/010/011 | history/retry/concurrency/disconnect |
| FR007 | T012/014 | verification và phân biệt stub/live |
| FR008 | T005/007/009 | meta/pending/heartbeat/terminal, commit failure |
| FR009 | T004/009/010/013 | SQL locks/constraints/rollback/recovery trên H2/PostgreSQL |
| FR010 | T010/011 | messages arrays, delete/tombstone |
| SC001 | T014 | OPEN — cần Team2 service thật, không dùng stub thay thế |
| SC002/003/004 | T008–013 | kết quả trong verification.md |

Không có requirement không được giao task hoặc task không có yêu cầu nguồn.
Phần thiếu được ghi explicit: HTTP Team2/live pipeline; UI/Viewer ngoài VLRA-41.
Không có CRITICAL/HIGH conflict giữa spec/plan/tasks sau quyết định v2.0.

Các chỉnh lý phát hiện trong review đã áp dụng trong bước tài liệu/implementation:
1. Bỏ duplicate Clarifications heading; cập nhật nguồn W4-Q1 trong docs tuần.
2. Ghi profile legacy mock riêng, không gọi hai API chat chính đồng thời.
3. Bổ sung machine-readable schema public và xuất payload thực trong StreamApiTests.
4. Kiểm tra PostgreSQL riêng thay vì kết luận khóa DB từ H2.

Đây là phân tích tài liệu và coverage, không thay kết luận nghiệm thu live.

5. Replay phải khóa cùng conversation với delete; đã bổ sung khóa và regression test trên H2/PostgreSQL (full suite cuối117 PASS).
