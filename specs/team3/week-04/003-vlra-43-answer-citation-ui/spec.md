# Feature Specification: VLRA-43 — Answer + Citation UI

**Feature Branch**: `test/retrieval-verification` — nhánh soạn tài liệu, chưa chọn nhánh triển khai.
**Feature Directory**: `specs/team3/week-04/003-vlra-43-answer-citation-ui`.
**Created**: 2026-10-21.
**Source alignment**: 2026-10-23 — Docs v2.0 và Jira là nguồn gốc; tài liệu này là thứ cấp.
**Responsible Team**: Team 3; chưa phân công thành viên.
**Status**: Draft — chỉ đặc tả, chưa phân công/plan/implementation; chưa thấy xung đột gốc riêng cho VLRA-43.
**Input**: Jira VLRA-43: hiển thị văn bản trả lời và thẻ `citations`, bấm xem chi tiết
văn bản gốc; AC hiển thị đầy đủ answer và citation theo thiết kế MVP.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Đọc câu trả lời và nhận biết căn cứ (Priority: P1)

Người dùng đọc được toàn bộ câu trả lời tiếng Việt và nhận biết nguồn trích dẫn
tương ứng, không nhầm thông báo lỗi hoặc thiếu căn cứ với một câu trả lời có nguồn.

**Why this priority**: Đây là chức năng chính và AC trực tiếp của VLRA-43.
**Independent Test**: Cấp các kết quả hợp lệ có answer/citation cho màn hình hiện có;
đối chiếu nội dung và thao tác trên trình duyệt, ghi rõ nếu dùng fixture.

**Acceptance Scenarios**:

1. **Given** kết quả có căn cứ hợp lệ, **When** hiển thị trên UI,
   **Then** toàn bộ answer và các citation được thể hiện, marker ánh xạ đúng thẻ nguồn.
2. **Given** answer tiếng Việt dài, nhiều đoạn và nhiều citation,
   **When** đọc ở kích thước desktop hoặc mobile được MVP hỗ trợ,
   **Then** nội dung không bị mất, đè lên nhau hoặc khiến nguồn không thể thao tác.
3. **Given** kết quả thiếu căn cứ hợp lệ, **When** hiển thị,
   **Then** có thông báo thiếu căn cứ, không dựng thêm thẻ nguồn không có trong dữ liệu.

### User Story 2 — Mở đúng văn bản gốc từ citation (Priority: P1)

Người dùng bấm marker hoặc thẻ citation để đối chiếu với nguyên văn đúng nguồn đã trích.

**Why this priority**: Answer + Citation phải cho phép truy vết, không chỉ hiển thị nhãn.
**Independent Test**: Dùng một citation và nguồn nguyên văn đã xác định, bấm từ answer
hoặc thẻ rồi kiểm tra định danh, nhãn điều và nội dung Viewer.

**Acceptance Scenarios**:

1. **Given** nguồn nguyên văn sẵn sàng, **When** bấm citation,
   **Then** mở đúng văn bản/điều/phiên bản được tham chiếu và hiển thị nội dung gốc.
2. **Given** citation có đường dẫn nguồn hợp lệ, **When** chọn mở nguồn gốc,
   **Then** mở đúng nguồn đó; không thay bằng URL suy ra từ tên văn bản.
3. **Given** nguồn không còn tồn tại hoặc tải lỗi, **When** mở citation,
   **Then** báo lỗi tại vùng xem nguồn, giữ answer và nguồn được trích ban đầu;
   không tự thay bằng phiên bản văn bản khác.

### User Story 3 — Thao tác rõ ràng trong khi chờ hoặc gặp lỗi (Priority: P2)

Người dùng biết hệ thống đang xử lý/tải nguồn hay đã thất bại; có thể tiếp tục đọc
câu trả lời và đóng/mở vùng nguồn bằng các thao tác giao diện thông thường.

**Why this priority**: Tránh nội dung trống hoặc mất trạng thái khi demo và sử dụng MVP.
**Independent Test**: Tạo trạng thái chờ/thành công/lỗi của answer và Viewer; đối chiếu
nhãn trạng thái và thao tác chuột/bàn phím hiện có, không cần pipeline thật.

**Acceptance Scenarios**:

1. **Given** answer hoặc nguồn đang tải, **When** chờ,
   **Then** UI có trạng thái phù hợp thay vì hiển thị nội dung mẫu như dữ liệu thật.
2. **Given** lỗi hệ thống, **When** UI nhận lỗi,
   **Then** hiển thị thông báo an toàn riêng, không trình bày như lời tư vấn pháp luật.
3. **Given** Viewer đang mở, **When** đóng Viewer hoặc đổi hội thoại,
   **Then** thao tác hoạt động và không giữ nguồn của hội thoại cũ trên lựa chọn mới.

### Edge Cases

- Answer dài, Unicode tiếng Việt, nhiều marker hoặc marker lặp lại cùng citation.
- Citation dài, có khoản/điểm null, nhiều nguồn; nội dung không gây tràn vùng đọc.
- Nguồn 404, timeout, unavailable, trả sai ID hoặc sai phiên bản.
- Thiếu căn cứ, failed hoặc pending; không hiện nguồn thừa và answer thành công giả.
- Nội dung từ bên ngoài có ký tự giống HTML: hiển thị an toàn, không thực thi mã.
- Output citation sai bị boundary chặn; UI không tự sửa hoặc tự tạo căn cứ để hiển thị.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dữ liệu answer/citation theo Docs v2.0 §8.6/§9.6/§9.9: public camelCase,
  citation từ complete event; mở nguồn bằng documentId/articleId theo §9.11.
  Giữ AC hiển thị đầy đủ answer/thẻ nguồn của Jira VLRA-43.
