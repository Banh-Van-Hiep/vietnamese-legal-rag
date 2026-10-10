# Context Builder

## Mục tiêu và budget

Đóng gói nguồn pháp luật đủ nghĩa cho LLM, giữ nguyên nội dung và metadata từ Team 1. Không làm lại chunking, tóm tắt điều luật hoặc ghép chunk thành nguyên văn điều luật.

| Giới hạn khởi đầu | Giá trị |
| --- | --- |
| Context | Tối đa 5 chunk |
| Budget legal context | 3000 token, gồm nội dung, metadata và nhãn nguồn |
| Dự phòng output | 1500 token |
| Safety margin | 256 token |

Đếm bằng tokenizer của LLM được chọn trên prompt đã serialize. Token embedding/reranker không thay thế token LLM. Budget khả dụng = min(3000, context window model − token system/question/history được gửi − output reserve − margin). Nếu phần còn lại không đủ, không gửi prompt vượt giới hạn.

## Thuật toán đóng gói

1. Duyệt toàn bộ pool theo thứ tự rerank, hoặc rank retrieval khi dùng baseline/fallback.
2. Kiểm tra metadata, bỏ chunk trùng `chunk_id`; bản ghi vi phạm contract là lỗi, không tự sửa ID hoặc URL.
3. Thử thêm nguyên chunk cùng metadata vào context và đếm lại token. Nếu vượt budget, bỏ qua chunk đó và xét chunk tiếp theo.
4. Dừng khi đủ 5 chunk hoặc hết pool; giữ thứ tự đã chọn. Gán nhãn nguồn tạm `C1..Cn` cho lượt này.
5. Prompt chứa mỗi nhãn, `chunk_id/document_id/article_id/document_title/article/clause/point/source_url` và `content` nguyên bản. Không cần gửi score cho LLM.
6. Không còn nguồn đủ nghĩa thì trả `insufficient_context`; không lấy history thay nguồn.

Nguồn có thể thiếu phần mở đầu/điều kiện nếu chúng nằm ở chunk khác hoặc `context_header` không có trong retrieval payload. Không suy ra chúng từ tên điều luật; khi thiếu căn cứ quan trọng, nói rõ giới hạn hoặc hỏi thêm. Week 1 chưa đề xuất tự tải mở rộng cả điều luật.

Đầu ra builder là context nội bộ dùng để dựng prompt; không thêm schema/API liên team. Citation chỉ được chọn từ những chunk thực sự nằm trong prompt, theo [citation-specification.md](citation-specification.md).
