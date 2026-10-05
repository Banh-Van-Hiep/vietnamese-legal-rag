# Schema cũ — deprecated / alias

Nguồn chuẩn là [bốn schema contracts/v0.1](../../../contracts/v0.1/README.md).
Các đường dẫn cũ giữ lại để không làm hỏng link trong README đã merge.

| File cũ | Hiện tại |
| --- | --- |
| request.schema.json | Alias query_request.schema.json |
| retrieval_output.schema.json | Alias retrieval_output.schema.json chung |
| rag_response.schema.json | Alias rag_response.schema.json chung |
| error_response.schema.json | Alias error_response.schema.json chung |
| citation.schema.json | Alias items của citations trong RagResponse chung |
| rerank_output.schema.json, context.schema.json, llm_input.schema.json, llm_output.schema.json | Bản nháp nội bộ deprecated; không dùng cho thiết kế mới/runtime |

Alias không hỗ trợ payload cũ question-only, document/source hoặc claim.
Mục tiêu là một nguồn validation, không phải duy trì protocol cũ.
Bốn bản nháp nội bộ được giữ để tra lịch sử; thiết kế mới mô tả bước nội bộ
trong Markdown, không đưa chúng thành contract liên team.
Resolver phải dùng file URI của schema để giải ref tương đối, không phụ thuộc mạng.
