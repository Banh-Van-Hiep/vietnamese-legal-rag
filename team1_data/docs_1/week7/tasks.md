# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 7
## Phân Hệ: Data & Retrieval (Team 1)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 7 (Quy đổi học phần: Tuần 4 cũ + 3 = Tuần 7 mới).
- **Mục tiêu trọng tâm:**
  - Chính thức đóng băng phiên bản dữ liệu pháp luật và Article Store v1 (Corpus Snapshot v1) kèm mã băm SHA-256 và `manifest.json`.
  - Tối ưu hóa hiệu năng và độ trễ của hàm `get_article()` (đạt p95 $\le 200$ms) để phục vụ trải nghiệm xem tức thì trên Document Viewer.
  - Phối hợp với Team 2 và Team 3 thẩm định tính hợp lệ pháp lý, đối chiếu căn cứ và xác minh `gold_chunk_ids` thực tế cho tập **Golden Dataset v1 (100–150 câu hỏi)** trước khi đóng băng.
  - Cung cấp nền tảng dữ liệu ổn định phục vụ buổi tích hợp và nghiệm thu toàn diện hệ thống: **Gate G2 (Mock Integration)** và **Gate G4 (Live RAG MVP)**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T1-10** | **Đóng băng Corpus Snapshot v1 & Sinh Manifest toàn vẹn dữ liệu**<br>- Rà soát toàn bộ các văn bản luật P0 đã thu thập và xử lý.<br>- Khóa chỉ mục BM25 và tạo snapshot collection trên Qdrant.<br>- Sinh file `data/manifests/snapshot_v1.json` ghi nhận commit hash, số lượng document/article/chunk, mã băm SHA-256 của toàn bộ các file dữ liệu. | - File manifest v1 được tạo lập và commit lên Git.<br>- Toàn bộ 3 team thống nhất sử dụng chung một `snapshot_id = "snapshot_v1"`.<br>- Không có bất kỳ thay đổi ngầm nào đối với corpus khi chưa tăng version. |
| **VLRA-T1-11** | **Tối ưu hóa hiệu năng Article Store & Caching Lookup**<br>- Chuyển đổi định dạng lưu trữ nguyên văn Điều luật sang chỉ mục tra cứu tốc độ cao (sử dụng indexed JSON / SQLite hoặc in-memory key-value map theo cặp `(document_id, article_id)`).<br>- Tối ưu bộ giải mã UTF-8 và giữ nguyên cấu trúc định dạng xuống dòng, thụt lề của Điều luật. | - Hàm `get_article(document_id, article_id)` đạt thời gian phản hồi p95 $\le 200$ms.<br>- Mở đúng 100% các Điều luật có trong danh mục P0 mà không bị lỗi thiếu chữ hoặc lỗi font. |
| **VLRA-T1-12** | **Thẩm định căn cứ & Xác minh Gold Chunk IDs cho Golden Dataset v1**<br>- Phối hợp với Team 3 rà soát danh sách 100–150 câu hỏi doanh nghiệp được đóng góp.<br>- Đối chiếu từng câu hỏi dạng `expected_status = "answered"` với nguyên văn luật để xác định các `gold_chunk_ids` chính xác và đầy đủ nhất.<br>- Xác định các nhóm đơn vị tương đương (`relevant_unit_groups`) đối với các Điều có nhiều sub-chunks. | - 100% câu hỏi `answered` trong Golden Dataset v1 có `gold_chunk_ids` hợp lệ tồn tại trong snapshot v1.<br>- Các câu `insufficient_context` có `gold_chunk_ids = []` và có ghi chú lý do pháp lý rõ ràng.<br>- Tập dataset được phê duyệt để đóng băng chia 60% Dev / 40% Test. |
| **VLRA-T1-13** | **Kiểm thử ổn định phục vụ Demo MVP End-to-End (Gate G4)**<br>- Tham gia đợt kiểm thử tích hợp chéo: Frontend React $\rightarrow$ Backend Java $\rightarrow$ FastAPI AI $\rightarrow$ Thư viện Team 1.<br>- Kiểm tra khả năng xử lý đồng thời khi có 5 người dùng tra cứu cùng lúc.<br>- Đảm bảo pipeline truy hồi không bị rò rỉ bộ nhớ (memory leak). | - Hệ thống chạy trơn tru trong kịch bản demo trực tiếp của Gate G4.<br>- Tỷ lệ lỗi tầng Retrieval đạt 0% trong suốt phiên kiểm thử tích hợp. |

---

## 3. Ý Tưởng Giải Thuật & Thiết Kế Kỹ Thuật Chi Tiết

