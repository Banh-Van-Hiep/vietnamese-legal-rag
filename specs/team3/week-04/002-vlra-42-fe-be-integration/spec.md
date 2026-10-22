# Feature Specification: VLRA-42 — Tích hợp Frontend ↔ Backend API

**Feature Branch**: nhánh bàn giao được người dùng chỉ định; commit nhỏ, không push.
**Feature Directory**: `specs/team3/week-04/002-vlra-42-fe-be-integration`.
**Created**: 2026-10-21.
**Source alignment**: 2026-10-23 — Docs v2.0 và Jira là nguồn gốc; tài liệu này là thứ cấp.
**Responsible Team**: Team 3; chưa phân công thành viên.
**Status**: Implemented / ready for review — FE–BE v2.0 đã kiểm chứng với Java thật và HTTP fixture; live RAG chờ Team2, chưa cập nhật Jira.
**Input**: Jira VLRA-42: kết nối giao diện với API Backend; AC Frontend gửi request
thành công và nhận lại dữ liệu JSON mượt mà. Nội dung JSON được giữ nguyên như nguồn
Jira; SSE data JSON theo Docs v2.0 và quyết định áp dụng v2.0 đã chốt. VLRA-41 có API nền trong commit841280d; không có câu hỏi route còn mở.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Gửi câu hỏi từ giao diện đến Backend (Priority: P1)

Người dùng nhập câu hỏi hợp lệ; giao diện gửi tới Backend đã cấu hình và nhận kết quả
để hiển thị, không phải sửa code ứng dụng mỗi lần đổi môi trường đã được hỗ trợ.

**Why this priority**: Đây là AC cốt lõi của kết nối hai chiều FE–BE.
**Independent Test**: Dùng trình duyệt với Backend chạy thật; đối chiếu thao tác,
request/response và dữ liệu được chuyển cho UI. Backend có thể dùng test double
được ghi rõ cho kiểm thử cơ chế; pipeline thật được nghiệm thu riêng ở VLRA-44.

**Acceptance Scenarios**:

1. **Given** contract được chốt và Backend sẵn sàng, **When** gửi câu hỏi hợp lệ,
   **Then** request đến đúng Backend, nội dung/nhận diện lượt theo contract và
   kết quả nhận về được chuyển đúng cho vùng hiển thị Answer/Citation.
2. **Given** câu hỏi rỗng hoặc vượt giới hạn được chốt, **When** gửi trên UI,
   **Then** có thông báo phù hợp và không gửi request hỏi đáp không hợp lệ.
3. **Given** gửi xong nhận kết quả, **When** thao tác giao diện kết thúc,
   **Then** trạng thái chờ được giải phóng, không giữ UI ở trạng thái đang gửi vô hạn.

### User Story 2 — Hiển thị đúng lỗi và thử lại đúng lượt (Priority: P1)

Người dùng phân biệt dịch vụ không phản hồi với thiếu căn cứ, và thử lại mà không
tạo lượt hỏi trùng khi chưa biết server đã xử lý hay chưa.

**Why this priority**: Luồng thành công đơn lẻ chưa đủ chứng minh kết nối ổn định.
**Independent Test**: Tạo các tình huống mạng/lỗi ở boundary FE–BE trong môi trường
kiểm thử; kiểm tra trạng thái UI, thông tin lỗi và nhận diện request gửi lại.

**Acceptance Scenarios**:

1. **Given** Backend báo lỗi hoặc mất kết nối, **When** gửi câu hỏi,
   **Then** UI hiển thị lỗi an toàn, không biến thành một answer thành công.
2. **Given** kết quả lượt hỏi chưa rõ do mất phản hồi, **When** người dùng thử lại,
   **Then** giữ nhận diện lượt theo contract để không nhân đôi thao tác.
3. **Given** đã biết lượt cũ thất bại, **When** thử lại theo hành vi đã thống nhất,
   **Then** dùng quy tắc retry của contract và vẫn giữ đúng hội thoại.

### User Story 3 — Giữ đúng dữ liệu khi mở lại hoặc đổi hội thoại (Priority: P2)

Người dùng chọn một hội thoại hoặc mở citation và nhận dữ liệu đúng với lựa chọn đó.

