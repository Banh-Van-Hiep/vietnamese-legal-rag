# Báo cáo kiểm thử tuần 3 — VLRA-28 và VLRA-29

**Ngày kiểm tra:** 21/10/2026, Asia/Saigon. **Nhóm kiểm thử:** Team 3 phối hợp Team 1.
**Kết luận:** Chưa đạt nghiệm thu. Hybrid có 3 smoke test PASS; D-01/D-02/D-03
và lỗi preprocess vẫn tồn tại; phát hiện thêm B-01 làm sai cấu trúc response BM25.

## Phạm vi và môi trường

**Snapshot:** `716f4b94d5a1225fd7fbcfea950a008d04c36197`, nhánh `feature/team3/tuan`.
Mục đích: xác nhận Hybrid mới và chạy lại các lỗi đã báo trên source sau merge.
Dùng venv Python 3.12.15 và các test hiện có; không sửa production, test source,
corpus hoặc contract. Báo cáo phản ánh lần chạy trên snapshot này; không sửa artifact khi cập nhật nội dung Markdown.

Môi trường: Windows 11; Python 3.12.15; bm25s 0.3.14; underthesea 9.5.0;
numpy 2.5.4; qdrant-client 1.19.1; jsonschema 4.26.0. Dense unit dùng
FakeEmbedder và Qdrant in-memory; chưa kiểm chứng model thật hoặc Qdrant server.

Căn cứ yêu cầu: nội dung VLRA-28/VLRA-29 được giao, các thiết kế BM25/Dense/Hybrid
trong `docs/team1_data/`, `contracts/v0.1/CONTRACT.md` và
`contracts/v0.1/retrieval_output.schema.json`. Code là hiện trạng; test/evidence mới
là căn cứ kết luận đã chạy. Toàn bộ regression ngoài retrieval chưa được chạy lại;
preprocess được kiểm tra riêng để xác nhận lỗi đã báo.

## Kết quả thực thi

| Phạm vi | Kết quả ngày 21/10 | Giới hạn |
| --- | --- | --- |
| Bộ retrieval hiện có | 56 test methods: **47 PASS / 4 FAIL / 5 ERROR / 0 SKIP** | JSON runner đếm trạng thái theo method; unittest log có 7 error events do subtests. Ba test Hybrid dạng hàm không được discovery này tự thu thập. |
| D-01/D-02/D-03 chạy riêng | **0 PASS / 3 FAIL / 0 ERROR / 0 SKIP** | Đây là ba ca thuộc bộ 56 ở trên; không cộng lại để tăng test count. |
| Ba test Hybrid đi kèm module mới | **3 PASS / 0 FAIL / 0 ERROR / 0 SKIP** | Gộp kết quả, lỗi một nhánh và timeout; dùng fake branches, chưa phải tích hợp BM25/Dense thật. |
| Preprocess chạy riêng | **1 PASS / 0 FAIL / 2 ERROR / 0 SKIP** | Vẫn lỗi `chunk_document` không tồn tại; ngoài phạm vi retrieval. |

Ba test trong `tests/test_hybrid_retrieval.py` được viết dạng hàm, trong khi runner
hiện dùng `unittest` discovery. Đã gọi riêng chúng bằng `unittest.FunctionTestCase`
qua harness local vì venv không có pytest; không sửa hoặc chuyển đổi file test.
Không coi việc suite discovery không thu thập các hàm này là Hybrid đã được kiểm tra.

## Các lỗi còn tồn tại

| ID | Ca tái hiện | Expected | Actual sau merge | Trạng thái |
| --- | --- | --- | --- | --- |
| D-01 — MEDIUM | `DenseIntegrityTests.test_connect_rejects_changed_query_prefix` | Từ chối kết nối khi query prefix không khớp manifest | Không raise `RetrievalUnavailableError` | **OPEN**, chưa sửa |
| D-02 — HIGH | `DenseIntegrityTests.test_connect_rejects_duplicate_physical_point_for_same_chunk` | Từ chối collection có nhiều point cùng `chunk_id` | Không raise `RetrievalUnavailableError` | **OPEN**, chưa sửa |
| D-03 — LOW | `EmbeddingEdgeTests.test_large_finite_vectors_never_silently_become_zero` | Vector chuẩn hóa có norm 1 hoặc bị từ chối rõ ràng | Input `[3e38, 3e38]` vẫn trả vector có norm 0 | **OPEN**, chưa sửa |
| R-P01 — MEDIUM, ngoài retrieval | `test_chunk_document_splits_article_and_clause`, `test_run_writes_chunks_and_report` | Hàm chunking được gọi tồn tại và chạy thành công | `AttributeError`: module chunker không có `chunk_document` | **OPEN**, vẫn 2 ERROR |

D-01 là thiếu kiểm tra tính tương thích cấu hình, chưa chứng minh tác động ngữ nghĩa
bằng model thật. D-03 là vector cực trị, không phải bằng chứng model thường sinh
vector bất thường. Không mở rộng tác động của lỗi ngoài những gì test đã tái hiện.

## B-01 — Lỗi mới ở cấu trúc kết quả BM25

