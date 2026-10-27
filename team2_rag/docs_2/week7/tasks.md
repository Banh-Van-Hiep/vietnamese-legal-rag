# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 7
## Phân Hệ: RAG & LLM (Team 2)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 7 (Quy đổi học phần: Tuần 4 cũ + 3 = Tuần 7 mới).
- **Mục tiêu trọng tâm:**
  - Hoàn thiện module **Citation Validator & Output Parser**: tự động trích xuất các nhãn trích dẫn `[Cn]` trong câu trả lời, remap đồng bộ và chuẩn hóa thứ tự xuất hiện sang danh sách đối tượng trích dẫn có đầy đủ 9 trường metadata.
  - Xử lý phân định triệt để và rạch ròi giữa trạng thái nghiệp vụ `insufficient_context` (trả về HTTP 200 OK kèm `citations = []`) và các lỗi kỹ thuật hệ thống (502 Upstream Invalid, 503 Service Unavailable, 504 Upstream Timeout).
  - Phối hợp với Team 1 và Team 3 thẩm định tính khả thi nghiệp vụ (`answerability`) và tiêu chí chấm điểm rubric cho bộ dữ liệu chuẩn **Golden Dataset v1 (100–150 câu hỏi)** trước khi đóng băng.
  - Ổn định dịch vụ AI Service, hỗ trợ chuyển đổi linh hoạt giữa Live mode và Mock mode qua cờ môi trường, phục vụ nghiệm thu **Gate G2 (Mock Integration)** và **Gate G4 (Live RAG MVP)**.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T2-10** | **Hoàn thiện Citation Validator & Đồng bộ Remapping nhãn `[Cn]`**<br>- Regex quét toàn bộ các marker trích dẫn `\[C\d+\]` trong nội dung `answer`.<br>- Kiểm tra tính hợp lệ: marker phải thuộc danh sách candidate đã đưa vào prompt (Context Membership).<br>- Tự động đánh số lại nhãn `[C1], [C2]...` theo thứ tự xuất hiện đầu tiên trong bài viết và cập nhật trường `citation_id` trong mảng `citations` tương ứng.<br>- Chặn hoàn toàn các trường hợp LLM tự sinh nhãn lạ hoặc mảng citations thừa/thiếu so với marker. | - Module `citation_validator.py` pass 100% test cases góc cạnh.<br>- Tỷ lệ không khớp giữa marker trong bài viết và mảng citations đạt 0%.<br>- Ném exception `UpstreamInvalidResponseError` (mã 502) nếu LLM sinh nội dung vi phạm ràng buộc ngữ nghĩa. |
| **VLRA-T2-11** | **Chuẩn hóa Error Handling & Phân định rạch ròi HTTP Status Codes**<br>- Rà soát toàn bộ các điểm phát sinh lỗi trong pipeline.<br>- Đảm bảo quy tắc: Thiếu căn cứ luật trong snapshot hoặc câu hỏi mơ hồ $\rightarrow$ Trả về HTTP 200 `status = "insufficient_context"`.<br>- Các sự cố: Qdrant sập/mất mạng $\rightarrow$ HTTP 503 `SERVICE_UNAVAILABLE`; LLM trả JSON rác $\rightarrow$ HTTP 502 `UPSTREAM_INVALID_RESPONSE`; Quá 45s $\rightarrow$ HTTP 504 `UPSTREAM_TIMEOUT`. | - Bộ middleware xử lý ngoại lệ trên FastAPI bắt trọn vẹn lỗi và trả về đúng Error Envelope.<br>- Tuyệt đối không biến lỗi sập mạng/timeout thành `insufficient_context`. |
| **VLRA-T2-12** | **Thẩm định Answerability cho Golden Dataset v1 (100–150 câu)**<br>- Tham gia rà soát cùng Team 3 trên danh sách 100–150 câu hỏi doanh nghiệp.<br>- Đánh giá tính khả thi: câu hỏi có đủ dữ kiện để LLM kết luận mà không cần suy đoán?<br>- Thiết lập đáp án mẫu (`ground_truth`) và danh sách điều kiện/ngoại lệ bắt buộc phải có trong câu trả lời chuẩn. | - 100% câu hỏi trong Golden Dataset v1 được gắn đúng nhãn `expected_status` (`answered` hoặc `insufficient_context`).<br>- Hoàn tất tài liệu hướng dẫn chấm Rubric 5 tiêu chí (thang điểm 0–10). |
| **VLRA-T2-13** | **Tích hợp E2E Live RAG MVP & Tổng duyệt Demo (Gate G4)**<br>- Kết nối toàn diện luồng: Frontend React $\rightarrow$ Backend Java $\rightarrow$ FastAPI AI Service $\rightarrow$ Retrieval Team 1 $\rightarrow$ LLM.<br>- Kiểm tra tính ổn định của luồng streaming SSE phía ngoài khi AI Service phản hồi kết quả hoàn chỉnh.<br>- Chuẩn bị kịch bản demo: 1 câu hỏi P0 trả lời chuẩn có citation, 1 câu hỏi thiếu dữ kiện trả về từ chối lịch sự, 1 tình huống xử lý lỗi. | - Bản demo Live RAG MVP hoạt động trơn tru trước nhóm.<br>- Trích dẫn hiển thị trên UI nhấp mở đúng Điều luật từ Article Store.<br>- Nghiệm thu thành công Gate G4. |

---

## 3. Ý Tưởng Giải Thuật, Quản Trị Token & Prompt Design

