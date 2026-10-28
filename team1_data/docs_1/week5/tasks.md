# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 5
## Phân Hệ: Data & Retrieval (Team 1)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 5 (Quy đổi học phần: Tuần 2 cũ + 3 = Tuần 5 mới).
- **Mục tiêu trọng tâm:**
  - Thu thập dữ liệu thô (raw) và xây dựng pipeline làm sạch (cleaning) cho ít nhất 50% danh mục văn bản P0 pháp luật doanh nghiệp.
  - Vận hành pipeline phân tách để sinh tập dữ liệu chuẩn mực: `chunks.jsonl` (đầy đủ metadata) và `articles.jsonl` (nguyên văn Điều luật).
  - Xây dựng bảng kiểm soát hiệu lực đến từng đơn vị Khoản/Điểm: `unit_applicability.jsonl` với trạng thái `verified_current` và `pending_review`.
  - Cung cấp triển khai Mock Interface `get_article(document_id, article_id)` và fixture kiểm thử cho Team 3 tích hợp Document Viewer.
  - Đóng góp 5–10 câu hỏi pháp luật doanh nghiệp kèm ground truth và `gold_chunk_ids` thực tế cho bộ Golden Dataset ban đầu (30–50 câu).
  - Đáp ứng các tiêu chí Jira tuần 5: **VLRA16**, **VLRA17**, **VLRA18** và nghiệm thu **Gate G2 (Mock Integration)**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA16** | **Thu thập raw & Xây dựng Preprocessing Pipeline làm sạch văn bản P0**<br>- Thu thập văn bản chính thức: Luật 59/2020/QH14, Luật 03/2022/QH15, NĐ 168/2025/NĐ-CP, TT 68/2025/TT-BTC, NĐ 122/2021/NĐ-CP (bao phủ $\ge 50\%$ danh mục P0).<br>- Lưu trữ kèm file `fetch_info.json` ghi nhận URL nguồn, ngày tải, mã băm SHA-256.<br>- Xây dựng module làm sạch (`cleaner.py`): chuẩn hóa UTF-8 NFC, giữ nguyên dấu câu, chữ số, cấu trúc bảng biểu, loại bỏ menu/header/footer rác. | - Thư mục `data/raw/` chứa đầy đủ file gốc và metadata nguồn.<br>- Script `cleaner.py` chạy tự động, tạo text sạch tại `data/interim/`.<br>- Báo cáo đối chiếu raw vs clean không bị mất điều kiện pháp lý hoặc lỗi giải mã Unicode. |
| **VLRA17** | **Tạo lập Chunks, Articles & Bảng kiểm soát hiệu lực Unit Applicability**<br>- Lập trình module parser (`parser.py`) nhận diện cấu trúc Chương, Mục, Điều, Khoản, Điểm.<br>- Triển khai thuật toán chunking R1–R4 sinh `data/processed/chunks.jsonl`.<br>- Trích xuất nguyên văn toàn bộ Điều luật sinh `data/processed/articles.jsonl`.<br>- Khởi tạo bảng `data/registry/unit_applicability.jsonl` kiểm soát thời hạn áp dụng của từng Khoản/Điểm. | - `chunks.jsonl` và `articles.jsonl` pass 100% qua bộ validator Pydantic/JSON Schema.<br>- 100% chunk có `chunk_id` duy nhất và liên kết chính xác tới `article_id`.<br>- Các đơn vị luật bị sửa đổi được đánh dấu `pending_review` hoặc liên kết đúng văn bản sửa đổi. |
| **VLRA18** | **Đóng gói Legal Dataset v1 & Cung cấp Mock Interface Document Viewer**<br>- Tự động hóa chuỗi xử lý bằng script điều phối chung `run_pipeline.py`.<br>- Viết hàm Mock `get_article(document_id, article_id)` trả về dữ liệu mẫu trong Article Store thử nghiệm (VD: `mock_v1/art1`).<br>- Viết tài liệu hướng dẫn chạy pipeline và báo cáo chất lượng dữ liệu. | - Chạy lệnh `python run_pipeline.py` tái lập được toàn bộ dataset từ raw.<br>- Hàm `get_article` mock chạy độc lập không cần database, Team 3 tích hợp thành công.<br>- Hoàn tất tài liệu `team1_data/README.md` mô tả cấu trúc dữ liệu. |
| **VLRA24-T1** | **Xây dựng tập câu hỏi mẫu Golden Dataset của Team 1**<br>- Đóng góp 5–10 câu hỏi thực tế về thành lập doanh nghiệp, góp vốn và người đại diện.<br>- Xác định `ground_truth` chuẩn và gán đúng các `gold_chunk_ids` từ `chunks.jsonl` vừa tạo. | - 5–10 câu hỏi đạt chuẩn được nộp cho Team 3 tổng hợp vào file `golden_phase1_30cai.json`.<br>- 100% `gold_chunk_ids` tồn tại thật trong snapshot dữ liệu tuần 5. |

