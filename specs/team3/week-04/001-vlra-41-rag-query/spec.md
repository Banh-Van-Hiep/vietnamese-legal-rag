# Feature Specification: VLRA-41 — API truy vấn kết nối RAG Pipeline

**Feature Branch**: nhánh bàn giao được người dùng chỉ định — nhánh bàn giao theo yêu cầu người dùng; soạn và kiểm thử trước đó trên `test/retrieval-verification`.
**Feature Directory**: `specs/team3/week-04/001-vlra-41-rag-query`.
**Created**: 2026-10-21.
**Source alignment**: 2026-10-23 — Docs v2.0 và Jira là nguồn gốc; tài liệu này là thứ cấp.
**Responsible Team**: Team 3; chưa phân công thành viên.
**Status**: Java implemented and verified — 117 test executions PASS; SC001/live RAG còn mở, chưa nghiệm thu toàn ticket. Người dùng chốt v2.0 ngày 23/10/2026.
**Input**: Jira VLRA-41 do người dùng cung cấp: xây `POST /api/v1/query`, nhận payload,
gọi RAG Pipeline Team 1/2 và trả JSON chứa Answer + Citation. Phạm vi tuần 4 đã được xác nhận.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Nhận câu trả lời từ pipeline thật (Priority: P1)

Người dùng gửi một câu hỏi và nhận được câu trả lời cùng căn cứ do pipeline đã cấu hình xử lý.

**Why this priority**: Đây là AC cốt lõi của VLRA-41 và điều kiện cho E2E MVP.
**Independent Test**: Gửi một câu hỏi có căn cứ trong corpus đã chốt qua giao diện
dịch vụ được duyệt; đối chiếu dấu vết xử lý và kết quả, chưa cần giao diện trình duyệt.

**Acceptance Scenarios**:

1. **Given** contract đợt này được xác nhận và pipeline thật sẵn sàng, **When** gửi
   câu hỏi hợp lệ có căn cứ, **Then** có evidence pipeline đã được gọi và kết quả chứa
   answer không rỗng, citation truy vết được về đúng nguồn.
2. **Given** pipeline trả kết quả thiếu căn cứ hợp lệ, **When** hoàn tất xử lý,
   **Then** trả trạng thái thiếu căn cứ với citation rỗng theo contract được duyệt.
3. **Given** test chạy bằng mock, **When** báo kết quả, **Then** ghi rõ profile mock;
   không dùng ca này thay cho nghiệm thu gọi pipeline thật.

### User Story 2 — Phân biệt lỗi kỹ thuật với kết quả pháp lý (Priority: P1)

Người dùng biết thao tác thất bại mà không nhận một câu trả lời có vẻ hợp lệ từ output lỗi.

**Why this priority**: Timeout, lỗi nguồn hoặc citation sai không được trình bày như kết luận pháp lý.
**Independent Test**: Kiểm tra input sai và các lớp lỗi upstream có kiểm soát qua boundary
dịch vụ, đối chiếu trạng thái/thông báo với contract đã chốt.

**Acceptance Scenarios**:

1. **Given** input không hợp lệ, **When** gửi query, **Then** bị từ chối và không gọi pipeline.
2. **Given** nguồn không sẵn sàng hoặc timeout, **When** xử lý query, **Then** có lỗi
   kỹ thuật truy vết được; không giả `insufficient_context`, không lộ secret hoặc lỗi thô.
3. **Given** answer/citation không đúng contract, **When** Backend nhận kết quả,
   **Then** không chấp nhận/lưu như câu trả lời thành công và trả lỗi tương ứng.

### User Story 3 — Giữ đúng ngữ cảnh và nhận diện lượt hỏi (Priority: P2)

Người dùng hỏi tiếp hoặc thử lại một lượt chưa rõ kết quả mà không bị ghép nhầm hội thoại,
nhân đôi lượt hay dùng lịch sử làm căn cứ pháp lý.

**Why this priority**: Tái sử dụng quản lý hội thoại hiện có khi nối pipeline thật.
**Independent Test**: Theo contract đích, đối chiếu một lượt mới, lượt nối tiếp và gửi
lại cùng lượt; kiểm tra history, kết quả và dấu vết gọi pipeline.

**Acceptance Scenarios**:

1. **Given** câu hỏi đầu của hội thoại, **When** gửi đến pipeline, **Then** không đính
   history của hội thoại khác; định danh công khai do Backend quản lý theo contract.
2. **Given** hội thoại có các lượt hoàn tất, đang xử lý hoặc lỗi, **When** hỏi tiếp,
   **Then** chỉ chọn history được contract cho phép, không gửi lẫn lượt hiện tại.
