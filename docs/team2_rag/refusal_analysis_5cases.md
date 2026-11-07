# Phân Tích Chi Tiết 5 Ca Từ Chối Trả Lời (Refusal Analysis) — Phối Hợp Người 1 & Người 2

**Thực hiện:** Người 2 (Verification Engine & Benchmark Suite)  
**Người nhận:** Người 1 (Đạt — Core Pipeline & Prompting)  
**Tập dữ liệu:** Golden Phase 1 (30 câu) — Đợt chạy Benchmark ngày 06/11/2026  
**Mã câu hỏi:** `gold_001`, `gold_003`, `gold_006`, `gold_014`, `gold_019`  

---

## 1. Tóm Tắt Hiện Trạng & Đánh Giá Tổng Quan

Cả 5 câu hỏi đều có trạng thái hệ thống trả về là **`insufficient_context`** (từ chối do không đủ dữ liệu căn cứ).

> [!IMPORTANT]
> **Nhận định cốt lõi của Người 2:**  
> LLM (`gemini-3.1-flash-lite`) và System Prompt v3 **hoạt động hoàn toàn đúng nguyên tắc**: Khi LEGAL CONTEXT không có điều luật quy định trực tiếp, LLM đã từ chối một cách trung thực, giải thích chi tiết lý do và không hề hallucination.  
> **Nguyên nhân gốc rễ (Root Cause) 100% nằm ở tầng Retrieval:** Với thiết lập `RAG_TOP_K=5`, các chunk điều luật mục tiêu bị phân tán và rớt khỏi Top-5.

---

## 2. Phân Tích Chi Tiết Từng Ca

### Ca 1: `gold_001`
- **Câu hỏi:** *Luật Doanh nghiệp quy định về những vấn đề gì?*
- **Điều luật mục tiêu:** Điều 1 Luật Doanh nghiệp 2020 (Phạm vi điều chỉnh).
- **Phản hồi của hệ thống:** *"Dữ liệu cung cấp không chứa thông tin tổng quát về phạm vi điều chỉnh hoặc các vấn đề mà Luật Doanh nghiệp quy định, mà chỉ cung cấp định nghĩa về vốn có quyền biểu quyết và quy định về chế độ làm việc của Hội đồng thành viên."*
- **Nguyên nhân:** Từ khóa câu hỏi quá rộng, BM25 bị nhiễu bởi từ *"Luật Doanh nghiệp"* xuất hiện ở hàng trăm chunk. Chunk Điều 1 bị trôi khỏi Top 5.

### Ca 2: `gold_003`
- **Câu hỏi:** *Theo Luật Doanh nghiệp, cổ đông là ai?*
- **Điều luật mục tiêu:** Khoản 3 Điều 4 Luật Doanh nghiệp 2020 (Giải thích từ ngữ: Cổ đông).
- **Phản hồi của hệ thống:** *"Các tài liệu được cung cấp không chứa quy định định nghĩa cụ thể về việc cổ đông là ai, mà chỉ đề cập đến các loại cổ đông như cổ đông sáng lập, cổ đông là nhà đầu tư nước ngoài..."*
- **Nguyên nhân:** Chunk trúng Top 5 chứa các quy định chi tiết về *cổ đông sáng lập*, *cổ đông ngoại*, trong khi chunk định nghĩa chung (Khoản 3 Điều 4) bị điểm thấp hơn và nằm ngoài Top 5.

### Ca 3: `gold_006`
- **Câu hỏi:** *Công ty TNHH hai thành viên trở lên được có tối thiểu và tối đa bao nhiêu thành viên? Thành viên có thể là tổ chức không?*
- **Điều luật mục tiêu:** Khoản 1 Điều 46 Luật Doanh nghiệp 2020 (từ 02 đến 50 thành viên, là cá nhân hoặc tổ chức).
- **Phản hồi của hệ thống:** *"Các tài liệu pháp luật được cung cấp không chứa thông tin về số lượng thành viên tối thiểu và tối đa của công ty trách nhiệm hữu hạn hai thành viên trở lên..."*
- **Nguyên nhân:** Các chunk được chọn rơi vào Điều 47 (góp vốn) hoặc Điều 48 mà không bốc trúng Điều 46 (định nghĩa công ty TNHH 2TV).

### Ca 4: `gold_014`
- **Câu hỏi:** *Điều lệ công ty phải quy định những nội dung chủ yếu nào theo Điều 24 Luật Doanh nghiệp?*
- **Điều luật mục tiêu:** Khoản 2 Điều 24 Luật Doanh nghiệp 2020 (Các nội dung chủ yếu của Điều lệ).
- **Phản hồi của hệ thống:** *"Các văn bản pháp luật được cung cấp tại LEGAL CONTEXT chỉ quy định về thành phần ký tên trên Điều lệ công ty khi đăng ký doanh nghiệp hoặc khi sửa đổi, bổ sung Điều lệ, không liệt kê các nội dung chủ yếu phải có trong Điều lệ công ty theo Điều 24..."*
- **Nguyên nhân:** Chunk được retrieve chứa Khoản 1 và Khoản 3 Điều 24 (người ký Điều lệ), nhưng đoạn trích dài bị cắt hoặc chunking tách Khoản 2 sang chunk khác.

### Ca 5: `gold_019`
- **Câu hỏi:** *Doanh nghiệp bị giải thể trong những trường hợp nào, phải đáp ứng điều kiện gì, và với trường hợp tự giải thể thì phải gửi hồ sơ cho cơ quan đăng ký kinh doanh theo các mốc thời hạn nào?*
- **Điều luật mục tiêu:** Điều 207 (Các trường hợp và điều kiện giải thể doanh nghiệp) và Điều 208.
- **Phản hồi của hệ thống:** *"Dữ liệu cung cấp không chứa thông tin về các trường hợp doanh nghiệp bị giải thể nói chung, điều kiện giải thể... Nguồn hiện tại chỉ quy định về trình tự, thủ tục giải thể trong trường hợp bị thu hồi Giấy chứng nhận đăng ký doanh nghiệp hoặc theo quyết định của Tòa án (Điều 209)."*
- **Nguyên nhân:** Retrieval lấy trúng chunk Điều 209 (giải thể cưỡng chế) thay vì Điều 207 và Điều 208.

---

## 3. Đề Xuất Giải Pháp Kỹ Thuật Gửi Người 1

1. **Về Prompt:** **Không cần sửa Prompt (giữ nguyên System Prompt v3).**  
   Prompt hiện tại từ chối rất chuẩn, giải thích rành mạch và có tính tự vệ cao trước ảo giác. Nếu nới lỏng prompt để LLM "cố trả lời" trong khi thiếu chunk, nguy cơ Hallucination sẽ tăng vọt.
2. **Về Retrieval & Tham Số:**
   - **Tăng `top_k` lên 10:** Khi chạy với `RAG_TOP_K=10` (đúng cấu hình mặc định của `runtime.py`), xác suất các điều luật như Điều 1, Điều 4, Điều 46, Điều 24 lọt vào context sẽ cao hơn đáng kể.
   - **Xem xét Query Preprocessing:** Các câu hỏi có chứa số hiệu điều luật cụ thể (ví dụ: *"theo Điều 24"*, *"theo Điều 16"*) nên được ưu tiên trích xuất và boost điểm cho chunk có metadata `article_id == "24"` trong bộ Hybrid Retriever của Team 1.
