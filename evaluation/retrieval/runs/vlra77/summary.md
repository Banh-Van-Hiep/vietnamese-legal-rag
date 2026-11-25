Dev Set `team1_data/golden/test_set_v1.json` sha256 `7fbd2cc19d79` · 62 câu có gold · corpus 2576 chunk được index

| Cấu hình | R@5 | R@10 | R@20 | MRR@20 | hit@5 | R@5 theo Điều | R@5 strict | p50 ms | p95 ms | build ms | chunk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hybrid_k60_aiteamvn_w0.5-1 | 1.000 | 1.000 | 1.000 | 0.957 | 1.000 | 1.000 | 0.927 | 136.4 | 148.6 | 1063682 | 2576 |

Theo nhóm câu hỏi (`review_status`):

| Cấu hình | Nhóm | Số câu | R@5 | R@20 | MRR@20 | hit@5 | R@5 theo Điều |
|---|---|---|---|---|---|---|---|
| hybrid_k60_aiteamvn_w0.5-1 | draft_needs_legal_review | 62 | 1.000 | 1.000 | 0.957 | 1.000 | 1.000 |
