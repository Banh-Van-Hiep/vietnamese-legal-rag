# Rubric Thẩm Định Trích Dẫn & Chống Ảo Giác (Citation Verification Rubric)
## Phân Hệ: RAG & LLM (Team 2 — Tuần 9, Mã Task: VLRA-T2-24, VLRA-67)

Tài liệu đặc tả phương pháp thẩm định ngữ nghĩa cho module **Citation Verification Engine** (`team2_rag/verification/`).

---

## 1. Mục Đích & Phạm Vi Ứng Dụng
Trong hệ thống hỏi đáp pháp lý, mô hình ngôn ngữ lớn (LLM) có thể mắc hai loại lỗi nghiêm trọng:
1. **Lỗi hình thức & Nguồn gốc (Provenance Error):** LLM tự bịa đặt mã trích dẫn, viện dẫn nhãn `[Cn]` không có trong context được cấp, hoặc tự sửa metadata Điều/Khoản luật.
2. **Lỗi ngữ nghĩa & Ảo giác (Semantic Hallucination):** LLM trích dẫn đúng điều luật có thật, nhưng câu trả lời lại khẳng định một nội dung mà điều luật đó không hề quy định, hoặc diễn giải trái ngược với quy định cấm của luật.

Module **Citation Verification** của Người 2 đóng vai trò là chốt chặn 2 tầng kiểm soát toàn bộ câu trả lời trước khi gửi ra ngoài.

---

## 2. Bản Chất Phương Pháp Thẩm Định
* **Phân loại phương pháp:** **Fast Lexical-Semantic Heuristic Filter** (Bộ lọc suy luận ngữ nghĩa gần đúng tầng đầu).
* **Đặc điểm kỹ thuật:**
  - Kết hợp phân tích phân cực phủ định/khẳng định và từ ngữ chỉ quyền hạn/nghĩa vụ (`_NEGATION_WORDS`, `_LEGAL_MODALS`).
  - Đối chiếu độ bao phủ từ vựng pháp lý (Legal Entity & Vocabulary Coverage) giữa từng nhận định (`Claim`) và đoạn văn bản luật được viện dẫn.
  - Tốc độ xử lý siêu nhanh ($< 1$ ms/claim trên CPU), chạy inline trực tiếp trong request mà không cần tốn chi phí gọi LLM lần 2 gây trễ hệ thống.
  - *Lưu ý:* Phương pháp này được sử dụng làm baseline và bộ lọc thời gian thực trong sản phẩm; chưa thay thế hoàn toàn cho mô hình Cross-Encoder NLI nặng hoặc chấm điểm chuyên gia ngoại tuyến.


> [!WARNING]
> **Giới hạn của phương pháp Lexical-Semantic Heuristic:**
> Rubric hiện tại chấm điểm dựa trên **độ trùng khớp từ vựng (word overlap)** kết hợp cực tính phủ định, KHÔNG phải mô hình hiểu ngữ nghĩa sâu (Full Semantic NLI / LLM-as-a-judge):
> - Điểm Citation Correctness / Coverage là **ước lượng gần đúng tầng đầu (fast lexical heuristic)**, chưa phải điểm NLI tuyệt đối.
> - Thống nhất đo ảo giác (Hallucination) song song ở 2 cấp: **Query-level** (tỷ lệ câu trả lời có ảo giác / tổng số câu answered) và **Claim-level** (tỷ lệ claim ảo giác / tổng số claim).

---

## 3. Rubric Thẩm Định Ngữ Nghĩa 4 Cấp Độ

Mỗi nhận định độc lập (`Claim`) được đối chiếu với các `ContextChunk` tương ứng theo thang điểm 4 mức:

