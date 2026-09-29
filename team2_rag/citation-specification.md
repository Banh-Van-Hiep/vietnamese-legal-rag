# Citation Specification

## Definition

Citation là liên kết từ một claim trong câu trả lời tới legal chunk làm nguồn tham khảo cho claim đó. Citation phải mang `chunk_id` và metadata nguồn khớp với chunk đầu vào; không được chỉ là URL hoặc tên điều luật do model tự đoán.

## Fields and Mapping

Citation schema: [`schemas/citation.schema.json`](schemas/citation.schema.json). Mỗi citation có `claim`, `chunk_id`, `document`, `article`, `clause` và `source`. Các metadata phải được sao chép từ chunk hợp lệ; `clause` có thể `null` nếu nguồn không cung cấp. `chunk_id`, document, article, clause và source không được chuẩn hóa lại theo suy đoán.

## Verification

Sau LLM output, Team 2 kiểm tra tối thiểu:

1. `chunk_id` tồn tại trong Context được gửi cho LLM (và do đó có trong tập retrieved sources đã chọn).
2. `document`, `article`, `clause` và `source` khớp metadata của đúng chunk đó, bao gồm nullability.
3. Citation claim không rỗng và citation phù hợp cấu trúc output.

Kiểm tra trên chỉ xác minh provenance/consistency, chưa chứng minh nguồn hỗ trợ ngữ nghĩa cho claim. Claim-support verification, citation coverage/accuracy và đánh giá chuyên gia là hướng mở rộng ở các tuần sau.

## Invalid Citation Handling

Không chuyển citation invalid tới Team 3 như citation đã xác minh. Ghi nhận lỗi validation nội bộ theo error handling đã thống nhất; bỏ citation không khớp. Nếu một claim cần nguồn nhưng không còn citation hợp lệ, thiết kế an toàn là loại/viết lại claim thành giới hạn thông tin hoặc trả lời rằng context không đủ, thay vì trình bày claim không có nguồn. Chính sách từ chối toàn bộ response so với lọc một phần cần được chốt trước implementation.

## Week 1 Status

Schema và verification rules là thiết kế; chưa có citation parser, verifier hoặc claim-support model.