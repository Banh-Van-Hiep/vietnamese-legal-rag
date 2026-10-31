# Tác động của Reranker trên Golden hiện tại

Khảo sát ngày 31/10/2026 cho phần Người 1 Team 2, VLRA-54/55. Trên 38 câu
chạy thành công cả hai nhánh, BGE làm Recall@5 giảm 7,48 điểm phần trăm và
MRR@20 giảm 0,0834 so với Hybrid. Hai câu còn lại lỗi do cặp đầu vào vượt
512 token. Kết quả hiện tại chưa ủng hộ chốt Hybrid + Reranker làm cấu hình
tối ưu cho VLRA-58.

Đây là khảo sát trên 40 câu Golden cũ, không phải nghiệm thu Dev/Test đã
đóng băng. Không có ca insufficient_context; relevance chưa được review lại
trong lần chạy này. Mỗi gold chunk tạm tính là một nhóm riêng vì dữ liệu
chưa có relevant_unit_groups. Không dùng các số dưới đây để xác nhận đạt
Recall@5 ≥85%, chất lượng câu trả lời hoặc G5.

## Cấu hình và bằng chứng

- Code chạy: `fa93cdf7332401d6bf76c23d67d4ebea3c9bcc09`, working tree sạch.
- Thời điểm runner bắt đầu: 10:38:30 ngày 31/10/2026, UTC+7.
- Corpus: 2.576 chunk, giữ nguyên file trong repo; index thực nghiệm mới
  `colab-042bd7f1696e-dea33aa1`. Không mặc định đây là snapshot MVP cũ.
- Golden: `team2_rag/data/golden/golden_phase1_30cai.json`, 40 câu answered,
  chưa có Dev/Test split hoặc gold groups đã review.
- Hybrid: BM25 + Dense, RRF k=60, trọng số 1:1, top 20.
- Dense: `AITeamVN/Vietnamese_Embedding`, revision
  `dea33aa1ab339f38d66ae0a40e6c40e0a9249568`.