**Mức độ:** HIGH. **Owner cần xử lý:** Team 1/BM25.
**Source:** `team1_data/retrieval/bm25.py`, `_search()` dòng 96 và `retrieve()` dòng 130
tại snapshot nêu trên.

Luồng dữ liệu gây lỗi: `_search()` trả object `{question, results}`, sau đó `retrieve()`
gán toàn bộ object đó vào field `results` của object mới. Contract v0.1 yêu cầu field
này là array các candidate.

```text
Expected: {question: "...", results: [...]}
Actual:   {question: "...", results: {question: "...", results: [...]}}
```

Ngay cả no-hit cũng trả object lồng thay cho `results=[]`. Sáu method BM25 bị ảnh
hưởng: **1 FAIL + 5 ERROR**. Các lỗi không phải sáu nguyên nhân độc lập; nhóm chung
vào B-01 để tránh trùng issue.

| Test hiện có | Actual |
| --- | --- |
| `BM25RetrieverTest.test_no_matching_word_returns_empty_results` | FAIL do output no-hit bị bọc thêm object |
| `BM25RetrieverTest.test_contract_schema_and_semantics` | ERROR: `results` không phải array |
| `BM25RetrieverTest.test_article_reference_query` | ERROR khi đọc `chunk_id` từ kết quả |
| `BM25RetrieverTest.test_basic_query_ranks_matching_chunk_first` | ERROR khi đọc `chunk_id` từ kết quả |
| `BM25RetrieverTest.test_result_has_chunk_id_content_and_score` | ERROR `KeyError: 0` khi truy cập candidate đầu tiên |
| `BM25EdgeTests.test_nfc_and_nfd_queries_retrieve_same_ids` | ERROR khi đọc `chunk_id` từ kết quả |

Ba FAIL còn lại trong bộ retrieval là D-01/D-02/D-03. Hướng xử lý đề xuất: owner thống
nhất `_search()` trả list candidate theo interface Hybrid; `retrieve()` chỉ bọc public
response một lần. Sau sửa cần chạy lại contract/no-hit/Unicode và tích hợp Hybrid.
Đây là đề xuất sửa, chưa thay đổi code hoặc API trong lần kiểm tra này.

## Hybrid hiện có và phần chưa kiểm chứng

- Đã có `rrf_fuse()`, `HybridRetriever`, hai nhánh chạy song song, timeout và đường
  `_search()` lấy tối đa 100 candidate. Public Top-K vẫn giới hạn 1..50.
- Ba smoke test dùng fake branches trả list đều PASS. Điều này chưa kiểm chứng
  đường kết nối với BM25 thật: `rrf_fuse()` mong list nhưng `_search()` của BM25 hiện
  trả dict. Nguy cơ lệch interface dựa trên source và B-01; chưa chạy ca tích hợp thật.
- Constructor Hybrid chưa kiểm tra `index_version`/tập `chunk_ids` theo handoff.
  Đây là khoảng thiếu quan sát qua source, chưa có ca runtime mới để nghiệm thu mục này.
- Chưa benchmark Dense/model thật, Qdrant server hoặc Hybrid trên corpus thật; không
  dùng ba smoke test để kết luận Recall@20 hoặc chất lượng ngữ nghĩa đạt yêu cầu.

## Đối chiếu nhiệm vụ Jira và việc cần tiếp tục

**VLRA-28:** đã có bộ test và báo cáo, nhưng BM25 hiện vi phạm contract do B-01.
Chưa thể xác nhận source hiện tại đạt; owner cần sửa và chạy lại các ca bị ảnh hưởng,
sau đó build/query/evaluate trên corpus thật. Chưa có số đo Recall/MRR/latency mới
cho snapshot này, không dùng số đo từ lần chạy khác để nghiệm thu.

**VLRA-29:** **có module Hybrid, mới kiểm tra smoke**. T007 chưa hoàn thành vì còn
kiểm chứng contract/integration, version/IDs,
RRF đầy đủ và benchmark. T005 model thật/server vẫn chưa chạy; D-01..D-03 còn OPEN.
Chưa nghiệm thu toàn tuần hoặc tự đổi trạng thái Jira.

## Evidence và phạm vi cập nhật

Thư mục `.local/team3/retest-20261021/` ignored, chưa được đưa lên GitHub.
Bằng chứng dưới đây là các output
của lần chạy 21/10, không phải kết quả được suy từ source hoặc từ một lần chạy khác.

| Phạm vi | Artifact local |
| --- | --- |
| Retrieval | `.local/team3/retest-20261021/retrieval/unit-results.json`, `junit.xml`, `unit.log` |
| Ba defect Dense | `.local/team3/retest-20261021/dense-defects/unit-results.json`, `unit.log` |
| Hybrid | `.local/team3/retest-20261021/hybrid/unit-results.json`, `junit.xml`, `unit.log` |
| Preprocess | `.local/team3/retest-20261021/preprocess/unit-results.json`, `junit.xml`, `unit.log` |

Chỉ thay nội dung báo cáo Markdown hiện có; không tạo thêm file, không chạy lại test
trong bước chỉnh tài liệu, không sửa code, không commit/push. PDF/Word chưa đồng bộ
với nội dung cập nhật này.
