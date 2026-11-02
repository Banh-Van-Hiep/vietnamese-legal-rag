# Tác động của Reranker — phần Người 1 Team 2

Lượt đo lại ngày 02/11/2026 trên 110 câu Golden, sau khi Người 2 thêm tùy chọn truncate. BGE gốc hoàn tất 97/110 câu; BGE truncate hoàn tất 110/110 câu. Trên cùng 97 câu thành công, Recall@5 giảm từ 87,66% (Hybrid) xuống 83,70% (cả hai chính sách BGE). Truncate xử lý lỗi độ dài nhưng không đổi thứ tự của 97 câu này. Không gọi LLM hoặc dùng fallback để che lỗi.

## Cấu hình và bằng chứng

- Code: `1f51f66fa87166f23af32cf428226426a56a4b5c`, working tree sạch; runner bắt đầu 21:53:44 ngày 02/11/2026, UTC+7.
- Corpus: 2.576 chunk; index `colab-042bd7f1696e-dea33aa1`; hai index cùng snapshot.
- Hybrid: BM25 + Dense, RRF k=60, trọng số 1:1, top 20; chỉ retrieval một lần/câu.
- Dense: `AITeamVN/Vietnamese_Embedding`, revision `dea33aa1ab339f38d66ae0a40e6c40e0a9249568`.
- Reranker: `BAAI/bge-reranker-v2-m3`, revision `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, batch 2, max_length 512.
- Hai nhánh dùng cùng weights/tokenizer và pool; chỉ đổi `truncate=False` thành `True` (`only_second`). Cả hai chạy strict, không fallback. Passage gốc và metadata không đổi.
- Môi trường: `Tesla T4`, CUDA 13.0, Python 3.13.16, PyTorch 2.11.0+cu130.

[Raw output, Golden đầu vào, manifest, hash và metadata](../../team2_rag/data/evaluation/colab-20261102/). [Notebook tái lập](../../notebooks/reranker_evaluation_colab.ipynb).

## Phạm vi dữ liệu

Golden của Team 1 gồm 40 câu `team2_reviewed` nhập từ bộ cũ và 70 câu `draft_needs_legal_review`. Cả 110 câu đều answered; chưa có insufficient_context, split hay relevant_unit_groups. Giữ nguyên nhãn nguồn; mỗi gold chunk tạm là một nhóm riêng. Đây là khảo sát theo nhãn hiện có, chưa phải nghiệm thu Dev/Test theo đặc tả, chưa đo chất lượng câu trả lời/citation hoặc Gate G4/G5.

## VLRA-54 — So sánh chất lượng

Bảng chính dùng **cùng 97 câu thành công ở cả hai chính sách**. Không so trực tiếp trung bình có mẫu số khác nhau.

| Chỉ số | Hybrid | BGE gốc | BGE truncate |
| --- | ---: | ---: | ---: |
| Recall@5 | 87,66% | 83,70% | 83,70% |
| Recall@10 | 93,15% | 89,06% | 89,06% |
| Recall@20 | 95,07% | 95,07% | 95,07% |
| MRR@20 | 0,6228 | 0,5835 | 0,5835 |
| Gold hit hạng 1 | 34,02% | 27,84% | 27,84% |

| Nhánh | Hoàn tất | Lỗi retrieval | Lỗi rerank | Failure rate |
| --- | ---: | ---: | ---: | ---: |
| BGE gốc | 97/110 | 0 | 13 | 11,82% |
| BGE truncate | 110/110 | 0 | 0 | 0,00% |

### 40 câu nhập từ bộ cũ

Tính trên cùng 38 câu thành công; nhãn review giữ theo nguồn.

| Chỉ số | Hybrid | BGE gốc | BGE truncate |
| --- | ---: | ---: | ---: |
| Recall@5 | 73,77% | 66,29% | 66,29% |
| Recall@10 | 85,15% | 77,34% | 77,34% |
| Recall@20 | 87,42% | 87,42% | 87,42% |
| MRR@20 | 0,6871 | 0,6037 | 0,6037 |
| Gold hit hạng 1 | 47,37% | 34,21% | 34,21% |

### 70 câu draft của Team 1

Tính trên cùng 59 câu thành công; nhãn review giữ theo nguồn.

| Chỉ số | Hybrid | BGE gốc | BGE truncate |
| --- | ---: | ---: | ---: |
| Recall@5 | 96,61% | 94,92% | 94,92% |
| Recall@10 | 98,31% | 96,61% | 96,61% |
| Recall@20 | 100,00% | 100,00% | 100,00% |
| MRR@20 | 0,5814 | 0,5705 | 0,5705 |
| Gold hit hạng 1 | 25,42% | 23,73% | 23,73% |

### Toàn bộ cặp thành công của nhánh truncate

Riêng 110 câu thành công của nhánh truncate: Hybrid Recall@5 = 88,39%, BGE truncate = 83,08%; MRR@20 tương ứng 0,6465 và 0,5968. Không dùng mẫu số này để đối chiếu trực tiếp với trung bình BGE gốc trên ít câu hơn.

Recall@20 giữ nguyên trên cùng câu vì rerank chỉ đổi thứ tự pool, không bổ sung căn cứ bị retrieval bỏ sót.

## VLRA-55 — Độ trễ và ca không hiệu quả

| Bước | Mẫu | p50 (ms) | p95 (ms) |
| --- | ---: | ---: | ---: |
| Hybrid | 110 | 103,79 | 180,74 |
| BGE gốc | 97 | 828,31 | 1086,24 |
| BGE truncate | 110 | 866,86 | 1253,82 |
| Tổng với BGE gốc | 97 | 967,38 | 1215,55 |
| Tổng với BGE truncate | 110 | 1009,03 | 1371,46 |

Latency loại setup/build/warm-up. Tổng từng câu cộng thời gian retrieval/kiểm tra đã đo với xử lý riêng chính sách đó; không gồm suy luận nhánh còn lại. p50/p95 tổng lấy từ các tổng từng câu, không cộng percentile. BGE gốc được chạy trước nhánh truncate ở mỗi câu; đây không phải đo tốc độ nhiều lượt có đảo thứ tự. Đây là một lượt trên T4, chưa phải request E2E/LLM/API, không suy ra độ trễ CPU trên máy cá nhân.

Ở nhánh truncate có 5 câu chỉ thêm nhóm đúng vào top 5, 12 câu chỉ mất nhóm đúng, 5 câu vừa thêm vừa mất và 88 câu không đổi nhóm được chạm. Không đổi coverage không đồng nghĩa giữ nguyên mọi thứ hạng.

| Câu | Nhãn nguồn | Recall@5 Hybrid → truncate | Quan sát |
| --- | --- | ---: | --- |
| gold_002 | team2_reviewed | 100,00% → 0,00% | Hai gold chunk Điều 2 từ hạng 2/1 xuống 12/8 |
| gold_053 | draft_needs_legal_review | 100,00% → 0,00% | Gold chunk Điều 202 Khoản 3 từ hạng 4 xuống 6 |
| gold_078 | draft_needs_legal_review | 0,00% → 100,00% | Gold chunk Điều 198 Khoản 1 từ hạng 8 lên 4 |
| gold_073 | draft_needs_legal_review | 0,00% → 100,00% | Gold chunk Điều 91 Khoản 1 từ hạng 16 lên 2 |

Ca lỗi BGE gốc: gold_027, gold_032, gold_054, gold_064, gold_065, gold_089, gold_090, gold_092, gold_093, gold_094, gold_100, gold_108, gold_109. Nhánh truncate khôi phục: gold_027, gold_032, gold_054, gold_064, gold_065, gold_089, gold_090, gold_092, gold_093, gold_094, gold_100, gold_108, gold_109. Kiểm tra token độc lập nằm trong `reranker-length-check.json`; xem raw để đối chiếu từng passage dài và điểm.

Hai ca được khôi phục cho thấy chạy đủ chưa chắc xếp hạng tốt: `gold_054` có gold từ hạng 2 xuống 6; `gold_093` từ hạng 1 xuống 20 sau truncate.

Các quan sát này mô tả thay đổi thứ hạng theo gold hiện tại. Chưa khẳng định nguyên nhân ngữ nghĩa hoặc tính đúng pháp lý; không mặc định rằng cắt đuôi giữ đủ căn cứ.

## VLRA-58 — Kết quả bàn giao

**Đề xuất từ thực nghiệm:** giữ Hybrid top 20 làm mốc và chưa chọn BGE truncate làm cấu hình tối ưu. Trên 110 câu, nó giảm Recall@5 5,31 điểm phần trăm và MRR@20 0,0497, đồng thời thêm khoảng 867 ms rerank ở trung vị. Đây là đề xuất theo nhãn hiện có, không tự đổi cấu hình sản phẩm.

Bàn giao bảng chất lượng/latency, raw ứng viên, điểm và ca lỗi để Người 2 tổng hợp cấu hình. Kiểm chứng truncate riêng biệt không chứng minh toàn bộ pipeline v2 đã đạt mục tiêu: runtime vẫn khởi tạo `BGEScorer()` mặc định không truncate, top_k mặc định 10, chưa có timer cưỡng chế rerank 4 giây. Việc chốt runtime/context thuộc bước thống nhất với Người 2.

Công cụ, lượt khảo sát 110 câu và báo cáo của Người 1 đã có bằng chứng. Phần nghiệm thu chính thức vẫn cần bộ Dev được review/đóng băng với gold groups và chạy lại; không tự gán nhãn review cho 70 câu draft hoặc ghi Done thay cho điều kiện đó.

Lượt 31/10 trên 40 câu tại `fa93cdf` vẫn được giữ trong [bằng chứng lịch sử](../../team2_rag/data/evaluation/colab-20261031/). Không ghi đè dữ liệu cũ; lượt mới có commit/môi trường riêng.