- Reranker: `BAAI/bge-reranker-v2-m3`, revision
  `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, batch 2, max_length 512,
  strict, không truncate và không fallback.
- Môi trường: Tesla T4, CUDA 13.0, PyTorch 2.11.0+cu130, Python 3.13.16.
  Embedding và reranker đều chạy CUDA; không gọi LLM.

[Raw output và metadata](../../team2_rag/data/evaluation/colab-20261031/)
gồm đủ 40 câu, ứng viên trước rerank, thứ tự sau rerank, điểm BGE, lỗi,
latency từng bước, hash nguồn, manifest index và phiên bản thư viện.
[Notebook tái lập](../../notebooks/reranker_evaluation_colab.ipynb) tự dựng
index trên Colab và xuất ZIP, không cần model/index trên máy cá nhân.

## So sánh chất lượng

Hai nhánh dùng chung pool top 20 của từng câu. Macro-average dưới đây chỉ
trên cùng 38 cặp answerable thành công; 2 lỗi vẫn nằm trong báo cáo raw và
failure rate là 2/40 = 5%. Không gán kết quả rerank giả cho ca lỗi.

| Chỉ số | Hybrid | Hybrid + Reranker | Chênh lệch |
| --- | ---: | ---: | ---: |
| Recall@5 | 73,77% | 66,29% | −7,48 điểm % |
| Recall@10 | 85,15% | 77,34% | −7,80 điểm % |
| Recall@20 | 87,42% | 87,42% | 0 |
| MRR@20 | 0,6871 | 0,6037 | −0,0834 |
| Gold hit ở vị trí 1 | 47,37% | 34,21% | −13,16 điểm % |

Recall@20 giữ nguyên vì rerank chỉ đổi thứ tự cùng tập ứng viên. Có 3 câu
chỉ tăng nhóm đúng trong top 5, 7 câu chỉ mất nhóm đúng, 5 câu vừa tăng vừa
mất và 23 câu không đổi nhóm được chạm. "Không đổi" ở đây không có nghĩa
mọi thứ hạng đều giữ nguyên hoặc câu trả lời có cùng chất lượng.

## Độ trễ trên Colab

| Bước | Số mẫu thành công | p50 (ms) | p95 (ms) |
| --- | ---: | ---: | ---: |
| Hybrid | 40 | 106,58 | 121,66 |
| Rerank | 38 | 730,43 | 988,29 |
| Tổng retrieval + kiểm tra + rerank | 38 | 849,49 | 1.099,09 |

Reranker bổ sung khoảng 730 ms ở trung vị trong cấu hình này. Tổng latency
được đo riêng từng câu, không cộng các percentile của từng bước. Thời gian
setup, dựng index và warm-up không tính vào bảng. Thời gian lỗi vẫn giữ
trong raw JSON; tổng chỉ lấy câu hoàn tất. Đây chưa phải latency LLM, API
hoặc E2E, và không suy ra thời gian trên Mac của người dùng.

## Các trường hợp cần bàn giao

Thứ hạng dưới đây lấy trực tiếp từ raw output; dùng nhãn gold hiện có,
chưa khẳng định nhãn đó đã đúng pháp lý hoặc đủ hiệu lực.

| Câu | Quan sát sau rerank | Ý nghĩa đối với top 5 |
| --- | --- | --- |
| gold_004 | Chunk `luat-59-2020-qh14-v1__dieu-4__k34__0` từ hạng 7 lên 5 | Có thêm căn cứ theo gold hiện tại |
| gold_002 | Hai chunk Điều 2 từ hạng 2/1 xuống 12/8 | Mất cả hai gold chunk khỏi top 5; Recall@5 từ 1 xuống 0 |
| gold_005 | Một chunk Điều 7 từ 12 lên 3, nhưng ba chunk khác từ 5/4/1 xuống 19/15/12 | Có nâng hạng nhưng Recall@5 giảm từ 4/11 xuống 2/11 |
| gold_012 | Bốn gold chunk từ 4/5/1/3 xuống 10/19/13/17 | Các đơn vị cần thiết theo gold bị đẩy khỏi top 5 |

Với các câu cần nhiều Khoản, một chunk được nâng lên không bảo đảm đủ các
đơn vị còn lại. Trên tập này, số câu mất nhóm đúng nhiều hơn số câu chỉ
được thêm nhóm đúng. Đây là tác động đo được; nguyên nhân ngữ nghĩa cần
Người 2 review query, passage và nhãn trong VLRA-56/57.

Hai ca lỗi có kiểm tra tokenizer độc lập trong
[reranker-length-check.json](../../team2_rag/data/evaluation/colab-20261031/reranker-length-check.json):

- `gold_027`: ba cặp vượt giới hạn, lần lượt 975, 715 và 913 token.
- `gold_032`: một cặp dài 532 token.

Đây là số token của cả query–passage bằng tokenizer đúng revision BGE.
Adapter từ chối các cặp vượt 512, nên hai câu không có kết quả rerank.
Không có lỗi retrieval trong lượt chạy. Việc xử lý passage dài thuộc phần
review và tối ưu của Người 2; lần khảo sát này giữ nguyên adapter hiện có.

## Đầu vào cho VLRA-58

Chưa chốt cấu hình tối ưu. Bàn giao Hybrid không rerank làm mốc đối chiếu
và giữ raw output của cả hai nhánh để Người 2 review các ca hạ hạng và
passage dài. Sau khi có Dev được review/đóng băng, chạy lại phép so sánh;
nếu sửa reranker/context thì ghi version mới và đo lại. Không chọn cấu hình
bằng Test Set hoặc coi khảo sát hiện tại là nghiệm thu cuối.

Phần công cụ, lượt khảo sát và báo cáo của Người 1 đã có bằng chứng.
VLRA-54/55 chưa được ghi Done theo điều kiện benchmark Dev chính thức;
VLRA-58 còn bước tổng hợp và thống nhất cấu hình với Người 2.
