# Phần AI và RAG cho báo cáo cuối kỳ

**VLRA-T2-49 — Nội dung bàn giao Team 3 ghép vào Final Project Report.**

Báo cáo tổng hợp bằng chứng đã lưu trong repo, không đo lại. Team 2 phụ trách điều phối RAG, sinh câu trả lời và kiểm tra căn cứ trích dẫn. Kết quả dưới đây phản ánh cấu hình và tập kiểm thử được ghi trong từng báo cáo nguồn; chưa đủ để khẳng định hệ thống trả lời đúng mọi câu hỏi pháp luật.

## Kiến trúc pipeline

```text
Câu hỏi và lịch sử hội thoại
  → Retrieval của Team 1 (BM25 hoặc Hybrid BM25 + Dense)
  → BGE Reranker (tùy chọn; lỗi/quá hạn thì giữ thứ hạng Retrieval)
  → Context Builder (chọn nguyên chunk, gắn nhãn nguồn)
  → Prompt → Gemini
  → Parse JSON → kiểm citation → verification claim khi bật
  → Phản hồi nội bộ cho Backend của Team 3
```

Retrieval cung cấp các đoạn luật cùng metadata nguồn. Team 2 nhận dữ liệu theo hợp đồng, không tự tạo định danh hay sửa nội dung luật. Khi bật BGE, các đoạn được chấm lại mức liên quan với câu hỏi trước khi chọn context. Rerank là bước tùy chọn; khi bị lỗi, pipeline có thể tiếp tục bằng thứ hạng truy xuất và ghi nhận việc lùi cấu hình.

Context Builder chọn nguyên chunk để giữ điều kiện và ngoại lệ pháp lý, rồi lưu ánh xạ nhãn tạm với nguồn gốc. Trong G5, cả hai cấu hình lấy `top_k=10`, giới hạn context ở `5` chunk và `9000` ký tự; cùng model `gemini-3.1-flash-lite`, temperature `0.0`. Đây là cấu hình đã chạy, không phải bằng chứng đã kiểm ngân sách bằng tokenizer. Nguồn: `docs/team2_rag/g5_b0_vs_t0_report.json`, trường `systems.*.config`.

Luồng này được triển khai tại `team2_rag/pipeline.py`, `team2_rag/runtime.py`, `team2_rag/prompts/context.py` và `team2_rag/answer.py`. B0 là **BM25-only, không rerank**; T0 là **Hybrid + BGE Rerank**. Do thay đổi cả Retrieval lẫn Rerank, so sánh B0/T0 chưa tách được đóng góp riêng của BGE.

## Prompt, trích dẫn và verification

Prompt yêu cầu trả lời bằng tiếng Việt, chỉ dùng `LEGAL CONTEXT` của lượt hiện tại. Câu hỏi và lịch sử giúp hiểu tình huống, không thay thế chứng cứ pháp luật. Khi nguồn có điều kiện hoặc ngoại lệ, câu trả lời phải trình bày cùng quy định chính; nếu chỉ đủ căn cứ cho một phần thì nêu rõ phần còn thiếu. Các chỉ dẫn chèn trong câu hỏi hoặc tài liệu không được ghi đè quy tắc hệ thống. Nguồn: `docs/team2_rag/prompt-design.md`; mẫu thực thi: `team2_rag/prompts/templates.py`.

Mỗi nhận định pháp lý cần marker `[Ck]` gắn với đoạn nguồn đã đưa vào prompt. Với `status="answered"`, các marker hợp lệ phải liên tục từ `[C1]`, khớp với mảng `citations` và metadata nguồn. Không được tự đoán `chunk_id`, `document_id`, `article_id` hay URL. Với `insufficient_context`, phản hồi phải có `citations=[]` và không có marker. Nguồn: `docs/team2_rag/citation-specification.md`, `docs/team2_rag/ui-integration-guide.md`.

Sau khi nhận JSON, hệ thống kiểm định dạng, schema, marker, đối chiếu chunk và metadata với context. Nếu đầu ra sai, hệ thống chặn bằng `INVALID_LLM_OUTPUT` hoặc `CITATION_INVALID`; không sửa nhãn, chèn nguồn hay viết lại câu trả lời để hợp thức hóa. Thiếu căn cứ là trạng thái nghiệp vụ `insufficient_context`; lỗi kỹ thuật được trả thành lỗi tương ứng. Nguồn: `docs/team2_rag/rag-io-specification.md`, `docs/team2_rag/ui-integration-guide.md`.

