# Phân Tích Chi Tiết 5 Ca Từ Chối Trả Lời (Refusal Analysis) — Phối Hợp Người 1 & Người 2

**Thực hiện:** Người 2 (Verification Engine & Benchmark Suite)  
**Người nhận:** Người 1 (Đạt — Core Pipeline & Prompting)  
**Tập dữ liệu:** Golden Phase 1 (30 câu) — Đợt chạy Benchmark ngày 06/11/2026  
**Mã câu hỏi:** `gold_001`, `gold_003`, `gold_006`, `gold_014`, `gold_019`  

---

## 1. Tóm Tắt Hiện Trạng & Đánh Giá Tổng Quan

Cả 5 câu hỏi đều có trạng thái hệ thống trả về là **`insufficient_context`** (từ chối do không đủ dữ liệu căn cứ).

> [!IMPORTANT]
> **Nhận định của Người 2 (giữ lại, chưa kiểm chứng đủ):** LLM và System Prompt v3 từ chối đúng nguyên tắc vì LEGAL CONTEXT không chứa điều luật cần thiết, nguyên nhân nằm ở tầng Retrieval với `RAG_TOP_K=5`.
> **Kiểm tra của Người 1 (mục 4):** với 3 trong 5 ca (gold_001, gold_006, gold_014), điều luật đúng đứng trong top 5 của Hybrid ở lượt Colab 02/11. Không thể kết luận "100% do top_k" khi chưa có danh sách chunk của lần chạy 06/11.

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

## 3. Đề Xuất Của Người 2 (chưa kiểm chứng)

1. Giữ nguyên System Prompt v3, vì nới lỏng sẽ tăng nguy cơ hallucination.
2. Tăng `top_k` lên 10 (đúng mặc định của `runtime.py`) và xem xét ưu tiên chunk theo số điều trong câu hỏi.

Cả hai chưa được chạy thử. Xem mục 4 để biết vì sao chưa thể kết luận.

---

## 4. Kiểm Tra Bằng Dữ Liệu Hybrid Có Sẵn (Người 1, 08/11/2026)

Nguồn: `team2_rag/data/evaluation/colab-20261102/reranker-exploratory.json`, Hybrid top 20 trên cùng 2.576 chunk, embedding `AITeamVN/Vietnamese_Embedding`, trọng số **1:1** (khác 0,5:1 của lượt 06/11), cùng Golden. Thứ hạng của chunk đúng (`gold_chunk_ids`) trong top 20:

| Ca | Thứ hạng chunk đúng trong Hybrid | Trong top 5? | Trong top 10? | Nhận xét |
| :--- | :--- | :---: | :---: | :--- |
| gold_001 | 2 | Có | Có | Điều 1 lẽ ra có trong context nhưng LLM vẫn từ chối |
| gold_003 | Không có trong top 20 | Không | Không | Retrieval trượt hoàn toàn; tăng `top_k` không giúp |
| gold_006 | 2 | Có | Có | Giống gold_001 |
| gold_014 | 1, 2, 4, 7 (4 nhóm gold) | 3/4 nhóm | 4/4 nhóm | Điều 24 khoản 2 ở vị trí 2 |
| gold_019 | 10 (1/5 nhóm gold) | Không | Có 1/5 | `top_k=10` chỉ lấy thêm một phần căn cứ |
| gold_002 (ca "thất bại thật") | 1, 2 | Có | Có | Chunk đúng ở vị trí 1; không phải "thiếu dữ liệu truy xuất" |

**Kết luận có bằng chứng:**
- Chỉ gold_003 và gold_019 phù hợp với giải thích "retrieval trượt". Còn lại không thể đổ hết cho `top_k=5` nếu Hybrid ở lượt 06/11 hoạt động giống lượt Colab.
- Khác biệt có thể nằm ở trọng số (0,5:1), hoặc retrieval của lượt 06/11 chạy khác (báo cáo ghi trọng số bằng giá trị mặc định cứng, không chứng minh Dense hoạt động), hoặc LLM từ chối quá mức dù chunk đúng có trong context. Ba khả năng này dẫn đến hai cách sửa khác nhau (retrieval hay prompt), nên không thể kết luận "không cần sửa prompt".
- Lượt 06/11 không lưu danh sách chunk. Runner đã được sửa để lưu `retrieved_chunk_ids`, `context_chunk_ids`, `gold_chunk_ids` cho mỗi câu.

**Việc cần làm để kết luận (chạy trên máy có Qdrant hoặc Colab):** chạy lại 30 câu với `RAG_TOP_K=10`, `RAG_RERANK=false`, `RAG_BM25_WEIGHT=0.5`, `RAG_DENSE_WEIGHT=1`, `LLM_ALLOW_FALLBACK=false`; với 5 ca này so `context_chunk_ids` với `gold_chunk_ids`. Chunk đúng có mặt mà LLM vẫn từ chối: lỗi prompt. Chunk đúng vắng mặt: lỗi retrieval.
