# Feature Specification: VLRA-44 — Kiểm thử E2E MVP Interface

**Feature Branch**: `test/retrieval-verification` — nhánh soạn tài liệu, chưa chọn nhánh triển khai.
**Feature Directory**: `specs/team3/week-04/004-vlra-44-mvp-e2e`.
**Created**: 2026-10-21.
**Source alignment**: 2026-10-23 — Docs v2.0 và Jira là nguồn gốc; tài liệu này là thứ cấp.
**Responsible Team**: Team 3; chưa phân công thành viên.
**Status**: Draft — chỉ đặc tả; chưa lập plan/implementation hoặc chạy nghiệm thu.
**Input**: Jira VLRA-44: kiểm thử thành công UI → Backend API → RAG Pipeline → hiển thị
Answer + Citation; hệ thống MVP hoàn chỉnh sẵn sàng demo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Hỏi đáp trọn tuyến trên giao diện MVP (Priority: P1)

Người dùng nhập một câu hỏi pháp luật trong phạm vi corpus và thấy answer/citation
được tạo bởi pipeline thật, qua đúng Backend và Frontend dùng cho buổi demo.

**Why this priority**: Đây là AC E2E bắt buộc của VLRA-44.
**Independent Test**: Khởi chạy hệ thống theo cấu hình demo đã thống nhất, dùng trình
duyệt nhập câu hỏi có nguồn đối chiếu rồi lần theo evidence qua từng ranh giới đến UI.

**Acceptance Scenarios**:

1. **Given** contract/môi trường demo đã chốt và các dịch vụ thật sẵn sàng,
   **When** nhập và gửi câu hỏi trên UI, **Then** request đi qua Backend, retrieval,
   rerank/context/LLM theo cấu hình đã duyệt và kết quả hiển thị đủ Answer + Citation.
2. **Given** kết quả có citation, **When** bấm thẻ hoặc marker,
   **Then** mở đúng nguồn nguyên văn theo VLRA-43 và giữ câu trả lời khi đóng Viewer.
3. **Given** một bước đang dùng mock/fixture hoặc không có evidence pipeline thật,
   **When** tổng hợp kết quả, **Then** không ghi ca đó đạt AC E2E pipeline thật.

### User Story 2 — Ứng xử đúng khi thiếu căn cứ hoặc dịch vụ lỗi (Priority: P1)

Người dùng nhận thông báo đúng loại thay vì một câu trả lời có vẻ có căn cứ khi hệ
thống thực tế thiếu nguồn hoặc thất bại giữa các tầng.

**Why this priority**: MVP sẵn sàng demo cần xác định rõ giới hạn và trạng thái lỗi.
**Independent Test**: Thực hiện các ca thiếu căn cứ/lỗi bắt buộc qua UI trong môi
trường cô lập; ghi lớp nào dùng lỗi được chủ động tạo và phần nào thực thi thật.

**Acceptance Scenarios**:

1. **Given** retrieval thành công nhưng không đủ căn cứ,
   **When** xử lý câu hỏi, **Then** UI hiển thị trạng thái thiếu căn cứ, citation rỗng.
2. **Given** upstream timeout/unavailable hoặc output không hợp lệ,
   **When** xử lý qua UI, **Then** có thông báo lỗi kỹ thuật an toàn, không có answer
   thành công giả và không lộ secret, prompt hoặc stack trace.
3. **Given** mất phản hồi khi chưa rõ kết quả lượt hỏi,
   **When** thử lại theo luồng được duyệt, **Then** không tạo trùng lượt hoặc gọi
   pipeline thêm do nhận diện sai; dữ liệu hiển thị vẫn đúng hội thoại.

### User Story 3 — Có bằng chứng để quyết định sẵn sàng demo (Priority: P1)

Team 3 và người nghiệm thu có một kết luận dựa trên ca đã chạy, biết lỗi nào còn
mở và có thể tái hiện đúng môi trường trước buổi demo.