**Why this priority**: Dữ liệu hợp lệ nhưng gắn sai hội thoại/nguồn vẫn là lỗi tích hợp.
**Independent Test**: Mở hội thoại, đổi lựa chọn trong khi có request và mở một citation;
đối chiếu dữ liệu trả về với lựa chọn đang hoạt động và contract đã chốt.

**Acceptance Scenarios**:

1. **Given** hội thoại có tin nhắn đã lưu, **When** mở lại,
   **Then** hiển thị dữ liệu Backend trả về theo đúng thứ tự, không tự gọi lại AI.
2. **Given** request cũ hoàn tất sau khi đã đổi hội thoại/nguồn,
   **When** response đến, **Then** không ghi đè nội dung của lựa chọn mới.
3. **Given** Backend không trả được tài liệu trích dẫn,
   **When** mở citation, **Then** lỗi ở vùng nguồn không làm mất answer đã nhận.

### Edge Cases

- Backend URL/CORS không phù hợp môi trường, mất mạng hoặc hết thời gian chờ.
- Response hỏng, sai media type hoặc bị gián đoạn trong khi đọc.
- Bấm gửi liên tục, gửi lại lượt chưa rõ kết quả, hội thoại bị xóa hoặc đang xử lý.
- Đổi màn hình/hội thoại khi request chưa xong; đóng viewer trong khi nguồn đang tải.
- Kết quả thiếu căn cứ hợp lệ và lỗi dịch vụ phải có trạng thái khác nhau.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: FE–BE theo Docs v2.0 §9.1–9.4: public camelCase, ID số, clientRequestId
  UUID v4, request JSON và response SSE chứa JSON; giữ nguyên AC nhận dữ liệu của
  Jira VLRA-42. Route đã chốt `/api/v1/chat/stream`; VLRA-41 đã có implementation trong commit841280d.
- **FR-002**: Thao tác hỏi đáp, tải hội thoại và mở nguồn phải gửi đúng dữ liệu đến
  Backend; không gọi trực tiếp Python/LLM từ Frontend.
- **FR-003**: FE phải xử lý kết quả thành công, thiếu căn cứ và lỗi theo contract;
  truyền nguyên nội dung/nhận diện citation cần thiết cho UI của VLRA-43.
- **FR-004**: Trạng thái chờ phải kết thúc khi hoàn tất, lỗi hoặc hủy; response của
  lựa chọn cũ không được gắn vào hội thoại/nguồn mới.
- **FR-005**: Timeout, response không đọc được và lỗi kết nối phải được xử lý an toàn;
  retry phải tuân thủ nhận diện lượt và trạng thái đã biết/chưa rõ kết quả.
- **FR-006**: Kiểm chứng phải qua trình duyệt và Backend thật, ghi URL/origin không
  chứa secret, contract/profile, thao tác và request/response đã được che dữ liệu nhạy cảm.
- **FR-007**: Parser/state phải xử lý meta/delta/complete/error, frame/UTF-8 bị chia,
  đúng một terminal và replay theo Docs v2.0 §9.4–9.7; lấy answer/citation chuẩn từ
  complete. Dừng nhận stream không được báo là đã hủy AI hoặc tự gửi lượt mới.

### Key Entities *(include if feature involves data)*

- **UI operation**: hỏi đáp, tải hội thoại hoặc mở nguồn, cùng lựa chọn đang hoạt động.
- **Request/response**: payload, nhận diện lượt và kết quả/lỗi theo contract được chọn.
- **UI state**: chờ, hoàn tất, thiếu căn cứ, lỗi hoặc hủy; liên hệ đúng thao tác nguồn.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Mỗi thao tác trong bộ ca hỏi đáp/tải hội thoại/mở nguồn tới đúng Backend
  và phản ánh đúng dữ liệu nhận được; có evidence browser ↔ Backend. Map FR-001/002/003/006.
- **SC-002**: Mọi ca lỗi mạng, timeout và response hỏng bắt buộc đều kết thúc trạng thái
  chờ, hiển thị đúng lỗi và không sinh answer giả. Map FR-003/004/005.
- **SC-003**: Các ca gửi lại và đổi hội thoại/nguồn không sinh lượt trùng hoặc gắn nhầm
  response; đối chiếu nhận diện và dữ liệu thực tế. Map FR-004/005/007.
