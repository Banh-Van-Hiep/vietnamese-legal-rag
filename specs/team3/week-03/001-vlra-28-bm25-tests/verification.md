# VLRA-28 — Verification

Ngày 19/10/2026, HEAD 5a9af42. Bàn giao đủ scope tester; chưa tự cập nhật Jira/nhóm phê duyệt.
Xem [báo cáo tuần](../verification.md) cho môi trường, hashes, lệnh, phương pháp và tổng regression.

## Kết quả

Baseline 18 tests PASS. Sau refactor5generic methods thành3mixin methods:16 methods BM25 PASS,
không phải mất kiểm tra: rank/schema/K/trim/eight-invalid được gom vào mixin, giữ tokenizer,
positive score/no-match, metadata, persistence và corpus validation. BM25 edge NFC/NFD PASS.
Evaluator9 tests PASS. Build/load/query2576 chunks và hai bộ corpus evaluation exit0.

| Dataset | Scored/total | Recall5 | Recall20 | MRR10 | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline Team 2 | 30/30 | 0.496842 | 0.738160 | 0.666667 | 2.220 | 4.635 |
| Supplement draft | 6/8 | 0.833333 | 0.833333 | 0.833333 | 1.655 | 138.707 |

## Ma trận yêu cầu/nghiệm thu

| Yêu cầu | Bằng chứng | Kết quả |
| --- | --- | --- |
| FR-001 | Baseline 18 PASS, inventory/refactor map | Đã kiểm kê/tái sử dụng |
| FR-002 | BM25PersistenceTest + CLI build/load/query | PASS |
| FR-003 | Mixin tám input/K1/20/50/4000 chars | PASS |
| FR-004 | TokenizerTest, NFC/NFD edge, positive score/no-match | PASS |
| FR-005 | Mixin schema/rank/unique/finiteness + corpus evaluator | PASS trên ca đã chạy |
| FR-006 | Evaluator so metadata/content với corpus/hash | PASS provenance; applicability chưa review |
| FR-007 | 38dòng kết quả trong CSV/JSON, expected cố định trước chạy | Đã đo; có MISS/PARTIAL cần review |
| FR-008 | Input/corpus/index error/no-match cases | PASS |
| FR-009 | JSON/JUnit/Markdown, environment/hashes/commands/issues | Đủ evidence |
| FR-010 | Source-preservation check, không production fix | Đạt ranh giới |
| FR-011 | Evaluator9 tests, Recall/MRR/latency/denominators/error cases | PASS công cụ; metric như bảng |
| FR-012 | Mixin cùng dùng BM25/Dense, giữ checks đặc thù | Đã triển khai/kiểm thử |
| FR-013 | Validator T2 + độc lập,30 baseline/8 supplement, sidecar38 IDs | PASS cấu trúc/ID; draft legal review |
| SC-001..004 | Mọi FR có evidence/verdict, counts khớp, issue/repro | Đủ công việc kiểm thử và bàn giao |

## Giới hạn và lỗi

[Issue list](issues.md): relevance/nhãn B-Q01, khả năng so sánh lần cũ B-L01,
unit applicability B-L02;2 ERROR preprocess R-P01 ngoài scope được ghi/bàn giao.
Không đặt Recall threshold BM25, không tuning hoặc sửa expected theo output.
Chi tiết các ca lỗi Dense không dùng để phủ định kết quả BM25; xem báo cáo VLRA-29.
Raw logs trong .local/team3/retrieval-audit-20261019/; bằng chứng chia sẻ ở ../evidence/.