Kiểm citation và kiểm nội dung claim là hai mức khác nhau. Citation hợp lệ xác nhận liên kết với nguồn, chưa bảo đảm kết luận pháp lý đúng. Khi bật `RAG_VERIFY_CLAIMS`, LLM khai các claim để bộ verification đối chiếu với đoạn được dẫn. Mặc định chạy online tắt bước kiểm claim để giảm độ trễ; lượt đo tải cũng tắt bước này. Chỉ số hallucination G5 dùng đối chiếu từ vựng, chưa phải kiểm chứng ngữ nghĩa sâu. Nguồn: `docs/team2_rag/ai_service_load_and_stability_report.md`, `docs/team2_rag/g5_b0_vs_t0_report.json`; cờ thực thi: `team2_rag/runtime.py`.

## Xử lý lỗi, timeout và tải đồng thời

Các mã dưới đây là mã nội bộ của AI Service; Backend có ánh xạ mã lỗi public riêng.

| Tình huống | Phản hồi nội bộ |
| :--- | :--- |
| Thiếu căn cứ hoặc dữ kiện để kết luận | HTTP `200`, `insufficient_context`, không có citation |
| JSON hoặc cấu trúc đầu ra LLM sai | HTTP `502`, `INVALID_LLM_OUTPUT` |
| Trích dẫn không hợp lệ | HTTP `502`, `CITATION_INVALID` |
| Hàng đợi đầy hoặc LLM tạm không phục vụ | HTTP `503`, `LLM_UNAVAILABLE`, có thể thử lại |
| Hết deadline khi chờ hoặc xử lý | HTTP `504`, `LLM_TIMEOUT`, có thể thử lại |

Nguồn bảng: `docs/team2_rag/ui-integration-guide.md`, `docs/team2_rag/rag-io-specification.md`.

Chuỗi timeout là **AI 45 giây < Backend Java 50 giây < Frontend 60 giây**. Trước khi gọi LLM, pipeline tính `remaining = deadline - time.monotonic()`. Nếu `remaining <= 1.0` giây thì ngắt sớm; nếu còn đủ thời gian thì truyền `llm_timeout_seconds = max(0.1, remaining - 0.5)`. Nguồn: `docs/team2_rag/ai_service_load_and_stability_report.md`, mục kiểm chứng NFR-08; thực thi tại `team2_rag/pipeline.py`.

AI Service hiện dùng khóa cho toàn pipeline: **1 lượt chạy + tối đa 4 lượt chờ**. Thời gian chờ nằm trong cùng deadline; hàng đầy trả lỗi ngay, chờ quá hạn thì không chạy pipeline. Nếu HTTP đã hết hạn nhưng công việc nền chưa kết thúc, slot vẫn được giữ đến khi công việc thực sự xong. Hàng đợi không bảo đảm FIFO và không làm tăng năng lực suy luận. Nguồn: `docs/team2_rag/ui-integration-guide.md`; đối chiếu `team2_rag/api/app.py` và `docs/decisions/0004-single-llm-slot.md`.

Giới hạn mặc định **12 request/phút** (`LLM_RATE_LIMIT_RPM=12`) được áp dụng bằng cách giãn cách các lần gọi Gemini, gồm cả retry và gọi model dự phòng. Việc chờ vẫn tiêu thụ ngân sách timeout. Đây là cấu hình vận hành, không phải thông lượng đã đo qua API. Nguồn: `team2_rag/docs_2/week12/tasks.md`, mục rủi ro demo; thực thi tại `team2_rag/config/settings.py`, `team2_rag/llm/gemini_client.py`.

**Khác biệt tài liệu cần giữ rõ:** báo cáo tải cũ mô tả từ chối ngay request kế tiếp khi slot bận; mã hiện tại đã có hàng đợi nêu trên. ADR về slot vẫn ở trạng thái `Proposed`. Vì vậy không dùng báo cáo tải cũ làm bằng chứng đã nghiệm thu hiệu năng hàng đợi hiện tại. Nguồn: `docs/team2_rag/ai_service_load_and_stability_report.md`, `docs/decisions/0004-single-llm-slot.md`.

## Kết quả G5: định lượng B0 và T0

Hai cấu hình chạy cùng Test Set, cùng model và các tham số sinh/context được kiểm soát; báo cáo JSON ghi `controlled_config_differences={}`. Tỷ lệ chất lượng không đưa câu `error` vào mẫu số; số đếm chi tiết nằm ở `metrics.counts`.

