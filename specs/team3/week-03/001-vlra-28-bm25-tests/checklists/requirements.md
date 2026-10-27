# Specification Quality Checklist: VLRA-28 — Kiểm thử BM25

**Purpose**: Review chất lượng đặc tả trước clarify/plan.
**Created**: 2026-10-19. **Feature**: [spec.md](../spec.md).
**Marker semantics**: [x] là đã review yêu cầu, không có nghĩa kiểm thử đã chạy/đạt.

## Content Quality

- [x] Không quy định cách viết implementation mới; tên module/schema chỉ là nguồn/inventory.
- [x] Tập trung giá trị kiểm thử độc lập và bàn giao lỗi cho người phụ trách.
- [x] Diễn đạt được luồng/nghiệm thu cho người tổng hợp; thuật ngữ BM25/Top-K/IDs là phạm vi Jira.
- [x] Đủ User Scenarios, Requirements, Success Criteria và Assumptions theo template được resolve.

## Requirement Completeness

- [x] Không còn marker NEEDS CLARIFICATION; đầu vào query/nhãn phải được chốt trước chạy.
- [x] FR-001..010 kiểm tra được, phân biệt yêu cầu với source hiện có.
- [x] SC-001..004 có cách đối chiếu và trạng thái không đạt/chưa chạy cụ thể.
- [x] Kết quả đo là evidence/ID/trạng thái, không phụ thuộc chọn framework hoặc thêm công nghệ.
- [x] Có acceptance scenario cho index/query, corpus thật và lỗi/report.
- [x] Có Unicode/Top-K/score/index/corpus error edge cases.
- [x] Phạm vi kiểm thử được giới hạn; không tự sửa production hoặc benchmark mở rộng.
- [x] Dependency/nhãn/snapshot và giới hạn applicability được ghi rõ.

## Feature Readiness

- [x] FR truy vết tới story và measurable outcome.
- [x] Các story kiểm tra độc lập, bao phủ đầu ra VLRA-28.
- [x] Success Criteria mô tả outcome cần chứng minh, chưa tự gán PASS.
- [x] Không lẫn kế hoạch viết code với yêu cầu; source paths không làm thành lựa chọn thiết kế mới.

## Notes

Review vòng 1: 16/16 tiêu chí chất lượng đạt. Không xác nhận pháp lý hoặc implementation.
18 hàm test hiện có mới được đọc; chưa chạy, có thể skip khi thiếu dependency.
Thu thập/cố định corpus hash, query/nhãn và môi trường tại clarify/plan trước implement.
Không có extensions.yml, không có before/after_specify hook cần thực thi.