### 3.1. Thuật Toán Remapping & Thẩm Tra Trích Dẫn (Citation Remapping Algorithm)
```python
import re
from typing import List, Dict, Any, Tuple

def validate_and_remap_citations(
    raw_answer: str,
    context_candidates: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, Any]]]:
    # 1. Tìm toàn bộ các marker có dạng [C1], [C2]... theo thứ tự xuất hiện
    pattern = r"\[C(\d+)\]"
    found_markers = re.findall(pattern, raw_answer)
    
    if not found_markers:
        # Nếu không có marker nào mà status là answered -> Lỗi hoặc chuyển insufficient
        return raw_answer, []
        
    # 2. Tạo bản đồ thứ tự xuất hiện đầu tiên (First-occurrence map)
    unique_old_indices = []
    for m in found_markers:
        idx = int(m)
        if idx not in unique_old_indices:
            unique_old_indices.append(idx)
            
    # 3. Kiểm tra tính hợp lệ: chỉ số cũ có nằm trong phạm vi context cung cấp?
    total_candidates = len(context_candidates)
    for old_idx in unique_old_indices:
        if old_idx < 1 or old_idx > total_candidates:
            raise UpstreamInvalidResponseError(f"LLM đã bịa đặt nhãn [C{old_idx}] không tồn tại trong context!")
            
    # 4. Thiết lập ánh xạ từ nhãn cũ sang nhãn mới liên tục [C1], [C2]...
    remap_dict = {}
    new_citations = []
    for new_idx, old_idx in enumerate(unique_old_indices, start=1):
        remap_dict[f"[C{old_idx}]"] = f"[C{new_idx}]"
        
        cand = context_candidates[old_idx - 1]
        citation_obj = {
            "citation_id": f"C{new_idx}",
            "chunk_id": cand["chunk_id"],
            "document_id": cand["document_id"],
            "article_id": cand["article_id"],
            "document_title": cand["document_title"],
            "article": cand["article"],
            "clause": cand.get("clause"),
            "point": cand.get("point"),
            "source_url": cand["source_url"]
        }
        new_citations.append(citation_obj)
        
    # 5. Thay thế đồng loạt các nhãn cũ trong câu trả lời bằng nhãn mới
    remapped_answer = raw_answer
    for old_tag, new_tag in remap_dict.items():
        remapped_answer = remapped_answer.replace(old_tag, new_tag)
        
    return remapped_answer, new_citations
```

### 3.2. Tiêu Chí Nghiệp Vụ BIZ-02: Phân Định Rõ Ràng Mã Lỗi & Trạng Thái
- **Quy tắc vàng:**
  $$\text{Thiếu thông tin / Không tìm thấy luật trong snapshot} \implies \text{HTTP 200 OK } (\text{status: "insufficient\_context"})$$
  $$\text{Sự cố mạng, lỗi cú pháp JSON, timeout LLM} \implies \text{HTTP 5xx } (\text{Error Envelope})$$
- Tuyệt đối cấm lập trình `except Exception: return {"status": "insufficient_context"}` vì sẽ che giấu các lỗi sập hạ tầng nghiêm trọng.

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Pydantic Schema Cho Error Envelope
```python
from pydantic import BaseModel
from typing import Literal

class ErrorDetail(BaseModel):
    code: Literal[
        "INVALID_REQUEST",
        "UPSTREAM_INVALID_RESPONSE",
        "UPSTREAM_CONTRACT_ERROR",
        "SERVICE_UNAVAILABLE",
        "UPSTREAM_TIMEOUT",
        "INTERNAL_ERROR"
    ]
    message: str
    retryable: bool

class ErrorResponse(BaseModel):
    error: ErrorDetail
```

### 4.2. Mẫu Phản Hồi Khi Gặp Sự Cố Kỹ Thuật (HTTP 502 / 503 / 504)
```json
{
  "error": {
    "code": "UPSTREAM_INVALID_RESPONSE",
    "message": "Mô hình ngôn ngữ sinh câu trả lời không đúng cấu trúc hoặc trích dẫn căn cứ không hợp lệ.",
    "retryable": false
  }
}
```

### 4.3. Mẫu Phản Hồi Khi Thiếu Căn Cứ (HTTP 200 Insufficient Context)
```json
{
  "status": "insufficient_context",
  "answer": "Theo các tài liệu pháp luật hiện có trong hệ thống, chưa có quy định cụ thể về việc thành lập công ty có 100% vốn đầu tư từ cá nhân nước ngoài trong ngành nghề này. Bạn vui lòng bổ sung thông tin chi tiết về mã ngành kinh tế để được giải đáp cụ thể.",
  "citations": []
}
```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 2 $\rightarrow$ Team 3 (Backend)** | - AI Service v1 hoàn chỉnh, ổn định 100% các trường dữ liệu và mã lỗi.<br>- Khả năng chuyển đổi mượt mà giữa mock và live qua cờ `MOCK_MODE`. | Team 3 tích hợp chốt hạ Public SSE stream và cơ chế phục hồi gián đoạn (Recovery pending > 60s). | Endpoint `/internal/v1/query` trên môi trường chạy thử. |
| **Team 1 $\rightarrow$ Team 2 (Retrieval)** | - Snapshot dữ liệu v1 đã đóng băng (`snapshot_v1.json`).<br>- Qdrant collection và BM25 index hoạt động ổn định không bị thay đổi ngầm. | Team 2 sử dụng để đảm bảo mọi trích dẫn sinh ra đều có thể truy hồi lại được nguyên văn Điều luật từ Article Store. | Chỉ mục local và thư viện `team1_data`. |
| **Team 2 $\rightarrow$ Cả nhóm (Evaluation)** | - Rubric chấm điểm 5 tiêu chí (0–10 điểm) và bảng thẩm định `answerability` cho tập Golden Dataset v1. | Toàn nhóm sử dụng để chuẩn bị cho các đợt tối ưu tuần 8–10 và benchmark tuần 11. | File `docs/evaluation.md` / Bảng tính rubric. |