| Chỉ số | B0: BM25-only | T0: Hybrid + BGE |
| :--- | ---: | ---: |
| Tổng số câu | 77 | 77 |
| `answered` | 60 | 61 |
| `insufficient_context` | 16 | 15 |
| `error` | 1 | 1 |
| Citation correctness | 100,00% | 100,00% |
| Citation coverage | 99,17% | 100,00% |
| Hallucination theo câu, ước lượng từ vựng | 1,67% | 0,00% |
| Hallucination theo claim, ước lượng từ vựng | 0,83% | 0,00% |
| Precision của từ chối | 87,50% | 93,33% |
| Recall của từ chối | 93,33% | 93,33% |
| Lùi về Hybrid do rerank lỗi/quá hạn | 0 | 3 |

Nguồn bảng: `docs/team2_rag/g5_b0_vs_t0_report.md` và `docs/team2_rag/g5_b0_vs_t0_report.json` (`systems.*.metrics`, tính từ `raw_results`).

B0 có lỗi `CITATION_INVALID` tại `test_045`; T0 có lỗi `LLM_TIMEOUT` tại `test_009`. T0 lùi về Hybrid tại `test_032`, `test_059`, `test_061`; các câu này vẫn hoàn thành phản hồi. Vì vậy kết quả T0 bao gồm cả lượt chạy suy giảm cấu hình, không phải mọi câu đều được BGE xử lý thành công. Nguồn: `docs/team2_rag/g5_error_analysis.md`, `docs/team2_rag/g5_b0_vs_t0_report.json`.

## Chấm mù và phân tích lỗi

Mẫu chấm mù gồm **40 câu hỏi**, do **2 giám khảo** chấm theo **5 tiêu chí**, mỗi tiêu chí **0–2 điểm**, tổng tối đa **10 điểm/câu**. Đây là mẫu được chọn từ Test Set, không phải điểm của toàn bộ tập. Nguồn: `docs/team2_rag/g5_blind_evaluation_report.md`.

| Tiêu chí, trung bình hai giám khảo | B0 | T0 |
| :--- | ---: | ---: |
| Đúng pháp lý | 1,73 | 1,83 |
| Đầy đủ | 1,73 | 1,83 |
| Căn cứ trích dẫn | 1,75 | 1,75 |
| Mạch lạc, dễ hiểu | 1,95 | 1,95 |
| An toàn, không bịa | 1,65 | 1,68 |
| Tổng điểm trung bình | 8,80/10 | 9,04/10 |

Nguồn bảng: `docs/team2_rag/g5_blind_evaluation_report.md`; phiếu gốc: `docs/team2_rag/g5_blind_scores_judge1.csv`, `docs/team2_rag/g5_blind_scores_judge2.csv`; giải mã: `docs/team2_rag/g5_blind_eval_key.json`.

Điểm trung bình T0 cao hơn **0,24 điểm** trên mẫu chấm mù, đã tính câu timeout của T0 bằng điểm **0/10**. Khi bỏ ca đó, báo cáo ghi T0 **9,27/10**, B0 **8,77/10** trên **39/40 câu**; kết quả chính vẫn là bảng có tính lỗi. Nguồn: `docs/team2_rag/g5_blind_evaluation_report.md`.

| Nhóm nguyên nhân được ghi nhận | B0 | T0 |
| :--- | ---: | ---: |
| Retrieval thiếu/câu ngoài phạm vi gần ngữ cảnh | 1 | 1 |
| Rerank hoặc chọn context đẩy chunk đúng ra ngoài top 5 | 2 | 3 |
| Prompt: từ chối nhầm dù có chunk đúng | 2 | 1 |
| Model: diễn đạt lệch từ vựng hoặc trích nhầm metadata | 3 | 0 |
| Timeout LLM, đếm riêng | 0 | 1 |
| BGE lỗi/quá hạn, lùi về Hybrid, đếm riêng | 0 | 3 |

Nguồn bảng: `docs/team2_rag/g5_error_analysis.md`. Đây là phân loại của báo cáo lỗi, không phải các trạng thái loại trừ nhau để cộng thành tổng request. Lỗi citation của B0 nằm trong nhóm Model; hàng timeout chỉ đếm timeout.

Các trường hợp minh họa cho thấy lợi ích và rủi ro cùng tồn tại. Ở `test_062`, B0 lấy ngữ cảnh xử phạt không phù hợp, còn T0 đưa được căn cứ về chủ hộ kinh doanh vào context. Ở `test_020`, B0 vẫn từ chối dù có chunk đúng: thêm bước xếp hạng không tự giải quyết hết vấn đề prompt. Ngược lại, tại `test_052`, T0 đẩy khoản chứa thời hạn ra khỏi context nên trả lời thiếu. `test_003` còn cho thấy bộ lọc từ vựng có thể gắn nhãn `UNSUPPORTED` cho một cách diễn đạt được giám khảo chấm đúng. Nguồn: `docs/team2_rag/g5_error_analysis.md`.

