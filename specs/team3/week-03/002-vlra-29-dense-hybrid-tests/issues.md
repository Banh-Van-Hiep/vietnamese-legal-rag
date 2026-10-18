# VLRA-29 — Defects và dependency

Ba defect dưới được tái hiện bằng tests/test_retrieval_edge_cases.py và giữ FAIL;
không dùng expectedFailure/skip để chuyển trạng thái. Production chưa sửa.

| ID | Severity | Test tái hiện | Expected | Actual | Owner |
| --- | --- | --- | --- | --- | --- |
| D-01 | MEDIUM | DenseIntegrityTests.test_connect_rejects_changed_query_prefix | Query embedding config phù hợp manifest hoặc bị từ chối | Prefix khác vẫn connect được; chưa đánh giá ảnh hưởng semantic bằng model thật | Team 1 |
| D-02 | HIGH | DenseIntegrityTests.test_connect_rejects_duplicate_physical_point_for_same_chunk | Từ chối collection có point trùng chunk_id | So set ID nên bỏ sót duplicate; query thực trả5 rows/4 IDs duy nhất | Team 1 |
| D-03 | LOW | EmbeddingEdgeTests.test_large_finite_vectors_never_silently_become_zero | Unit vector hữu hạn hoặc lỗi rõ | Norm float32 overflow, output[0,0] | Team 1 |

D-01: manifest query_prefix='query: ', embedder.query_prefix='different: ', name/rev/dim
vẫn bằng nhau; connect không raise. Tác động là thiếu integrity guard, không tuyên bố
đã quan sát câu trả lời pháp lý sai. Owner cần đối chiếu cả passage prefix khi sửa.
D-02: build4 chunks, upsert point UUID khác với payload chunk_id cũ; count5, connect nhận,
retrieve trả duplicate. Cần kiểm physical count/mapping, không chỉ set(payload.chunk_id).
D-03: input[3e38,3e38] đều hữu hạn nhưng norm overflow. Đây là ca cực trị, không phải
bằng chứng model mặc định thường sinh vector bất thường.

Chạy lại: python scripts/run_retrieval_tests.py --pattern test_retrieval_edge_cases.py
--output-dir .local/team3/retrieval-audit-20261019/repro (dùng venv trong quickstart).
Chi tiết traceback: ../evidence/unit-results.json; số liệu: dense-diagnostics.json.

| Dependency | Trạng thái | Điều kiện tiếp tục |
| --- | --- | --- |
| Dense model thật | BLOCKED, chưa tải/load weights | Model revision dea33aa1ab339f38d66ae0a40e6c40e0a9249568; FP32 weights ít nhất2,12 GiB, máy cònkhoảng 1,1 GB RAM |
| Qdrant server | BLOCKED | Docker version endpoint lỗi500 sau khi thử start; cần daemon/server và image version thống nhất |
| Hybrid runtime | BLOCKED | Owner VLRA-27 bàn giao implementation/factory + candidate100 API; không nới public K50 |

Đã cài dependency CPU trong venv riêng. Đã dừng Docker Desktop vừa khởi động sau lần
kiểm tra để trả môi trường về trạng thái ban đầu. Không giữ Qdrant container/service.
Phép tính RRF chỉ là oracle bàn giao, xem hybrid-handoff.md; không là runtime PASS.
