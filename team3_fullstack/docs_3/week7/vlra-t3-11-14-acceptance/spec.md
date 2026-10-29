# Đặc tả nghiệm thu tuần7 — VLRA-T3-11–14

**Đối chiếu:**29/10/2026. [Tasks tuần7](../tasks.md),
[ARCHITECTURE](../../../../docs/ARCHITECTURE.md) §3/6/8.2,
[thiết kế hội thoại](../../../../docs/team3_fullstack/conversation-design.md),
[thiết kế FE](../../../../docs/team3_fullstack/frontend-design.md).

## Mục tiêu và phạm vi

Nghiệm thu implementation hiện có: idempotency IDEM01–12, Viewer/IDs/404/nguồn an
toàn/responsive/thời gian mở; kiểm điều kiện Golden v1 và G4. Lượt audit không sửa app/test,
không làm thay Team1/2, không tự sinh câu hoặc freeze dữ liệu. T3-13 nay có bộ triển khai riêng được dẫn bên dưới.

## Clarify từ quyết định và nguồn

- Phân công mới29/10: Team1 đủ150, Team2 kiểm chứng, Team3 chỉ chia90/60 và xuất
  split report, không phê duyệt/freeze. [Spec riêng T3-13](../vlra-t3-13-golden-split/spec.md).
- IDEM matrix kiểm hành vi, không buộc tạo thêm lớp12 test trùng với suite có sẵn.
  Được dùng lại evidence nếu source hash khớp, ghi rõ ngày chạy và không gọi chạy mới.
- Lookup thật/nguồn nhà nước/G4 chờ bàn giao; fixture chỉ chứng minh cơ chế UI/mock.
  Không coi hiệu năng mock là p95 production/corpus thật.
- Recovery định kỳ còn thiếu là backlog Team3 theo baseline; direct recover test
  không chứng minh scheduler. Không sửa trong lượt nghiệm thu hoặc gán cho Team1/2.

## Tiêu chí nghiệm thu

- AC11: IDEM01–12 có bằng chứng tương ứng, state/snapshot/replay và concurrent DB
  không tạo thêm cặp message/AI call. Chỉ đánh dấu theo test/source đã đối chiếu.
- AC12: Viewer đúng nguyên văn/IDs/version,404/HTTPS target+rel an toàn; drawer không
  tràn ngang ở360/768px, Escape/focus hoạt động. Đo click→content ít nhất20 lần trong
  môi trường mock, ghi median/p95 và giới hạn; độ trễ thật giữ trạng thái chờ.
- AC13: theo phạm vi T3-13 mới, tool chia150→90/60 giữ record và phân tầng trạng thái,
  có SHA256/seed/split_only. Nguồn thật do Team1/2 bàn giao, không tự tạo hoặc freeze.
- AC14: Demo live P0/citation/Viewer, insufficient, replay UUID cùng ảnh/video/phê duyệt
  G4. Mock hoặc ready503 không đạt; không đổi API và không hạ gate.

## Phụ thuộc và ngoài phạm vi

Team1 bàn giao index/snapshot/article; Team2 bàn giao live query/article và kết quả
review Golden. Team3 chia tập/kiểm tích hợp sau bàn giao. Không triển khai retrieval/LLM,
không chốt chất lượng pháp lý hoặc đổi tiêu chí nguồn bằng validator PASS.
