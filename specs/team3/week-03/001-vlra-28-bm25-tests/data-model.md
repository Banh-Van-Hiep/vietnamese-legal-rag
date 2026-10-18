# Evidence data model

Golden giữ tám field validator T2; ID/question duy nhất, answered có gold IDs tồn tại,
insufficient_context có gold rỗng và lý do. Review pháp lý tách khỏi cấu trúc.
Sidecar: id → legal_reference | everyday | out_of_corpus, quy tắc công bố trước đo.
Run: timestamp UTC, HEAD/dirty, source hashes, môi trường/packages, method/index/model/revision.
Case: id/question/group, expected IDs, actual IDs/rank/score, Recall5/20/RR10 hoặc null,
elapsed_ms, status/error. Query lỗi không có metric thành công.
Aggregate: denominator, error count, empty-gold excluded count, macro metrics,
latency p50/p95 nội suy tuyến tính trên successful retrieve. Báo nhóm và toàn bộ.
RetrievalOutput v0.1: question trim 1–4000 code point; K nguyên 1–50, không bool;
rank 1..N, ID duy nhất, score hữu hạn/giảm không tăng. Giữ metadata nguồn.
Issue: ID/severity/repro/expected/actual/impact/owner/evidence và trạng thái OPEN/BLOCKED.
