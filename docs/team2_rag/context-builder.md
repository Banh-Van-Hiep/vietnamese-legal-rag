# VLRA-10 — Context Builder

## Ngân sách thử nghiệm

| Thành phần | Giá trị |
| --- | ---: |
| Chunk đã chọn | Tối đa 5 |
| Legal context (gồm nhãn, metadata, separator) | Tối đa 3000 token |
| Output reserve | 1500 token |
| Safety margin | 256 token |

context_budget = min(3000, model_window - system_tokens - question_tokens
- output_reserve - safety_margin). Đếm với tokenizer/token counter của LLM đã chọn,
kể cả framing/messages. Nếu bật thinking thì tính cả thinking trong output reserve.
Không dùng số từ/ký tự/token_count embedding để thay số token LLM.
Week 1 chưa có token counter/runtime; đây là cấu hình thử nghiệm.

Team 1 đề xuất 512 token bằng tokenizer embedding. 5 × 512 không bảo đảm vừa
3000 token LLM khác; phải đếm lại khi đóng gói.

## Thuật toán

```text
budget = ngân sách context còn lại
selected = []
for candidate in pool đã rerank:
    nếu chunk_id đã chọn: bỏ qua
    block = metadata v0.1 + content nguyên vẹn
    nếu toàn context sau khi thêm block vượt budget: bỏ qua
    chọn block, giữ thứ tự relevance
    dừng khi đủ 5 chunk
gán C1..Cn và bảng nguồn trong bộ nhớ
```

Không cắt giữa Điều/Khoản, không LLM-tóm-tắt nguồn, không gộp hai chunk rồi tạo ID mới.
Cùng article_id nhưng chunk_id khác vẫn giữ riêng; không bỏ ngoại lệ vì cùng Điều.
Đếm lại toàn prompt trước khi gửi. Không còn chunk vừa → thiếu căn cứ,
không gửi prompt bị truncate.

## Định dạng context

Mỗi block serialize JSON đã escape; tách khỏi trusted system instruction:

```text
{
  "citation_id": "C1",
  "chunk_id": "<ID thật>",
  "document_id": "<ID thật>",
  "article_id": "<ID thật>",
  "document_title": "<nhãn thật>",
  "article": "<nhãn thật>",
  "clause": null,
  "point": null,
  "source_url": "<HTTPS URL thật>",
  "content": "<nguyên văn chunk>"
}
```

C1 là nhãn lượt hiện tại, không bắt Team 1 sinh.
Giữ null và metadata thật. Score/rank chỉ nằm trong diagnostics nội bộ.

## Đủ căn cứ/câu dẫn

Context không rỗng chưa chắc đủ căn cứ: giữ điều kiện/ngoại lệ, yêu cầu làm rõ
nếu thiếu dữ kiện, không dùng nội dung phụ thuộc câu dẫn chưa được gửi.
Team 1 có context_header chứa câu dẫn Điều nhưng field đó không có trong v0.1.
Team 2 không tự dựng câu dẫn từ tên Điều hoặc suy ra metadata thiếu.
Xem [điểm cần review](cross-team-review.md).
Article expansion/small-to-big để sau; không triển khai viewer thay Team 3.
