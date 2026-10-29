# Team 3 — Nhiệm vụ và nghiệm thu theo tuần

**Cập nhật:** 29/10/2026. Chỉ giữ bộ nhiệm vụ tuần hiện hành; không lưu các bản nhiệm vụ cũ.
Đặc tả chung của dự án/phân hệ nằm trong [docs/](../../docs/README.md).

## Bộ nhiệm vụ hiện hành

| Tuần | Nhiệm vụ | Báo cáo nghiệm thu (ngày ghi trong biên bản) |
| --- | --- | --- |
| 4 | [tasks.md](week4/tasks.md) | [verification.md](week4/verification.md) — 29/10: đủ điều kiện G1 nội bộ theo kiểm chứng và xác nhận nhóm; schema mới đạt76/76, HTTP12/12; bàn giao bằng commit local; chưa push/PR |
| 5 | [tasks.md](week5/tasks.md) | [verification.md](week5/verification.md) — 29/10: VLRA22/23/T3-06 đủ điều kiện chốt kỹ thuật mock; VLRA24 đã bàn giao50 mẫu (49/1), Team2 phụ trách kiểm chứng |
| 6 | [tasks.md](week6/tasks.md) | [verification.md](week6/verification.md) — 29/10: Backend94/94, FE72/72, E2E10/10;09/10 đạt kỹ thuật; G3 chờ runtime index và endpoint article Team2 |
| 7 | [tasks.md](week7/tasks.md) | [verification.md](week7/verification.md) — idempotency và Viewer mock đạt; thiếu dataset v1 và G4 live |
| 8 | [tasks.md](week8/tasks.md) | [verification.md](week8/verification.md) — mock 5 phiên/50 query đạt; chưa đủ benchmark live và tối ưu frontend |

Các kết quả là kiểm chứng kỹ thuật của source hiện tại, không thay phê duyệt nhóm,
không cập nhật trạng thái Jira và không chứng minh RAG thật từ một response mock.
Backend giữ Java 25 / Spring Boot 4.1.1 theo quyết định 28/10/2026;
quy chuẩn tại [CODING_CONVENTIONS.md](../../docs/CODING_CONVENTIONS.md).

## Căn cứ áp dụng

[ARCHITECTURE.md](../../docs/ARCHITECTURE.md) là đặc tả chính hiện hành;
[CODING_CONVENTIONS.md](../../docs/CODING_CONVENTIONS.md) quy định cách thực hiện/DoD;
`weekN/tasks.md` phân rã nhiệm vụ theo baseline. Jira là công cụ quản lý/đối chiếu,
không loại bỏ tiêu chí hiện hành chỉ vì mô tả ticket cũ ngắn hơn.
G1–G4 là mốc trong kế hoạch tuần; các chỉ tiêu chất lượng ở ARCHITECTURE §8.2.B vẫn
phải kiểm riêng. Khi có sai lệch schema/baseline/nhiệm vụ thì ghi nhận và thống nhất,
không tự sửa API hoặc biến kết quả mock thành nghiệm thu live.

## Quy trình thực hiện nhiệm vụ

1. Tiếp nhận Jira vào `weekN/tasks.md`: mã gốc, phụ trách, mục tiêu, DoD và phụ thuộc.
   Mã nội bộ `VLRA-T3-*` không tự thay mã Jira thật; số tuần theo lịch học phần đã ghi trong task.
2. Đọc phần kiến trúc/API/quy chuẩn liên quan trong `docs/`; đối chiếu code/config/test
   trước khi giao việc, không suy tiến độ từ số file hoặc mô tả thiết kế.
3. Mỗi task khi bắt đầu triển khai phải có bộ Spec Kit tại `weekN/<jira>-<chuc-nang>/`,
   cập nhật bộ đã có để tránh tạo trùng, và thực hiện từng bước theo quy trình
   `$speckit-specify` → `$speckit-clarify` → `$speckit-plan` → `$speckit-tasks`
   → `$speckit-analyze` → sửa vấn đề → `$speckit-implement`.
   `SPECIFY_FEATURE_DIRECTORY` trỏ đúng thư mục nhiệm vụ, không trỏ thư mục tổng tuần.
4. Giữ spec/plan/tasks/quickstart và tài liệu bổ trợ trong cùng bộ nhiệm vụ;
   schema/interface chung tham chiếu phiên bản trong `contracts/`, không tạo chuẩn khác.
5. Lưu kết quả validate của task tại **`weekN/<jira>-<chuc-nang>/validation.md`**:
   kết quả analyze, các vấn đề đã sửa/còn mở, lệnh build/test/schema và expected/actual,
   trạng thái pass/fail/chưa chạy, môi trường/source và giới hạn mock/live.
   Checklist, analysis và evidence chia sẻ được đặt trong cùng bộ task thuộc tuần đó;
   loại secret/dữ liệu cá nhân, không đưa cache/build/browser profile vào tài liệu.
   Không tạo thêm bản validate hoặc bộ Spec Kit trong `specs/`.
6. Báo cáo nghiệm thu tổng hợp tại **`weekN/verification.md`**, dẫn kết quả validate
   của từng task thay vì chép lại toàn bộ, đối chiếu từng task/DoD,
   ghi expected/actual, source/commit, lệnh, môi trường, evidence, giới hạn và việc cần làm.
   Chỉ tổng hợp lên Jira/gate khi đủ bằng chứng; mock và live được kết luận riêng.

Ví dụ bố trí khi triển khai một task mới (không tạo trước thư mục rỗng):

```text
team3_fullstack/docs_3/weekN/
├── tasks.md
├── <jira>-<chuc-nang>/
│   ├── spec.md
│   ├── plan.md
│   ├── tasks.md
│   ├── validation.md
│   └── ...                 # analysis, checklist, quickstart và evidence phù hợp
└── verification.md         # Tổng hợp nghiệm thu tuần
```

Analyze chỉ báo vấn đề; sửa vấn đề ở bước kế tiếp rồi kiểm tra lại trước implement.
Chỉ đánh dấu task hoàn thành sau khi đã thực hiện và kiểm chứng đủ tiêu chí.

Không tự hạ tiêu chí tuần để khớp implementation. Lượt nghiệm thu chỉ sửa tài liệu,
không thực hiện các phần code còn thiếu hoặc sửa dataset để đổi kết quả thành PASS.
