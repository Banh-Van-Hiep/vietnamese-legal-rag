# Báo Cáo Phân Tích Lỗi Sinh Câu Trả Lời (`B0` vs `T0`) — Mốc G5 (VLRA-78)
## Phân Hệ: RAG & LLM (Team 2 — Tuần 11)

- **Ticket Jira:** `VLRA-78` (`VLRA-T2-43`)
- **Nguồn đối soát:** `docs/team2_rag/g5_b0_vs_t0_report.json` (`raw_results` của 77 câu thuộc `test_set_v1.json`).
- **Phương pháp phân loại:** Mỗi ca không đạt kỳ vọng (sai trạng thái `answered`/`insufficient_context`, bị đẩy chunk đúng ra khỏi top context, có claim `UNSUPPORTED`/`PARTIAL`, hoặc lỗi dịch vụ) được gắn **một nguyên nhân gốc rễ duy nhất** theo 3 nhóm của Jira (**Context**, **Prompt**, **Model**) và tách riêng **Lỗi dịch vụ** (`error`/`timeout`).

---

## 1. Bảng Tổng Hợp Phân Loại Lỗi (`B0` vs `T0`)

| Nhóm nguyên nhân | Nhóm con | Số ca ở **B0 (`BM25-only`)** | Số ca ở **T0 (`Hybrid + Rerank`)** | Mã câu hỏi trong `raw_results` |
| :--- | :--- | :---: | :---: | :--- |
| **1. Context** | **Retrieval thiếu** | `1` *(câu ngoài phạm vi gần ngữ cảnh)* | `1` *(câu ngoài phạm vi gần ngữ cảnh)* | `B0`: `test_073`<br>`T0`: `test_073` |
| | **Rerank / Context cut đẩy chunk đúng ra ngoài top 5** | `2` | `3` | `B0`: `test_054`, `test_062`<br>`T0`: `test_044`, `test_052`, `test_053` |
| **2. Prompt** | Từ chối nhầm khi chunk đúng đã có trong context | `2` | `1` | `B0`: `test_020`, `test_051`<br>`T0`: `test_051` |
| **3. Model** | Diễn đạt lệch từ vựng / trích nhầm nhãn metadata | `3` | `0` | `B0`: `test_003`, `test_045`, `test_053`<br>`T0`: *(không ghi nhận)* |
| **Lỗi dịch vụ** *(đếm riêng)* | Lỗi timeout LLM (`LLM_TIMEOUT`) | `0` | `1` | `T0`: `test_009` |
| **Vận hành phụ trợ** *(đếm riêng)* | Lùi về thứ hạng Hybrid do `RerankModelError` | `0` | `3` | `T0`: `test_032`, `test_059`, `test_061` *(vẫn trả lời đúng)* |

---

## 2. Chi Tiết Từng Ca Lỗi Truy Xuất Từ `raw_results`

### 2.1. Nhóm Context (`Retrieval thiếu` và `Đẩy chunk đúng ra ngoài Top 5 Context`)
1. **`test_062` (B0 — Đẩy chunk đúng ra ngoài Top 5 Context):**
   - *Hiện tượng:* Câu hỏi về trách nhiệm nợ khi thuê người quản lý và quyền góp vốn của chủ hộ kinh doanh (`Điều 84 Khoản 2, 4 NĐ 168/2025/NĐ-CP`). BM25 tìm được chunk đúng nhưng chấm điểm thấp hơn `nd-122-2021-nd-cp-v1__dieu-56__k1__0` (xử phạt hành chính), khiến LLM trả lời sai bản chất pháp lý (`1/10` điểm). Ở `T0`, Hybrid + Rerank đưa đúng `Điều 84` lên top và đạt `10/10`.
2. **`test_054` (B0 — Thiếu bản hợp nhất trong Top 5 Context):**
   - *Hiện tượng:* `vbhn-67-vbhn-vpqh-v1__dieu-39__k1/k2` nằm ngoài top 5 (`llm_context_chunk_ids`), tuy nhiên bản gốc `luat-59-2020-qh14-v1__dieu-39__k1/k2` vẫn lọt vào top 5 nên câu trả lời của B0 vẫn đúng nội dung (`10/10`).
3. **`test_052` (T0 — Rerank đẩy `Điều 67 Khoản 2` ra ngoài Top 5 Context):**
   - *Hiện tượng:* Câu hỏi 2 ý về thẩm quyền chấp thuận hợp đồng và thời hạn 15 ngày (`Điều 67 Khoản 1 & 2 Luật Doanh nghiệp`). Reranker của `T0` xếp `Điều 86` (DNNN) lên trên `Điều 67 Khoản 2`, làm `T0` thiếu vế thời hạn 15 ngày (`5/10` điểm), trong khi `B0` giữ đủ cả 2 khoản (`10/10`).
