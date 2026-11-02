Dev Set `team1_data/golden/golden_phase1.json` sha256 `f89956d5d61b` · 110 câu có gold · corpus 2576 chunk được index

| Cấu hình | R@5 | R@10 | R@20 | MRR@20 | hit@5 | R@5 theo Điều | R@5 strict | p50 ms | p95 ms | build ms | chunk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dense_e5small | 0.908 | 0.940 | 0.951 | 0.868 | 0.973 | 0.948 | 0.872 | 120.8 | 166.8 | 138373 | 2576 |
| hybrid_k60_e5small | 0.896 | 0.946 | 0.954 | 0.889 | 0.964 | 0.922 | 0.828 | 114.6 | 148.3 | 152673 | 2576 |

Theo nhóm câu hỏi (`review_status`):

| Cấu hình | Nhóm | Số câu | R@5 | R@20 | MRR@20 | hit@5 | R@5 theo Điều |
|---|---|---|---|---|---|---|---|
| dense_e5small | draft_needs_legal_review | 70 | 0.986 | 1.000 | 0.853 | 0.986 | 1.000 |
| dense_e5small | team2_reviewed | 40 | 0.772 | 0.865 | 0.894 | 0.950 | 0.857 |
| hybrid_k60_e5small | draft_needs_legal_review | 70 | 1.000 | 1.000 | 0.904 | 1.000 | 1.000 |
| hybrid_k60_e5small | team2_reviewed | 40 | 0.714 | 0.874 | 0.863 | 0.900 | 0.786 |
