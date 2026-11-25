# Kịch bản demo B0 và T0 từ kết quả đã lưu

**VLRA-T2-51 — Demo đối chiếu có và không có Reranker.**

## Mở đầu và cách trình bày

Phần đối chiếu dùng câu trả lời đã lưu, không gọi lại model. B0 là BM25-only, không rerank; T0 là Hybrid + BGE Rerank. Hai cấu hình đổi cả Retrieval và Rerank, nên demo minh họa khác biệt giữa B0/T0, chưa đo riêng tác động của BGE. Các ca được chọn để giải thích kết quả, không đại diện cho toàn Test Set.

Lời mở: “Chúng tôi trình bày cả ca T0 tốt hơn và ca T0 kém hơn. Mỗi câu trả lời giữ nguyên từ bản chạy; nguồn trích dẫn và context giúp giải thích chỗ khác nhau.”

Nguồn câu hỏi, trạng thái, câu trả lời, citation và context: `docs/team2_rag/runs/g5/b0.json`, `docs/team2_rag/runs/g5/t0.json`, tại `records[id]`. Các khối `text` dưới đây chép đầy đủ trường `answer`, không sửa chữ hoặc marker. Đây là đầu ra thí nghiệm, có cả câu sai; không xem chúng là kết luận pháp lý đã được duyệt.

Điểm được giải mã A/B **theo từng câu** bằng `docs/team2_rag/g5_blind_eval_key.json`; lấy cột `A_total` hoặc `B_total` từ `docs/team2_rag/g5_blind_scores_judge1.csv` và `docs/team2_rag/g5_blind_scores_judge2.csv`, rồi tính trung bình hai giám khảo. Thang tối đa 10 điểm theo `docs/team2_rag/g5_blind_evaluation_report.md`.

## `test_062` — T0 tốt hơn

**Câu hỏi:** Chủ hộ kinh doanh thuê người quản lý thì có còn chịu trách nhiệm về nợ không, và có được góp vốn, mua cổ phần trong doanh nghiệp không?

### B0 — `outcome=answered`

```text
Pháp luật hiện hành quy định việc góp vốn thành lập hoặc mua cổ phần, phần vốn góp trong công ty hợp danh, công ty trách nhiệm hữu hạn hoặc công ty cổ phần là hành vi bị xử phạt vi phạm hành chính nếu chủ hộ kinh doanh đồng thời thực hiện hành vi này [C1]. Đối với vấn đề trách nhiệm về nợ khi chủ hộ kinh doanh thuê người quản lý, các tài liệu được cung cấp không chứa thông tin quy định về nội dung này.
```

Citation đã lưu (nhãn → chunk):

- `[C1]` → `nd-122-2021-nd-cp-v1__dieu-56__k1__0`

`llm_context_chunk_ids` đã lưu:

- `nd-122-2021-nd-cp-v1__dieu-56__k1__0`
- `luat-59-2020-qh14-v1__dieu-119__k2__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-119__k2__0`
- `nd-168-2025-nd-cp-v1__dieu-27__k2__0`
- `nd-168-2025-nd-cp-v1__dieu-45__k4__0`

### T0 — `outcome=answered`

```text
Khi chủ hộ kinh doanh thuê người khác quản lý, điều hành hoạt động kinh doanh, chủ hộ kinh doanh và các thành viên hộ gia đình đăng ký hộ kinh doanh vẫn phải chịu trách nhiệm đối với các khoản nợ và nghĩa vụ tài sản khác phát sinh từ hoạt động kinh doanh của hộ kinh doanh [C1]. Ngoài ra, chủ hộ kinh doanh và các thành viên hộ gia đình đăng ký hộ kinh doanh có quyền góp vốn, mua cổ phần, mua phần vốn góp trong doanh nghiệp với tư cách cá nhân [C2].
```

Citation đã lưu (nhãn → chunk):

