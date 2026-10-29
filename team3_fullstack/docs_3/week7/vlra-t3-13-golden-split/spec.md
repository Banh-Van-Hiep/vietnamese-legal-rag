# Feature Specification: Phân chia Golden Dataset v1 — T3-13

**Ngày:**29/10/2026. **Trạng thái:** triển khai công cụ theo phạm vi đã làm rõ.
Nguồn: [task tuần7](../tasks.md), [ARCHITECTURE](../../../../docs/ARCHITECTURE.md) §8.2.A.

## Clarifications

### Session 2026-10-29

- Người dùng chọn chờ dữ liệu đã kiểm chứng, không tạo thêm câu dự thảo.
- Người dùng xác nhận Team1 bổ sung đủ150 câu ở tuần7; Team3 chỉ thực hiện phân chia.
  Team2 phụ trách kiểm chứng nội dung; việc phê duyệt/freeze chính thức ngoài công cụ này.
- Phân tầng theo expected_status,90 Dev/60 Test. Quy trình không tự sửa tỷ lệ đầu vào
  thành75/25 hoặc thay nhãn; báo thống kê để các team kiểm tra trước khi bàn giao.

## User Scenarios & Testing

### User Story 1 — Chia tập tái lập được (Priority P1)

Người điều phối nhận150 mẫu từ Team1 đã qua Team2 kiểm chứng, chia90/60 giữ nguyên
record và phân bố hai trạng thái gần với đầu vào nhất. Cùng dữ liệu/seed phải cho
cùng kết quả, không phụ thuộc thứ tự record đầu vào.

Acceptance:150 record hợp lệ →90 Dev+60 Test; hợp hai tập bằng đầu vào, không trùng
ID/câu hỏi đã chuẩn hóa và không record nào bị sửa/mất/nhân bản.

### User Story 2 — Bàn giao có thể đối chiếu (Priority P2)

Người nhận kiểm tra SHA-256 nguồn/hai tập và thống kê phân tầng mà không nhầm kết
quả chia tập với việc nhóm đã phê duyệt hoặc đóng băng dataset.

Acceptance: xuất2 tập và báo cáo chia tập có seed/count/status/hash; không ghi tên,
email, đường dẫn người dùng hoặc tự xác nhận review/freeze. Giữ nguyên metadata nguồn.

### User Story 3 — Từ chối đầu vào hoặc ghi đè sai (Priority P1)

Thiếu150 mẫu, trùng ID/câu hỏi, thiếu field/sai enum/type hoặc sai logic chunk/status
phải báo lỗi dễ kiểm tra. Output đã tồn tại không được ghi đè.

Acceptance: nguồn50 hiện tại bị từ chối và không sinh file release. Các dữ liệu lỗi
không để lại output dở; không sửa nguồn hoặc file do team khác quản lý.

### Edge Cases

112/38 hoặc113/37 được làm tròn phân tầng vẫn đủ90/60. Stratum có1 mẫu không thể ở
cả2 tập: không nhân bản, ghi cảnh báo. Chỉ1 trạng thái vẫn được chia và ghi cảnh báo
chất lượng đầu vào cho Team2, không tự tuyên bố đạt75/25. Không phát hiện paraphrase
bằng so chuỗi; review trùng ý thuộc Team2. Record ngoài chuẩn bị từ chối, không tự sửa.

## Requirements

- FR-001: nhận đúng150 bản ghi có đủ8 field hiện hành, giữ cả field bổ sung nếu có, UTF-8/NFC; kiểm type/enum/chunk logic.
- FR-002: chia90/60 theo expected_status với sai số làm tròn nguyên tối thiểu, không rò ID/câu hỏi trùng giữa hai tập.
- FR-003: giữ nguyên toàn bộ nội dung/metadata/ID; không thêm câu hoặc đổi nhãn/căn cứ.
- FR-004: cùng seed và tập record tạo cùng2 output, kể cả đảo thứ tự đầu vào.
- FR-005: ghi SHA-256 bytes nguồn/hai output, seed/count/phân bố/warnings; ghi rõ split_only, không phê duyệt/freeze.
- FR-006: input lỗi/output tồn tại bị từ chối, không ghi đè; nguồn luôn giữ nguyên.
- FR-007: không sửa code/data/schema Team1/2; công cụ nằm ở Team3, không thêm dependency.

### Key Entities

Nguồn150 mẫu; Dev90; Test60; báo cáo chia tập có provenance và thống kê. Schema8
field của record giữ nguyên; báo cáo kỹ thuật tách riêng khỏi dữ liệu.

## Success Criteria

- SC-001: bộ kỹ thuật150 mẫu cho90/60, không mất/sửa/trùng record, phân tầng đúng làm tròn.
- SC-002: cùng seed cho output tái lập; SHA-256 kiểm lại đúng100%.
- SC-003: ca thiếu mẫu/duplicate/sai kiểu/enum/ghi đè bị từ chối, không sửa nguồn.
- SC-004: hiện chưa có150 mẫu thật nên không tự xuất/chốt Dev/Test thật; hồ sơ nêu
  việc còn chờ Team1/2 và lệnh chạy khi nhận đủ dữ liệu.

## Scope and Dependencies

Chỉ triển khai phần chia tập của Team3 theo chỉ đạo mới. Không sinh/review đáp án
pháp luật, sửa validator enum đã đúng, benchmark, thu chữ ký hoặc freeze thay các team.
Nguồn thật hiện có50; Team1 bàn giao150, Team2 kiểm chứng trước khi sử dụng kết quả.