4. **`test_053` (T0 — Rerank đẩy `Điều 83` ra ngoài Top 5 Context):**
   - *Hiện tượng:* Câu hỏi về nguyên tắc thực hiện quyền/nghĩa vụ của người quản lý công ty TNHH một thành viên (`Điều 83 Khoản 2, 3`). Reranker đẩy `Điều 83` ra ngoài top 5, giữ `Điều 71` (quyền/nghĩa vụ chủ sở hữu), khiến `T0` trả lời đúng ý nhưng dẫn nhầm sang `Điều 71`.
5. **`test_044` (T0 — Rerank đẩy `Điều 3 Khoản 1 NĐ 288/2026` ra ngoài Top 5 Context):**
   - *Hiện tượng:* `gold_chunk_id` là `nd-288-2026-nd-cp-v1__dieu-3__k1__0` (hành vi không kê khai chủ sở hữu hưởng lợi), nhưng reranker xếp `Điều 2 Khoản 6` (kê khai không trung thực) lên đầu, làm câu trả lời lệch sang hành vi kê khai không trung thực.
6. **`test_073` (Cả B0 và T0 — Câu ngoài phạm vi gần ngữ cảnh / `insufficient_context`):**
   - *Hiện tượng:* Câu hỏi thuộc nhóm `refusal` (`expected_status: insufficient_context`), nhưng hệ thống truy xuất được các điều khoản định nghĩa chủ sở hữu hưởng lợi (`Điều 25 Luật DN`, `Điều 17–18 NĐ 168/2025`), dẫn đến việc cả hai hệ thống trả lời dựa trên ngữ cảnh tìm được thay vì từ chối.

### 2.2. Nhóm Prompt (`Từ chối nhầm dù chunk đúng đã nằm trong Top 5 Context`)
1. **`test_051` (Cả B0 và T0):**
   - *Hiện tượng:* Chunk `luat-59-2020-qh14-v1__dieu-106__k1__0` đã nằm trong `llm_context_chunk_ids` của cả B0 (vị trí 1) và T0 (vị trí 2), nhưng câu hỏi dùng cụm *"làm việc theo chế độ nào"* trong khi văn bản luật dùng *"xây dựng kế hoạch công tác hằng tháng, hằng quý, hằng năm..."*. Ràng buộc từ chối bảo thủ của prompt khiến LLM kết luận *"không chứa thông tin"*.
2. **`test_020` (B0):**
   - *Hiện tượng:* Chunk `luat-59-2020-qh14-v1__dieu-80__k5__0` đã có trong `llm_context_chunk_ids`, nhưng prompt yêu cầu đối chiếu chặt loại hình khiến LLM nhầm lẫn giữa *"công ty TNHH một thành viên"* và *"công ty TNHH một thành viên do tổ chức làm chủ sở hữu"* nên từ chối nhầm (`2/10` điểm). `T0` trả lời chính xác (`10/10`).

### 2.3. Nhóm Model (`Lỗi sinh trích dẫn hoặc suy luận diễn đạt`)
1. **`test_045` (B0 — `CITATION_INVALID`):**
   - *Hiện tượng:* Chunk đúng `nd-288-2026-nd-cp-v1__dieu-4__k3__0` đứng vị trí số 1 trong context, nhưng LLM sinh nhãn/metadata trích dẫn không khớp chunk đầu vào nên bị bộ kiểm chứng chặn với mã lỗi `CITATION_INVALID`.
2. **`test_003` (B0 — Claim `K2` bị đánh dấu `UNSUPPORTED` bởi bộ lọc từ vựng):**
   - *Hiện tượng:* LLM diễn đạt lại ngoại lệ *"trừ trường hợp... có thỏa thuận khác"* thành *"trách nhiệm này không áp dụng nếu... có thỏa thuận khác"*. Về mặt pháp lý câu trả lời hoàn toàn đúng (`10/10` điểm chấm mù), nhưng bộ kiểm chứng từ vựng (`rubric.py`) đánh dấu `UNSUPPORTED` do thay đổi cấu trúc phủ định/từ vựng.
3. **`test_053` (B0 — Claim `K1` bị đánh dấu `PARTIAL`):**
   - *Hiện tượng:* LLM chỉ nêu nguyên tắc *"trung thành"* ở `Điều 83 Khoản 3` mà bỏ sót nguyên tắc *"trung thực, cẩn trọng, tốt nhất"* ở `Điều 83 Khoản 2` (do chunk `k2` không nằm trong top 5 context).

### 2.4. Nhóm Lỗi Dịch Vụ & Fallback Vận Hành (Đếm Tách Riêng)
- **`test_009` (T0 — `LLM_TIMEOUT`):** Lỗi quá thời gian chờ phản hồi từ LLM provider (`45s` pipeline budget) sau khi đã truy xuất và rerank xong context đúng.
- **`test_032`, `test_059`, `test_061` (T0 — `RerankModelError` fallback):** Reranker gặp lỗi/quá hạn 4s nên hệ thống tự động lùi an toàn về thứ hạng Hybrid (đúng bất biến `System Invariant #2`); cả 3 câu đều giữ được chunk đúng và trả lời đạt `10/10` điểm.
