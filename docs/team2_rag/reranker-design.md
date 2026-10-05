# VLRA-10 — Reranker

## Lựa chọn Week 1

Đề xuất BAAI/bge-reranker-v2-m3, cross-encoder đa ngôn ngữ,
dùng sentence-transformers.CrossEncoder hoặc FlagEmbedding khi triển khai.
[Model card chính chủ](https://huggingface.co/BAAI/bge-reranker-v2-m3)
mô tả chấm query/passage trực tiếp và hỗ trợ multilingual.
Cross-Encoder là kiến trúc; BGE là model cụ thể, không phải hai lựa chọn loại trừ nhau.

| Phương án | Nhận xét |
| --- | --- |
| Không rerank | Baseline theo rank Team 1, ít latency |
| bge-reranker-base/large | Model card tập trung Trung/Anh; chưa ưu tiên cho tiếng Việt |
| bge-reranker-v2-m3 | Chọn thử nghiệm vì multilingual, đầu vào cặp văn bản |

Chưa có kết quả chứng minh tốt nhất cho luật lao động. Không tải model,
cài dependency, fine-tune hoặc đổi embedding Team 1 trong Week 1.

## Thuật toán

1. Validate RetrievalOutput: rank 1…N, score hữu hạn, không ID trùng.
2. Nhận tối đa 20 candidate từ retrieve(question, top_k=20).
3. Chấm cặp (question, nhãn document/article/clause/point + content).
4. Sắp rerank_score giảm; hòa điểm dùng rank gốc tăng rồi chunk_id.
5. Chuyển cả pool đã sắp cho builder, chọn tối đa 5 chunk vừa budget.
   Không cắt pool ngay tại 5 vì còn phải xét candidate sau khi chunk quá dài.

Giữ nguyên 12 field từ Team 1. score/rank vẫn thuộc retrieval;
rerank_score/vị trí rerank chỉ là nội bộ, không đưa vào citation/public response.
Score kể cả sigmoid 0–1 không là xác suất đúng về pháp luật.
Không đặt ngưỡng 0.5 tùy tiện để quyết định đủ căn cứ.

## Giới hạn và dự phòng

Giá trị thử nghiệm: batch_size=4, max_length=1024 token của tokenizer reranker,
ngân sách rerank 5 giây trong deadline AI 45 giây. Đây là mục tiêu, chưa đo.
CPU dùng FP32; chỉ thử FP16 trên accelerator hỗ trợ.
Kiểm tra độ dài trước khi chấm, không để tokenizer âm thầm truncate.
Nếu cặp quá dài, model lỗi hoặc hết budget: bypass rerank cho toàn pool của lượt,
giữ rank Team 1, ghi diagnostics nội bộ. Không trộn điểm đã/chưa chấm.
Content gốc luôn giữ nguyên cho builder; không dùng bản bị cắt làm chứng cứ.

## Benchmark Week 2

Cùng query set và candidate pool: baseline vs BGE; đo nDCG@5/MRR@5,
recall nguồn sau đóng gói, latency p50/p95, RAM và chất lượng answer/citation.
Ghi model revision, tokenizer, thiết bị và cấu hình. Tách tune/test.
Không tự thay retrieval/Hybrid/RRF của Team 1.
