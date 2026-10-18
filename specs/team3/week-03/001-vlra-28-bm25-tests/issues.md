# VLRA-28 — Lỗi và giới hạn

## BM25
Không phát hiện lỗi cơ chế/contract trong các unit test đã chạy. Benchmark là kết quả đo,
không phải tuyên bố toàn bộ câu hỏi đã tìm đủ căn cứ.

| ID | Loại | Evidence | Trạng thái/owner |
| --- | --- | --- | --- |
| B-Q01 | Relevance/nhãn cần review | 14/30 baseline thiếu ít nhất một gold ID ở top 20; 4/30 không có gold ID. Supplement retrieval_qa_036 không có gold trong top 20 | OPEN, Team 1/reviewer nhãn; xem bm25-cases.csv |
| B-L01 | Giới hạn snapshot | Recall20 hiện0.738160 khác0.805 minh họa; chưa có hash/protocol cũ để kết luận regression | Không so trực tiếp; giữ dữ liệu/lần đo riêng |
| B-L02 | Giới hạn pháp lý | Document legal_status, labels/corpus chưa chứng minh unit applicability | Review theo C5, không sửa corpus |

B-Q01 là exact chunk-ID recall theo nhãn hiện có. Các bản hợp nhất có thể chứa nội dung
liên quan tương đương nhưng chưa được gán nhãn; không tự sửa gold hoặc kết luận mọi miss
là lỗi thuật toán. Không tối ưu tham số trên chính bộ test trong lượt kiểm thử này.

## Lỗi regression ngoài phạm vi retrieval
R-P01 (MEDIUM, Team 1): scripts/preprocess_legal_data.py:143 gọi chunk_document,
nhưng data/doanh-nghiep/chunk_documents.py không cung cấp hàm đó. Hai test preprocess
ERROR, tái hiện cả chạy độc lập3 tests lẫn discovery81 tests. Không sửa pipeline/corpus.
Bằng chứng: ../evidence/preprocess-isolated.json và regression-results.json.
