# Tuần 4 — Tích hợp MVP và kiểm thử giao diện End-to-End

**Tiếp nhận:** 21/10/2026. **Tuần triển khai:** 4, do người dùng xác nhận.
**Phân công:** đây là toàn bộ nhiệm vụ tuần 4 của Team 3; chưa phân thành viên phụ trách.
**Nguồn gốc:** Docs v2.0 và Jira; các ticket tuần này cùng thuộc
[VLRA-4](https://banhvanhiep.atlassian.net/browse/VLRA-4). **Chuẩn hóa nguồn:** 23/10/2026.
Trạng thái các ticket được cung cấp là **To Do**; chưa đọc hoặc cập nhật trạng thái Jira trực tiếp.

## Nguồn yêu cầu và quy tắc đối chiếu

Chỉ hai nguồn dưới là căn cứ yêu cầu:

1. [Docs v2.0 — Legal RAG](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0),
   §0.1, §8, §9 và §10.4–10.5. Đã đọc lại các mục liên quan ngày 23/10/2026;
   nội dung mở đầu ghi v2.0, metadata modifiedTime 13/10/2026. Tab Doc chứa đặc tả;
   tab Note đã kiểm tra ở lần đọc 21/10 không trả về nội dung văn bản.
2. Jira VLRA-41/42/43/44: nội dung người dùng cung cấp ngày 21/10 được giữ tại mục 1.
   Chưa truy cập trực tiếp Jira để xác nhận có chỉnh sửa mô tả/trạng thái sau đó.

Docs trong repo, specs, báo cáo phối hợp tuần 4, C1–C5 và contract files đều thứ cấp;
được sửa để phản ánh hai nguồn gốc, không là yêu cầu độc lập. Code/test/config là
căn cứ hiện trạng. Không tự đặt ưu tiên khi Docs v2.0 và Jira khác nhau: ghi đúng
hai nguồn, ảnh hưởng và báo người dùng; giữ phần phụ thuộc chờ quyết định.

## 1. Nhiệm vụ và tiêu chí được giao

| Jira | Mục tiêu / công việc | AC theo nội dung được cung cấp |
| --- | --- | --- |
| [VLRA-41](https://banhvanhiep.atlassian.net/browse/VLRA-41) | Xây dựng `POST /api/v1/query`, tiếp nhận payload và gọi RAG Pipeline của Team 1/2 | API tiếp nhận query, gọi RAG Pipeline thành công và trả JSON chứa Answer + Citation. |
| [VLRA-42](https://banhvanhiep.atlassian.net/browse/VLRA-42) | Tích hợp hai chiều Frontend ↔ Backend API | Frontend gửi request thành công tới Backend API và nhận lại dữ liệu JSON mượt mà. |
| [VLRA-43](https://banhvanhiep.atlassian.net/browse/VLRA-43) | Hiển thị answer, thẻ citation và cho phép bấm xem chi tiết văn bản gốc | Giao diện hiển thị đầy đủ câu trả lời và các thẻ trích dẫn theo thiết kế MVP. |
| [VLRA-44](https://banhvanhiep.atlassian.net/browse/VLRA-44) | Kiểm thử toàn bộ giao diện MVP End-to-End | Nhập câu hỏi trên UI → Backend API → RAG Pipeline → hiển thị Answer + Citation; MVP sẵn sàng demo. |

Không sửa nội dung các ticket để tự giải quyết xung đột với đặc tả trước đây.
Không coi từ “mượt mà” là một SLA mới; chỉ tiêu thời gian cụ thể cần căn cứ contract được chốt.

## 2. Xung đột giữa hai nguồn gốc

### W4-Q1 — Route public của VLRA-41

**Trạng thái:** RESOLVED ngày 23/10/2026. Người dùng chốt: “làm theo đặc tả v2.0 nhé bây giờ hãy triển khai task 41”. Public dùng `/api/v1/chat/stream`; internal `/internal/v1/query`. Chưa sửa Jira trực tiếp; nguyên văn ticket bên trên được giữ để truy vết.
Xung đột cụ thể nằm ở tên route, không phải ở việc dùng định dạng JSON.

| Nguồn gốc / vị trí | Nội dung |
| --- | --- |
| Jira VLRA-41, tiêu đề và công việc được cung cấp | “Xây dựng API Endpoint POST /api/v1/query kết nối RAG Pipeline”; AC trả JSON chứa Answer + Citation. |
| Docs v2.0 §9.2 và đoạn kết bảng lộ trình §11.1 | Public chat chính là `POST /api/v1/chat/stream`; `/api/v1/query` trong kế hoạch cũ được thay thế, không giữ làm route chính song song. |

**Ảnh hưởng:** tên endpoint FE–BE, scope adapter/migration, bộ ca contract và route
nghiệm thu VLRA-41; kéo theo kết nối/AC tích hợp 42 và 44. Không tự sửa ticket,
không dựng hai endpoint public chính song song để coi là đã thỏa cả hai nguồn.

**Quyết định áp dụng:** triển khai VLRA-41 theo v2.0; không giữ `/api/v1/query`
làm route chính song song trong profile `rag`. Profile `mock` cũ chỉ phục vụ kiểm thử
lịch sử v1.2, không dùng làm bằng chứng đạt v2.0. Chưa cập nhật nguồn Jira.

### Các điểm đã rõ từ nguồn gốc, không phải xung đột mới

- VLRA-42 ghi nhận JSON không đồng nghĩa bắt buộc một response JSON đồng bộ.
  Docs v2.0 §9.1/§9.4 quy định mỗi SSE data là JSON. Không đánh dấu JSON ↔ SSE là
  mâu thuẫn tự thân, hoặc coi public/internal là hai form cạnh tranh cùng endpoint.
- Theo Docs v2.0 §9.1/9.8/9.9: public React ↔ Java dùng SSE/camelCase/ID số;
  Java ↔ Python dùng JSON snake_case qua `POST /internal/v1/query`. Java map giữa hai biên.
- Theo §9.4: meta trước, heartbeat khi chờ; chỉ phát delta/complete sau khi kết quả
  RAG đã validate và persist. Chưa yêu cầu provider token streaming hoặc hiển thị suy nghĩ LLM.
- Theo §8.6/§9.7: hội thoại pending chặn gửi lượt mới; không tự thêm ngắt lời hay
  bổ sung vào lượt đang chạy. Dừng nhận stream không có nghĩa hủy xử lý AI (§9.5).
- Mã lỗi public theo §9.13–9.14: INVALID_LLM_OUTPUT/CITATION_INVALID →
  UPSTREAM_INVALID_RESPONSE; LLM_UNAVAILABLE/RETRIEVAL_UNAVAILABLE → SERVICE_UNAVAILABLE;
  LLM_TIMEOUT/RETRIEVAL_TIMEOUT → UPSTREAM_TIMEOUT. Báo cáo phối hợp thứ cấp không
  được dùng để đổi thành các mã Python trên public boundary. Không có W4-Q2 giữa
  hai nguồn gốc chỉ vì một báo cáo thứ cấp ghi khác.

## 3. Kiểm tra `origin/develop` ngày 21/10/2026

Đã chạy `git fetch origin develop`, đọc source bằng `git show`, `git ls-tree` và
`git grep` trực tiếp trên ref; không checkout hoặc merge develop trong lượt này.
**Commit kiểm tra:** `3d64c4d38b93f11ac321623159f74e5202d1e953`.
Nhánh làm việc tại lúc kiểm tra: `test/retrieval-verification`, HEAD `27ef448`.

| Thành phần | Căn cứ cụ thể trên develop | Kết luận về hiện trạng |
| --- | --- | --- |
| API public Java | `ChatController.java`, `ChatService.java` có `/api/v1/query` và `@Profile("mock")` | Có endpoint/mock; chưa phải API gọi pipeline thật. |
| Java gọi Python | `team3_fullstack/backend/src/main/java/com/legalai/backend/ai/HttpAiClient.java` là class rỗng, không có bean/gọi HTTP | Chưa triển khai adapter HTTP. |
| Python entry point | `team2_rag/service.py`: `query()` gọi `make_mock_response()`; docstring ghi không retrieval/LLM | Vẫn là mock, không phải toàn tuyến RAG thật. |
| Context → LLM → citation | `team2_rag/answer.py`: `generate_answer()` nhận output reranker, tạo context/gọi LLM và kiểm citation; `llm/` có provider adapters | Đã có các thành phần xử lý; chưa chứng minh được query HTTP → retrieval → rerank → answer. |
| HTTP trong `llm/` | `team2_rag/llm/http.py` triển khai `urllib.request` để gửi request ra LLM provider | Đây là HTTP client đi ra ngoài, không phải server RAG cho Java gọi. |
| HTTP server RAG | Kiểm tra cây file và tìm entry point/route Python (`FastAPI`, `Flask`, `APIRouter`, `uvicorn`, `HTTPServer`, `aiohttp`, route query) không tìm được server trong develop | Chưa thấy implementation endpoint HTTP RAG chạy được trên ref đã kiểm tra. Không suy kết quả này sang các nhánh riêng chưa bàn giao. |
| Tài liệu request/response/error | Ở snapshot develop 3d64c4d, `docs/team2_rag/rag-io-specification.md` §1/3/4 và bản `team3.md` khi đó mô tả I/O v1.2 | Có thiết kế thứ cấp, không đồng nghĩa server đã chạy. Bản `team3.md` local được diễn giải lại theo Docs v2.0 ngày 23/10; không thay inventory code ngày 21/10. |
| Cách chạy service HTTP | `team2_rag/README.md` hướng dẫn gọi hàm Python; `__main__.py` là mock CLI; Compose vẫn placeholder | Chưa có lệnh/URL service RAG HTTP được bàn giao trong develop để chạy E2E thật. |
| FE gọi BE | `src/api/chatApi.ts`, `client.ts`, `hooks/useChat.ts` có gửi request/nhận JSON, timeout/retry | Có luồng JSON hiện tại; lượt này chỉ đọc code, chưa nghiệm thu tích hợp tuần 4. |
| Answer/Citation/Viewer | `MessageBubble.tsx`, `CitationList.tsx`, `CitationCard.tsx`, `DocumentViewer.tsx`, `ChatPage.tsx` | Có component và thao tác mở nguồn; cần kiểm chứng với response và nguồn văn bản thật. |

**Kết luận về Team 2:** develop có code RAG/LLM từng phần và tài liệu I/O, nhưng **chưa
có dịch vụ RAG HTTP chạy thật được bàn giao** cho Java. Đây là khoảng thiếu/dependency,
không phải kết luận Team 2 chưa làm RAG hoặc tự mâu thuẫn yêu cầu. Không tự chọn
FastAPI/Flask, triển khai HTTP server, factory retrieval hoặc sửa pipeline thay Team 1/2.

## 4. Phụ thuộc và điều kiện tiếp tục

| ID | Cần có / bên phối hợp | Phần bị ảnh hưởng |
| --- | --- | --- |
| W4-Q1 | RESOLVED: người dùng chốt v2.0 ngày 23/10 | Route đích `/api/v1/chat/stream`; không còn chặn lập plan/implement Java. Jira chưa sửa trực tiếp. |
| W4-D1 | Team 2 bàn giao service HTTP: commit, endpoint/base URL, request/response/error, timeout/trace, cấu hình và lệnh chạy | VLRA-41 và E2E thật VLRA-44. Không đặt field cấu hình hoặc framework mới trước khi chốt. |
| W4-D2 | Team 1/2 nối retrieval → rerank → context → LLM, index/corpus/model version và môi trường chạy | Kết quả có căn cứ thật và minh chứng toàn tuyến. |
| W4-D3 | Nguồn nguyên văn theo document/article ID và phiên bản citation; thống nhất interface để mở Viewer | VLRA-43 và luồng mở citation trong VLRA-44; không lấy answer LLM thay nguyên văn. |

Lỗi B-01 BM25 và D-01..D-03 Dense đã tái hiện ở [kiểm thử tuần 3](../week-03/verification.md).
Đây là rủi ro/dependency retrieval cần owner xử lý; không tự sửa source Team 1 trong task tích hợp.
Không yêu cầu benchmark/model/server mới ở lượt lập tài liệu này.

## 5. Phạm vi và cách nghiệm thu

- Tái sử dụng Backend/Frontend hiện tại, chỉ package `ai/` giao tiếp Python; không dựng lại ứng dụng.
- Phần độc lập có thể tiếp tục: inventory/test mapping, kiểm tra UI có sẵn và lập kịch bản
  thành công/thiếu căn cứ/lỗi/mở citation. Giữ rõ profile mock hay thật trong evidence.
- Mock dùng để kiểm thử cơ chế; AC gọi RAG thật và MVP demo của 41/44 cần minh chứng toàn tuyến.
- Chốt task → kiểm chứng task → đối chiếu từng VLRA → kết luận tuần/demo. Không tự thêm
  auth, SLA/coverage hoặc công cụ E2E ngoài nguồn gốc. Docs v2.0 quy định SSE; W4-Q1
  đã được người dùng chốt theo v2.0, không còn chặn implementation.
- Lượt chuẩn hóa nguồn ngày 23/10 chỉ sửa tài liệu thứ cấp Team 3; không sửa nguồn
  Google Docs/Jira, code Team 1/2, shared schema, build/test, commit hoặc push.

Phân rã cấp tuần tại [tasks.md](tasks.md). Bốn đặc tả riêng:
[VLRA-41](001-vlra-41-rag-query/spec.md),
[VLRA-42](002-vlra-42-fe-be-integration/spec.md),
[VLRA-43](003-vlra-43-answer-citation-ui/spec.md),
[VLRA-44](004-vlra-44-mvp-e2e/spec.md).
VLRA-41 đã có plan/tasks và được triển khai theo yêu cầu ngày 23/10; xem [báo cáo](001-vlra-41-rag-query/verification.md). VLRA-42/43/44 vẫn Draft, chưa triển khai. Chưa phân thành viên; thứ tự dependency không là phân công.

## 6. Tái kiểm tra develop trước triển khai 23/10/2026

Đã git fetch origin develop theo yêu cầu mới của người dùng; ref vẫn là
3d64c4d38b93f11ac321623159f74e5202d1e953 (20/10). Diff source Team1/2/3,
contracts và docs giữa HEAD và ref này không có thay đổi; inventory mục 3 còn đúng
cho develop. RAG HTTP chưa bàn giao: không coi HTTP stub Java là pipeline thật.