**Why this priority**: Chạy thành công một lần hoặc có code không đủ thay cho bàn giao MVP.
**Independent Test**: Một người khác thực hiện lại kịch bản demo theo hướng dẫn đã
được kiểm chứng và đối chiếu evidence, snapshot, môi trường và danh sách lỗi.

**Acceptance Scenarios**:

1. **Given** bộ ca theo AC và môi trường đã chốt,
   **When** chạy/đánh giá, **Then** mỗi ca có input, expected, actual, verdict và evidence;
   BLOCKED/NOT RUN/SKIP không được quy thành PASS.
2. **Given** lỗi ảnh hưởng luồng demo còn mở,
   **When** kết luận, **Then** ghi chưa sẵn sàng hoặc phần chưa nghiệm thu cùng owner
   cần phối hợp; không tự thay phạm vi AC để chấm đạt.
3. **Given** các AC bắt buộc đã đạt trên cùng baseline,
   **When** bàn giao, **Then** có kịch bản/lệnh đã chạy và thông tin để tái hiện;
   xác nhận kỹ thuật được tách khỏi phê duyệt demo của nhóm.

### Edge Cases

- Một dịch vụ chưa chạy, cấu hình URL/origin sai, provider/model/index không sẵn sàng.
- Câu hỏi hợp lệ nhưng không đủ nguồn, nguồn citation không tồn tại hoặc lệch phiên bản.
- Mất mạng/timeout/response hỏng giữa chừng; gửi lại hoặc đổi hội thoại khi đang xử lý.
- UI có route/fixture chưa tích hợp thật: phải ghi phạm vi và giới hạn khi kiểm tra MVP.
- Các tầng dùng corpus/model/index khác snapshot hoặc model giả nhưng không được ghi rõ.
- Lỗi retrieval đã báo chưa sửa, làm ngăn luồng trọn tuyến hoặc sai output contract.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Bộ ca theo Docs v2.0 §9/§10.4–10.5 và AC Jira VLRA-44: public SSE
  chứa JSON, internal JSON, đúng trạng thái/trace/Viewer. Trước khi chốt route chạy
  E2E thật, phải xử lý W4-Q1 của VLRA-41; không tự bỏ hoặc đổi AC để vượt dependency.
- **FR-002**: AC thành công phải thực thi từ thao tác UI qua Backend và pipeline thật
  đến Answer + Citation; phải có evidence tương quan giữa các tầng.
- **FR-003**: Citation hiển thị phải truy vết được đến nguồn dùng để tạo kết quả;
  mở nguyên văn phải đúng định danh/phiên bản, không dùng lời LLM thay nguồn.
- **FR-004**: Bộ ca phải phân biệt thành công, thiếu căn cứ, output sai, unavailable,
  timeout và gửi lại chưa rõ kết quả; kiểm tra trạng thái UI và bảo toàn lượt/hội thoại.
- **FR-005**: Mỗi kết quả phải ghi source commit, môi trường/profile, phiên bản
  corpus/index/model liên quan, input/expected/actual/verdict, lỗi và evidence an toàn.
- **FR-006**: Kết luận demo phải đối chiếu AC của 41/42/43 rồi 44, có danh sách lỗi và
  mục chưa chạy; không suy PASS từ mock, build/unit tests hoặc source inspection.
- **FR-007**: Trước bàn giao phải có cách chạy và kịch bản demo đã kiểm chứng trên
  môi trường được nhóm chọn; không công khai API key hoặc dữ liệu nhạy cảm.

### Key Entities *(include if feature involves data)*

- **E2E case/run**: kịch bản người dùng, môi trường/profile, đầu vào, verdict và evidence.
- **Trace chain**: nhận diện lượt/dấu vết tương ứng qua UI, Backend và pipeline.
- **Source baseline**: commit, corpus/index/model và contract dùng cho một lần đánh giá.
- **Demo verdict**: từng AC đạt/chưa đạt, lỗi còn mở và xác nhận của nhóm khi có.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ít nhất một ca có căn cứ thực thi trọn tuyến thật từ UI đến Answer +
  Citation và mở nguồn đúng; evidence truy vết được từng ranh giới. Map FR-001/002/003/005.