- **SC-004**: Bộ ca event/frame chia, UTF-8, complete/error và replay đều phản ánh
  đúng dữ liệu/trạng thái, không ghép JSON event thành answer hoặc nhân đôi nội dung.
  Map FR-001/003/007.

## Assumptions

- Dùng Frontend/Backend hiện có và cấu hình môi trường theo repository; không tự
  coi “hai chiều” là yêu cầu WebSocket hoặc thêm một transport khác.
- Yêu cầu JSON của Jira phù hợp SSE data JSON. Format/ID lấy từ Docs v2.0;
  W4-Q1 đã được người dùng giải quyết theo v2.0; không lấy code cũ làm contract.
- “Mượt mà” được kiểm tra bằng thao tác có phản hồi/trạng thái hợp lý; không tự đặt SLA.
- Mock có thể phục vụ kiểm thử cơ chế, phải ghi rõ và không thay AC pipeline thật của 41/44.

## Scope and Dependencies

Trong phạm vi: nối/kiểm chứng FE–BE cho hỏi đáp và các thao tác hội thoại/nguồn liên
quan MVP hiện có; timeout, retry và đồng bộ trạng thái. Ngoài phạm vi: thiết kế lại UI,
pipeline Python, nguồn corpus, auth, DB migration hoặc transport ngoài nguồn gốc.

Kế thừa API VLRA-41. Proxy Viewer tối thiểu đã nối trong task42; nguồn thật vẫn phụ thuộc Team1/2. Thiết kế UI chi tiết và nghiệm thu nguồn thuộc VLRA43/44.
Nguồn gốc: [Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0)
§8.6–8.7/§9 và [Jira VLRA-42](https://banhvanhiep.atlassian.net/browse/VLRA-42).
W4-Q1 đã chốt v2.0; phạm vi, triển khai và giới hạn kiểm chứng nằm trong bộ feature này, đặc biệt verification.md.
[Team 3](../../../../docs/team3_fullstack/team3.md), C1–C5 và báo cáo phối hợp là thứ cấp.

Hiện có `src/api/chatApi.ts`, `client.ts`, `conversationApi.ts`, `documentApi.ts`,
`hooks/useChat.ts`, `useArticle.ts` và test client/retry trong Frontend. Đây là phần tái sử dụng; kết quả hiện tại: FE56test, Backend119test và11ca browser PASS (fixture), xem verification.md.

## Clarifications

### Session 2026-10-21

- Toàn bộ VLRA-41–44 thuộc tuần 4, chưa phân công thành viên.
- W4-Q1 resolved theo quyết định người dùng 23/10; ticket này vẫn chỉ đặc tả, chưa triển khai.

### Session 2026-10-23

- Docs v2.0/Jira là hai nguồn gốc. VLRA-42 nhận JSON không mâu thuẫn SSE data JSON;
  bỏ câu hỏi giả về lựa chọn format/ID. W4-Q1 đã chốt v2.0, không còn chặn route VLRA-41.
- Bản nháp ban đầu chỉ có đặc tả; lượt triển khai sau đã có parser, tests và evidence trong verification.md.

**Cập nhật dependency 23/10/2026:** người dùng đã chốt W4-Q1 theo v2.0; các ghi nhận chờ ở phiên trước là lịch sử. Kết quả triển khai được cập nhật tại verification.md.

### Session 2026-10-23 — triển khai được giao

- Người dùng yêu cầu triển khai VLRA-42, chờ Team2; không triển khai Python service.
- Được phép dùng HTTP stub đúng internal contract để kiểm chứng kết nối, nhưng không
  kết luận RAG thật hoặc VLRA-44 đã hoàn thành. Không có câu hỏi contract còn mở.
- Commit theo từng phần build được để có thể revert, dùng tài khoản GitHub của người dùng;
  chưa có yêu cầu push. Không sửa tác giả của commit đã có.
- Giữ component UI hiện có; adapter chuyển public camelCase/ID số sang view model nội bộ
  đang dùng string/snake_case. View model không phải wire contract và không gửi ra network.
- API Viewer v2.0 chưa đăng ký trong rag: bổ sung proxy/mapping tối thiểu đúng Docs §9.11–12
  để kiểm chứng request mở nguồn; không thiết kế lại Viewer hoặc làm thay VLRA-43.
