# Research decisions — 29/10/2026

| Decision | Rationale / source | Alternative rejected |
| --- | --- | --- |
| Sửa query_request tại đúng v0.1 | Người dùng xác nhận sửa file gốc theo baseline hiện hành | Bộ public riêng khiến khó biết thay file nào |
| Bổ sung chat_stream | Chưa có schema payload SSE tương ứng; không thay rag_response nội bộ | Gộp request và mọi payload vào một tên chat không rõ vai trò |
| Giữ nguyên 4 schema nội bộ | Code và test Team1/2 đang dùng rag/retrieval/article/error | Đổi snake_case/giới hạn nội bộ theo public |
| Dùng $ref local và Registry | Tái sử dụng ID/UUID, không truy cập mạng | Nhân bản các điều kiện chung giữa hai file |
| Kiểm runtime cả SSE/legacy và Team2 | Schema request không được app tự đọc; vẫn kiểm regression trước bàn giao | Suy chắc chắn không ảnh hưởng chỉ từ việc không sửa code |
| Vai trò/ngày xác nhận | Người dùng yêu cầu không danh tính | Ghi tên/tài khoản/đường dẫn người dùng vào hồ sơ |

Không cần công nghệ mới. Đã chốt việc schema request không còn dùng kiểm JSON legacy;
API legacy hiện có vẫn giữ nguyên code. Không coi schema format PASS là đúng pháp lý.