| Cấp độ (Verdict) | Điểm số | Trạng thái | Tiêu chuẩn đánh giá |
| :--- | :---: | :---: | :--- |
| **SUPPORTED** | `1.0` | Hợp lệ | - Toàn bộ các thực thể, hành vi, quyền hạn, nghĩa vụ hoặc điều kiện áp dụng trong Claim đều tìm thấy căn cứ rõ ràng trong đoạn luật nguồn.<br>- Độ bao phủ từ vựng pháp lý $\ge 60\%$ và không có xung đột phân cực. |
| **PARTIAL** | `0.5` | Chấp nhận được | - Claim phản ánh phần lớn nội dung của điều luật nhưng có thể khái quát hóa hoặc thiếu một số điều kiện ràng buộc nhỏ.<br>- Độ bao phủ từ vựng từ $35\%$ đến $< 60\%$. |
| **UNSUPPORTED** | `0.0` | **ẢO GIÁC (Hallucination)** | - Khẳng định trong Claim không hề được đề cập hoặc suy diễn ngoài phạm vi điều luật được trích dẫn.<br>- Độ bao phủ từ vựng $< 35\%$. |
| **CONTRADICTED** | `-1.0` | **ẢO GIÁC NGHIÊM TRỌNG** | - Phát hiện mâu thuẫn trực tiếp về tính cấm đoán/quyền hạn (Ví dụ: điều luật quy định *"không có quyền thành lập"* nhưng Claim lại ghi *"được quyền thành lập"*). |

---

## 4. Quy Chuẩn Đo Lường Các Chỉ Số Benchmark (VLRA-T2-25)

Để tránh hiện tượng ngộ nhận kết quả khi không có mẫu đo thật, các chỉ số được định nghĩa chặt chẽ như sau:

### 4.1. Citation Correctness (Mục tiêu $\ge 90\%$)
$$\text{Citation Correctness} = \frac{\text{Số citation hợp lệ và thực sự hỗ trợ cho claim}}{\text{Tổng số citation trong câu trả lời}} \times 100\%$$
* *Quy tắc:* Nếu $\text{Tổng số citation} = 0$, chỉ số trả về `None` (ghi rõ `"chưa đo"`), **tuyệt đối không gán mặc định $100\%$**.

### 4.2. Citation Coverage (Mục tiêu $\ge 85\%$)
$$\text{Citation Coverage} = \frac{\text{Số claim được chứng minh bởi ít nhất một citation hợp lệ}}{\text{Tổng số claim trong câu trả lời}} \times 100\%$$
* *Quy tắc:* Nếu $\text{Tổng số claim} = 0$, chỉ số trả về `None` (ghi rõ `"chưa đo"`).

### 4.3. Thống Nhất Định Nghĩa Tỷ Lệ Ảo Giác (Hallucination Rate — Mục tiêu $\le 5\%$)
Hệ thống báo cáo đồng thời 2 chỉ số độc lập:
1. **Query-level Hallucination Rate (Theo câu trả lời):**
   $$\text{Query Hallucination Rate} = \frac{\text{Số câu trả lời có chứa ít nhất 1 claim bị UNSUPPORTED / CONTRADICTED}}{\text{Tổng số câu trả lời ở trạng thái answered}} \times 100\%$$
2. **Claim-level Hallucination Rate (Theo nhận định):**
   $$\text{Claim Hallucination Rate} = \frac{\text{Số claim bị UNSUPPORTED / CONTRADICTED}}{\text{Tổng số claim được phân tích}} \times 100\%$$

---

## 5. Ánh Xạ Lỗi Trong Pipeline & Contract
Khi tích hợp vào `RAGPipeline(verifier=verify_response)`:
* Nếu phát hiện Claim bị `UNSUPPORTED` / `CONTRADICTED` hoặc citation trỏ sai metadata Điều/Khoản:
  $\rightarrow$ Pipeline ném ngoại lệ `CitationInvalidError`.
  $\rightarrow$ FastAPI Service bắt lỗi và ánh xạ thành mã lỗi hợp đồng: **HTTP 502 / `CITATION_INVALID`** (đúng theo thỏa thuận liên team trong `contracts/v0.1/`).
