# Chunk Format Specification

## 1. Mục tiêu

Định nghĩa cách chia văn bản pháp luật thành các chunk
để phục vụ BM25 và Dense Retrieval.

## 2. Nguyên tắc chunking

Chunk được tổ chức ưu tiên theo:

Văn bản → Chương → Điều → Khoản

Một khoản có thể được xem là một đơn vị chunk khi nội dung
đủ ngắn và có ý nghĩa hoàn chỉnh.

Trường hợp nội dung quá dài, có thể tiếp tục chia thành
các chunk nhỏ hơn nhưng phải giữ lại thông tin Điều/Khoản.

## 3. Metadata

Mỗi chunk gồm các trường:

| Field | Ý nghĩa |
|---|---|
| chunk_id | Mã định danh duy nhất của chunk |
| document | Tên văn bản pháp luật |
| chapter | Chương |
| article | Điều |
| clause | Khoản |
| content | Nội dung của chunk |
| source | Nguồn văn bản |

## 4. Chunk Length

Chunk được ưu tiên tạo theo Điều/Khoản.

Độ dài cụ thể sẽ được thử nghiệm trong giai đoạn
đánh giá Retrieval.

Nếu một Điều/Khoản quá dài, có thể tiếp tục chia nhỏ
thành các chunk con trong khi vẫn giữ thông tin
Điều/Khoản tương ứng.