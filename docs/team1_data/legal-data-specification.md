# Legal Data Specification

## 1. Mục tiêu

Xác định phạm vi và cấu trúc dữ liệu pháp luật được sử dụng
cho hệ thống Vietnamese Legal RAG Assistant.

## 2. Phạm vi dữ liệu

Phạm vi dữ liệu ban đầu tập trung vào:

- Luật Doanh nghiệp 2020
- Các Nghị định liên quan
- Các Thông tư liên quan

## 3. Đơn vị dữ liệu

Dữ liệu pháp luật được tổ chức theo cấu trúc:

Văn bản → Chương → Điều → Khoản → Nội dung

## 4. Cấu trúc dữ liệu

Mỗi đơn vị dữ liệu sau khi xử lý sẽ được gắn các thông tin:

- chunk_id
- document
- chapter
- article
- clause
- content
- source

## 5. Nguồn dữ liệu

Mỗi văn bản được lưu kèm thông tin nguồn để có thể
truy xuất lại văn bản gốc.

## 6. Nguyên tắc lựa chọn dữ liệu

- Ưu tiên văn bản thuộc phạm vi Luật Doanh nghiệp 2020.
- Ưu tiên văn bản có liên quan trực tiếp đến nội dung được truy vấn.
- Bảo đảm có thông tin nguồn để truy xuất và kiểm chứng.