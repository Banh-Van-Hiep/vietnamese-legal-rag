# Tuần 3 — Phân rã nhiệm vụ kiểm thử retrieval

**Tiếp nhận:** 19/10/2026. **Nguồn:** [requirements.md](requirements.md).
Hồ sơ Team 3, phạm vi kiểm thử Team 1 theo phân công người dùng. Không đổi owner retrieval.

## 1. Nhiệm vụ và phụ thuộc

| Bộ task | Jira | Phạm vi | Phụ thuộc | Hiện trạng hồ sơ |
| --- | --- | --- | --- | --- |
| [001-vlra-28-bm25-tests](001-vlra-28-bm25-tests/spec.md) | VLRA-28 | Kiểm thử index/query/Top-K/chunk_id BM25, corpus thật, error và report | Thiết kế/contract, dependency và corpus có nhãn đối chiếu | Đã kiểm thử/bàn giao, xem verification.md; chưa tự cập nhật Jira |
| [002-vlra-29-dense-hybrid-tests](002-vlra-29-dense-hybrid-tests/spec.md) | VLRA-29 | Embedding/vector/cosine; RRF/dedup/rank; error và report | Dense/model hoặc test double có nhãn; module Hybrid còn thiếu | Đã kiểm thử Dense giả,3 lỗi; model thật/Hybrid BLOCKED; chưa nghiệm thu |

Chỉ số 001/002 là hồ sơ của tuần 3; dùng mã Jira trong tên để phân biệt với T01/T02
Backend của tuần 2. Không đánh số lại T01–T06 đã có.

BM25 và phần Dense có thể kiểm thử độc lập sau khi thống nhất corpus/contract.
Chạy một bộ test không phải điều kiện để bắt đầu bộ còn lại; không chạy đồng thời
các tác vụ ghi chung index/alias hoặc sử dụng chung tài nguyên mà chưa cô lập.
Hybrid phụ thuộc hai danh sách candidate tương thích snapshot và module thật;
không chặn việc đọc/kiểm thử BM25 hoặc Dense độc lập.

## 2. Quy trình thực hiện

1. Clarify từng spec với nguồn: corpus/nhãn, profile Dense thật/giả và dependency Hybrid.
2. Plan dựa vào test hiện có, chỉ bổ sung phần thiếu, ghi môi trường và component tác động.
3. Sinh tasks.md riêng cho từng bộ task theo dependency; file hiện tại chỉ là phân rã cấp tuần.
4. Analyze → sửa vấn đề → implement/kiểm thử theo từng bộ, ghi expected/actual và lỗi.
5. Đối chiếu từng AC rồi tổng hợp VLRA-28/VLRA-29 tại verification của tuần khi có evidence.

Danh sách triển khai nằm trong tasks.md từng bộ; trạng thái theo evidence. Checklist
requirements.md trong mỗi bộ chỉ kiểm tra **chất lượng đặc tả**, không chứng minh test PASS.

## 3. Nơi đặt kết quả khi thực hiện

Spec/plan/tasks, case mapping, verification và issue list của nhiệm vụ nằm trong bộ
task tương ứng. Log/index/vector/raw outputs tạm phải được cô lập và ignore; vị trí
cụ thể được chốt ở plan. Không sửa corpus/index đang phục vụ hoặc ghi output vào docs.
Không tự commit/push hoặc dùng kết quả lịch sử của thành viên khác làm lần kiểm chứng mới.

## Kết quả thực thi19/10

Xem [verification.md](verification.md): retrieval53 PASS/3 FAIL, regression76 PASS/3 FAIL/2 ERROR; VLRA-28 bàn giao đủ scope tester, VLRA-29 còn T005/T007.
