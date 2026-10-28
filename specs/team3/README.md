# Team 3 — Hồ sơ triển khai

## 1. Điểm đọc

- [Tuần 4: VLRA-41–44](week-04/requirements.md): API gọi RAG, FE–BE, Answer/Citation UI và E2E; [phân rã](week-04/tasks.md). W4-Q1 đã được người dùng chốt v2.0 ngày 23/10; VLRA-41 đang triển khai, live RAG còn phụ thuộc Team2.
- Đặc tả tuần 4: [VLRA-41](week-04/001-vlra-41-rag-query/spec.md), [VLRA-42](week-04/002-vlra-42-fe-be-integration/spec.md), [VLRA-43](week-04/003-vlra-43-answer-citation-ui/spec.md), [VLRA-44](week-04/004-vlra-44-mvp-e2e/spec.md). Tất cả Draft, chưa phân thành viên, chưa plan/implementation.
- [Tuần 3: VLRA-28 / VLRA-29](week-03/README.md): biên bản, testcase, evidence và bàn giao kiểm thử retrieval của Team 1.
- [Tuần 2 đã lưu trong repository](../team3-week2/tasks.md): giữ nguyên vị trí trong lần bàn giao kiểm thử này.
- [Tài liệu chức năng Team 3](../../docs/team3_fullstack/README.md): bản diễn giải thứ cấp từ Docs v2.0/Jira, không là nguồn yêu cầu độc lập hoặc bằng chứng đã triển khai.

Không đổi cấu trúc tài liệu của team khác trong lần chuẩn hóa này. Đọc thiết kế
Team 1/contract liên quan khi sửa retrieval để hiểu implementation và khác biệt cần báo.

## 2. Nguồn và ranh giới

**Quy tắc nguồn được người dùng xác nhận ngày 23/10/2026:** chỉ
[Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0)
và các ticket Jira là nguồn yêu cầu gốc. Không tự cho một nguồn ưu tiên hơn nguồn kia.
Nếu hai nguồn gốc xung đột, nêu chính xác mục/ticket và ảnh hưởng, báo người dùng,
giữ phần phụ thuộc chờ quyết định; tiếp tục phần độc lập.

Docs trong repo, specs, báo cáo phối hợp, checklist, các tóm tắt C1–C5 và ghi chú
triển khai đều là thứ cấp, được sửa để bám hai nguồn gốc. Code/cấu hình/test là căn cứ
hiện trạng triển khai, không tự tạo yêu cầu hay chứng minh yêu cầu đã hoàn thành.
Các bộ tuần cũ giữ kết quả ở snapshot đã kiểm chứng; không sửa kết quả lịch sử để
tuyên bố đã đạt yêu cầu mới. Không chỉnh Team 1/2 hoặc shared contracts trong phạm vi này.

## 3. Quyết định kế thừa và ranh giới

Các mã dưới là tóm tắt để tra cứu, không thay thế việc đối chiếu Docs v2.0/Jira.

| Mã | Quyết định đã xác nhận |
| --- | --- |
| C1 | v2.0 là yêu cầu đích; JSON v1.2 là lịch sử/hiện trạng, chưa là bằng chứng hoàn thành v2.0. |
| C2 | Pháp luật doanh nghiệp và các quy định liên quan từ bộ luật khác. |
| C3 | Mẫu insufficient_context có gold_chunk_ids rỗng và lý do là hợp lệ; validator không xác nhận pháp lý. |
| C4 | Yêu cầu reranker/fallback theo đặc tả chính thức; implementation thuộc Team 2. |
| C5 | Áp dụng unit applicability theo đặc tả chính thức; đợt kiểm thử giữ nguyên dữ liệu/code, không tự xác minh hiệu lực pháp lý. |

Team 3 kiểm thử theo VLRA-28/29; Team 1 sở hữu BM25/Dense/Hybrid. Không sửa production,
schema hoặc nhãn golden để chuyển FAIL thành PASS. Kết quả phải gắn snapshot, nguồn
evidence và phần chưa chạy; nghiệm thu task trước khi tổng hợp Jira và tuần.

Tuần 4 Team 3 được giao VLRA-41–44 trong phạm vi fullstack/tích hợp/E2E. Trách nhiệm
retrieval/LLM vẫn thuộc Team 1/2; chỉ package `ai/` Backend giao tiếp dịch vụ Python.
Nhiệm vụ theo tuần nằm trong `specs/team3/week-NN/`; tài liệu chức năng chung trong
docs được đọc làm căn cứ, không chuyển bộ nhiệm vụ tuần vào docs.