- `[C1]` → `nd-168-2025-nd-cp-v1__dieu-84__k2__0`
- `[C2]` → `nd-168-2025-nd-cp-v1__dieu-84__k4__0`

`llm_context_chunk_ids` đã lưu:

- `nd-168-2025-nd-cp-v1__dieu-84__k2__0`
- `nd-168-2025-nd-cp-v1__dieu-84__k4__0`
- `luat-59-2020-qh14-v1__dieu-187__k2__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-187__k2__0`
- `luat-59-2020-qh14-v1__dieu-111__k1__0`

### Điểm chấm mù và diễn giải

| Hệ thống | Cột sau giải mã | Giám khảo 1 | Giám khảo 2 | Trung bình /10 |
| :--- | :---: | ---: | ---: | ---: |
| B0 | B | 1 | 1 | 1,0 |
| T0 | A | 10 | 10 | 10,0 |

Nguồn bảng: `docs/team2_rag/g5_blind_scores_judge1.csv`, `docs/team2_rag/g5_blind_scores_judge2.csv` (dòng `id=test_062`); ánh xạ: `docs/team2_rag/g5_blind_eval_key.json`, `mapping[id=test_062]`.

**Lý do khác nhau:** Theo `docs/team2_rag/g5_error_analysis.md`, mục Context: B0 không giữ được Điều 84 Khoản 2 và Khoản 4 Nghị định 168/2025 trong top 5 context; câu trả lời chuyển sang quy định xử phạt. T0 giữ được cả hai khoản, trả lời đủ trách nhiệm nợ và quyền góp vốn.

**Lời thoại:** “B0 vẫn có citation hợp lệ về liên kết, nhưng kết luận sai theo đánh giá. T0 đưa được các khoản phù hợp vào context nên trả lời đủ hai ý.”

## `test_020` — T0 tốt hơn

**Câu hỏi:** Cuộc họp Hội đồng thành viên của công ty trách nhiệm hữu hạn một thành viên do tổ chức làm chủ sở hữu được tiến hành khi có bao nhiêu thành viên dự họp?

### B0 — `outcome=insufficient_context`

```text
Các quy định trong ngữ cảnh pháp lý được cung cấp chỉ đề cập đến điều kiện tiến hành cuộc họp Hội đồng thành viên của công ty trách nhiệm hữu hạn hai thành viên trở lên (Điều 58) và Hội đồng thành viên của công ty trách nhiệm hữu hạn một thành viên (Điều 80), nhưng không nêu rõ quy định về việc tiến hành cuộc họp Hội đồng thành viên đối với loại hình công ty trách nhiệm hữu hạn một thành viên do tổ chức làm chủ sở hữu.
```

Citation đã lưu: `[]`.

`llm_context_chunk_ids` đã lưu:

- `luat-59-2020-qh14-v1__dieu-58__k1__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-58__k1__0`
- `luat-59-2020-qh14-v1__dieu-80__k5__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-80__k5__0`
- `luat-59-2020-qh14-v1__dieu-58__k2__0`

### T0 — `outcome=answered`

```text
Cuộc họp Hội đồng thành viên của công ty trách nhiệm hữu hạn một thành viên do tổ chức làm chủ sở hữu được tiến hành khi có ít nhất hai phần ba tổng số thành viên Hội đồng thành viên dự họp [C1], [C2].
```

Citation đã lưu (nhãn → chunk):

- `[C1]` → `luat-59-2020-qh14-v1__dieu-80__k5__0`
- `[C2]` → `vbhn-67-vbhn-vpqh-v1__dieu-80__k5__0`

`llm_context_chunk_ids` đã lưu:

- `luat-59-2020-qh14-v1__dieu-58__k1__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-58__k1__0`
- `luat-59-2020-qh14-v1__dieu-80__k5__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-80__k5__0`
- `luat-59-2020-qh14-v1__dieu-98__k4__0`

### Điểm chấm mù và diễn giải

