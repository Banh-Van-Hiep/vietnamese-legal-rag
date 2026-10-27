# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 4
## Phân Hệ: Data & Retrieval (Team 1)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 4 (Quy đổi học phần: Tuần 1 cũ + 3 = Tuần 4 mới).
- **Mục tiêu trọng tâm:**
  - Thiết kế kiến trúc tổng thể của tầng Data Processing và Data Pipeline phục vụ tra cứu pháp luật doanh nghiệp Việt Nam (phạm vi P0).
  - Thiết lập quy chuẩn định danh ID pháp lý bất biến (`document_key`, `document_id`, `article_id`, `chunk_id`) và sơ đồ phân cấp dữ liệu.
  - Xây dựng quy tắc phân tách đoạn văn bản pháp lý (Chunking Rules R1–R4) với ngân sách token nghiêm ngặt (`MAX_TOKENS = 512`, `TARGET_TOKENS = 384`, `OVERLAP_TOKENS = 64`).
  - Thiết kế cấu trúc lưu trữ và tra cứu nguyên văn Điều luật (Article Store) phục vụ tính năng Document Viewer.
  - Đạt điều kiện nghiệm thu cổng **Gate G1 (Document Baseline)**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T1-01** | **Phân tích danh mục nguồn luật P0 & Thiết kế phân tầng lưu trữ dữ liệu**<br>- Khảo sát và đối chiếu nguồn chính thức: Luật 59/2020/QH14 [L1], Luật 03/2022/QH15 [L2], Luật 76/2025/QH15 [L3], NĐ 168/2025/NĐ-CP [L4], NĐ 296/2026/NĐ-CP [L5], TT 68/2025/TT-BTC [L6], TT 121/2026/TT-BTC [L7].<br>- Thiết lập cấu trúc thư mục dữ liệu phân tầng: `raw/`, `interim/`, `registry/`, `processed/`, `indexes/`, `manifests/`. | - Tài liệu danh mục nguồn P0 hoàn tất, có URL chính thức và mã băm.<br>- Cây thư mục `team1_data/data/` được khởi tạo chuẩn hóa.<br>- Được Team 2 và Team 3 ký duyệt kiến trúc. |
| **VLRA-T1-02** | **Quy chuẩn định danh ID pháp lý bất biến & Thiết kế Metadata**<br>- Định nghĩa cú pháp chuẩn cho 4 loại ID: `document_key`, `document_id`, `article_id`, `chunk_id`.<br>- Thiết kế schema metadata đầy đủ cho chunk và văn bản, phân định rõ version nội dung (`content_version`) và hiệu lực pháp lý (`effective_date`). | - Bộ quy tắc sinh ID được viết thành tài liệu đặc tả, 100% ID tuân thủ ký tự ASCII `[a-z0-9_-]`.<br>- JSON Schema định nghĩa trường metadata của chunk được tạo lập và validate thành công. |
| **VLRA-T1-03** | **Đặc tả giải thuật Chunking R1–R4 & Công thức Search Text**<br>- Thiết kế chi tiết logic cắt chunk theo cấp bậc cấu trúc Điều/Khoản/Điểm nhằm giữ nguyên vẹn câu dẫn và điều kiện pháp lý.<br>- Xác lập công thức `Search Text = context_header + "\n" + content`.<br>- Định lượng ngân sách token: `MAX = 512`, `TARGET = 384`, `OVERLAP = 64`, `MIN = 20`. | - Bộ quy tắc R1–R4 được mô tả bằng mã giả (pseudocode) và sơ đồ luồng.<br>- Các trường hợp góc cạnh (khoản dài, điểm phụ thuộc, bảng biểu) có giải pháp xử lý rõ ràng. |
| **VLRA-T1-04** | **Thiết kế kiến trúc Article Store & Cơ chế tra cứu toàn văn Điều**<br>- Thiết kế cơ sở dữ liệu/định dạng lưu trữ nguyên văn Điều luật (`articles.jsonl`) độc lập với chunk.<br>- Thiết kế cơ chế khóa kép `(document_id, article_id)` phục vụ API Document Viewer của Team 3 mà không cần nối ghép chunk. | - File schema của Article Store (`article.schema.json`) được ban hành.<br>- Thiết kế phương án lưu trữ đảm bảo truy xuất O(1) hoặc độ trễ p95 <= 1s. |
| **VLRA-T1-05** | **Đề xuất công nghệ Retrieval (BM25 + Qdrant) & Hợp nhất RRF**<br>- Khảo sát và lựa chọn thư viện lexical: `bm25s` kết hợp tokenizer tiếng Việt `Underthesea`.<br>- Thiết kế kiến trúc vector database Qdrant và mô hình embedding (`AITeamVN/Vietnamese_Embedding`).<br>- Thiết kế thuật toán Reciprocal Rank Fusion (RRF, `k = 60`). | - Tài liệu kiến trúc Retrieval được phê duyệt trong `docs/ARCHITECTURE.md`.<br>- Cấu hình Docker Compose mẫu cho Qdrant được chuẩn bị. |

