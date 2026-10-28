# Team 3 — Backend & Frontend

Thiết kế chức năng chung của phân hệ Fullstack. Đối chiếu source `62c3556` ngày 28/10/2026;
không phải danh sách nhiệm vụ hoặc báo cáo tiến độ theo tuần.

## Trách nhiệm và công nghệ

Team 3 sở hữu Java public gateway, hội thoại/persistence/idempotency, React UI và Viewer.
Team 1 sở hữu data/retrieval/article store; Team 2 sở hữu RAG/LLM và HTTP nội bộ.
Backend giữ Java 25/Spring Boot 4.1.1/Maven Wrapper/PostgreSQL; Frontend dùng
React 18/TypeScript/Vite/Tailwind 4. Không đổi stack hoặc implementation của team khác
để làm một bản mô tả thiết kế khớp code.

## Tài liệu thiết kế theo chức năng

| Tài liệu | Nội dung / nhiệm vụ cần đọc |
| --- | --- |
| [fullstack-architecture.md](fullstack-architecture.md) |Phạm vi, luồng liên team, package, profile và cấu hình |
| [public-api-specification.md](public-api-specification.md) |Endpoint, DTO, input, SSE, CORS và public errors |
| [persistence-design.md](persistence-design.md) |ERD, đủ4 bảng/cột, keys/constraints, snapshot, cascade/tombstone |
| [conversation-design.md](conversation-design.md) |State machine, transaction/locks, IDEM-01–12, history/title/recovery |
| [rag-integration-specification.md](rag-integration-specification.md) |AI boundary, validation, snake/camel mapping, timeout và lỗi upstream |
| [frontend-design.md](frontend-design.md) |Component/routes, wireframe desktop/mobile, states, Viewer và render an toàn |

[team3.md](team3.md) là điểm đọc ngắn tới các phần trên, không duy trì một bản đặc tả
thứ hai. Khi thay API/schema/state/citation phải đọc đúng phần chi tiết và cập nhật
nguồn liên quan, không đọc lại toàn bộ docs theo thói quen.

## Nguồn và xử lý khác biệt

[ARCHITECTURE](../ARCHITECTURE.md) là đặc tả chính hiện hành;
[CODING_CONVENTIONS](../CODING_CONVENTIONS.md) quy định triển khai/phối hợp/DoD.
Tra schema/version tại [contracts](../../contracts/README.md) khi sửa giao tiếp.
Jira theo dõi công việc, không dùng ticket hoặc Google Docs cũ ghi đè baseline mới.
Khi baseline, schema, quyết định và code lệch nhau: ghi hai nội dung/vị trí/ảnh hưởng,
báo người phụ trách để thống nhất; không tự nâng hành vi code thành contract mới.

Các tài liệu phân biệt quy tắc đã chốt, implementation đọc từ source và khoảng thiếu.
Những điểm đã nhận diện gồm recovery chưa định kỳ, NFC/legal ID validation cần đối chiếu,
các phần UI chưa có. DDL đã có CHECK JS-safe cho cả conversation.id và message.id.
Ghi nhận không đồng nghĩa đã sửa code.
Wireframe và ERD đã được đại diện Team 3 xác nhận ngày 29/10/2026; quyết định G1 theo
hồ sơ tuần, không tự suy từ việc tạo tài liệu hoặc build/test đạt.

## Ranh giới hồ sơ

Nhiệm vụ, phân công, Spec Kit, validation, bằng chứng và phê duyệt theo tuần nằm tại
[team3_fullstack/docs_3](../../team3_fullstack/docs_3/README.md).
Không đưa bảng task/tiến độ/test count vào tài liệu chung. Lượt tách tài liệu không sửa
code/Team 1/Team 2/shared contracts, không chạy lại build/test hoặc tạo kết quả nghiệm thu mới.