3. **Given** client gửi lại một lượt chưa rõ kết quả, **When** đối soát theo contract,
   **Then** không gọi pipeline hoặc lưu nhân đôi chỉ vì thao tác gửi lại.

### Edge Cases

- Payload thiếu/sai kiểu, câu hỏi rỗng hoặc vượt giới hạn của contract đích.
- Response thiếu field, status lạ, answer rỗng, citation không khớp marker/nguồn.
- Upstream mất kết nối, timeout, response không đọc được hoặc lỗi nội bộ.
- Lịch sử không đọc được, hội thoại đã xóa, lượt gửi lại hoặc đang xử lý đồng thời.
- Không có nguồn dùng được sau retrieval thành công: phân biệt thiếu căn cứ với lỗi retrieval.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Theo quyết định người dùng ngày 23/10/2026, triển khai public
  `POST /api/v1/chat/stream` bằng SSE/camelCase/ID số theo Docs v2.0 §9.
  Java gọi Python `POST /internal/v1/query` bằng JSON snake_case; không giữ
  `/api/v1/query` làm route chat chính trong profile v2.0. Jira chưa được sửa trực tiếp.
- **FR-002**: Câu hỏi hợp lệ phải đi qua boundary tích hợp Backend–RAG và có dấu vết
  đối chiếu được với kết quả; câu hỏi không hợp lệ không được gọi pipeline.
- **FR-003**: Kết quả có căn cứ phải chứa answer và citation hợp lệ, giữ định danh
  nguồn và ánh xạ marker; thiếu căn cứ phải dùng trạng thái nghiệp vụ riêng theo contract.
- **FR-004**: Kết quả upstream sai định dạng hoặc citation không hợp lệ phải bị chặn;
  không tự bổ sung/sửa citation để biến thành output được chấp nhận.
- **FR-005**: Timeout/unavailable/output sai phải ánh xạ mã Python sang public code
  theo Docs v2.0 §9.13–9.14, có truy vết an toàn; trước stream là HTTP error, sau mở
  stream là error event. Không đổi lỗi kỹ thuật thành thiếu căn cứ hoặc copy mã Python
  nguyên trạng ra public chỉ vì báo cáo thứ cấp ghi khác.
- **FR-006**: History/ID/retry theo Docs v2.0 §8.4/§9.7–9.8; chỉ Backend quản lý hội
  thoại, history không thay corpus. Hội thoại pending không nhận lượt mới; đóng
  stream không tự hủy AI. Không thêm tính năng ngắt lời trong nhiệm vụ này.
- **FR-007**: Bằng chứng nghiệm thu phải ghi snapshot, profile, cấu hình nguồn/model/index
  liên quan và kết quả; phân biệt test double với pipeline thật.

- **FR-008**: meta đúng một lần sau commit; heartbeat khi chờ; delta/complete chỉ sau validate và commit completed. insufficient_context không có delta giả. Một terminal; lỗi sau meta dùng event:error, replay failed dùng logical HTTP status.
- **FR-009**: Persistence PostgreSQL bảo vệ unique receipt, khóa hội thoại, một assistant pending, sequence và cập nhật có điều kiện; pending quá 60 giây được recovery, late output không ghi đè terminal. Lỗi DB không được phát complete.
- **FR-010**: Cung cấp đọc messages/hội thoại và xóa tối thiểu phục vụ retry/recovery của lượt chat; tombstone giữ IDs/trạng thái/thời gian, bỏ nội dung/fingerprint/snapshot. Không triển khai Viewer/UI trong VLRA-41.

### Key Entities *(include if feature involves data)*

- **Query / lượt hỏi**: câu hỏi, ngữ cảnh hội thoại và nhận diện lượt theo contract đích.
- **RAG result**: trạng thái trả lời/thiếu căn cứ, nội dung và tập citation tương ứng.
- **Citation**: tham chiếu bất biến đến chunk/văn bản/điều và nguồn; không tự đổi phiên bản.
- **Technical failure**: lớp lỗi, thông báo an toàn và thông tin truy vết theo contract.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Một lượt hỏi có căn cứ được xử lý trọn vẹn bởi pipeline thật; answer và
  toàn bộ citation trả về đối chiếu được với nguồn đã dùng. Map FR-001/002/003/007.
- **SC-002**: Trong bộ ca bắt buộc input sai, output sai, timeout và unavailable,
  mỗi ca đều có kết quả đúng loại; không có lỗi kỹ thuật được chấm thành câu trả lời
  pháp lý hoặc thiếu căn cứ. Map FR-002/004/005.
