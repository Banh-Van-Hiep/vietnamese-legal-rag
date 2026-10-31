Dev Set `team1_data/golden/golden_phase1.json` sha256 `f89956d5d61b` · 110 câu có gold · corpus 2576 chunk được index

| Cấu hình | R@5 | R@10 | R@20 | MRR@20 | hit@5 | R@5 theo Điều | R@5 strict | p50 ms | p95 ms | build ms | chunk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bm25 | 0.863 | 0.912 | 0.929 | 0.814 | 0.946 | 0.914 | 0.781 | 1.8 | 2.7 | 11940 | 2576 |
| dense_lsa384 | 0.864 | 0.920 | 0.929 | 0.784 | 0.946 | 0.929 | 0.792 | 47.7 | 77.5 | 12794 | 2576 |
| hybrid_k60_lsa256 | 0.876 | 0.915 | 0.933 | 0.829 | 0.955 | 0.928 | 0.802 | 48.1 | 73.3 | 14949 | 2576 |
| hybrid_k60_lsa384 | 0.876 | 0.917 | 0.935 | 0.839 | 0.955 | 0.928 | 0.835 | 57.5 | 100.2 | 24734 | 2576 |
| hybrid_k60_lsa768 | 0.886 | 0.916 | 0.938 | 0.859 | 0.964 | 0.928 | 0.841 | 78.9 | 264.7 | 23466 | 2576 |

Theo nhóm câu hỏi (`review_status`):

| Cấu hình | Nhóm | Số câu | R@5 | R@20 | MRR@20 | hit@5 | R@5 theo Điều |
|---|---|---|---|---|---|---|---|
| bm25 | draft_needs_legal_review | 70 | 0.986 | 1.000 | 0.827 | 0.986 | 0.986 |
| bm25 | team2_reviewed | 40 | 0.648 | 0.804 | 0.790 | 0.875 | 0.789 |
| dense_lsa384 | draft_needs_legal_review | 70 | 0.971 | 1.000 | 0.779 | 0.971 | 1.000 |
| dense_lsa384 | team2_reviewed | 40 | 0.677 | 0.805 | 0.791 | 0.900 | 0.806 |
| hybrid_k60_lsa256 | draft_needs_legal_review | 70 | 0.986 | 1.000 | 0.825 | 0.986 | 1.000 |
| hybrid_k60_lsa256 | team2_reviewed | 40 | 0.683 | 0.815 | 0.836 | 0.900 | 0.802 |
| hybrid_k60_lsa384 | draft_needs_legal_review | 70 | 0.986 | 1.000 | 0.839 | 0.986 | 1.000 |
| hybrid_k60_lsa384 | team2_reviewed | 40 | 0.684 | 0.820 | 0.840 | 0.900 | 0.802 |
| hybrid_k60_lsa768 | draft_needs_legal_review | 70 | 1.000 | 1.000 | 0.876 | 1.000 | 1.000 |
| hybrid_k60_lsa768 | team2_reviewed | 40 | 0.686 | 0.830 | 0.829 | 0.900 | 0.802 |
