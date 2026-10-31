Dev Set `team1_data/golden/golden_phase1.json` sha256 `f89956d5d61b` · 110 câu có gold · corpus 2576 chunk được index

| Cấu hình | R@5 | R@10 | R@20 | MRR@20 | R@5 strict | p50 ms | p95 ms | build ms | chunk |
|---|---|---|---|---|---|---|---|---|---|
| bm25 | 0.863 | 0.912 | 0.929 | 0.814 | 0.781 | 1.3 | 2.2 | 10906 | 2576 |
| dense_lsa256 | 0.852 | 0.920 | 0.929 | 0.757 | 0.760 | 37.3 | 46.3 | 4736 | 2576 |
| hybrid_rrf_k60 | 0.876 | 0.915 | 0.933 | 0.829 | 0.802 | 43.3 | 56.3 | 15642 | 2576 |
