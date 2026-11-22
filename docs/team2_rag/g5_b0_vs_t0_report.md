# G5: B0 (BM25) so với T0 (Hybrid + Rerank), nhãn `test`

Dataset: `team1_data/golden/test_set_v1.json` (sha256 `2d4b1f4db19e`)

| Chỉ số | B0 | T0 |
| :--- | ---: | ---: |
| Citation correctness (≥ 90%) | 100.00% | 100.00% |
| Citation coverage | 99.17% | 100.00% |
| Hallucination theo câu | 1.67% | 0.00% |
| Hallucination theo claim | 0.83% | 0.00% |
| Từ chối: Precision | 87.50% | 93.33% |
| Từ chối: Recall | 93.33% | 93.33% |
| Số câu `total` | 77 | 77 |
| Số câu `answered` | 60 | 61 |
| Số câu `insufficient_context` | 16 | 15 |
| Số câu `error` | 1 | 1 |
| Lùi về thứ hạng Hybrid do rerank lỗi/quá hạn | 0 | 3 |

Biến kiểm soát giữa B0 và T0: giống nhau.

Hallucination: verification/rubric.py: đối chiếu từ vựng, chưa phải kiểm tra ngữ nghĩa sâu.
Câu `error` không vào mẫu số chỉ số chất lượng; số mẫu số từng chỉ số xem `metrics.counts` trong JSON.
