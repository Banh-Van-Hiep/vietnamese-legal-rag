# Data Processing Flow

## 1. Mục tiêu

Xây dựng quy trình xử lý dữ liệu pháp luật từ văn bản gốc
thành các chunk có cấu trúc và metadata thống nhất, phục vụ
cho BM25 Retrieval và Dense Retrieval.

---

## 2. Tổng quan quy trình

```text
Legal Documents
      ↓
Data Collection
      ↓
Cleaning & Normalization
      ↓
Structure Extraction
      ↓
Chunking
      ↓
Generate chunk_id
      ↓
Add Metadata
      ↓
Data Validation
      ↓
Legal Dataset
      ↓
Retrieval

## 3. Các bước xử lý

### 3.1. Data Collection
Thu thập các văn bản trong phạm vi dữ liệu đã xác định.

### 3.2. Cleaning & Normalization
- Loại bỏ định dạng không cần thiết.
- Chuẩn hóa khoảng trắng.
- Loại bỏ ký tự lỗi.
- Giữ nguyên nội dung pháp lý.

### 3.3. Structure Extraction
Xác định cấu trúc:
Document → Chapter → Article → Clause → Content

### 3.4. Chunking
Chia văn bản theo Điều/Khoản theo Chunk Format Specification.

### 3.5. Generate chunk_id
Tạo `chunk_id` duy nhất cho mỗi chunk.

### 3.6. Add Metadata
Gắn các metadata:
- chunk_id
- document
- chapter
- article
- clause
- content
- source

### 3.7. Data Validation
Kiểm tra:
- chunk_id không trùng
- content không rỗng
- metadata đầy đủ
- thông tin Điều/Khoản phù hợp với nội dung
- source tồn tại

### 3.8. Legal Dataset
Xuất dataset đã xử lý để phục vụ BM25 và Dense Retrieval.

## 4. Output

Mỗi chunk sau xử lý có dạng:

{
  "chunk_id": "...",
  "document": "...",
  "chapter": "...",
  "article": "...",
  "clause": "...",
  "content": "...",
  "source": "..."
}