---

## 3. Ý Tưởng Giải Thuật & Thiết Kế Kỹ Thuật Chi Tiết

### 3.1. Pipeline Làm Sạch & Chuẩn Hóa Văn Bản (Cleaning Pipeline)
```
[Raw HTML / DOCX / PDF] 
       │
       ▼
[cleaner.py] ──> Chuẩn hóa Unicode NFC ──> Chuẩn hóa khoảng trắng & ngắt dòng
       │          Loại bỏ Header/Footer/Menu (Regex) ──> Bảo toàn ký tự pháp lý & Bảng
       ▼
[data/interim/{document_id}.txt]
       │
       ▼
[parser.py] ───> Regex nhận diện: Chương [IVXLCDM]+, Điều \d+, Khoản \d+, Điểm [a-z]\)
       │
       ├───> [articles.jsonl] (Lưu nguyên văn toàn Điều từ dòng tiêu đề đến hết Điều)
       └───> [chunker.py] (Áp dụng R1–R4, tính token embedding, gộp Search Text)
               │
               ▼
       [chunks.jsonl]
```

### 3.2. Cấu Trúc Bảng Kiểm Soát Hiệu Lực (Unit Applicability)
Mỗi bản ghi trong `data/registry/unit_applicability.jsonl` quản lý hiệu lực chi tiết đến cấp Khoản/Điểm:
```json
{
  "document_id": "luat-59-2020-qh14-v1",
  "article_id": "dieu-12",
  "clause": "k1",
  "point": null,
  "applicable_from": "2021-01-01",
  "applicable_to": null,
  "applicability_status": "verified_current",
  "checked_at": "2026-10-07T00:00:00Z",
  "checked_by": "Team1_Lead",
  "evidence_urls": ["https://vbpl.vn/..."],
  "related_document_keys": ["luat-03-2022-qh15"]
}
```
- **Quy tắc Indexing:** Chỉ các chunk có trạng thái `verified_current` mới được đưa vào index BM25 và Qdrant. Các chunk có trạng thái `pending_review` (đang đối chiếu sửa đổi) hoặc `verified_historical` (hết hiệu lực) bị cô lập khỏi context truy vấn mặc định.

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Chữ Ký Hàm Nội Bộ (Python Interface)
```python
from typing import Dict, Any, Optional

class LegalDataError(Exception):
    """Exception cơ sở cho phân hệ dữ liệu."""
    pass

class DocumentNotFoundError(LegalDataError):
    pass

class ArticleNotFoundError(LegalDataError):
    pass

def get_article(document_id: str, article_id: str, is_mock: bool = False) -> Dict[str, Any]:
    """
    Truy xuất nguyên văn toàn văn một Điều luật.
    
    Args:
        document_id: Định danh phiên bản văn bản (vd: 'luat-59-2020-qh14-v1').
        article_id: Định danh Điều (vd: 'dieu-12').
        is_mock: Cờ bật chế độ Mock trả về fixture thử nghiệm độc lập.
        
    Returns:
        Dict tuân thủ ArticleResponse schema:
        {
            "document_id": str,
            "document_title": str,
            "article_id": str,
            "article": str,
            "content": str,
            "source_url": str
        }
        
    Raises:
        DocumentNotFoundError: Mã lỗi 404 khi không tìm thấy văn bản.
        ArticleNotFoundError: Mã lỗi 404 khi không tìm thấy Điều.
    """
    if is_mock:
        if document_id == "mock_v1" and article_id == "art1":
            return {
                "document_id": "mock_v1",
                "document_title": "Văn bản thử nghiệm tích hợp Mock",
                "article_id": "art1",
                "article": "Điều 1",
                "content": "Điều 1. Quy định kiểm thử tích hợp\nNội dung mẫu này được dùng để chứng minh luồng mở Document Viewer hoạt động độc lập mà không cần nạp toàn bộ cơ sở dữ liệu thật.",
                "source_url": "https://example.com/mock-law"
            }
        raise ArticleNotFoundError(f"Mock article {article_id} in {document_id} not found")
    
    # Logic đọc thật từ articles.jsonl (sẽ hoàn thiện tại Tuần 6-7)
    raise NotImplementedError("Live Article Store đang trong quá trình lập chỉ mục")
```

