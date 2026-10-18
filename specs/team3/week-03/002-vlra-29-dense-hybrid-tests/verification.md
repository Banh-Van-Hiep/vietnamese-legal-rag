# VLRA-29 — Verification

**Trạng thái: PARTIAL, chưa nghiệm thu.** Model thật và Hybrid chưa thực thi;3 lỗi còn OPEN.
[Report tuần](../verification.md) giữ môi trường/hash/commands/counts và giới hạn chung.

## Kết quả thực tế

Baseline Dense 22/22 PASS. Sau refactor3generic methods thành3mixin methods vẫn22 PASS.
Bộ edge chung9 tests:6 PASS/3 FAIL (gồm1BM25 edge); những FAIL đều Dense/integrity/embedding.
Cosine vector kiểm soát Q=[3,4], D=[[3,4],[4,3]]: expected[1,0.96], actual
[1.0000000238418578,0.9600000295639035], trong sai số1e-6.
Normalization/NFC/prefix adapter dùng model double; không gọi model provider.

## Ma trận yêu cầu/nghiệm thu

| Yêu cầu | Bằng chứng | Kết quả |
| --- | --- | --- |
| FR-001 | Baseline 22 và profile labels trong JSON | Đã phân lớp/kiểm kê |
| FR-002 | EmbeddingEdgeTests + vector geometry | PARTIAL:3 PASS, norm overflow FAIL D-03 |
| FR-003 | DensePersistence/Integrity tests | PARTIAL: prefix/duplicate guard FAIL D-01/D-02 |
| FR-004 | Mixin healthy fixture + duplicate-point diagnostics | Healthy PASS; corrupted collection FAIL unique IDs D-02 |
| FR-005 | dense-real.json, model metadata/RAM/server | BLOCKED, chưa tải/load model |
| FR-006 | rrf-oracle.json exact fractions | Reference sẵn; runtime BLOCKED |
| FR-007 | Handoff dedup/rank/tie cases | Runtime BLOCKED |
| FR-008 | Manifest/query-dim/error tests + handoff | Dense có PASS/FAIL như issues; Hybrid BLOCKED |
| FR-009 | Dense controlled-vector scores; corpus/model run chưa có | PARTIAL/BLOCKED |
| FR-010 | JSON/JUnit/Markdown/counts/issues | Đủ báo cáo thực tế |
| FR-011 | Hybrid status/report không giả PASS | Đạt quy tắc dependency |
| FR-012 | Source hashes và không sửa production | Đạt ranh giới |
| FR-013 | Evaluator/mixin/golden tái dùng, metric tests PASS | Công cụ sẵn; Dense/Hybrid benchmark BLOCKED |
| FR-014 | hybrid-handoff.md timeout5s/version/candidates/interface | Handoff xong; runtime BLOCKED |
| SC-001/002 | Mapping/counts/reproduction | Đủ minh bạch bàn giao partial |
| SC-003..005 | Profile/IDs/oracle có chứng cứ; real/runtime thiếu | Chưa đủ nghiệm thu toàn VLRA-29 |

## Còn mở

T005: máy đủ RAM để load FP32 model revision đã pin và Qdrant server/image thống nhất.
T007: owner VLRA-27 bàn giao runtime Hybrid/factory, candidate100 API giữ publicK50.
D-01/D-02/D-03: Team 1 review và sửa theo phạm vi riêng; không tự sửa production hoặc
đánh expectedFailure để che test đỏ. Chi tiết tại [issues.md](issues.md),
[handoff](hybrid-handoff.md), [diagnostics](../evidence/dense-diagnostics.json).
Raw logs local, JSON/JUnit chia sẻ ở ../evidence/. Không commit/push/cập nhật Jira.
