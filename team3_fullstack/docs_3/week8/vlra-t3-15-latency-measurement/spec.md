# Feature Specification: VLRA-T3-15 — Đo độ trễ toàn trình

**Feature Branch**: Team3 feature branch (baseline `c62b4b4`)
**Created**: 2026-10-31
**Status**: Công cụ đã triển khai; benchmark live chờ bàn giao — xem [validation](validation.md)
**Input**: Triển khai riêng VLRA-T3-15 trong nhiệm vụ tuần8.

## Mục tiêu, phạm vi và nguồn

Người kiểm thử có thể đo độ trễ từ gửi câu hỏi đến nhận kết quả cuối, tra cứu Điều,
xác định pha Backend tốn thời gian và xuất báo cáo có thể tái lập.
Nguồn: [nhiệm vụ tuần8](../tasks.md) §2 T3-15; [ARCHITECTURE](../../../../docs/ARCHITECTURE.md) §3/§8;
[API public](../../../../docs/team3_fullstack/public-api-specification.md),
[tích hợp RAG](../../../../docs/team3_fullstack/rag-integration-specification.md).

Phạm vi: runner, phân vị, kết quả lỗi, timing bốn pha Backend, trace và báo cáo.
Ngoài phạm vi: recovery/pool acceptance T3-16; sửa Retrieval/Reranker/Article Store T3-17;
latency badge/render optimization T3-18; tạo/review/chia Golden; sửa API/schema công khai;
đo hoặc khẳng định chất lượng pháp lý của câu trả lời.

## User Scenarios & Testing

### User Story 1 — Đo và xuất kết quả minh bạch (Priority: P1)

Người kiểm thử chạy bộ câu hỏi và xem thời gian kết thúc từng lượt, các phân vị,
tỷ lệ lỗi và độ trễ tra cứu Điều trong cùng một báo cáo.

**Why this priority**: Thay phép đo tạm bằng công cụ tái lập cho nghiệm thu.
**Independent Test**: Chạy với dịch vụ mock; đối chiếu số mẫu, trạng thái và phân vị.

**Acceptance Scenarios**:
1. **Given** một bộ câu hỏi hợp lệ, **When** chạy phép đo, **Then** mỗi lượt có mã riêng, thời gian và trạng thái; báo cáo có p50/p90/p95/p99 trên mẫu thành công.
2. **Given** timeout, lỗi hệ thống hoặc stream sai, **When** chạy phép đo, **Then** ghi lượt lỗi và thời gian thực, không biến lỗi thành thiếu căn cứ hoặc bỏ khỏi tổng số lượt.
3. **Given** phản hồi thiếu căn cứ hợp lệ, **When** nhận kết quả cuối, **Then** tính là request thành công nhưng không tạo citation hoặc tự chọn văn bản khác để đo Viewer.

### User Story 2 — Đối chiếu các pha bằng trace (Priority: P1)

Người kiểm thử biết phần thời gian thuộc khởi tạo lượt, chờ AI, lưu kết quả và
kết thúc stream mà không thay đổi dữ liệu trao đổi của sản phẩm.

**Why this priority**: Chỉ số tổng chưa chỉ ra được vị trí cần tối ưu.
**Independent Test**: Đối chiếu timing cùng trace với kết quả của lượt hỏi thực.

**Acceptance Scenarios**:
1. **Given** lượt hỏi mới, **When** hoàn tất, **Then** có timing bốn pha và tổng thời gian Backend cùng mã trace; các pha không đếm trùng thời gian.
2. **Given** lỗi xảy ra trước một pha, **When** tổng hợp, **Then** pha chưa chạy được ghi là thiếu, không bịa số0.
3. **Given** replay hoặc log không đủ, **When** tổng hợp benchmark, **Then** nhận diện riêng, không coi là lượt chạy pipeline mới hoặc là báo cáo đủ timing.

### User Story 3 — Phân biệt smoke và benchmark live (Priority: P2)

Người kiểm thử dùng mock để kiểm công cụ, sau đó dùng Dev Set đã bàn giao để đo live
mà không trộn hai loại kết quả hoặc lấy fixture làm nghiệm thu model.

**Why this priority**: Hiện chưa có bộ150/Dev Set và runtime live sẵn sàng.
**Independent Test**: Đầu vào thiếu, mock hoặc dịch vụ chưa ready không được báo đạt live.

**Acceptance Scenarios**:
1. **Given** dữ liệu mock/thăm dò, **When** chạy, **Then** báo cáo gắn đúng chế độ, không kết luận nghiệm thu live.
2. **Given** Dev Set, bằng chứng phân chia và dịch vụ live ready, **When** đo đủ timing, **Then** đối chiếu p95 chat≤45000ms và tra cứu Điều≤1000ms, kèm giới hạn phép đo.
3. **Given** thiếu Dev Set, split report, timing hoặc upstream sẵn sàng, **When** chạy live, **Then** dừng/đánh dấu chưa đủ điều kiện và báo lý do; không tự tạo dữ liệu thay thế.