## NFR-07, NFR-08 và NFR-09

Phép đo tải dùng `bm25_only_local`, `RAG_TOP_K=5`, tắt rerank và kiểm claim; không phải cấu hình T0 của G5. Nguồn: `docs/team2_rag/ai_service_load_and_stability_report.md`, mục cấu hình.

| Yêu cầu | Bằng chứng đã lưu | Phạm vi kết luận |
| :--- | :--- | :--- |
| NFR-07: p95 qua `RAGPipeline.query` ≤ 45,0 s | 50 câu; mean 5,986 s; p95 19,330 s; max 28,481 s | Đạt trên BM25-only local; chưa chứng minh Hybrid + BGE hoặc tải đồng thời qua toàn hệ thống |
| NFR-08: AI < Java < Frontend | 45,0 s < 50,0 s < 60,0 s; truyền ngân sách còn lại và kiểm timeout/slot | Bằng chứng cấp Team 2; mô tả từ chối ngay khi bận trong báo cáo cũ đã khác cơ chế hàng đợi hiện tại |
| NFR-09: tra cứu Điều luật | Cold-start HTTP 44,346 ms; warm HTTP p95 6,751 ms trên 20 lượt; ngưỡng chặng Java → AI ≤ 10 s | Đo endpoint AI bằng TestClient; chưa phải thời gian qua Java và UI, nơi yêu cầu viewer ≤ 15 s |

Nguồn bảng: `docs/team2_rag/ai_service_load_and_stability_report.md` và `docs/team2_rag/ai_service_load_and_stability_report.json` (`config`, `stage_latency`, `article_viewer`).

| Kết quả lượt đo tải | Số câu |
| :--- | ---: |
| Tổng | 50 |
| `answered` | 40 |
| `insufficient_context` | 8 |
| `timeout` | 0 |
| `error` | 2 |

Nguồn bảng: `docs/team2_rag/ai_service_load_and_stability_report.md` và `.json` (`request_outcomes`, `raw_results`). Các lỗi được ghi là `INVALID_LLM_OUTPUT` và `LLM_UNAVAILABLE`; không được diễn giải kết quả độ trễ thành không có lỗi.

Endpoint xem Điều luật đã kiểm `DOCUMENT_NOT_FOUND` và `ARTICLE_NOT_FOUND` trả HTTP `404`, `INVALID_REQUEST` trả HTTP `400`. Việc nghiệm thu luồng mở Điều luật qua Backend và Frontend cần bằng chứng tích hợp của Team 3. Nguồn: `docs/team2_rag/ai_service_load_and_stability_report.md`, mục NFR-09.

## Giới hạn và hướng tiếp theo

- Hallucination được ước lượng bằng đối chiếu từ vựng; mức **0,00%** của T0 không chứng minh không có sai lệch ngữ nghĩa. Citation correctness **100,00%** cũng không thay thế rà soát pháp lý. Nguồn: `docs/team2_rag/g5_b0_vs_t0_report.md`, `docs/team2_rag/g5_error_analysis.md`.
- Test Set có **77 câu**, các bản ghi vẫn mang `review_status="draft_needs_legal_review"`. Cần người có chuyên môn rà soát nhãn và câu trả lời chuẩn trước khi khẳng định chất lượng pháp lý rộng hơn. Số câu: `docs/team2_rag/g5_b0_vs_t0_report.md`; trạng thái nhãn: `team1_data/golden/test_set_v1.json`.
- Mỗi bên có **1 câu lỗi**; T0 có **3 câu BGE lỗi/quá hạn lùi về Hybrid**. Cần giữ các ca này trong báo cáo vận hành, kể cả khi bảng chất lượng loại câu lỗi khỏi mẫu số. Nguồn: `docs/team2_rag/g5_b0_vs_t0_report.md`, `docs/team2_rag/g5_error_analysis.md`.
- NFR-07 mới có số đo BM25-only; NFR-09 mới có số đo endpoint AI. Cần đo bổ sung Hybrid + BGE, thời gian chờ hàng đợi và luồng Java/Frontend trước khi kết luận hiệu năng toàn hệ thống. Nguồn: `docs/team2_rag/ai_service_load_and_stability_report.md`.
- B0/T0 thay đổi đồng thời cách truy xuất và xếp hạng. Hướng tiếp theo là giữ nguyên Retrieval để đo riêng tác động của BGE, kiểm cách chọn context cho câu nhiều ý và cải thiện nhận diện từ chối nhầm. Các ca cần theo dõi đã được nêu trong `docs/team2_rag/g5_error_analysis.md`.