| Hệ thống | Cột sau giải mã | Giám khảo 1 | Giám khảo 2 | Trung bình /10 |
| :--- | :---: | ---: | ---: | ---: |
| B0 | B | 2 | 2 | 2,0 |
| T0 | A | 10 | 10 | 10,0 |

Nguồn bảng: `docs/team2_rag/g5_blind_scores_judge1.csv`, `docs/team2_rag/g5_blind_scores_judge2.csv` (dòng `id=test_020`); ánh xạ: `docs/team2_rag/g5_blind_eval_key.json`, `mapping[id=test_020]`.

**Lý do khác nhau:** Theo `docs/team2_rag/g5_error_analysis.md`, mục Prompt: B0 đã có Điều 80 Khoản 5 trong context nhưng từ chối nhầm vì phân biệt quá chặt tên loại hình công ty. T0 trả lời được điều kiện dự họp. Chunk đúng có trong context của cả hai bên; không thể quy toàn bộ khác biệt cho việc tìm thấy thêm nguồn.

**Lời thoại:** “B0 đã có đoạn đúng nhưng vẫn nói thiếu căn cứ. Đây là lỗi từ chối ở bước sinh câu trả lời; kết quả T0 tốt hơn không có nghĩa reranker tự giải quyết mọi lỗi prompt.”

## `test_049` — T0 tốt hơn

**Câu hỏi:** Công ty cổ phần được chọn những mô hình tổ chức quản lý nào, và ai là người đại diện theo pháp luật khi Điều lệ chưa quy định?

### B0 — `outcome=answered`

```text
Đối với công ty cổ phần, trường hợp công ty chỉ có một người đại diện theo pháp luật mà Điều lệ chưa có quy định cụ thể thì Chủ tịch Hội đồng quản trị là người đại diện theo pháp luật của công ty [C1], [C2]. LEGAL CONTEXT hiện tại không cung cấp thông tin về các mô hình tổ chức quản lý mà công ty cổ phần được lựa chọn.
```

Citation đã lưu (nhãn → chunk):

- `[C1]` → `luat-59-2020-qh14-v1__dieu-137__k2__0`
- `[C2]` → `vbhn-67-vbhn-vpqh-v1__dieu-137__k2__0`

`llm_context_chunk_ids` đã lưu:

- `luat-59-2020-qh14-v1__dieu-137__k2__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-137__k2__0`
- `luat-59-2020-qh14-v1__dieu-12__k2__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-12__k2__0`
- `luat-59-2020-qh14-v1__dieu-24__k3__0`

### T0 — `outcome=answered`

```text
Công ty cổ phần có quyền lựa chọn một trong hai mô hình tổ chức quản lý: (1) Đại hội đồng cổ đông, Hội đồng quản trị, Ban kiểm soát và Giám đốc hoặc Tổng giám đốc (trường hợp công ty có dưới 11 cổ đông và các cổ đông là tổ chức sở hữu dưới 50% tổng số cổ phần thì không bắt buộc có Ban kiểm soát); hoặc (2) Đại hội đồng cổ đông, Hội đồng quản trị và Giám đốc hoặc Tổng giám đốc (trường hợp này phải có Ủy ban kiểm toán trực thuộc Hội đồng quản trị và ít nhất 20% thành viên Hội đồng quản trị là thành viên độc lập) [C1], [C2]. Đối với người đại diện theo pháp luật, nếu Điều lệ chưa có quy định thì Chủ tịch Hội đồng quản trị là người đại diện theo pháp luật của công ty [C3], [C4].
```

Citation đã lưu (nhãn → chunk):

- `[C1]` → `luat-59-2020-qh14-v1__dieu-137__k1__0`
- `[C2]` → `vbhn-67-vbhn-vpqh-v1__dieu-137__k1__0`
- `[C3]` → `luat-59-2020-qh14-v1__dieu-137__k2__0`
- `[C4]` → `vbhn-67-vbhn-vpqh-v1__dieu-137__k2__0`