### Edge Cases

Đầu vào rỗng/JSON lỗi/trùng ID; Unicode tiếng Việt; kết nối lỗi; stream chỉ heartbeat;
UTF-8/frame bị cắt; error sau meta; complete sai binding/citation; dữ liệu HTTP404/503;
thiếu timing, log sai JSON hoặc trùng trace; không có mẫu thành công; warm-up lỗi;
output đã tồn tại; đường dẫn log chứa thông tin khác không được xuất nguyên dòng.

## Requirements

### Functional Requirements

- **FR-001**: Chạy trên một bộ câu hỏi được chỉ định; kiểm tra định dạng/ID/Unicode trước khi gửi; giữ nguyên dữ liệu nguồn.
- **FR-002**: Đo thời gian đơn điệu đến terminal complete/error, giới hạn toàn lượt; không retry ngầm hoặc dùng lại mã lượt gây replay.
- **FR-003**: Giữ tổng số lượt và lỗi; phân vị nearest-rank trên lượt thành công; warm-up được ghi riêng và loại khỏi phân vị chính.
- **FR-004**: Tra cứu đúng document/article từ citation nhận được hoặc fixture được khai báo ở chế độ mock; kiểm tra đủ trường/binding, không tự đổi phiên bản.
- **FR-005**: Xuất p50/p90/p95/p99 và raw timing từng mẫu, đơn vị rõ ràng; tập rỗng trả giá trị thiếu; không làm tròn trước khi tính phân vị.
- **FR-006**: Timing bốn pha khởi tạo, AI, DB persist, stream và tổng Backend cùng trace; bật theo cấu hình, không log câu hỏi, answer, API key hoặc thay contract.
- **FR-007**: Ghép timing theo trace và mã lượt; không nhận log lỗi/trùng/replay như dữ liệu hợp lệ; pha chưa chạy/mất log phải được nhận diện.
- **FR-008**: Ghi rõ chế độ, hash dữ liệu/source, cấu hình, số lượt, lỗi, độ phủ timing và giới hạn; không tự ghi đè báo cáo hoặc lộ đường dẫn cá nhân/secret.
- **FR-009**: Live dùng Dev Set từ split report đúng hash; kiểm readiness và từ chối mock được nhận diện; thiếu điều kiện hoặc timing không được kết luận đạt live.
- **FR-010**: Đối chiếu p95 chat≤45000ms và article≤1000ms; công bố đây là thời gian client API, khác thời gian render Viewer và các pha Retrieval/Rerank/LLM chưa bàn giao.

### Key Entities

- **Measurement run**: chế độ, nguồn/snapshot, cấu hình, các mẫu và tổng kết.
- **Sample**: mã dữ liệu, mã lượt, trace, outcome, thời gian, citation lookup liên quan; không cần lưu câu hỏi/đáp án.
- **Backend timing**: trace/mã lượt, outcome/replay, pha đo được hoặc thiếu.
- **Dev provenance**: split report và hash file Dev; không tự chứng minh review pháp lý.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Bộ smoke có ít nhất20 lượt hỏi và20 lookup thành công, counts/phân vị khớp dữ liệu thô; mọi lỗi được giữ trong báo cáo.
- **SC-002**: Các lượt hoàn tất mới trong phép đo tích hợp có100% timing bốn pha ghép đúng trace; trường hợp lỗi/mất log/replay bị nhận diện.
- **SC-003**: Public contract và các hành vi persistence/error/replay hiện có tiếp tục qua kiểm thử liên quan.
- **SC-004**: Không có kết quả mock/thăm dò hoặc thiếu điều kiện được báo đạt live. Benchmark live chỉ khép sau khi Dev Set/runtime bàn giao và đạt hai ngưỡng p95.

## Assumptions

- Team1 bổ sung đủ150, Team2 kiểm chứng, Team3 chỉ chia90 Dev/60 Test theo phân công đã chốt; runner không thêm nhãn vào record nguồn.
- Review dataset và snapshot do bên bàn giao xác nhận; split report chỉ chứng minh chia tập/hash.
- Timing AI Service gồm toàn bộ HTTP chờ xử lý; thời gian riêng retrieval/rerank/model chỉ thêm sau bàn giao Team2, không suy đoán từ tổng.
- HTTP lookup không bao gồm thời gian render UI; tiêu chí Viewer UI toàn tuần vẫn cần phép đo trình duyệt riêng.
- Hiện trạng kiểm tra: branch Team3c62b4b4, mock đã chạy được; Team2fa93cdf chưa tích hợp, query live chưa sẵn sàng và article fallback còn sai thứ tự Khoản.

## Clarifications

### Session 2026-10-31

Không có câu hỏi quan trọng chưa được nguồn hoặc quyết định hiện hành giải đáp.
Giữ contract public, không sửa các team khác hoặc tasks.md tổng tuần; hoàn thiện
công cụ/kiểm chứng độc lập và để mở bước benchmark live còn thiếu bàn giao.