- **SC-003**: Các ca lượt mới, hỏi tiếp và gửi lại không trộn history hoặc sinh lượt
  trùng; có evidence theo clientRequestId UUID v4 và conversationId số. Map FR-006.
- **SC-004**: Mọi kết luận nghiệm thu có command/thao tác, snapshot, profile,
  expected/actual và evidence; chưa đủ service hoặc contract thì ghi chưa chạy,
  không chấm PASS. Map FR-007 và toàn bộ acceptance scenarios.

## Assumptions

- Tuần triển khai 4 được người dùng xác nhận ngày 21/10; chưa xác định ngày demo cụ thể.
- Giữ kiến trúc và ranh giới team; không tự chọn framework server cho Team 2.
- Phần JSON v1.2 có sẵn là hiện trạng tái sử dụng có điều kiện, không là yêu cầu gốc
  hoặc căn cứ tự thay Docs v2.0/Jira. JSON payload không tự mâu thuẫn SSE.
- Mock được dùng kiểm tra cơ chế, không thay bằng chứng gọi RAG thật.
- Không tự thêm ngưỡng SLA/coverage hoặc cơ chế đăng nhập/triển khai hạ tầng.

## Scope and Dependencies

Trong phạm vi: tiếp nhận query, boundary gọi RAG, validation, trạng thái/lỗi, history/
gửi lại theo contract được duyệt và kiểm thử API tích hợp. Ngoài phạm vi: dựng lại UI,
thêm ngoại lệ transport ngoài hai nguồn gốc, triển khai retrieval/LLM/HTTP server Team 2,
thiết kế DB ngoài persistence tối thiểu của lượt chat hoặc tự tạo nguồn nguyên văn. Viewer thuộc VLRA-43; E2E UI thuộc VLRA-44.

W4-Q1 đã được người dùng giải quyết. W4-D1/D2 còn mở: Team2 cần bàn giao service HTTP chạy thật và toàn tuyến retrieval/rerank/LLM cùng snapshot để nghiệm thu SC001.
**Develop đã kiểm tra:** `3d64c4d38b93f11ac321623159f74e5202d1e953`, ngày 23/10/2026 (fetch lại cùng commit).
`HttpAiClient` rỗng; Python `service.query()` mock; có `generate_answer()` nhưng chưa
có server HTTP RAG được bàn giao. Đây là inventory source, chưa là kiểm thử runtime.

Nguồn gốc: [Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0)
§8/§9 và [Jira VLRA-41](https://banhvanhiep.atlassian.net/browse/VLRA-41).
[Tài liệu Team 3](../../../../docs/team3_fullstack/team3.md), I/O Team 2, contract files
và C1–C5 là thứ cấp, không được ghi đè hai nguồn trên. Quyết định W4-Q1 được ghi
trong [Clarifications](#clarifications); phụ thuộc live nằm trong mục này và verification.md.

## Clarifications

### Session 2026-10-21

- Tuần 4 đã được người dùng xác nhận.
- W4-Q1 được ghi nhận chờ trưởng nhóm; phạm vi xung đột đã được làm rõ ở phiên 23/10 bên dưới.
- Đã kiểm tra develop theo yêu cầu; W4-D1 còn thiếu service HTTP. Không đặt thêm câu
  hỏi giống nội dung người dùng đã yêu cầu chờ; tiếp tục phần tài liệu độc lập.

### Session 2026-10-23

- Chỉ Docs v2.0 và Jira là nguồn yêu cầu gốc; sửa tài liệu thứ cấp theo nguồn.
- Làm rõ W4-Q1 chỉ là route/mốc áp dụng VLRA-41 khác Docs §9.2/§11.1; không coi
  JSON và SSE tự mâu thuẫn. Quyết định áp dụng v2.0 được ghi ngay dưới.
- Public SSE/internal JSON, mapping lỗi và quy tắc pending là yêu cầu từ Docs v2.0,
  không phải lựa chọn do báo cáo phối hợp hoặc code hiện tại quyết định.

- Q: VLRA-41 dùng route Jira cũ hay Docs v2.0? → A: Người dùng: “làm theo đặc tả v2.0 nhé bây giờ hãy triển khai task 41”. Áp dụng SSE public, JSON nội bộ; chưa cập nhật Jira.
- Tái kiểm tra origin/develop sau git fetch ngày 23/10: 3d64c4d38b93f11ac321623159f74e5202d1e953. HttpAiClient rỗng, Python service.query vẫn mock, không thấy HTTP server. Không sửa implementation Team 2 thay họ.