`llm_context_chunk_ids` đã lưu:

- `luat-59-2020-qh14-v1__dieu-137__k1__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-137__k1__0`
- `luat-59-2020-qh14-v1__dieu-137__k2__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-137__k2__0`
- `luat-59-2020-qh14-v1__dieu-14__k2__0`

### Điểm chấm mù và diễn giải

| Hệ thống | Cột sau giải mã | Giám khảo 1 | Giám khảo 2 | Trung bình /10 |
| :--- | :---: | ---: | ---: | ---: |
| B0 | A | 4 | 4 | 4,0 |
| T0 | B | 10 | 10 | 10,0 |

Nguồn bảng: `docs/team2_rag/g5_blind_scores_judge1.csv`, `docs/team2_rag/g5_blind_scores_judge2.csv` (dòng `id=test_049`); ánh xạ: `docs/team2_rag/g5_blind_eval_key.json`, `mapping[id=test_049]`.

**Lý do khác nhau:** **Khoảng trống nguồn:** `docs/team2_rag/g5_error_analysis.md` chưa có mục riêng cho `test_049`; không gán nguyên nhân gốc rễ như thể đã được báo cáo đó xác nhận. Đối chiếu `llm_context_chunk_ids` đã lưu cho thấy B0 có Điều 137 Khoản 2 nhưng thiếu Khoản 1; T0 có cả hai khoản. Ghi chú của cả hai giám khảo trong các CSV xác nhận B0 thiếu phần mô hình quản lý và để lộ cụm `LEGAL CONTEXT`. Đây là giải thích từ context và phiếu điểm, chưa phải kết luận nguyên nhân riêng của BGE.

**Lời thoại:** “B0 chỉ trả lời được phần người đại diện. T0 có thêm khoản về mô hình quản lý nên đầy đủ hơn. Ca này chưa được phân tích riêng trong báo cáo lỗi; ở đây chúng tôi đối chiếu bản lưu và ghi chú giám khảo.”

## `test_052` — T0 kém hơn

**Câu hỏi:** Hợp đồng giữa công ty trách nhiệm hữu hạn hai thành viên trở lên với Giám đốc của công ty phải được ai chấp thuận, và thời hạn quyết định là bao lâu?

### B0 — `outcome=answered`

```text
Hợp đồng giữa công ty trách nhiệm hữu hạn hai thành viên trở lên với Giám đốc của công ty phải được Hội đồng thành viên chấp thuận [C1], [C2]. Trường hợp Điều lệ công ty không quy định khác, Hội đồng thành viên phải quyết định chấp thuận hoặc không chấp thuận hợp đồng trong thời hạn 15 ngày kể từ ngày nhận được thông báo [C3], [C4].
```

Citation đã lưu (nhãn → chunk):

- `[C1]` → `luat-59-2020-qh14-v1__dieu-67__k1__0`
- `[C2]` → `vbhn-67-vbhn-vpqh-v1__dieu-67__k1__0`
- `[C3]` → `luat-59-2020-qh14-v1__dieu-67__k2__0`
- `[C4]` → `vbhn-67-vbhn-vpqh-v1__dieu-67__k2__0`

`llm_context_chunk_ids` đã lưu:

- `luat-59-2020-qh14-v1__dieu-67__k1__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-67__k1__0`
- `luat-59-2020-qh14-v1__dieu-67__k2__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-67__k2__0`
- `luat-59-2020-qh14-v1__dieu-67__k3__0`

### T0 — `outcome=answered`

```text
Hợp đồng, giao dịch giữa công ty trách nhiệm hữu hạn hai thành viên trở lên với Giám đốc của công ty phải được Hội đồng thành viên chấp thuận [C1]. Tuy nhiên, các văn bản pháp luật được cung cấp không quy định cụ thể về thời hạn quyết định đối với loại hình công ty trách nhiệm hữu hạn hai thành viên trở lên.
```

