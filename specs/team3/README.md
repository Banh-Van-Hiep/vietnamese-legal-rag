# Team 3 — Hồ sơ triển khai

## 1. Điểm đọc

- [Tuần 3: VLRA-28 / VLRA-29](week-03/README.md): biên bản, testcase, evidence và bàn giao kiểm thử retrieval của Team 1.
- [Tuần 2 đã lưu trong repository](../team3-week2/tasks.md): giữ nguyên vị trí trong lần bàn giao kiểm thử này.
- [Tài liệu Team 3 hiện có](../../docs/team3_fullstack/README.md): tài liệu JSON/mock lịch sử; không dùng làm bằng chứng đã triển khai yêu cầu đích v2.0.

Lần bàn giao kiểm thử không bao gồm việc tổ chức lại tài liệu đang làm ở máy local. Đọc đặc tả
Team 1 và contract được liên kết trong requirements của tuần 3 khi sửa retrieval.

## 2. Nguồn và ranh giới

Nguồn yêu cầu đích: [đặc tả chính thức v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.9c432bmgzvck).
Các quyết định dưới đã được người dùng xác nhận trước đợt kiểm thử ngày 19/10/2026;
chỉ ghi ngữ cảnh cần thiết, không thay đổi contract, code hoặc tài liệu Team 1/2.

## 3. Quyết định kế thừa và ranh giới

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
