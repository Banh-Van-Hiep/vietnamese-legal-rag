# Reranker Design

## Lựa chọn khởi đầu

Đề xuất cross-encoder `BAAI/bge-reranker-v2-m3`: chấm trực tiếp cặp câu hỏi–đoạn văn, hỗ trợ đa ngôn ngữ theo [model card BAAI](https://huggingface.co/BAAI/bge-reranker-v2-m3). Đây là lý do chọn để thử trên tiếng Việt; chưa chứng minh độ chính xác với luật lao động. Không chọn `bge-reranker-base/large` làm mặc định vì model card mô tả chúng cho tiếng Trung/Anh.

| Tham số | Proposal |
| --- | --- |
| Candidate pool | 20 từ Team 1 |
| Context cuối | Tối đa 5 chunk, còn phụ thuộc token budget |
| Baseline đối chiếu | Không rerank, giữ rank của Team 1 |

## Thuật toán

1. Nhận candidate theo [I/O](rag-io-specification.md); kiểm tra định danh, metadata và thứ tự rank.
2. Chấm cặp `(câu hỏi đã diễn giải, content gốc)` cho toàn bộ pool.
3. Sắp điểm rerank giảm dần; khi bằng điểm, dùng rank retrieval gốc.
4. Chuyển toàn bộ pool đã xếp lại cho Context Builder. Builder chọn tối đa 5 chunk vừa budget; không loại pool xuống 5 trước khi kiểm tra độ dài.

Giữ nguyên 12 trường candidate Team 1. Điểm rerank lưu riêng theo `chunk_id`, không ghi đè `score/rank/retrieval_method`, không sửa nội dung hoặc tạo ID mới. Điểm retrieval và rerank không cùng thang đo, không biểu diễn độ chắc chắn pháp lý.

Đề xuất giới hạn rerank 5 giây trong ngân sách AI 45 giây. Cấu hình CPU/batch/input length cần đo khi implementation. Không cắt ngầm nội dung quá dài để chấm; nếu vượt giới hạn model hoặc rerank lỗi, dùng toàn bộ thứ tự retrieval gốc và ghi lý do nội bộ, không tạo điểm rerank giả. Fallback này chỉ áp dụng reranker; không che lỗi retrieval của Team 1.

## Đánh giá sau Week 1

So sánh baseline và model trên cùng pool/query set, đo nDCG@5/MRR, citation support và latency p50/p95. Câu hỏi điều kiện/ngoại lệ cần có trong tập đánh giá. Chỉ chốt model và tham số sau khi đo; Week 1 chưa cài model hoặc chạy benchmark.