---

## 3. Ý Tưởng Giải Thuật & Thiết Kế Kỹ Thuật Chi Tiết

### 3.1. Phân Tầng Dữ Liệu
```
team1_data/
├── data/
│   ├── raw/{document_id}/          # Văn bản gốc tải từ nguồn nhà nước (HTML, DOCX, PDF) + fetch_info.json
│   ├── interim/                    # Văn bản sau làm sạch sơ bộ, chuẩn hóa UTF-8 NFC
│   ├── registry/                   # Registry văn bản (documents.json) & bảng hiệu lực (unit_applicability.jsonl)
│   ├── processed/
│   │   ├── chunks.jsonl            # Tập chunk phục vụ Indexing & Retrieval
│   │   └── articles.jsonl          # Tập nguyên văn Điều luật phục vụ Document Viewer
│   ├── indexes/{snapshot_id}/      # Chỉ mục BM25 (sparse matrix) & Qdrant snapshots
│   └── manifests/{snapshot_id}.json # Manifest đóng băng phiên bản dữ liệu
```

### 3.2. Quy Chuẩn Sinh ID Pháp Lý Bất Biến
1. **`document_key`**: Định danh văn bản theo cấu trúc `{loại}-{số}-{năm}-{cơ_quan}` (chữ thường, gạch ngang).  
   *Ví dụ:* `luat-59-2020-qh14`, `nd-168-2025-nd-cp`.
2. **`document_id`**: Định danh phiên bản nội dung trích xuất của văn bản: `{document_key}-v{content_version}`.  
   *Ví dụ:* `luat-59-2020-qh14-v1`.  
   *Lưu ý:* `document_id` là bất biến theo nội dung file trích xuất; sửa lỗi chính tả/OCR sẽ tăng version text, không đồng nghĩa văn bản đổi ngày hiệu lực.
3. **`article_id`**: Định danh Điều luật: `dieu-{số/chữ}`.  
   *Ví dụ:* `dieu-12`, `dieu-13a`.
4. **`chunk_id`**: Khóa duy nhất toàn hệ thống của từng đoạn cắt:  
   `{document_id}__{article_id}__k{khoản}__{chunk_index}`  
   - Điều không chia Khoản: bắt buộc ghi `k0` (VD: `luat-59-2020-qh14-v1__dieu-1__k0__0`).
   - Điều có Khoản: ghi `k{số_khoản}` (VD: `luat-59-2020-qh14-v1__dieu-12__k1__0`).
   - `chunk_index`: số nguyên từ `0`, tăng liên tục khi 1 Khoản/Điểm bị cắt thành nhiều sub-chunks.

