# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 11
## Phân Hệ: RAG & LLM (Team 2)

Đối chiếu với `develop` tại `cc830f3` (17/11/2026), sau khi Harness Engineering được merge (PR #64). Mục tiêu tuần này là cổng **G5 Evaluation** trong `docs/REQUIREMENTS.md` mục 6.

---

## 1. Thông Tin Chung & Mục Tiêu
- **Giai đoạn:** Tuần 11, ứng với **VLRA Sprint 8** trên Jira, từ 17/11 đến 23/11/2026.
- **Hạn:** cả hai ticket Team 2 đến hạn 23/11/2026.
- **Người phụ trách:** Người 1 (Đạt) làm phần đo định lượng. Người 2 (Hiệp) làm phần chấm mù, phân tích lỗi và báo cáo.
- **Mục tiêu:** chứng minh Target T0 không kém Baseline B0 trên một Test Set độc lập, có số liệu tái lập được, đủ để Team 3 ghép vào Final Evaluation Report (mốc G5).

Ticket Sprint 8 liên quan:

| Jira | Tên ticket | Phụ trách |
| :--- | :--- | :--- |
| **VLRA-78** | Đo lường Citation/Hallucination & So sánh Baseline B0 vs Target T0 | Team 2: Người 1 đo, Người 2 phân tích lỗi |
| **VLRA-79** | Tổ chức chấm mù 30–50 câu phức tạp theo Rubric 5 tiêu chí | Team 2: Người 2 |
| VLRA-77 | Đánh giá Retrieval & phân tích lỗi truy hồi trên Test Set (Recall@5/10/20, MRR@20) | Team 1 |
| VLRA-81 | Tổng hợp Final Evaluation Report & nghiệm thu G5 | Team 3 chủ trì, nhận số liệu từ VLRA-77/78/79 |

Ngưỡng cần đạt (`docs/REQUIREMENTS.md`):

| Mã | Chỉ số | Ngưỡng | Ticket |
| :--- | :--- | :--- | :--- |
| NFR-01 | Recall@5 | ≥ 85% | VLRA-77 (Team 1) |
| NFR-02 | Citation correctness | ≥ 90% | VLRA-78 |
| NFR-03 | Điểm câu trả lời T0 so với B0 (chấm mù, cùng rubric, cùng Test Set) | T0 ≥ B0, kèm hallucination rate | VLRA-78, VLRA-79 |

### Hai hệ thống được so sánh

| Hệ thống | Retrieval | Rerank | Cách bật trong `runtime.py` |
| :--- | :--- | :--- | :--- |
| **B0 (Baseline)** | BM25 | Không | `RAG_BM25_ONLY=true` |
| **T0 (Target)** | Hybrid BM25 + Dense (RRF) | BGE-Reranker-v2-m3 | `RAG_BM25_INDEX`, `RAG_DENSE_INDEX`, `RAG_RERANK=true` |

Các biến giữ cố định cho cả hai: cùng prompt template (`team2_rag/prompts/templates.py`), cùng model Gemini, `temperature=0`, cùng `maxOutputTokens`, cùng giới hạn context (5 chunk, 9000 ký tự), cùng `RAG_TOP_K`, `RAG_VERIFY_CLAIMS=true`, cùng thứ tự câu hỏi. Trọng số Hybrid ghi tường minh (`RAG_BM25_WEIGHT`, `RAG_DENSE_WEIGHT`, mặc định `0.5:1` theo `retrieval_v2.json`).

### Hiện trạng trước khi làm
- **Chưa có Test Set.** `team1_data/golden/golden_phase1.json` có 110 câu, tất cả `split: "dev"`. `out_of_scope_v1.json` có 33 câu cũng là `dev`. Dev Set đã đóng băng (sha256 `92233687…`) nhưng không dùng làm tập kiểm tra độc lập được vì Team 2 đã chỉnh cấu hình trên nó.
- `scripts/benchmark_rag_v2.py` đã đo citation correctness, citation coverage và hallucination rate qua `team2_rag/verification/metrics.py`, nhưng chỉ chạy một cấu hình mỗi lần. File Golden mặc định là `team2_rag/data/golden/golden_phase1_30cai.json` (bản đã bị chỉnh, khác bộ của Team 1).
- Hallucination rate hiện do bộ kiểm tra từ vựng trong `verification/rubric.py` tính, chưa phải kiểm tra ngữ nghĩa sâu. Báo cáo phải ghi rõ giới hạn này.
- Gate 3 của `scripts/harness_verify.py` mới đối soát `ai_service_load_and_stability_report.json`, chưa kiểm báo cáo đánh giá.
- T0 cần Dense (Qdrant + model embedding) và BGE-Reranker, không chạy được ở chế độ BM25-only trên máy cá nhân.

---

## 2. Phân Rã Công Việc

Mã nội bộ nối tiếp Tuần 10 (kết thúc ở `VLRA-T2-36`). T2-37 đến T2-40 và T2-43 thuộc **VLRA-78**; T2-41, T2-42 và T2-44 thuộc **VLRA-79**.

### 2.1. Người 1 (Đạt): Thực nghiệm định lượng B0 vs T0 (VLRA-78)

| Mã | Việc | Đạt khi |
| :--- | :--- | :--- |
| **VLRA-T2-37** | Nhận Test Set đã đóng băng từ Team 1 và kiểm tra trước khi đo: có `split: "test"`, không trùng câu với Dev Set, có cả câu answerable và câu cần từ chối, ghi sha256. | Test Set qua `validate_dataset` không cần `--exploratory`; hash được ghi vào báo cáo. Có test khóa hash. |
| **VLRA-T2-38** | Thêm chế độ so sánh vào runner (`scripts/benchmark_rag_v2.py`): chạy B0 và T0 trên cùng Test Set, cùng biến cố định, lưu cấu hình thực tế đang chạy của từng hệ thống. | Một lệnh chạy ra hai bộ kết quả. Report ghi đúng commit SHA, trọng số, `top_k`, rerank, model, hash Test Set. Ca lỗi Gemini (503, timeout) giữ trong kết quả, không bỏ đi. |
| **VLRA-T2-39** | Đo các chỉ số cho từng hệ thống: citation correctness, citation coverage, hallucination rate (theo câu và theo claim), precision/recall của việc từ chối (`insufficient_context`). Recall@5 do Team 1 đo ở VLRA-77; ở đây chỉ lưu `retrieved_chunk_ids` để phân tích lỗi. | Mọi chỉ số tính từ `raw_results`. Bảng so sánh B0/T0 có số câu làm mẫu số cho từng chỉ số. |
| **VLRA-T2-40** | Đóng gói bằng chứng: raw outputs từng câu và bảng tổng hợp vào `docs/team2_rag/`, mở rộng Gate 3 để kiểm cả báo cáo đánh giá. | DoD 1 của VLRA-78: có báo cáo JSON + Markdown B0 và T0 kèm `raw_results`. `scripts/harness_verify.py` PASS; Gate 3 bắt được lỗi khi bảng tổng lệch với `raw_results`. |

### 2.2. Người 2 (Hiệp): Chấm mù (VLRA-79) và phân tích lỗi (VLRA-78)

| Mã | Việc | Đạt khi |
| :--- | :--- | :--- |
| **VLRA-T2-41** | Chọn 30–50 câu khó từ Test Set (nhiều điều kiện, cần tổng hợp nhiều điều luật, dễ nhầm; số câu tùy quy mô Test Set). Tạo gói chấm mù: mỗi câu có hai câu trả lời, gán ngẫu nhiên nhãn A/B, ẩn tên hệ thống. | Giám khảo không biết câu nào của B0, câu nào của T0. Bảng khóa A/B lưu riêng, chỉ mở sau khi chấm xong. |
| **VLRA-T2-42** | Tổ chức 2 giám khảo chấm độc lập theo rubric 5 tiêu chí (mục 3.3), thang 0–10. | DoD 1 của VLRA-79: có file bảng điểm riêng của từng giám khảo (CSV/JSON/Markdown) trong `docs/team2_rag/`. Hai người chấm riêng, không trao đổi trước khi nộp. |
| **VLRA-T2-43** | Phân tích lỗi sinh câu trả lời của B0 và T0 theo 3 nguyên nhân Jira yêu cầu: prompt, context, model (mục 3.4). | DoD 2 của VLRA-78: có báo cáo phân tích lỗi, mỗi ca gắn đúng một nguyên nhân và truy được về câu trong `raw_results`. |
| **VLRA-T2-44** | Tổng hợp điểm: trung bình từng tiêu chí và tổng điểm của B0, T0; chênh lệch giữa 2 giám khảo. Viết phần AI/RAG cho Final Evaluation Report và gửi Team 3 (VLRA-81). | DoD 2 của VLRA-79: có bảng tổng hợp 5 tiêu chí. Team 3 xác nhận đã nhận. Báo cáo ghi rõ phần nào đạt, phần nào chưa, phần nào chưa đo. |

### 2.3. Thứ tự phụ thuộc
1. Team 1 giao Test Set → T2-37.
2. T2-37 → T2-38 → T2-39 → T2-40 (Người 1).
3. T2-39 có kết quả B0/T0 → T2-41 → T2-42 → T2-44 (Người 2). T2-43 làm song song ngay khi có `raw_results`.
4. Trong lúc chờ Test Set: Người 1 làm phần code của T2-38 và T2-40 bằng Dev Set (nhãn `exploratory`, không đưa vào báo cáo G5). Người 2 soạn rubric chi tiết, mẫu phiếu chấm và mời giám khảo.

---

## 3. Đặc Tả

### 3.1. Định nghĩa chỉ số (Người 1)

| Chỉ số | Cách tính | Mẫu số |
| :--- | :--- | :--- |
| **Citation correctness** | Số citation mà nội dung chunk được trích thực sự hỗ trợ claim / tổng số citation | Citation trong các câu `answered` |
| **Citation coverage** | Số claim có ít nhất một citation hợp lệ / tổng số claim | Claim trong các câu `answered` |
| **Hallucination rate (theo câu)** | Câu `answered` có ít nhất một claim `UNSUPPORTED` hoặc `CONTRADICTED` / số câu `answered` | Câu `answered` |
| **Hallucination rate (theo claim)** | Claim `UNSUPPORTED` hoặc `CONTRADICTED` / tổng số claim | Claim trong các câu `answered` |
| **Từ chối: Precision** | Câu bị từ chối đúng (đáng lẽ phải từ chối) / tổng câu hệ thống từ chối | Câu có status `insufficient_context` |
| **Từ chối: Recall** | Câu bị từ chối đúng / tổng câu đáng lẽ phải từ chối | Câu ngoài phạm vi hoặc không đủ căn cứ trong Test Set |

Quy tắc chung:
- Câu `error` hoặc `timeout` đếm riêng, không gộp vào mẫu số của chỉ số chất lượng, nhưng phải hiện trong bảng tổng.
- Nếu T0 bị lùi về thứ hạng Hybrid vì rerank quá 4 giây, ghi số ca lùi. Nếu số ca này lớn, kết quả T0 không còn là "Hybrid + Rerank" thật, phải nêu trong báo cáo.
- Hallucination ở đây do bộ kiểm tra từ vựng tính. Ghi rõ đây là ước lượng, phần chấm mù của Người 2 là nguồn đối chiếu.

### 3.2. Định dạng báo cáo định lượng (Người 1)
- File: `docs/team2_rag/g5_b0_vs_t0_report.json` và `.md`.
- JSON gồm `git_commit`, `timestamp_utc`, `test_set_path`, `test_set_sha256`, `controlled_config` (phần chung), `systems.b0` và `systems.t0` (mỗi bên có `config`, `metrics`, `request_outcomes`, `raw_results`).
- Mỗi phần tử `raw_results`: `id`, `question`, `outcome`, `error_code`, `retrieved_chunk_ids`, `answer`, `citations`, `claims` kèm verdict, `stage_latency_s`.
- Gate 3 kiểm: số phần tử `raw_results` khớp `total`, số ca từng loại khớp bảng tổng, các chỉ số tính lại từ `raw_results` khớp bảng tổng (sai số ≤ 0,0001), hash Test Set khớp file đang có trong repo.

### 3.3. Rubric chấm mù 5 tiêu chí (Người 2)
Mỗi tiêu chí 0–2 điểm, tổng 0–10.

| Tiêu chí | 0 điểm | 1 điểm | 2 điểm |
| :--- | :--- | :--- | :--- |
| **Đúng pháp lý** | Sai nội dung luật | Đúng một phần hoặc thiếu điều kiện quan trọng | Đúng |
| **Đầy đủ** | Bỏ sót ý chính | Có ý chính, thiếu ý phụ | Đủ các ý câu hỏi cần |
| **Căn cứ trích dẫn** | Trích sai điều hoặc không có trích dẫn | Trích đúng điều nhưng chưa đủ | Mỗi nhận định đều có căn cứ đúng |
| **Mạch lạc, dễ hiểu** | Khó hiểu | Hiểu được nhưng rối | Rõ ràng |
| **An toàn, không bịa** | Có thông tin bịa hoặc khẳng định ngoài căn cứ | Có chỗ suy diễn nhẹ | Không bịa; từ chối đúng lúc khi thiếu căn cứ |

Quy tắc chấm:
- Giám khảo được xem câu hỏi, câu trả lời, và nội dung các đoạn luật được trích. Không được xem tên hệ thống, độ trễ hay cấu hình.
- Câu trả lời từ chối (`insufficient_context`) vẫn được chấm; nếu từ chối đúng thì tiêu chí "An toàn" được 2 điểm.
- Độ đồng thuận: báo chênh lệch tuyệt đối trung bình giữa 2 giám khảo, tỷ lệ câu chênh ≤ 2 điểm, và hệ số tương quan Spearman. Câu chênh > 3 điểm thì hai người xem lại và ghi lý do, không tự lấy trung bình.

### 3.4. Phân loại lỗi sinh câu trả lời (Người 2, VLRA-78)
Ba nhóm chính theo Jira; nhóm context tách thêm nhóm con để Team 1 biết lỗi nào thuộc truy hồi.

| Nhóm | Nhóm con | Dấu hiệu | Kiểm bằng |
| :--- | :--- | :--- | :--- |
| **Context** | Retrieval thiếu | Chunk đúng không có trong danh sách tìm được | `retrieved_chunk_ids` so với `relevant_unit_groups` |
| | Rerank xếp sai | Chunk đúng có trong kết quả Hybrid nhưng bị rerank đẩy ra khỏi 5 chunk đưa vào prompt | So thứ hạng trước và sau rerank (chỉ T0) |
| **Prompt** | | Chunk đúng đã có trong context, nhưng câu trả lời làm sai một quy tắc prompt đã nêu: không nêu ngoại lệ, từ chối khi đủ căn cứ, sai định dạng marker | Đối chiếu `answer` với quy tắc trong `team2_rag/prompts/templates.py` |
| **Model** | | Chunk đúng đã có trong context, prompt đã nêu rõ, nhưng LLM vẫn suy luận sai hoặc gắn nhầm `[Ci]` | `answer`, `citations`, verdict claim |
| *Lỗi dịch vụ* (đếm riêng) | | `error` hoặc `timeout` (Gemini 503, quá 45 giây) | `error_code` |

---

## 4. Rủi Ro & Việc Cần Chốt

| # | Vấn đề | Ảnh hưởng | Hướng xử lý |
| :--- | :--- | :--- | :--- |
| 1 | Team 1 chưa giao Test Set, và Sprint 8 không có ticket nào giao việc tạo Test Set (VLRA-77 coi như đã có) | Không chạy được VLRA-77, 78, 79 | Báo người quản lý Jira thêm việc tạo Test Set hoặc ghi rõ ai làm. Test Set cần có cả câu ngoài phạm vi để đo Precision/Recall từ chối. |
| 2 | T0 cần Dense và BGE-Reranker, phải chạy trên máy có GPU (Colab) | Tốn chi phí; Tuần 9 nhóm đã quyết định không chạy thêm Colab | Cả nhóm chốt lại: chạy một lượt Colab cho G5, hay tìm máy khác. Không chạy thì không có kết quả T0. |
| 3 | Gọi Gemini cho 2 hệ thống × toàn bộ Test Set, cộng claims | Tốn quota, dễ gặp 503 | Đặt khoảng nghỉ giữa các câu. Câu lỗi được chạy lại theo cùng một quy tắc cho cả B0 và T0, ghi số lần thử. |
| 4 | Hai file Golden lệch nhau (`team1_data/golden/golden_phase1.json` và `team2_rag/data/golden/golden_phase1_30cai.json`) | Đo nhầm bộ | Chỉ dùng Test Set do Team 1 giao. Không dùng file mặc định của runner. |
| 5 | 70/110 câu Dev Set và 33 câu ngoài phạm vi chưa được người có chuyên môn pháp lý soát | Test Set có thể kế thừa cùng vấn đề | Hỏi Team 1 trạng thái soát của Test Set; ghi rõ trong báo cáo. |
| 6 | Cần 2 giám khảo độc lập | Thiếu người thì không có độ đồng thuận | Người 2 mời giám khảo ngay đầu tuần. |

---

## 5. Lệnh Kiểm Chứng

```bash
# Cổng Harness (Gate 1–4) trước khi mở PR
.venv/bin/python scripts/harness_verify.py

# Test Team 2
.venv/bin/python -m pytest team2_rag/tests -q
.venv/bin/python -m pytest tests -q
```

---

## 6. Trạng Thái Thực Thi (cập nhật ngày 18/11/2026)

| Mã | Jira | Người phụ trách | Trạng thái | Ghi chú |
| :--- | :--- | :--- | :---: | :--- |
| `VLRA-T2-37` | VLRA-78 | Người 1 | **BLOCKED** | Chờ Test Set. |
| `VLRA-T2-38` | VLRA-78 | Người 1 | TODO | Làm phần code trên Dev Set (`exploratory`) trong lúc chờ. |
| `VLRA-T2-39` | VLRA-78 | Người 1 | TODO | Cần T2-38. |
| `VLRA-T2-40` | VLRA-78 | Người 1 | TODO | Mở rộng Gate 3 làm được ngay. |
| `VLRA-T2-41` | VLRA-79 | Người 2 | TODO | Cần kết quả B0/T0 từ T2-39. |
| `VLRA-T2-42` | VLRA-79 | Người 2 | TODO | Mời 2 giám khảo, soạn phiếu chấm ngay. |
| `VLRA-T2-43` | VLRA-78 | Người 2 | TODO | Cần `raw_results` từ T2-39. |
| `VLRA-T2-44` | VLRA-79 | Người 2 | TODO | Cần T2-42; gửi Team 3 cho VLRA-81. |
