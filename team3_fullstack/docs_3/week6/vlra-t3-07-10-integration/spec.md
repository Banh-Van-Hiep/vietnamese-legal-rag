# Đặc tả kiểm chứng tích hợp tuần6 — VLRA-T3-07–10

**Ngày:**29/10/2026. [Tasks tuần6](../tasks.md),
[ARCHITECTURE](../../../../docs/ARCHITECTURE.md),
[tích hợp RAG](../../../../docs/team3_fullstack/rag-integration-specification.md).

## Mục tiêu và phạm vi

Kiểm chứng implementation hiện có trước khi giao lại việc hoặc sửa code. Bao gồm
HTTP query/article, mapping, persistence/history, SSE/UI và readiness Python thật.
Tách kiểm chứng với FastAPI mock khỏi nghiệm thu G3 dữ liệu thật. Không sửa Team1/2,
API/schema, không tự dựng index/tải model hoặc ghi nhận Golden đã được Team2 duyệt.

## Clarify từ nguồn và hiện trạng

- Giữ Java25/SpringBoot4.1.1, React/TypeScript hiện có; tiếp tục trên nhánh hiện tại.
- JDK HttpClient và mapper tại DTO/controller đã đáp ứng trách nhiệm thiết kế; tên
  lớp AiContractMapper/MessageRepository trong ví dụ không buộc tạo bản trùng.
- Phần G3 chỉ đạt khi Java gọi pipeline/snapshot thật và Viewer mở đúng nguồn. Mock
  hoặc health200 không đủ. Thiếu readiness/article route là khoảng thiếu bàn giao,
  không tự suy là yêu cầu thay API. Tiếp tục kiểm phần độc lập.

## Hành vi và tiêu chí nghiệm thu

- AC07: Query chỉ gửi question/history với trace UUID; connect≤2s, wait≤50s;
  lỗi502/503/504 an toàn, không retry ngầm, không giữ DB transaction khi chờ HTTP.
- AC08: Citation9 field và article6 field được map snake_case→camelCase, giữ ID/URL,
  nullable và phiên bản; sai upstream bị từ chối, không tự thay nguồn.
- AC09: PostgreSQL chuyển pending→completed/failed nhất quán; history chỉ tối đa5
  cặp completed/answered, theo thời gian,≤20000 code point; loại failed/insufficient.
- AC10: FE lấy conversationId từ meta, cập nhật URL, khóa gửi khi pending, nối delta,
  hiển thị thiếu căn cứ riêng và không chạy HTML/script từ câu trả lời.
- AC-G3: Factory FastAPI thật ready200, query thật qua Java/UI và Viewer đọc đúng
  article snapshot. Nếu chưa đủ, ghi trạng thái chưa kiểm chứng/blocker và owner.

## Đầu vào/đầu ra, lỗi và phụ thuộc

Public dùng camelCase/SSE; internal query question/history và response3 field,
article6 field theo contracts hiện hành. Input sai400; unavailable503, timeout504,
invalid upstream502; lỗi kỹ thuật không chuyển thành insufficient. Team1 cung cấp
index/article snapshot, Team2 phục vụ pipeline/query/article/readiness/config runtime;
Team3 thực hiện adapter/persistence/UI. Không log secret hoặc thông tin cá nhân.
