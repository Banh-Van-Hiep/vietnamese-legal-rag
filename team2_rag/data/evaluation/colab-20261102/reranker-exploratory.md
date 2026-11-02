# Đánh giá tác động của Reranker

Trạng thái: ERROR.
Phạm vi: exploratory.

So sánh Hybrid top 20 và BGE rerank trên cùng ứng viên; không gọi LLM.
Đây là ablation retrieval, chưa phải đánh giá B0/T0 toàn hệ thống.

Cấu hình truncate: False; so sánh hai chính sách: True.

Nhãn review của dữ liệu nguồn: {'team2_reviewed': 40, 'draft_needs_legal_review': 70}. Runner không xác nhận thay cho review relevance/pháp lý.

Tổng 110 câu; 97 cặp answerable thành công; 0 câu không tính Recall/MRR; 0 lỗi retrieval, 13 lỗi reranker.

Metric tính trên cùng các cặp thành công. Run có lỗi không được dùng để xác nhận đạt mục tiêu.

| Chỉ số | Hybrid | Hybrid + Reranker | Chênh lệch |
| --- | ---: | ---: | ---: |
| recall_at_5 | 0.8766 | 0.8370 | -0.0396 |
| recall_at_10 | 0.9315 | 0.8906 | -0.0409 |
| recall_at_20 | 0.9507 | 0.9507 | 0.0000 |
| mrr_at_20 | 0.6228 | 0.5835 | -0.0393 |
| top1_hit | 0.3402 | 0.2784 | -0.0619 |

Recall tính theo gold unit group; top1_hit chỉ đo trúng căn cứ, không chấm câu trả lời.

| Độ trễ (ms) | Mẫu | p50 | p95 |
| --- | ---: | ---: | ---: |
| retrieval_ms | 110 | 103.7851 | 180.7429 |
| rerank_ms | 97 | 828.3070 | 1086.2399 |
| total_ms | 97 | 967.3797 | 1215.5481 |

Độ trễ trên là các bước thành công, không gồm setup/warm-up. Thời gian lỗi nằm trong JSON; total_ms chỉ gồm retrieval, kiểm tra và rerank, chưa phải latency toàn hệ thống.

| Tác động ở top 5 | Số câu | Tỷ lệ trên cặp answerable |
| --- | ---: | ---: |
| promoted | 5 | 0.0515 |
| demoted | 10 | 0.1031 |
| mixed | 5 | 0.0515 |
| unchanged | 77 | 0.7938 |

## Kiểm chứng truncate của Người 2

Hai chính sách dùng đúng cùng pool; strict=True, không fallback. Chỉ bật truncation=only_second ở nhánh truncate, không sửa chunk gốc.
Nhánh truncate: 110 cặp answerable thành công; 0 lỗi rerank, 0 lỗi retrieval.

So sánh chất lượng trên cùng 97 câu thành công ở cả hai chính sách:

| Chỉ số | Hybrid | BGE gốc | BGE truncate |
| --- | ---: | ---: | ---: |
| recall_at_5 | 0.8766 | 0.8370 | 0.8370 |
| recall_at_10 | 0.9315 | 0.8906 | 0.8906 |
| recall_at_20 | 0.9507 | 0.9507 | 0.9507 |
| mrr_at_20 | 0.6228 | 0.5835 | 0.5835 |
| top1_hit | 0.3402 | 0.2784 | 0.2784 |

Metric trên toàn bộ cặp thành công của nhánh truncate nằm riêng trong JSON; không so trực tiếp hai trung bình có mẫu số khác nhau.

| Độ trễ nhánh truncate (ms) | Mẫu | p50 | p95 |
| --- | ---: | ---: | ---: |
| retrieval_ms | 110 | 103.7851 | 180.7429 |
| rerank_ms | 110 | 866.8585 | 1253.8238 |
| total_ms | 110 | 1009.0283 | 1371.4623 |

total_ms cộng thời gian retrieval/kiểm tra đã đo một lần với xử lý riêng từng nhánh. Không cộng thời gian chạy chính sách còn lại; chưa phải request E2E.

## Các ca cần xem lại