Citation đã lưu (nhãn → chunk):

- `[C1]` → `luat-59-2020-qh14-v1__dieu-67__k1__0`

`llm_context_chunk_ids` đã lưu:

- `luat-59-2020-qh14-v1__dieu-86__k3__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-86__k3__0`
- `luat-59-2020-qh14-v1__dieu-86__k1__0`
- `vbhn-67-vbhn-vpqh-v1__dieu-86__k1__0`
- `luat-59-2020-qh14-v1__dieu-67__k1__0`

### Điểm chấm mù và diễn giải

| Hệ thống | Cột sau giải mã | Giám khảo 1 | Giám khảo 2 | Trung bình /10 |
| :--- | :---: | ---: | ---: | ---: |
| B0 | B | 10 | 10 | 10,0 |
| T0 | A | 5 | 5 | 5,0 |

Nguồn bảng: `docs/team2_rag/g5_blind_scores_judge1.csv`, `docs/team2_rag/g5_blind_scores_judge2.csv` (dòng `id=test_052`); ánh xạ: `docs/team2_rag/g5_blind_eval_key.json`, `mapping[id=test_052]`.

**Lý do khác nhau:** Theo `docs/team2_rag/g5_error_analysis.md`, mục Context: T0 xếp Điều 86 về doanh nghiệp nhà nước lên trước, đẩy Điều 67 Khoản 2 ra ngoài top 5. Vì thiếu khoản này, câu trả lời bỏ sót thời hạn 15 ngày. B0 giữ được cả Khoản 1 và Khoản 2 Điều 67 nên trả lời đủ.

**Lời thoại:** “Đây là ca ngược lại: T0 làm mất khoản chứa thời hạn và trả lời thiếu. Rerank có thể cải thiện thứ hạng nhưng cũng có thể làm giảm độ phủ của câu hỏi nhiều ý.”

## Chạy lại live khi chuẩn bị buổi demo

Các lệnh sau là hướng dẫn cho lần chạy sau, chưa được thực thi khi soạn tài liệu này. Live cần corpus/chunks, dependencies và `GEMINI_API_KEY` đã được cấp vào biến môi trường; không đưa key lên màn hình. Kết quả mới có thể khác bản lưu. Nguồn chế độ chạy: `team2_rag/docs_2/week12/tasks.md`, mục 3.1; cấu hình: `team2_rag/runtime.py`.

### BM25-only trên CPU

Từ thư mục gốc repo, với môi trường đã cài đặt:

```bash
RAG_BM25_ONLY=true RAG_RERANK=false \
RAG_CHUNKS=data/doanh-nghiep/processed/chunks.jsonl \
RAG_TOP_K=10 LLM_PROVIDER=gemini LLM_MODEL=gemini-3.1-flash-lite \
LLM_RATE_LIMIT_RPM=12 LLM_ALLOW_FALLBACK=false \
.venv/bin/python -m uvicorn team2_rag.api:create_app \
  --factory --host 127.0.0.1 --port 8001 --workers 1
```

Kiểm tra `/internal/v1/ready`, sau đó nhập lần lượt nguyên câu hỏi ở trên qua giao diện đã nối Backend. BM25-only không nạp BGE và không tái hiện nhánh T0. Giữ một worker để giới hạn slot áp dụng cho toàn phiên demo. Nguồn lệnh/endpoint: `docs/team2_rag/week4-integration.md`; giới hạn gọi: `team2_rag/docs_2/week12/tasks.md`; model và `top_k`: `docs/team2_rag/runs/g5/b0.json`, trường `config`.

Nếu cần chạy lại benchmark B0, ghi kết quả mới ở đường dẫn tạm, giữ nguyên bằng chứng G5:

