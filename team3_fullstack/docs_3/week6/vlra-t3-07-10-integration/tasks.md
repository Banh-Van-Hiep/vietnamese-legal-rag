# Tasks — VLRA-T3-07–10 kiểm chứng tuần6

- [x] W6-01 Fetch/so develop, đọc nguồn và lập spec/clarify/plan/analyze; snapshot hash vào backend/target/week6-acceptance-20261029.
- [x] W6-02 Chạy5 suite Maven với PostgreSQL test thật; đối chiếu HTTP/mapping/history/state và transaction boundary (AC07–09).
- [x] W6-03 Chạy FE unit/build và E2E với FastAPI mock, lưu kết quả UI/Viewer/network/error (AC10, AC08).
- [x] W6-04 Chạy readiness/OpenAPI/query/article của FastAPI factory thật, ghi actual và điều kiện còn thiếu (AC-G3).
- [x] W6-05 Tổng hợp validation.md và week6/verification.md, cập nhật index/lệnh, kiểm link/diff và dọn dịch vụ test.
- [ ] W6-06 Sau bàn giao runtime/index/article snapshot: chạy query thật qua Java/UI và Viewer, xác nhận G3 (AC-G3).

W6-02→W6-03; W6-04 độc lập với test mock nhưng chạy riêng để không lẫn cổng/nguồn.
W6-05 sau02–04; W6-06 phụ thuộc readiness và bàn giao thật, không đánh dấu từ mock.

Phân định29/10: implementation thuộc Team3 đã sẵn sàng nhận bàn giao; phần còn thiếu
ở Team1/2 để team sở hữu tự làm. W6-06 là việc Team3 chạy sau bàn giao, không phải
nhiệm vụ triển khai thay runtime/index/article của team khác. Chưa chốt G3 bằng mock.