### 3.3. Giải Thuật Phân Đoạn Văn Bản (Chunking Rules R1–R4)
- **Quy tắc R1 (Điều đơn nguyên):** Nếu Điều không có Khoản và tổng số token $\le 512$ token $\rightarrow$ Đóng gói toàn bộ Điều thành 1 chunk duy nhất (`clause = null`, `point = null`).
- **Quy tắc R2 (Tách theo Khoản):** Nếu Điều có nhiều Khoản $\rightarrow$ Mỗi Khoản là 1 đơn vị cơ sở để tạo chunk. Tuyệt đối không gộp 2 Khoản ngắn vào cùng 1 chunk nhằm tránh xung đột trích dẫn.
- **Quy tắc R3 (Khoản dài có Điểm):** Nếu Khoản có nhiều Điểm và vượt ngưỡng `TARGET_TOKENS` (384 tokens) $\rightarrow$ Gom nhóm các Điểm liên tiếp. **Bắt buộc lặp lại câu dẫn nguyên văn của Khoản ở đầu mỗi chunk** để giữ trọn vẹn điều kiện pháp lý.
- **Quy tắc R4 (Cắt câu với Overlap):** Nếu một đơn vị Khoản/Điểm vẫn vượt `MAX_TOKENS` (512 tokens) $\rightarrow$ Cắt theo ranh giới câu trọn vẹn, áp dụng `OVERLAP_TOKENS = 64`. Overlap chỉ diễn ra nội bộ trong cùng đơn vị, không lan sang Khoản khác.
- **Cấu trúc Search Text:**
  $$\text{Search Text} = \text{context\_header} + \text{"\textbackslash n"} + \text{content}$$
  Trong đó `context_header` chứa phân cấp: `Văn bản > Chương > Mục > Điều {X}: {Tiêu đề Điều}`.

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Chữ Ký Hàm Nội Bộ (Python Interface)
```python
from typing import Dict, Any, Optional

def get_article(document_id: str, article_id: str) -> Dict[str, Any]:
    """
    Truy xuất nguyên văn toàn bộ Điều luật từ Article Store phục vụ Document Viewer.
    
    Args:
        document_id: Định danh phiên bản văn bản (vd: 'luat-59-2020-qh14-v1').
        article_id: Định danh Điều (vd: 'dieu-12').
        
    Returns:
        Dict tuân thủ ArticleResponse schema (đủ 6 trường snake_case).
        
    Raises:
        DocumentNotFoundError: Khi không tìm thấy văn bản.
        ArticleNotFoundError: Khi văn bản tồn tại nhưng không có Điều này.
    """
    pass
```

### 4.2. Pydantic Schema Cho Chunk & Article Store
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class ChunkMetadataSchema(BaseModel):
    chunk_id: str = Field(..., regex=r"^[a-z0-9_-]+__[a-z0-9_-]+__k\d+__\d+$")
    document_id: str = Field(..., regex=r"^[a-z0-9_-]+$")
    article_id: str = Field(..., regex=r"^dieu-[a-z0-9]+$")
    document_title: str = Field(..., min_length=1, max_length=500)
    article: str = Field(..., min_length=1, max_length=100)
    clause: Optional[str] = Field(None, max_length=100)
    point: Optional[str] = Field(None, max_length=100)
    content: str = Field(..., min_length=1, max_length=20000)
    context_header: str = Field(..., min_length=1, max_length=2000)
    source_url: HttpUrl
    token_count: int = Field(..., ge=1, le=1024)

class ArticleRecordSchema(BaseModel):
    document_id: str = Field(..., min_length=1, max_length=200)
    document_title: str = Field(..., min_length=1, max_length=500)
    article_id: str = Field(..., min_length=1, max_length=100)
    article: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=200000)
    source_url: HttpUrl
```

### 4.3. Mock Data Fixture Chuẩn
```json
{
  "document_id": "mock_v1",
  "document_title": "Luật Doanh nghiệp 2020 (Thử nghiệm)",
  "article_id": "art1",
  "article": "Điều 1",
  "content": "Điều 1. Phạm vi điều chỉnh\nLuật này quy định về việc thành lập, tổ chức quản lý, tổ chức lại, giải thể và hoạt động có liên quan của doanh nghiệp...",
  "source_url": "https://example.com/mock-law"
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 1 $\rightarrow$ Team 2 (RAG)** | - Đặc tả cấu trúc `chunk_id` và các trường metadata.<br>- Ngân sách token (`MAX_TOKENS = 512`) để tính toán prompt injection.<br>- Mock fixture của candidates retrieval. | Team 2 thiết kế Context Builder, Reranker và bộ lọc nhãn trích dẫn tạm `[C1]`, `[C2]`. | Thư mục `team1_data/data/registry/` và tài liệu tuần `tasks.md`. |
| **Team 1 $\rightarrow$ Team 3 (Viewer)** | - Chữ ký hàm `get_article(document_id, article_id)`.<br>- Schema 6 trường của Article Response (`document_id`, `document_title`, `article_id`, `article`, `content`, `source_url`). | Team 3 xây dựng endpoint Backend `GET /api/v1/documents/{documentId}?articleId={articleId}` và component UI Document Viewer. | Contract `contracts/v0.1/article_response.json` & Python stub. |
| **Team 2, 3 $\rightarrow$ Team 1** | - Danh mục câu hỏi kiểm thử ban đầu (User seed cases).<br>- Yêu cầu về thời gian phản hồi (p95 Retrieval $\le 1$s, Viewer $\le 1$s). | Team 1 cấu hình chỉ mục và tối ưu hóa giải thuật chunking phù hợp. | Họp review Gate G1 và văn bản kiến trúc hệ thống. |