```bash
RAG_CHUNKS=data/doanh-nghiep/processed/chunks.jsonl \
RAG_TOP_K=10 LLM_PROVIDER=gemini LLM_MODEL=gemini-3.1-flash-lite \
LLM_RATE_LIMIT_RPM=12 \
.venv/bin/python scripts/benchmark_g5.py run --system b0 \
  --dataset team1_data/golden/test_set_v1.json \
  --out /tmp/g5-demo-b0.json
```

Runner chạy Test Set, không chỉ các câu chọn cho demo. Nguồn cách dùng: `scripts/benchmark_g5.py`; cấu hình đối chiếu: `docs/team2_rag/runs/g5/b0.json`. Bản đo NFR-07 dùng `top_k=5`, còn G5 dùng `top_k=10`; không dùng số đo độ trễ của cấu hình trước để bảo đảm thời gian của lần chạy này. Nguồn: `docs/team2_rag/ai_service_load_and_stability_report.md`, `docs/team2_rag/g5_b0_vs_t0_report.json`.

### Hybrid + BGE trên GPU

Chuẩn bị GPU theo `notebooks/g5_t0_colab.ipynb`: kiểm CUDA, dùng cùng Test Set/model/tham số G5, dựng BM25 và Dense từ cùng snapshot chunks, chuẩn bị Qdrant local và model đã chỉ định trong notebook. Chạy notebook ở môi trường GPU riêng; các bước cài/tải dữ liệu và gọi Gemini của notebook chỉ thực hiện khi chuẩn bị lượt live.

Khi chạy AI Service, cần `RAG_BM25_ONLY=false`, `RAG_RERANK=true`, `RAG_RERANK_DEVICE=cuda`, cùng `RAG_BM25_INDEX`, `RAG_DENSE_INDEX`, `RAG_QDRANT_PATH`, `RAG_CHUNKS` trỏ đến dữ liệu đã chuẩn bị. Với benchmark, dùng runner `--system t0` và đầu ra mới, ví dụ `/tmp/g5-demo-t0.json`. Nguồn: `team2_rag/runtime.py`, `scripts/benchmark_g5.py`, `notebooks/g5_t0_colab.ipynb`.

Không bật BGE trên CPU để kỳ vọng tái hiện điều kiện GPU của T0; nếu thiếu GPU hoặc index, trình chiếu các cặp trả lời đã lưu. Lượt mới cần ghi lại fallback và lỗi, không thay thế âm thầm kết quả trong kịch bản.

## Phương án dự phòng: mock server

Khi không có key/index hoặc live gián đoạn, dừng server live rồi chạy:

```bash
RAG_MOCK_SCENARIO=answered_markdown \
.venv/bin/python -m uvicorn team2_rag.api.mock_app:create_mock_app \
  --factory --host 127.0.0.1 --port 8001 --workers 1
```

Nguồn: `team2_rag/docs_2/week12/tasks.md`, mục chế độ mock; `team2_rag/api/mock_app.py`.

Mock không cần key, không gọi LLM và trả fixture để minh họa luồng giao diện/citation. Mock **không phát lại** các bản B0/T0 ở trên và không chứng minh chất lượng rerank. Vẫn mở tài liệu này để trình bày các cặp kết quả thật đã lưu.

Lời thoại chuyển dự phòng: “Phần live đang dùng dữ liệu mẫu để minh họa luồng tích hợp. Phần so sánh B0/T0 vẫn lấy từ kết quả thí nghiệm đã lưu, không lấy từ mock.”

## Điểm cần nói rõ khi kết thúc

- `test_049` chưa có phân tích riêng trong `docs/team2_rag/g5_error_analysis.md`; diễn giải tại đây dựa trên context và phiếu điểm.
- Test Set còn `draft_needs_legal_review` theo `team1_data/golden/test_set_v1.json`; điểm chấm mù không thay thế thẩm định pháp lý.
- Các lệnh live/GPU là hướng dẫn chạy lại, chưa được kiểm thực thi trong lần soạn này. Khi trình bày kết quả cũ, luôn gọi đúng là “bản chạy đã lưu”.

