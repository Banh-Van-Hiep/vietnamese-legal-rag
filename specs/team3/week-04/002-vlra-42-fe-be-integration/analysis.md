# Analysis — VLRA-42

Ngày23/10/2026, theo constitution1.0.1 và Docs v2.0. Không có extension hooks.
W4-Q1 đã được người dùng chốt; không còn câu hỏi contract chặn implementation.
Checklist chất lượng16/16 không phải nghiệm thu ứng dụng.

| Requirement | Tasks | Kiểm chứng |
| --- | --- | --- |
| FR001 | T002–004/008 | strict SSE/IDs/camelCase và browser request thực |
| FR002 | T005–007/010 | conversations/messages arrays, document query proxy/trace/IDs |
| FR003 | T003/005/008/010 | answered/insufficient/error, canonical answer/citations |
| FR004 | T008–011 | abort/epoch/source guards, switching và history pending |
| FR005 | T003/008/009 | timeout body, UUID reuse/new, session reload |
| FR006 | T011–013 | Edge→Vite→Java→PostgreSQL→HTTP fixture, evidence có nhãn |
| FR007 | T002–004/008/009/011 | fragmented UTF8/CRLF/multiline, terminal/replay/stop |
| SC001–004 | T003/005–013 | kết quả phân lớp tại verification.md |

Không có requirement không được giao task; không có CRITICAL/HIGH inconsistency còn mở.
Khắc phục trước/chính trong implementation: (1) readiness không phụ thuộc việc Team2
đã có live service; (2) tách public wire với view model, không sửa API để khớp UI;
(3) bổ sung proxy Viewer tối thiểu để không đưa request vào route v1.2 không có trong rag;
(4) retry trước meta cần giữ UUID qua reload, tránh tạo conv/lượt mới;
(5) không hiển thị pending như failed sau reload.

Chưa hoàn thành live RAG hoặc VLRA44. T014 là dependency Team2; không triển khai server
Python hoặc sửa retrieval/corpus/prompt. Git commits incremental có thể revert từ cuối.