- **FR-002**: UI phải hiển thị đủ answer, marker và thẻ citation hợp lệ, giữ đúng ánh
  xạ dữ liệu, nhãn văn bản/điều và khoản/điểm khi có; không bịa nội dung còn thiếu.
- **FR-003**: Bấm marker/thẻ phải mở nguồn bằng định danh của citation, hiển thị nguyên
  văn đúng phiên bản, không gọi LLM để viết lại nội dung nguồn.
- **FR-004**: Loading, thiếu căn cứ và lỗi phải có trạng thái riêng; lỗi Viewer không
  làm mất answer hoặc âm thầm thay đổi citation.
- **FR-005**: Nội dung phải đọc và thao tác được trên desktop/mobile của MVP; văn bản
  ngoại sinh phải được hiển thị an toàn và các thao tác nguồn có nhãn rõ ràng.
- **FR-006**: Khi đối chiếu thiết kế MVP, phải ghi màn hình/kích thước, dữ liệu đầu vào,
  thao tác và ảnh chụp/evidence; fixture phải được phân biệt với dữ liệu thật.

### Key Entities *(include if feature involves data)*

- **Answer view**: nội dung, trạng thái và các marker tham chiếu đến citation.
- **Citation card**: nhãn nguồn và định danh để mở đúng nội dung pháp lý.
- **Source view**: nội dung nguyên văn/đường dẫn nguồn và trạng thái tải/lỗi.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Với mỗi kết quả có căn cứ trong bộ ca, toàn bộ answer/citation hiện đúng
  nội dung và mọi marker thao tác được đều mở đúng nguồn. Map FR-001/002/003.
- **SC-002**: Bộ ca nguồn hợp lệ, không tồn tại, timeout và lỗi ID đều cho kết quả đúng
  loại; không có ca mất answer hoặc đổi phiên bản nguồn âm thầm. Map FR-003/004.
- **SC-003**: Các ca nội dung dài/Unicode/nhiều nguồn và trạng thái chờ/thiếu căn cứ/lỗi
  được đối chiếu trên desktop/mobile; không mất nội dung hoặc không thể thao tác do bố cục.
  Có evidence và nhận xét chỗ khác thiết kế. Map FR-002/004/005/006.

## Assumptions

- Kế thừa giao diện hiện có và các luồng trong tài liệu Team 3; chưa có mẫu thiết kế
  mới được cung cấp ở nhiệm vụ này. Không tự gọi ảnh chụp implementation là thiết kế
  đã được duyệt; nếu thiếu căn cứ đối chiếu thị giác, ghi mục chưa được xác nhận khi review.
- Binding dữ liệu/định danh lấy từ Docs v2.0; W4-Q1 ở VLRA-41 là phụ thuộc khi nối
  luồng thực tế, không tạo câu hỏi mới về PublicCitation hoặc UI của VLRA-43.
- Dùng fixture hợp lệ để kiểm tra hiển thị được phép; không tính là E2E thật của VLRA-44.
- Không tự thêm chức năng tìm kiếm, đánh giá câu trả lời, đăng nhập hoặc xuất tài liệu.

## Scope and Dependencies

Trong phạm vi: hiển thị answer/citation, thao tác xem nguyên văn/nguồn, trạng thái UI
và kiểm chứng bố cục/hành vi MVP liên quan. Ngoài phạm vi: pipeline RAG, xác minh pháp
lý corpus, redesign toàn ứng dụng hoặc triển khai transport/Backend của các task khác.

Phụ thuộc nguồn thật W4-D3 và dữ liệu từ VLRA-42; W4-Q1 ở VLRA-41 chỉ chặn phần
tích hợp có liên quan, không chặn mô tả UI/dữ liệu đã rõ trong nguồn gốc.
Nguồn gốc: [Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0)
§8.6–8.7/§9.6/§9.9/§9.11–9.12 và [Jira VLRA-43](https://banhvanhiep.atlassian.net/browse/VLRA-43).
[Yêu cầu tuần](../requirements.md) và [Team 3](../../../../docs/team3_fullstack/team3.md)
là thứ cấp; không dùng làm yêu cầu độc lập thay hai nguồn trên.

Đã có `MessageBubble`, `CitationList`, `CitationCard`, `DocumentViewer`, `DocumentDrawer`
và wiring trong `ChatPage`. Lượt này chỉ đọc source; chưa chạy UI hoặc xác nhận AC đạt.

## Clarifications

### Session 2026-10-21

- Team 3 chưa phân thành viên; chỉ đặc tả trước khi lập kế hoạch/triển khai.
- W4-Q1 resolved: người dùng chốt v2.0 ngày 23/10; ticket này chưa triển khai.

### Session 2026-10-23

- Chỉ Docs v2.0/Jira là nguồn gốc. Đã rõ contract answer/citation/Viewer từ Docs;
  không coi bản API v1.2 hoặc báo cáo phối hợp là lựa chọn cạnh tranh.
- Chưa thấy xung đột riêng giữa Jira VLRA-43 và Docs v2.0. W4-Q1 của VLRA-41 đã được người dùng chốt v2.0 ở cấp tuần; service/nguồn thật còn là dependency để nghiệm thu, không là yêu cầu mơ hồ.

**Cập nhật dependency 23/10/2026:** người dùng đã chốt W4-Q1 theo v2.0; các ghi nhận chờ ở phiên trước là lịch sử. Chưa triển khai ticket này.
