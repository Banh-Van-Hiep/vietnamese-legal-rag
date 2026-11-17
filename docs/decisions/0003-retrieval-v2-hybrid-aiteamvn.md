# 0003. Retrieval v2: Hybrid RRF k=60, BM25:Dense 0.5:1, AITeamVN embedding

- Ngày: 2026-10-31 · Trạng thái: Accepted, cần đo lại trên Dev Set đã đóng băng
- Nguồn: commit `24a7b2f` (người commit: Claude), `team1_data/retrieval/retrieval_v2.json`, `evaluation/retrieval/runs/vlra49` … `vlra53-aiteamvn-weights`, `team1_data/docs_1/week8/tasks.md` mục 6.

## Bối cảnh
Team 1 so BM25, dense (LSA, e5-small, bge-m3, AITeamVN) và hybrid RRF với nhiều giá trị k và trọng số trên 110 câu Golden, corpus 2.576 chunk.

## Quyết định
`hybrid_rrf`, `top_k` 20, RRF k = 60, trọng số BM25:Dense = 0.5:1, tối đa 100 candidate mỗi nhánh. BM25 Lucene (k1 1.2, b 0.75) với tokenizer underthesea. Dense dùng `AITeamVN/Vietnamese_Embedding` (revision `dea33aa1`), cosine.

## Lý do
Cấu hình này cho R@5 0.912 và MRR@20 0.946 trên 110 câu, cao nhất trong lượt `vlra53-aiteamvn-weights`. BM25 đơn lẻ đạt R@5 0.863 ở lượt `vlra53`.

## Phương án đã loại
- BM25 đơn lẻ và hybrid với dense LSA: R@5 từ 0.863 đến 0.886 (lượt `vlra53`).
- Trọng số 1:1 và 0.3:1 với AITeamVN: R@5 0.908 và 0.903.
- e5-small và bge-m3 (lượt `vlra52`): R@5 gần bằng (dense e5-small 0.908, dense bge-m3 0.910, hybrid bge-m3 0.899) nhưng MRR@20 thấp hơn rõ (tối đa 0.910 so với 0.946). Chênh lệch R@5 nhỏ, nên ưu tiên MRR.

## Hệ quả và giới hạn
- Riêng 40 câu `team2_reviewed`, R@5 chỉ đạt 0.783, dưới mốc 0.85 của NFR-01. Báo cáo nên tách theo `review_status`.
- Lượt đo dùng file golden có hash `f89956d5d61b`. File hiện tại có hash `62420b515936`, sau commit `a1765bf` và `a6a4ce8` (người commit: Claude). Cần chạy lại trên Dev Set đã đóng băng trước khi dùng số này trong báo cáo cuối.
