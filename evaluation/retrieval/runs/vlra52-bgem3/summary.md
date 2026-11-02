Dev Set `team1_data/golden/golden_phase1.json` sha256 `f89956d5d61b` · 110 câu có gold · corpus 2576 chunk được index

| Cấu hình | R@5 | R@10 | R@20 | MRR@20 | hit@5 | R@5 theo Điều | R@5 strict | p50 ms | p95 ms | build ms | chunk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dense_bgem3 | 0.910 | 0.950 | 0.964 | 0.866 | 0.982 | 0.949 | 0.876 | 295.1 | 370.3 | 1136636 | 2576 |
| hybrid_k60_bgem3 | 0.899 | 0.946 | 0.957 | 0.910 | 0.973 | 0.934 | 0.858 | 336.7 | 428.6 | 1148319 | 2576 |

Theo nhóm câu hỏi (`review_status`):

| Cấu hình | Nhóm | Số câu | R@5 | R@20 | MRR@20 | hit@5 | R@5 theo Điều |
|---|---|---|---|---|---|---|---|
| dense_bgem3 | draft_needs_legal_review | 70 | 0.986 | 1.000 | 0.887 | 0.986 | 0.986 |
| dense_bgem3 | team2_reviewed | 40 | 0.778 | 0.900 | 0.829 | 0.975 | 0.885 |
| hybrid_k60_bgem3 | draft_needs_legal_review | 70 | 1.000 | 1.000 | 0.924 | 1.000 | 1.000 |
| hybrid_k60_bgem3 | team2_reviewed | 40 | 0.723 | 0.880 | 0.885 | 0.925 | 0.818 |
