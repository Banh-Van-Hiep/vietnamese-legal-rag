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

---

## 6. Kết Quả Thực Hiện (31/10/2026)

Ghi nhận tự động các task Team 1 thuộc phạm vi tuần 7 (hợp đồng Retrieval → Reranker, Golden Dataset, E2E). Chuyển từ `docs/weekly-changes/2026-10-31.md`.

### T1. `BM25Retriever._search` trả sai kiểu → test hồi quy
- **Đã đổi gì:** Không đổi code. Lỗi (`_search` trả `dict`, `retrieve()` bọc thêm lần nữa, Hybrid RRF nhận dict) **đã được sửa sẵn trên `develop`** (`eea5604`): `_search` trả `list[dict]`, `retrieve()` trả `{question, results}` phẳng. Chỉ thêm 2 test hồi quy dùng BM25 thật (test Hybrid cũ chỉ dùng retriever giả nên không bắt được lỗi này).
- **Vì sao:** Chặn lỗi tái xuất hiện khi merge các nhánh cũ (liên quan VLRA-35/37).
- **File:** `tests/test_bm25_retrieval.py`
- **Test chứng minh:** `BM25RetrieverTest::test_search_returns_flat_list_of_rows`, `BM25RetrieverTest::test_hybrid_rrf_receives_all_bm25_rows`.
- **Kết quả test (toàn bộ, `python3 -m pytest -q`):** trước 445 passed / 3 failed → sau 447 passed / 3 failed. 3 lỗi có sẵn trên `develop`, không liên quan (`tests/test_retrieval_edge_cases.py`: `DenseIntegrityTests` ×2, `EmbeddingEdgeTests` ×1). Không có lỗi mới.

### VLRA-35. Chuẩn hóa chunk_id/metadata Retrieval → Reranker
- **Đã đổi gì:**
  - `DenseRetriever.connect` từ chối index khi `query_prefix`/`passage_prefix` của embedder khác manifest (trước đây nối được, truy vấn ra vector sai không gian).
  - `DenseRetriever.connect` đếm point theo từng `chunk_id`: collection có 2 point cùng `chunk_id` → `RetrievalUnavailableError` (trước đây so sánh bằng `set` nên lọt, Reranker sẽ nhận `chunk_id` trùng và báo `Duplicate chunk_id`).
  - `l2_normalize` tính norm trên float64: vector float32 rất lớn không còn bị tràn thành vector 0.
  - Test hợp đồng mới: mọi chunk được index (2.576 chunk, lọc `legal_status`) sau `output_row` đều qua `team2_rag.reranker._validate`; đầu ra BM25 thật và Hybrid RRF qua được validator và giữ nguyên 9 trường metadata so với chunk nguồn.
- **Vì sao:** AC VLRA-35 "Reranker nhận đủ và chính xác chunk_id + metadata, không lỗi parse". Kiểm tra trên toàn corpus: 0 chunk bị Reranker từ chối. Trường "trang" không có trong contract v0.1 / chunk schema nên không áp dụng.
- **File:** `team1_data/retrieval/dense.py`, `team1_data/retrieval/embedding.py`, `tests/test_retrieval_reranker_contract.py`
- **Test chứng minh:** 3 test trước đây FAIL trong `tests/test_retrieval_edge_cases.py` (`DenseIntegrityTests` ×2, `EmbeddingEdgeTests` ×1) nay PASS; `tests/test_retrieval_reranker_contract.py` (3 test).
- **Kết quả test toàn bộ:** trước 447 passed / 3 failed → sau 453 passed / 0 failed.

### VLRA-37. Kiểm thử luồng truy xuất trong E2E MVP — [!] làm một phần
- **Đã đổi gì:** Test E2E mới ghép đúng như `team2_rag.runtime.build_runtime`: corpus thật 2.576 chunk → BM25 `save`/`load` → Dense trên Qdrant in-memory (`save`/`connect`) → `HybridRetriever(BM25SearchAdapter(bm25), dense)` → `RAGPipeline` Team 2 (reranker `strict=True` + LLM giả). Kiểm tra: 2 manifest cùng `index_version` + cùng tập `chunk_id` (điều kiện runtime), đầu ra Hybrid đúng `contracts/v0.1/retrieval_output.schema.json`, metadata trùng chunk nguồn, chỉ chunk còn hiệu lực; pipeline trả `answered` với trích dẫn đúng chunk đã truy xuất (5 câu hỏi).
- **Chưa làm được (lý do không chuyển Done):** chỉ thay model bằng bản giả (embedder băm, scorer đếm từ, LLM giả) vì môi trường chặn HuggingFace (403) và không có Ollama/Qdrant server; phần "phối hợp với Team 3" khi Frontend/Backend gọi API thật cần người chạy cùng Team 3 (VLRA-62/63).
- **File:** `tests/test_retrieval_e2e.py`
- **Test chứng minh:** `RetrievalE2ETest` (3 test, 10 subtest, ~15 s).
- **Kết quả test toàn bộ:** 453 passed → 456 passed, 0 failed.

### VLRA-36. Golden Dataset Phase 1 (110 câu)
- **Đã đổi gì:** `team1_data/golden/golden_phase1.json` = 40 câu Team 2 (giữ nguyên, thêm `source`/`review_status`) + 70 câu mới (`gold_041`–`gold_110`): 48 câu từ Luật Doanh nghiệp hợp nhất 67/VBHN-VPQH, 22 câu từ Nghị định 168/2025/NĐ-CP; mỗi câu 1 `gold_chunk_ids` cấp Khoản, `ground_truth` trích **nguyên văn** chunk, `citation` Khoản/Điều/số văn bản; không trùng Điều với 40 câu cũ. Đây là Dev Set cố định cho VLRA-48..53.
- **Vì sao:** VLRA-36 cần 100–150 QA pairs có ground-truth chunk; không bịa nội dung pháp luật (đáp án lấy thẳng từ văn bản trong repo).
- **Lưu ý:** 70 câu mới đánh `review_status = draft_needs_legal_review` — cách đặt câu hỏi nên được người có chuyên môn pháp lý rà soát.
- **File:** `team1_data/golden/golden_phase1.json`, `team1_data/golden/README.md`, `tests/test_golden_phase1.py`
- **Test chứng minh:** `tests/test_golden_phase1.py` (5 test, 220 subtest): đủ 100–150 câu, qua `validate_cases`, đủ trường, đáp án nguyên văn, 40 câu Team 2 không bị sửa.
- **Kết quả test toàn bộ:** 456 → 461 passed, 0 failed.

