# Context Builder

## Responsibility

Context Builder nhận danh sách reranked chunks, chọn tập phù hợp với câu hỏi và giới hạn context, sắp thứ tự để dễ đọc, đồng thời nhóm các chunk theo `document` và `article` để giữ quan hệ nguồn. Đây là thiết kế; chưa có thuật toán chọn hoặc tokenizer implementation.

## Proposed Selection and Ordering

1. Nhận kết quả theo thứ tự giảm dần `rerank_score`.
2. Loại các bản ghi thiếu định danh hoặc content rỗng theo lỗi contract; không tự sửa metadata.
3. Chọn theo độ liên quan cho tới khi đạt token/context budget. Nếu một chunk vượt phần budget còn lại, policy cắt/loại chunk cần được thống nhất và không được làm sai lệch nguồn; proposal ban đầu là bỏ qua chunk không vừa thay vì cắt nội dung pháp lý.
4. Giữ thứ tự relevance làm thứ tự phẳng của `chunks`; gom `chunk_ids` theo `document` + `article` trong `groups` để có thể trình bày theo nguồn.
5. Giữ nguyên `chunk_id`, `content`, `document`, `article`, `clause`, `source`, `retrieval_score` và `rerank_score` trên mỗi chunk.

Tokenization phụ thuộc provider/model. `token_budget` và `estimated_tokens` là số nguyên không âm; cách tính chính xác và mức dự phòng cho prompt phải được xác nhận trong benchmark/integration.

## Input and Output

**Input:** câu hỏi và danh sách reranked results theo [`schemas/rerank_output.schema.json`](schemas/rerank_output.schema.json).

**Output:** object Context theo [`schemas/context.schema.json`](schemas/context.schema.json), gồm `question`, `token_budget`, `estimated_tokens`, thứ tự `chunks` đã chọn và `groups` tham chiếu chunk theo document/article. Không bỏ metadata nguồn khi biến context thành prompt input.

## Example

Ví dụ minh họa cấu trúc, không phải trích dẫn pháp luật:

```json
{
  "question": "Người lao động được nghỉ phép bao nhiêu ngày?",
  "token_budget": 3000,
  "estimated_tokens": 180,
  "chunks": [
    {
      "chunk_id": "chunk-example-001",
      "content": "Example legal text supplied by the retrieval system.",
      "document": "Example document",
      "article": "Example article",
      "clause": null,
      "source": "example-source",
      "retrieval_score": 0.72,
      "rerank_score": 0.91,
      "position": 1
    }
  ],
  "groups": [
    {
      "document": "Example document",
      "article": "Example article",
      "chunk_ids": ["chunk-example-001"]
    }
  ]
}
```

## Open Decisions

Team 1 cần xác nhận field semantics/nullability và giới hạn candidate size. Team 2 cần benchmark tokenizer/budget và thống nhất xử lý chunk vượt budget trước khi triển khai.