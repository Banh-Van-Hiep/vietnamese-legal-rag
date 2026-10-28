# Feature Specification: Hoàn thiện public SSE contract tuần 4

**Created:** 2026-10-29. **Status:** Verified locally theo quyết định sửa file gốc; bàn giao bằng commit theo yêu cầu.
**Phạm vi:** phần còn thiếu W4-02 của VLRA-T3-02; không triển khai lại chat.
**Nguồn:** [nhiệm vụ tuần](../tasks.md), [ARCHITECTURE §3.1](../../../../docs/ARCHITECTURE.md#31-public-client-api-team-3-frontend---team-3-backend),
[đặc tả public Team 3](../../../../docs/team3_fullstack/public-api-specification.md),
quyết định người dùng ngày 29/10/2026. Bốn nguyên tắc constitution vẫn áp dụng;
đường dẫn lịch sử trong constitution không ghi đè baseline hiện hành.

## Clarifications

### Session 2026-10-29

- Quyết định mới thay quyết định giữ public schema cũ: sửa trực tiếp contracts/v0.1/query_request.schema.json theo public SSE hiện hành, giữ đúng tên; bổ sung chat_stream.schema.json cho payload SSE chưa có file tương ứng. Bỏ bộ public trùng vừa tạo. Các schema nội bộ Team 1/2 giữ nguyên.
- Wireframe đã được đại diện Team 3 xác nhận duyệt; không cần đòi thêm nguồn hoặc danh tính. Có thể điều chỉnh UI sau này và cập nhật tài liệu tương ứng.
- Phần đóng góp Golden đã làm trước đó trong ground_truth; ghi nhận xác nhận này, không tự dựng lại phân công hoặc suy ra dataset đã được thẩm định pháp lý.
- Trưởng nhóm duyệt; thành viên không được push trực tiếp main, tuần hoàn tất được nghiệm thu nội bộ rồi merge develop. Không có xác nhận cho phép bỏ review. Người dùng xác nhận GitHub đã cưỡng chế giới hạn push main; đây là xác nhận vận hành, không phải kết quả đọc rules API.
- Không ghi tên, tài khoản hoặc danh tính cá nhân vào hồ sơ/fixture công khai.
- Người dùng xác nhận dùng ERD persistence-design hiện hành làm thiết kế chi tiết theo ARCHITECTURE.

## User Scenarios & Testing

### User Story 1 — Kiểm tra đúng phiên bản dữ liệu chat (Priority: P1)

Người tích hợp kiểm được dữ liệu chat hiện hành mà không áp schema JSON cũ lên SSE.
**Independent Test:** dữ liệu hợp lệ được chấp nhận; dữ liệu sai cấu trúc/kiểu bị từ chối.

1. Given lượt hỏi mới/tiếp nối hợp lệ, When kiểm tra request và payload sự kiện,
   Then giữ đúng định danh, casing và kết quả answered/insufficient_context.
2. Given UUID/ID/casing/field sai hoặc citation không hợp lệ, When kiểm tra,
   Then báo lỗi và không tự sửa payload để cho qua.

### User Story 2 — Bàn giao có bằng chứng và bảo toàn contract nội bộ (Priority: P2)

Người review phân biệt phần đã kiểm, xác nhận vận hành và phần chưa xác minh.
**Independent Test:** đối chiếu payload thực từ test có sẵn; so hash các schema nội bộ giữ nguyên;
đọc biên bản không có danh tính cá nhân hoặc tuyên bố cấu hình GitHub đã được kiểm.

1. Given contract cũ và source không đổi, When bổ sung hồ sơ mới,
   Then schema nội bộ Team 1/2 và ứng dụng giữ nguyên; query_request được cập nhật có chủ đích, route public vẫn /api/v1/chat/stream.

### Edge Cases

- IDs bằng 0, âm, chuỗi, vượt số nguyên an toàn; UUID không phải v4; key snake_case.
- question trống/quá giới hạn; tiếng Việt/emoji tính theo code point.
- complete thiếu field, answered không citation, insufficient_context còn citation/marker.
- Lỗi dùng cấu trúc error/code/message/retryable; heartbeat là comment không có JSON.
- Schema một payload không tự chứng minh thứ tự frame, binding ID/time hoặc grounding pháp lý.

## Requirements

### Functional Requirements

- **FR-001:** Mô tả request đúng public v2: question, clientRequestId UUIDv4,
  conversationId tùy chọn/null hoặc integer 1..9007199254740991; không nhận field lạ;
  question sau trim dài 1–2000 Unicode code point.
- **FR-002:** Mô tả meta 5 field, delta/text, complete 8 field, error envelope và
  citation 9 field; UTC; answered có 1–10 citation, insufficient_context có mảng rỗng.
- **FR-003:** Tách kiểm tra cấu trúc với marker/citation, ID/time binding và thứ tự
  frame; ví dụ sai phải bị từ chối, không coi schema PASS là bằng chứng đúng pháp lý.
- **FR-004:** Đồng bộ public schema tại đúng file gốc, không thay URL/transport, internal
  contract, dữ liệu, dependency hoặc code nghiệp vụ/test ứng dụng; thay query_request và tài liệu chỉ mục theo cho phép trực tiếp.
- **FR-005:** Ghi quyết định duyệt/Golden/quy trình Git theo xác nhận đã có, dùng vai
  trò, không ghi danh tính hoặc tự khẳng định branch protection đã kiểm chứng.
- **FR-006:** Có lệnh kiểm tra tái lập, exit code khác 0 khi lỗi, ví dụ có nhãn mock,
  đối chiếu payload thật do test HTTP hiện có xuất ra và bằng chứng bảo toàn file cũ.

### Key Entities

ChatRequest; Meta; Delta; Complete; ErrorResponse; PublicCitation. Không thêm entity DB.
Quan hệ giữa chúng giữ theo tài liệu chức năng chung, không tạo contract nội bộ mới.

## Success Criteria

- **SC-001:** Mọi payload hợp lệ trong bộ kiểm chứng được chấp nhận; mỗi nhóm lỗi
  trong Edge Cases có ca bị từ chối và kết quả expected/actual.
- **SC-002:** Payload request/meta/delta/complete thực từ kiểm thử HTTP có sẵn qua
  kiểm tra mới; các schema nội bộ cùng code/dữ liệu ngoài phạm vi giữ nguyên checksum; query_request và tài liệu chung đổi đúng phạm vi được cho phép.
- **SC-003:** Hồ sơ chỉ rõ phần nghiệm thu kỹ thuật, xác nhận nhóm và kiểm tra chưa
  thực hiện; không chứa danh tính cá nhân và không tự đánh dấu G1/release đã bàn giao.

## Assumptions, Dependencies và ngoài phạm vi

Không cần RAG/LLM thật để đặc tả public transport. Dùng Python/jsonschema và test HTTP
đã có để kiểm chứng; không thêm framework mới. Legal ID viết thường theo quy chuẩn;
code hiện còn chấp nhận chữ hoa và chưa chuẩn hóa NFC tường minh, là khoảng thiếu
implementation, không tự nâng thành contract. Không sửa lỗi đó trong task tài liệu này.
Không tự sửa CODEOWNERS khi chưa biết owner hợp lệ hoặc đổi rules GitHub. Commit đã được yêu cầu; chưa được yêu cầu push/merge,
hoặc suy xác nhận pháp lý/phân công cá nhân từ trường author trong dataset.
