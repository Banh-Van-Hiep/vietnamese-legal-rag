Dev Set `team1_data/golden/golden_phase1.json` sha256 `f89956d5d61b` · 110 câu có gold · corpus 2576 chunk được index

| Cấu hình | R@5 | R@10 | R@20 | MRR@20 | hit@5 | R@5 theo Điều | R@5 strict | p50 ms | p95 ms | build ms | chunk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dense_aiteamvn | 0.902 | 0.949 | 0.964 | 0.950 | 0.982 | 0.935 | 0.875 | 290.1 | 375.7 | 1376426 | 2576 |
| hybrid_k60_aiteamvn | 0.908 | 0.951 | 0.960 | 0.919 | 0.973 | 0.951 | 0.884 | 354.9 | 499.4 | 1387691 | 2576 |

Theo nhóm câu hỏi (`review_status`):

| Cấu hình | Nhóm | Số câu | R@5 | R@20 | MRR@20 | hit@5 | R@5 theo Điều |
|---|---|---|---|---|---|---|---|
| dense_aiteamvn | draft_needs_legal_review | 70 | 0.986 | 0.986 | 0.941 | 0.986 | 0.986 |
| dense_aiteamvn | team2_reviewed | 40 | 0.754 | 0.925 | 0.966 | 0.975 | 0.848 |
| hybrid_k60_aiteamvn | draft_needs_legal_review | 70 | 0.986 | 1.000 | 0.935 | 0.986 | 1.000 |
| hybrid_k60_aiteamvn | team2_reviewed | 40 | 0.773 | 0.889 | 0.891 | 0.950 | 0.865 |
