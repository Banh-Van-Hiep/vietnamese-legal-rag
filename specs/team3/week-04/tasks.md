# Tuần 4 — Phân rã nhiệm vụ Team 3

**Nguồn gốc:** Docs v2.0 và Jira, được trích/đối chiếu tại [requirements.md](requirements.md).
File này là tài liệu thứ cấp phân rã cấp tuần, không phải
tasks triển khai sinh từ plan. Toàn bộ nhiệm vụ thuộc Team 3, **chưa phân thành viên**.
Tất cả nhiệm vụ còn mở; việc đọc code hoặc viết đặc tả không là evidence nghiệm thu.

| Thứ tự | Jira / bộ task | Công việc cần giải quyết | Đã có để tái sử dụng | Phụ thuộc / trạng thái |
| --- | --- | --- | --- | --- |
| 1 | VLRA-41 — [001-vlra-41-rag-query](001-vlra-41-rag-query/spec.md) | Áp dụng quyết định v2.0 ngày 23/10; tích hợp public SSE với service RAG thật; validation/mapping theo Docs v2.0 và kiểm thử | Controller/service/DTO/validator/mock boundary | Đã có plan/tasks và implementation Java v2.0; xem báo cáo feature. W4-D1/D2 vẫn chặn live AC. |
| 2 | VLRA-42 — [002-vlra-42-fe-be-integration](002-vlra-42-fe-be-integration/spec.md) | Đối chiếu và kiểm chứng request/response FE–BE, trạng thái lỗi, timeout/retry/CORS theo contract được chọn | `chatApi.ts`, `client.ts`, `useChat.ts`, tests retry/client | Draft spec; wiring/AC phụ thuộc API của 41 (W4-Q1 resolved); chưa plan/implementation. |
| 3 | VLRA-43 — [003-vlra-43-answer-citation-ui](003-vlra-43-answer-citation-ui/spec.md) | Tái sử dụng/bổ sung answer, citation, thao tác mở nguyên văn, loading/empty/error và kiểm chứng thiết kế | `MessageBubble`, `CitationList`, `CitationCard`, `DocumentViewer` | Draft spec; UI review có thể độc lập; binding theo quyết định v2.0, nguồn thật phụ thuộc W4-D3; chưa plan/implementation. |
| 4 | VLRA-44 — [004-vlra-44-mvp-e2e](004-vlra-44-mvp-e2e/spec.md) | Chạy UI → BE → pipeline thật → Answer/Citation, mở nguồn; thu evidence và đối chiếu demo | Luồng mock và các thành phần trên; không suy mock là E2E thật | Draft spec; phụ thuộc 41/42/43 và môi trường; chưa plan/implementation/kiểm thử. |

## Dependency

W4-Q1 resolved (v2.0); W4-D1/D2 → VLRA-41 → VLRA-42 và binding VLRA-43
→ VLRA-44. Nguồn nguyên văn W4-D3 cần cho thao tác mở citation.
VLRA-42/43 có thể review phần đã có độc lập; chưa gắn nhãn làm song song cho bước
implementation vì chưa có plan hoặc phân vùng file để chứng minh độc lập.

## Quy trình từng task

1. Kiểm tra spec đã có; dùng thư mục tuần 4 đúng mã Jira, không tạo trùng.
2. Specify → clarify → plan → tasks → analyze → sửa vấn đề → implement, từng bước riêng.
3. Với W4-Q1, báo người dùng đúng hai nguồn: Jira VLRA-41 `/query`, Docs v2.0
   `/chat/stream`; người dùng đã chọn v2.0 ngày 23/10. Không tạo xung đột giả giữa JSON
   và SSE hoặc coi báo cáo phối hợp là nguồn gốc thứ ba.
4. Với service HTTP chưa bàn giao, ghi dependency và tiếp tục phần độc lập;
   không dựng implementation của Team 2 trong task Team 3.
5. Ghi command/profile/source/evidence và kết quả thật khi kiểm chứng; chưa tạo
   checkbox hoàn thành, report PASS hay nghiệm thu demo từ tài liệu này.

VLRA-41 đã có plan/tasks/implementation và kiểm chứng riêng; ba thư mục còn lại chỉ có spec/checklist, chưa triển khai. Việc chia thứ tự này không phân thành viên hoặc tuyên bố đã thực hiện task.
