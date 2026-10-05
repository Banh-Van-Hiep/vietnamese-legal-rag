# Citation Specification

## Form theo Team 3

Theo [Team 3 v1.2, mục 1.7](../team3_fullstack/team3.md), citation có **9 trường bắt buộc**:

| Field | Nguồn và ràng buộc |
| --- | --- |
| `citation_id` | Team 2 gán `C1..C10`, liên tục theo lần xuất hiện đầu tiên trong answer |
| `chunk_id` | ID chunk trong context, 1–200 ký tự |
| `document_id`, `article_id` | Chép từ chunk; 1–200 / 1–100; ASCII chữ/số/`_`/`-` |
| `document_title`, `article` | Chép tên hiển thị; 1–500 / 1–100 |
| `clause`, `point` | Chép đúng string 1–100 hoặc null; luôn có key |
| `source_url` | Chép URL HTTPS tuyệt đối, tối đa 2048 ký tự |

Không thêm `claim/document/source/score` vào citation gửi Backend. Schema JSON cũ trong `schemas/` vẫn được giữ nguyên nhưng không mô tả form v1.2 này.

## Hiển thị và kiểm tra

Answer dùng marker `[C1]`, `[C2]` ngay sau nhận định được hỗ trợ. Frontend lấy citation tương ứng; mở điều luật bằng `document_id/article_id`, không suy ID từ tên hiển thị. Có thể hiển thị tên văn bản, điều/khoản/điểm và link nguồn.

Team 2 kiểm tra theo thứ tự:

1. Output hợp lệ về kiểu, `status` và giới hạn answer/citations.
2. Nhãn nguồn của LLM ánh xạ tới đúng chunk trong context đã gửi; metadata khớp nguồn. Nhãn lạ, URL/ID sửa hoặc trùng chunk là citation invalid.
3. Lấy các nguồn thực sự được dùng theo lần xuất hiện đầu tiên; ánh xạ nhãn tạm sang `C1..Cn` và thay marker đồng thời để không va chạm nhãn. Ví dụ chỉ dùng nguồn tạm C3 thì citation cuối và marker đều thành C1.
4. Tạo citation cuối từ metadata của đúng chunk đó; không có citation thừa, marker thiếu nguồn hoặc dùng nguồn không gửi cho LLM.
5. `answered` cần ≥1 citation, tối đa 10 theo API (thiết kế context tối đa 5); `insufficient_context` cần `[]` và không có marker.

Không bỏ citation sai rồi giữ lại nhận định chưa được hỗ trợ. Trả `CITATION_INVALID` khi provenance không hợp lệ, `INVALID_LLM_OUTPUT` khi JSON/form sai; Backend ánh xạ lỗi theo [I/O](rag-io-specification.md).

Khớp ID/metadata chỉ chứng minh nguồn nhất quán, không chứng minh nội dung nguồn hỗ trợ kết luận. Prompt yêu cầu bám nguồn; đánh giá thủ công phải kiểm tra điều kiện/ngoại lệ và citation support. Week 1 chưa triển khai verifier hoặc công bố chất lượng đã đo.
