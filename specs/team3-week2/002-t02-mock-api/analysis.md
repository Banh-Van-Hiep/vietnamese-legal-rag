# T02 — analysis và remediation trước implement
**Ngày:** 2026-10-09. Analyze chỉ đọc; sửa sau analyze theo ủy quyền.

| ID | Severity | Vấn đề | Sửa / kết quả |
| --- | --- | --- | --- |
| U1 | MEDIUM | quickstart build còn placeholder EnvFile | Đường dẫn target/t02/build.env thực, tạo fixture và môi trường kiểm soát; đã kiểm tra lại |
| C1 | MEDIUM | task smoke chưa nêu GET document body/query trong error mode | T015 và quickstart thêm ?extra=1/body{} →400; đã kiểm tra lại |

16 FR + 5 SC, 18 tasks, 8 AC; 21/21 yêu cầu có task. Task không ánh xạ: 0.
Không critical/high, mơ hồ chức năng hoặc duplicate đáng kể; dependency graph không vòng.
Q1–Q3/constitution/API/ranh giới team giữ nguyên. Checkbox tất cả mở trước implement.
U1/C1 đã sửa, không vấn đề mới; đủ chuyển implement. Scope T02 không UI/AI thật/DB/GT.
Checklist 14/16 giữ hai ngoại lệ tham chiếu API nguồn; người dùng đã yêu cầu tự quyết/tiến hành.
