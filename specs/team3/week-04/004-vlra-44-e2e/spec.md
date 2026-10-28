# VLRA-44 — Kiểm thử E2E giao diện MVP

**Ngày:** 25/10/2026. **Nhánh:** `feature/team3/haunx` = `feature/team3-fullstack` (VLRA-41/42/43) + `develop` `7a97fa3`
(PR #36 của Team 2). **Jira:** [VLRA-44](https://banhvanhiep.atlassian.net/browse/VLRA-44), tuần 4, EPIC 4 Fullstack.

## Nguồn yêu cầu

- Phân chia công việc tuần 4: "Kiểm thử toàn bộ giao diện người dùng End-to-End (E2E MVP Interface)", MVP sẵn sàng demo.
- [Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0)
  §11.1.2 tuần 7 và mốc G2/G4: "React SSE → Java → Python mock; hai status/error và Viewer" (G2);
  "Pipeline đầy đủ và demo E2E" (G4). §8.7 trạng thái UI, §9.4 SSE, §9.11–9.14 Viewer và mã lỗi.
- Bàn giao Team 2 (PR #36, `docs/team2_rag/week4-integration.md`): HTTP mock `team2_rag.api.mock_app`
  cùng route/schema với live; live còn chờ index, article snapshot của Team 1 và cấu hình provider.

## Phạm vi

Hai mức, nghiệm thu riêng như Docs v2.0 yêu cầu:

| Mức | Luồng | Trạng thái |
| --- | --- | --- |
| G2 — mock integration | React → Java profile `rag` (PostgreSQL) → FastAPI `mock_app` của Team 2 | Đã kiểm, xem verification.md |
| G4 — live RAG | React → Java → FastAPI `create_app` → Hybrid → reranker → LLM; Viewer từ `articles.jsonl` | Chưa đủ điều kiện |

## Yêu cầu kiểm thử (mức G2)

- **E2E-01** Ba service lên được; Python trả `X-RAG-Mode: mock`.
- **E2E-02** Câu hỏi đầu qua SSE: câu trả lời và trích dẫn đến từ service Python, URL hội thoại theo ID số.
- **E2E-03** Bấm trích dẫn: Java gọi `GET /internal/v1/documents/{id}/articles/{id}` của Python, Viewer hiển thị đúng nguyên văn và nguồn.
- **E2E-04/05** Hỏi tiếp giữ hội thoại; lịch sử lưu PostgreSQL, tải lại không gọi AI.
- **E2E-06** 404 `DOCUMENT_NOT_FOUND`/`ARTICLE_NOT_FOUND` từ Python được giữ nguyên ra public API và UI.
- **E2E-07** `insufficient_context` từ Python: thông báo riêng, không có trích dẫn.
- **E2E-08/09** Python ngừng: lỗi 503 `SERVICE_UNAVAILABLE` có thể thử lại, lượt `failed` được lưu; bật lại và Thử lại tạo lượt mới UUID mới.
- **E2E-10** Request public đúng v2.0: camelCase, `clientRequestId` UUID v4, không gửi `history`/`scenario`; không lỗi JavaScript.

## Ngoài phạm vi

Chất lượng câu trả lời, latency, benchmark; tạo index/article snapshot thay Team 1; cấu hình LLM thay Team 2.
Các ca stream gián đoạn/replay/đổi hội thoại đã có ở smoke VLRA-42 với stub và không lặp lại ở đây.