Các dấu hiệu dưới đây phục vụ review; chưa khẳng định nguyên nhân lỗi ngữ nghĩa.

- gold_002: demoted; nhóm tăng [], nhóm mất [0, 1], nhóm thiếu từ Hybrid top 20 [].
- gold_003: unchanged; nhóm tăng [], nhóm mất [], nhóm thiếu từ Hybrid top 20 [0].
- gold_005: mixed; nhóm tăng [1], nhóm mất [8, 9, 10], nhóm thiếu từ Hybrid top 20 [].
- gold_011: demoted; nhóm tăng [], nhóm mất [2, 3], nhóm thiếu từ Hybrid top 20 [].
- gold_012: demoted; nhóm tăng [], nhóm mất [0, 1, 3, 4], nhóm thiếu từ Hybrid top 20 [].
- gold_013: mixed; nhóm tăng [8], nhóm mất [2, 5, 6], nhóm thiếu từ Hybrid top 20 [].
- gold_014: mixed; nhóm tăng [1], nhóm mất [0, 3], nhóm thiếu từ Hybrid top 20 [].
- gold_015: demoted; nhóm tăng [], nhóm mất [1], nhóm thiếu từ Hybrid top 20 [].
- gold_016: unchanged; nhóm tăng [], nhóm mất [], nhóm thiếu từ Hybrid top 20 [2, 4].
- gold_017: unchanged; nhóm tăng [], nhóm mất [], nhóm thiếu từ Hybrid top 20 [1, 3, 4, 5, 6].
- gold_018: unchanged; nhóm tăng [], nhóm mất [], nhóm thiếu từ Hybrid top 20 [1, 2].
- gold_019: unchanged; nhóm tăng [], nhóm mất [], nhóm thiếu từ Hybrid top 20 [0, 1, 2, 4].
- gold_020: mixed; nhóm tăng [0], nhóm mất [2, 3], nhóm thiếu từ Hybrid top 20 [1].
- gold_021: mixed; nhóm tăng [7], nhóm mất [5, 8, 9], nhóm thiếu từ Hybrid top 20 [4, 6].
- gold_022: unchanged; nhóm tăng [], nhóm mất [], nhóm thiếu từ Hybrid top 20 [0].
- gold_025: demoted; nhóm tăng [], nhóm mất [0], nhóm thiếu từ Hybrid top 20 [].
- gold_027: RERANK_ERROR (RerankModelError).
- gold_028: demoted; nhóm tăng [], nhóm mất [0, 1], nhóm thiếu từ Hybrid top 20 [].
- gold_029: demoted; nhóm tăng [], nhóm mất [1, 6], nhóm thiếu từ Hybrid top 20 [].
- gold_030: unchanged; nhóm tăng [], nhóm mất [], nhóm thiếu từ Hybrid top 20 [2, 3].
- gold_032: RERANK_ERROR (RerankModelError).
- gold_053: demoted; nhóm tăng [], nhóm mất [0], nhóm thiếu từ Hybrid top 20 [].
- gold_054: RERANK_ERROR (RerankModelError).
- gold_064: RERANK_ERROR (RerankModelError).
- gold_065: RERANK_ERROR (RerankModelError).
- gold_074: demoted; nhóm tăng [], nhóm mất [0], nhóm thiếu từ Hybrid top 20 [].
- gold_081: demoted; nhóm tăng [], nhóm mất [0], nhóm thiếu từ Hybrid top 20 [].
- gold_089: RERANK_ERROR (RerankModelError).
- gold_090: RERANK_ERROR (RerankModelError).
- gold_092: RERANK_ERROR (RerankModelError).
- gold_093: RERANK_ERROR (RerankModelError).
- gold_094: RERANK_ERROR (RerankModelError).
- gold_100: RERANK_ERROR (RerankModelError).
- gold_108: RERANK_ERROR (RerankModelError).
- gold_109: RERANK_ERROR (RerankModelError).

Dùng JSON để xem câu hỏi, ứng viên, thứ tự và điểm BGE. Chưa chốt cấu hình RAG: Người 2 tổng hợp thêm phân tích lỗi và Context Builder cho VLRA-58.
