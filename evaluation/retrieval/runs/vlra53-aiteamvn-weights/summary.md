Dev Set `team1_data/golden/golden_phase1.json` sha256 `f89956d5d61b` · 110 câu có gold · corpus 2576 chunk được index

| Cấu hình | R@5 | R@10 | R@20 | MRR@20 | hit@5 | R@5 theo Điều | R@5 strict | p50 ms | p95 ms | build ms | chunk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dense_aiteamvn | 0.902 | 0.949 | 0.964 | 0.950 | 0.982 | 0.935 | 0.875 | 292.1 | 364.4 | 999322 | 2576 |
| hybrid_k60_aiteamvn_w1-1 | 0.908 | 0.951 | 0.960 | 0.919 | 0.973 | 0.951 | 0.884 | 345.8 | 450.5 | 1010520 | 2576 |
| hybrid_k60_aiteamvn_w0.5-1 | 0.912 | 0.942 | 0.966 | 0.946 | 0.982 | 0.956 | 0.892 | 331.2 | 429.1 | 1010520 | 2576 |
| hybrid_k60_aiteamvn_w0.3-1 | 0.903 | 0.952 | 0.972 | 0.950 | 0.982 | 0.949 | 0.880 | 326.3 | 404.0 | 1010520 | 2576 |

Theo nhóm câu hỏi (`review_status`):

| Cấu hình | Nhóm | Số câu | R@5 | R@20 | MRR@20 | hit@5 | R@5 theo Điều |
|---|---|---|---|---|---|---|---|
| dense_aiteamvn | draft_needs_legal_review | 70 | 0.986 | 0.986 | 0.941 | 0.986 | 0.986 |
| dense_aiteamvn | team2_reviewed | 40 | 0.754 | 0.925 | 0.966 | 0.975 | 0.848 |
| hybrid_k60_aiteamvn_w1-1 | draft_needs_legal_review | 70 | 0.986 | 1.000 | 0.935 | 0.986 | 1.000 |
| hybrid_k60_aiteamvn_w1-1 | team2_reviewed | 40 | 0.773 | 0.889 | 0.891 | 0.950 | 0.865 |
| hybrid_k60_aiteamvn_w0.5-1 | draft_needs_legal_review | 70 | 0.986 | 1.000 | 0.966 | 0.986 | 0.986 |
| hybrid_k60_aiteamvn_w0.5-1 | team2_reviewed | 40 | 0.783 | 0.905 | 0.911 | 0.975 | 0.902 |
| hybrid_k60_aiteamvn_w0.3-1 | draft_needs_legal_review | 70 | 0.986 | 1.000 | 0.956 | 0.986 | 0.986 |
| hybrid_k60_aiteamvn_w0.3-1 | team2_reviewed | 40 | 0.758 | 0.922 | 0.941 | 0.975 | 0.886 |
