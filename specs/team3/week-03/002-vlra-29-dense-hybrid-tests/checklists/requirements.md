# Specification Quality Checklist: VLRA-29 — Kiểm thử Dense/Hybrid

**Purpose**: Review chất lượng đặc tả trước clarify/plan.
**Created**: 2026-10-19. **Feature**: [spec.md](../spec.md).
**Marker semantics**: [x] là đã review yêu cầu; không có nghĩa Dense/Hybrid đã chạy hoặc PASS.

## Content Quality

- [x] Không quyết định implementation mới; thuật toán RRF và tên score là nội dung Jira/thiết kế kế thừa.
- [x] Giá trị người dùng là kiểm chứng retrieval và bàn giao sai khác có thể tái hiện.
- [x] Luồng/outcome mô tả cho người kiểm thử/tổng hợp, tránh chỉ dẫn cách viết production.
- [x] Đủ các phần mandatory của template đã resolve.

## Requirement Completeness

- [x] Không còn marker NEEDS CLARIFICATION; model/corpus/module là dependency ghi cụ thể trước plan.
- [x] FR-001..012 tách Dense/Hybrid, model giả/thật và oracle/production.
- [x] SC-001..005 đo được bằng mapping/evidence/IDs/verdict.
- [x] Outcome không áp framework mới, coverage gate hoặc benchmark threshold tự đặt.
- [x] Có acceptance scenario cho vector, fusion, corpus và dependency chưa đủ.
- [x] Edge cases bao gồm vector lỗi, index/version, score, tie/dedup, nhánh rỗng/lỗi.
- [x] Giới hạn kiểm thử; không tự triển khai module Hybrid đang thiếu.
- [x] Dependency/assumptions, source vs requirements và việc có thể tiếp tục Dense được ghi rõ.

## Feature Readiness

- [x] Mọi FR có luồng/outcome để xây case/evidence ở bước plan/tasks.
- [x] Story kiểm tra độc lập; Hybrid runtime là dependency, không bị che bằng oracle test.
- [x] Mục tiêu bàn giao kiểm thử tách khỏi kết luận module hết lỗi/đạt chất lượng.
- [x] Không đưa kế hoạch viết code vào spec; đường dẫn source phục vụ đối chiếu hiện trạng.

## Notes

Review vòng 1: 16/16 tiêu chí chất lượng đạt. Không phải 16 test runtime PASS.
Hiện có 22 hàm test Dense đọc từ source; chưa chạy. Model thật/Hybrid còn cần đầu vào.
Clarify xác định corpus/query labels, tài nguyên model/revision và dependency Hybrid;
phần không đủ phải giữ trạng thái chưa kiểm chứng, không loại khỏi phạm vi để báo DONE.
Không có extensions.yml, không có before/after_specify hook cần thực thi.