### 3.1. Cấu Trúc Manifest Đóng Băng Dữ Liệu (`snapshot_v1.json`)
```json
{
  "snapshot_id": "snapshot_v1",
  "created_at": "2026-10-15T00:00:00Z",
  "git_commit": "ecf2e9c9669a57182e6822c495152f7b19de7ef4",
  "domain": "phap-luat-doanh-nghiep",
  "statistics": {
    "total_documents": 8,
    "total_articles": 320,
    "total_chunks": 2576,
    "verified_current_chunks": 2450,
    "pending_review_chunks": 126
  },
  "embedding_model": {
    "name": "AITeamVN/Vietnamese_Embedding",
    "dimension": 768,
    "max_seq_length": 512
  },
  "bm25_config": {
    "tokenizer": "underthesea_word_tokenize",
    "k1": 1.5,
    "b": 0.75
  },
  "file_hashes": {
    "chunks.jsonl": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "articles.jsonl": "sha256:ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
    "unit_applicability.jsonl": "sha256:5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"
  }
}
```

### 3.2. Thiết Kế Tối Ưu Hóa Article Store Tra Cứu Toàn Văn Điều
Để Document Viewer phản hồi tức thì dưới 200ms:
1. **In-Memory Hash Index:** Khi khởi động AI Service, một bảng chỉ mục bộ nhớ đệm `Dict[Tuple[str, str], int]` được xây dựng ánh xạ cặp khóa `(document_id, article_id)` tới vị trí byte offset trong file `articles.jsonl`.
2. **Seek & Read O(1):** Khi có yêu cầu xem Điều, hàm `get_article` thực hiện lệnh `f.seek(offset)` và đọc đúng 1 dòng JSON của Điều đó, không cần quét toàn bộ file hoặc tải toàn bộ nội dung lên RAM.

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Chữ Ký Hàm Article Store Đã Tối Ưu
```python
from typing import Dict, Any

def get_article(document_id: str, article_id: str) -> Dict[str, Any]:
    """
    Truy xuất nguyên văn Điều luật với độ trễ cực thấp (p95 <= 200ms).
    
    Args:
        document_id: Định danh phiên bản văn bản (vd: 'luat-59-2020-qh14-v1').
        article_id: Định danh Điều (vd: 'dieu-12').
        
    Returns:
        Dict gồm 6 trường phục vụ hiển thị Document Viewer:
        {
            "document_id": str,
            "document_title": str,
            "article_id": str,
            "article": str,
            "content": str,
            "source_url": str
        }
    """
    pass
```

### 4.2. Pydantic Schema Cho Golden Dataset Record
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class GoldenRecordSchema(BaseModel):
    id: str = Field(..., regex=r"^gold_[a-z0-9_]+_\d{3}$")
    question: str = Field(..., min_length=10, max_length=1000)
    expected_status: Literal["answered", "insufficient_context"]
    ground_truth: str = Field(..., min_length=1)
    gold_chunk_ids: List[str]
    citation: Optional[str] = None
    category: str
    author: str
```

### 4.3. Fixture Mẫu Cho Cặp Question - Gold Chunks Đã Xác Minh
```json
{
  "id": "gold_t1_001",
  "question": "Công ty cổ phần có bắt buộc phải có Ban kiểm soát không?",
  "expected_status": "answered",
  "ground_truth": "Công ty cổ phần có dưới 11 cổ đông và các cổ đông là tổ chức sở hữu dưới 50% tổng số cổ phần của công ty thì không bắt buộc phải có Ban kiểm soát, trừ trường hợp Điều lệ công ty có quy định khác.",
  "gold_chunk_ids": [
    "luat-59-2020-qh14-v1__dieu-137__k1__0"
  ],
  "citation": "Khoản 1 Điều 137 Luật Doanh nghiệp 2020",
  "category": "quan-tri-doanh-nghiep",
  "author": "Team1_Lead"
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 1 $\rightarrow$ Team 2 (RAG)** | - File manifest `snapshot_v1.json` và snapshot collection Qdrant ổn định.<br>- Kết quả xác minh `gold_chunk_ids` cho 100–150 câu hỏi Golden Dataset. | Team 2 sử dụng để kiểm thử grounded answer, tinh chỉnh prompt và đo đạc độ bao phủ trích dẫn (citation coverage). | Thư mục `team1_data/data/manifests/` và `team2_rag/data/golden/`. |
| **Team 1 $\rightarrow$ Team 3 (Viewer)** | - Dịch vụ tra cứu Điều luật siêu tốc qua `get_article()` đã test p95 $\le 200$ms. | Team 3 tích hợp Document Viewer mượt mà trên giao diện React, đảm bảo người dùng click citation mở ra Điều ngay lập tức. | Endpoint `/internal/v1/documents/{document_id}/articles/{article_id}`. |
| **Cả nhóm $\rightarrow$ Team 1** | - Các báo cáo lỗi không tìm thấy Điều luật hoặc mismatch ID phát sinh trong các ca kiểm thử E2E. | Team 1 bổ sung các alias hoặc xử lý các ca lỗi dữ liệu cá biệt. | Issue tracker trên Jira hoặc kênh trao đổi kỹ thuật. |
