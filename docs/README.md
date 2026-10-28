# Tài liệu chung của dự án

`docs/` chứa đặc tả chung, kiến trúc, quy chuẩn và thiết kế chức năng của các phân hệ.
Nhiệm vụ, phân công, tiến độ và báo cáo nghiệm thu từng tuần quản lý cùng thư mục team;
không duy trì bảng task hoặc kết quả test theo tuần trong tài liệu chung Team 3.

## Tài liệu nền

| Tài liệu | Nội dung |
| --- | --- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Đặc tả chính hiện hành: phạm vi, yêu cầu, kiến trúc, interface và mục tiêu nghiệm thu |
| [CODING_CONVENTIONS.md](CODING_CONVENTIONS.md) | Quy chuẩn code, interface, Git và phối hợp |

## Thiết kế các phân hệ

| Phân hệ | Điểm đọc |
| --- | --- |
| Team 1 — Data & Retrieval | [Mục lục thiết kế](team1_data/README.md) |
| Team 2 — RAG & LLM | [Mục lục thiết kế](team2_rag/README.md) |
| Team 3 — Backend & Frontend | [Mục lục thiết kế](team3_fullstack/README.md) |

Thiết kế không chứng minh chức năng đã triển khai hoặc đã nghiệm thu. Khi sửa API/schema,
đối chiếu ARCHITECTURE, CODING_CONVENTIONS và [contracts](../contracts/README.md); báo khác biệt để thống nhất,
không tự sửa phần thuộc team khác.

## Hồ sơ triển khai Team 3

Nhiệm vụ mới theo tuần đặt tại [team3_fullstack/docs_3](../team3_fullstack/docs_3/README.md).
Báo cáo nghiệm thu nằm trong từng thư mục tuần. Không duy trì bản nhiệm vụ Team 3
trùng trong `specs/`. Tổ chức lại Team 3 không di chuyển hoặc sửa hồ sơ Team 1/2.