### 4.2. Pydantic Schema Cho Unit Applicability
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class ApplicabilityStatus(str, Enum):
    VERIFIED_CURRENT = "verified_current"
    VERIFIED_HISTORICAL = "verified_historical"
    PENDING_REVIEW = "pending_review"

class UnitApplicabilityRecord(BaseModel):
    document_id: str = Field(..., regex=r"^[a-z0-9_-]+$")
    article_id: str = Field(..., regex=r"^dieu-[a-z0-9]+$")
    clause: Optional[str] = Field(None, regex=r"^k\d+$")
    point: Optional[str] = Field(None, regex=r"^[a-z]$")
    applicable_from: date
    applicable_to: Optional[date] = None
    applicability_status: ApplicabilityStatus
    checked_at: datetime
    checked_by: str
    evidence_urls: List[HttpUrl]
    related_document_keys: List[str]
```

### 4.3. Mẫu Dữ Liệu Chunks.jsonl (Ví dụ chuẩn)
```json
{
  "chunk_id": "luat-59-2020-qh14-v1__dieu-12__k1__0",
  "document_id": "luat-59-2020-qh14-v1",
  "document_key": "luat-59-2020-qh14",
  "document_title": "Luật Doanh nghiệp số 59/2020/QH14",
  "article_id": "dieu-12",
  "article": "Điều 12",
  "article_title": "Người đại diện theo pháp luật của doanh nghiệp",
  "clause": "Khoản 1",
  "point": null,
  "content": "Người đại diện theo pháp luật của doanh nghiệp là cá nhân đại diện cho doanh nghiệp thực hiện các quyền và nghĩa vụ phát sinh từ giao dịch của doanh nghiệp, đại diện cho doanh nghiệp với tư cách người yêu cầu giải quyết việc dân sự, nguyên đơn, bị đơn, người có quyền lợi, nghĩa vụ liên quan trước Trọng tài, Tòa án và các quyền, nghĩa vụ khác theo quy định của pháp luật.",
  "context_header": "Luật Doanh nghiệp số 59/2020/QH14 > Chương I: Những quy định chung > Điều 12: Người đại diện theo pháp luật của doanh nghiệp",
  "token_count": 105,
  "chunk_index": 0,
  "chunk_count": 1,
  "source_url": "https://vbpl.vn/bocongthuong/Pages/vbpq-toanvan.aspx?ItemID=143940"
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 1 $\rightarrow$ Team 2 (RAG)** | - File `chunks.jsonl` sơ bộ chứa các chunk thực tế của Luật Doanh nghiệp 2020.<br>- Báo cáo phân bố token và danh sách `chunk_id` thật. | Team 2 dùng để kiểm thử bộ Context Builder, đo đạc giới hạn prompt và thử nghiệm các kịch bản RAG Mock sát thực tế. | Lưu tại `team1_data/data/processed/chunks.jsonl`. |
| **Team 1 $\rightarrow$ Team 3 (Viewer)** | - Triển khai hàm `get_article(..., is_mock=True)`.<br>- Fixture mock `mock_v1` / `art1`. | Team 3 kiểm thử luồng click citation trên UI mở ra Document Viewer thành công trong kịch bản Mock (Gate G2). | Thư viện Python `team1_data` & JSON fixture. |
| **Team 1 $\rightarrow$ Cả nhóm (Evaluation)** | - 5–10 câu hỏi Golden Dataset đóng góp từ Team 1 có kèm `gold_chunk_ids` chính xác. | Team 3 tổng hợp thành tập `golden_phase1_30cai.json` ban đầu để kiểm thử độ phủ nghiệp vụ P0. | Gửi PR cập nhật vào `team2_rag/data/golden/`. |