- **SC-002**: Mọi ca bắt buộc về thiếu căn cứ, lỗi và gửi lại có verdict đúng loại;
  không có lỗi kỹ thuật được trình bày như answer có căn cứ hoặc làm trùng lượt.
  Map FR-004/005.
- **SC-003**: Mỗi AC của bốn VLRA có kết quả và evidence hoặc lý do chưa chạy; chỉ
  kết luận sẵn sàng khi các AC bắt buộc đạt và không còn lỗi chặn kịch bản demo.
  Map FR-005/006.
- **SC-004**: Kịch bản chạy lại nêu đủ điều kiện/cấu hình cần thiết đã được kiểm tra;
  xác nhận nhóm chưa có được ghi rõ, không tự tạo phê duyệt. Map FR-007.

## Assumptions

- VLRA-44 nghiệm thu luồng MVP của 41/42/43; không tự thêm chức năng sản phẩm ngoài
  bốn ticket. Danh sách màn hình/kịch bản demo cụ thể phải được nhóm xác nhận khi lập plan.
- Không có ngày, môi trường hoặc người demo được chỉ định trong nội dung Jira đã cung cấp.
- Lỗi có kiểm soát/test double hỗ trợ kiểm tra nhánh lỗi nhưng phải ghi rõ; luồng
  thành công chứng minh AC thật không thay pipeline/model bằng fixture.
- Chưa chọn công cụ E2E, trình duyệt/version hoặc số lần lặp; ghi trong plan sau khi
  chốt điều kiện, không tự thêm tiêu chuẩn công nghệ hay SLA vào đặc tả.

## Scope and Dependencies

Trong phạm vi: kiểm thử/thu evidence/truy vết và báo cáo sẵn sàng demo cho luồng MVP.
Ngoài phạm vi: triển khai thay các task 41/42/43, sửa retrieval/pipeline Team 1/2,
load testing, xác nhận pháp lý toàn corpus hoặc tự triển khai production.

Phụ thuộc [VLRA-41](../001-vlra-41-rag-query/spec.md),
[VLRA-42](../002-vlra-42-fe-be-integration/spec.md),
[VLRA-43](../003-vlra-43-answer-citation-ui/spec.md), W4-Q1 và W4-D1/D2/D3 trong
[requirements.md](../requirements.md). Nguồn gốc: [Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0)
§8/§9/§10.4–10.5 và [Jira VLRA-44](https://banhvanhiep.atlassian.net/browse/VLRA-44).
[Team 3](../../../../docs/team3_fullstack/team3.md), C1–C5 và báo cáo phối hợp là thứ cấp.

Develop `3d64c4d38b93f11ac321623159f74e5202d1e953` chưa bàn giao HTTP RAG thật;
Java `HttpAiClient` rỗng, Python `service.query()` mock. Các lỗi retrieval trong
[báo cáo tuần 3](../../week-03/verification.md) cần được owner xử lý/đối chiếu trước khi
chốt readiness. Đây là kiểm tra source và evidence có sẵn, chưa là lần chạy E2E mới.

## Clarifications

### Session 2026-10-21

- Bộ VLRA-41–44 là toàn bộ nhiệm vụ tuần 4 của Team 3, chưa phân thành viên.
- Chỉ chuẩn bị đặc tả, chưa lập kế hoạch triển khai hoặc thực hiện kiểm thử.
- W4-Q1 đã chốt v2.0 ngày 23/10; thiếu service thật là dependency, không sửa thay Team 2.

### Session 2026-10-23

- Docs v2.0/Jira là nguồn gốc. Jira VLRA-44 không tự tạo xung đột transport;
  W4-Q1 là dependency từ route ở VLRA-41. Không coi JSON và SSE là hai lựa chọn đối lập.
- Phân biệt ca mock G2 và live G4 theo Docs §10.5; không suy trạng thái demo từ spec.

**Cập nhật dependency 23/10/2026:** người dùng đã chốt W4-Q1 theo v2.0; các ghi nhận chờ ở phiên trước là lịch sử. Chưa triển khai ticket này.
