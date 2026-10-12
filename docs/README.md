# Tài liệu chung của dự án

`docs/` chứa **nhiệm vụ chung và bối cảnh dự án**: nhiệm vụ tuần theo Jira, mục tiêu/đầu ra,
phân công theo nhóm, kiến trúc, API/luồng và thiết kế/interface cấp dự án hoặc cấp team.
Trạng thái phê duyệt của thiết kế được ghi trong tài liệu nguồn.

`specs/` chứa **triển khai theo task**: phân rã, phạm vi kỹ thuật, dependency, spec/plan/tasks,
quyết định triển khai, tiêu chí kiểm chứng, bằng chứng và nghiệm thu task rồi tổng hợp lên Jira.

Hai thư mục độc lập về nội dung và trách nhiệm. `docs/` giúp hiểu cần bàn giao gì;
`specs/` giúp theo dõi làm thế nào, đã làm đến đâu và đã kiểm chứng gì.
Liên kết giữa chúng dùng để truy vết nguồn yêu cầu; không giữ hai bản của cùng bảng task
hoặc cùng báo cáo kiểm thử.

| Nội dung | Nơi quản lý |
| --- | --- |
| Nhiệm vụ tuần, mã Jira, mục tiêu/đầu ra, điều kiện hoàn thành nhiệm vụ chung | `docs/<team>/week*.md` |
| Kiến trúc/API/luồng/interface cấp nhóm hoặc dự án | `docs/<team>/`, phối hợp với `contracts/` |
| Chia task, phạm vi kỹ thuật, thứ tự/phụ thuộc, bước triển khai | `specs/` |
| Tiêu chí chi tiết, command, expected/actual, test evidence, nghiệm thu task → Jira | `specs/` |
| Code, dependency, cấu hình và hướng dẫn chạy của module | Thư mục implementation tương ứng |

## Điểm đọc

- [Team 3 — Fullstack](team3_fullstack/README.md): kiến trúc/API và nhiệm vụ tuần.
- [Team 3 tuần 2](team3_fullstack/week2.md): chỉ 3 nhiệm vụ chung VLRA-22, VLRA-23, VLRA-24.
- [Thiết kế RAG Team 2](team2_rag/rag-flow.md): tài liệu thiết kế luồng RAG tuần 1.
- [Mục lục triển khai và nghiệm thu](../specs/README.md): phần task và kết quả được chia sẻ qua Git.

Việc tổ chức lại Team 3 không di chuyển tài liệu hoặc implementation của Team 1/2.
