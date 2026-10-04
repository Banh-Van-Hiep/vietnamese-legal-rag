# Reranker Design

## Role

Team 1 trả về các candidate chunks được tìm thấy bằng retrieval. Reranker của Team 2 đánh giá mức liên quan của từng candidate với câu hỏi và sắp xếp lại thứ tự trước khi Context Builder chọn context. Reranking không thay thế BM25, dense retrieval, hybrid retrieval hoặc RRF; các phần retrieval này thuộc Team 1.

## Initial Top-K Proposal

| Parameter | Initial proposal | Meaning |
| --- | ---: | --- |
| Retrieval Top-K | 20 | Số candidate Team 1 chuyển sang Team 2 |
| Reranker Top-K | 5 | Số candidate Team 2 giữ lại cho context selection |

Đây là giá trị khởi đầu để benchmark, không phải cấu hình cuối. Reranker có thể đề xuất dùng cross-encoder để chấm cặp `(question, chunk)`; chưa chọn model, thư viện hoặc runtime cụ thể.

## Data Preservation

Mỗi kết quả sau rerank giữ nguyên `chunk_id`, `content`, `document`, `article`, `clause` và `source`. Điểm đầu vào `score` được biểu diễn là `retrieval_score`; reranker thêm `rerank_score`. Hai điểm có ý nghĩa và thang đo khác nhau, không ghi đè lên nhau. Thứ tự `results` là thứ tự giảm dần theo `rerank_score`.

Schema: [`schemas/retrieval_output.schema.json`](schemas/retrieval_output.schema.json) và [`schemas/rerank_output.schema.json`](schemas/rerank_output.schema.json).

## Future Benchmark Plan

Sau khi có dữ liệu đánh giá và implementation, so sánh baseline không rerank với cross-encoder trên cùng query set và cùng candidate pool. Theo dõi retrieval Top-K, reranker Top-K, Recall@K/MRR hoặc nDCG phù hợp, chất lượng answer/citation downstream, latency, throughput và chi phí. Tách tập tune và tập đánh giá; ghi rõ model/version, cấu hình và ngày chạy. Chưa kết luận model hoặc Top-K nào tốt nhất trước benchmark.

## Week 1 Status

Đây là thiết kế/proposal. Chưa có reranker code, model dependency hoặc benchmark result.