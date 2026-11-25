# Team 2 — RAG và AI Service

Module điều phối Retrieval → Reranker (tùy chọn) → Context Builder → LLM → kiểm tra trích dẫn,
cung cấp API nội bộ cho Backend Java. Hợp đồng chuẩn: [contracts/v0.1](../contracts/v0.1/).
Phản hồi có ba trường `status`, `answer`, `citations`; `answered` phải có marker `[C1]…[Cn]`
khớp liên tục với citations. Đầu ra sai bị từ chối, không tự sửa trích dẫn.

## Cài đặt

Chạy mọi lệnh từ **gốc repo**. Không chạy Python bên trong `team2_rag/` vì `types.py` che module chuẩn `types`.
Ví dụ trên macOS/Linux, Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r team2_rag/requirements.txt && pip install -e .
```

Bản khóa dành cho BM25-only, API và test; không gồm torch/Dense/BGE. Hybrid + Rerank cài thêm
`pip install -e '.[dense,reranker]'`; extras vẫn dùng khoảng phiên bản trong `pyproject.toml`, chưa khóa
hoặc kiểm trên GPU. Phụ thuộc gián tiếp ngoài các gói đã liệt kê vẫn do trình cài giải quyết.

## Cấu hình

Nếu chưa có `.env`, sao chép mẫu rồi tự điền provider, model và key trong file đó:

```bash
cp -n configs/team2-api.env.example .env
```

Với Gemini, điền `LLM_PROVIDER=gemini`, `LLM_MODEL` đúng tên model được cấp và `GEMINI_API_KEY`.
**API key chỉ lưu trong `.env`**, không ghi vào lệnh, mã nguồn hoặc log. Runtime đọc `.env` ở gốc repo;
biến môi trường của process ghi đè giá trị cùng tên. Cấu hình bàn giao mặc định chọn **BM25-only** bằng
`RAG_BM25_ONLY=true`; mặc định của code nếu bỏ biến này là `false` (Hybrid).

Bảng ghi **mặc định trong code**, đối chiếu [mẫu cấu hình](../configs/team2-api.env.example),
`config/settings.py`, `runtime.py` và `api/app.py`. Mẫu để trống provider/model/key; đường dẫn index
trong mẫu chỉ là ví dụ, không bảo đảm dữ liệu đã có.

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `LLM_PROVIDER` | `openai` | `openai`, `gemini`, `qwen` hoặc `ollama`; chọn đúng provider live. |
| `LLM_MODEL` | Trống | Bắt buộc khi chạy live. |
| `OPENAI_API_KEY` | Trống | Bắt buộc khi chọn `openai`. |
| `GEMINI_API_KEY` | Trống | Bắt buộc khi chọn `gemini`. |
| `QWEN_API_KEY` | Trống | Bắt buộc khi chọn `qwen`; `ollama` không cần key. |
| `QWEN_BASE_URL` | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | Địa chỉ API Qwen tương thích. |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Địa chỉ server Ollama. |
| `LLM_TIMEOUT_SECONDS` | `30.0` | Hạn gọi provider; remote tối đa 30 giây, Ollama tối đa 600; API vẫn có deadline 45 giây. |
| `LLM_MAX_RETRIES` | `0` | Chỉ chấp nhận 0 tại tầng dịch vụ LLM; Gemini có xử lý thử lại riêng cho 429/503. |
| `LLM_ALLOW_FALLBACK` | `true` | Cho Gemini dùng model dự phòng; đặt `false` khi benchmark. |
| `LLM_RATE_LIMIT_RPM` | `12` | Số lần gọi Gemini/phút, tính cả retry; `0` tắt giới hạn. |
| `LLM_TEMPERATURE` | `0.0` | Tham số sinh câu trả lời. |
| `LLM_MAX_OUTPUT_TOKENS` | `1500` | Ngân sách token đầu ra. |
| `LLM_CONTEXT_WINDOW_TOKENS` | Không đặt | Cửa sổ đúng của model; bắt buộc với Ollama. Bật ngân sách token khi đặt. |
| `LLM_MAX_CONTEXT_TOKENS` | `3000` | Trần token ngữ cảnh khi dùng ngân sách token. |
| `LLM_SAFETY_MARGIN_TOKENS` | `256` | Token dự phòng; cửa sổ phải lớn hơn đầu ra cộng phần dự phòng. |
| `LLM_MAX_CONTEXT_CHUNKS` | `5` | Số chunk tối đa trong context. |
| `LLM_MAX_CONTEXT_CHARS` | `9000` | Ngân sách ký tự xấp xỉ khi chưa đặt cửa sổ token. |

Nếu chưa đặt `LLM_CONTEXT_WINDOW_TOKENS`, giới hạn ký tự chưa đáp ứng đặc tả ngân sách token.
Gemini/Qwen/Ollama dùng bộ đếm chặn trên theo byte UTF-8 khi bật ngân sách token. Nhánh `openai`
cần thêm gói tùy chọn `tiktoken` để đếm token; gói này chưa cài và chưa khóa trong môi trường kiểm.

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `RAG_CHUNKS` | `data/doanh-nghiep/processed/chunks.jsonl` | Dữ liệu chunk; đường dẫn tương đối tính từ gốc repo. |
| `RAG_BM25_ONLY` | `false` | `true`: dựng BM25 từ chunks khi khởi động, bỏ Dense và rerank. |
| `RAG_BM25_INDEX` | Không có | Bắt buộc với Hybrid; mẫu: `data/index/bm25/week4-v1`. |
| `RAG_DENSE_INDEX` | Không có | Bắt buộc với Hybrid; mẫu: `data/index/dense/week4-v1`. |
| `RAG_QDRANT_URL` | `http://localhost:6333` | Qdrant server cho Hybrid. |
| `RAG_QDRANT_PATH` | Không đặt | Qdrant lưu cục bộ; nếu đặt sẽ ưu tiên hơn URL. |
| `RAG_TOP_K` | `10` | Số kết quả truy xuất chuyển vào pipeline. |
| `RAG_BM25_WEIGHT` | `0.5` | Trọng số BM25 trong Hybrid. |
| `RAG_DENSE_WEIGHT` | `1.0` | Trọng số Dense trong Hybrid. |
| `RAG_RETRIEVAL_TIMEOUT` | `10` | Hạn truy xuất Hybrid, đơn vị giây. |
| `RAG_RERANK` | `false` | Bật BGE trong Hybrid; khi tắt không nạp/warm-up BGE. |
| `RAG_RERANK_DEVICE` | `cpu` | Thiết bị BGE; dùng `cuda` khi có GPU phù hợp. |
| `RAG_RERANK_TRUNCATE` | `false` | Cho phép cắt passage dài thay vì lỗi quá 512 token. |
| `RAG_STRICT_RERANK` | `false` | Khi tắt, lỗi/quá hạn rerank sẽ giữ thứ hạng Hybrid. |
| `RAG_RERANK_TIMEOUT_SECONDS` | `4` | Hạn rerank trong pipeline, đơn vị giây. |
| `RAG_VERIFY_CLAIMS` | `false` | Yêu cầu claims và kiểm tra nhận định; thường bật khi benchmark. |
| `RAG_MOCK_SCENARIO` | `answered` | Chỉ dùng cho mock server, đọc từ môi trường process. |

`RAG_MOCK_SCENARIO` nhận `answered`, `answered_markdown`, `insufficient_context`, `error_timeout`,
`error_busy`, `error_invalid_output`. Mock server không tự đọc `.env`; đặt biến ngay trong lệnh chạy.

## Bốn chế độ chạy

Theo [task tuần 12, mục 3.1](docs_2/week12/tasks.md#31-chế-độ-chạy-ai-service):

| Chế độ | Lệnh từ gốc repo (venv đã kích hoạt) | Cần |
| --- | --- | --- |
| Mock CLI | `python -m team2_rag --scenario answered` | Không key, không index; còn có `--scenario insufficient_context`. |
| Mock server | `RAG_MOCK_SCENARIO=answered_markdown python -m uvicorn team2_rag.api.mock_app:create_mock_app --factory --port 8001` | Không key, không index. |
| Live BM25-only | `RAG_BM25_ONLY=true python -m uvicorn team2_rag.api:create_app --factory --host 127.0.0.1 --port 8001` | `LLM_PROVIDER`, `LLM_MODEL`, key tương ứng và chunks. |
| Live Hybrid + Rerank | `RAG_BM25_ONLY=false RAG_RERANK=true RAG_RERANK_DEVICE=cuda python -m uvicorn team2_rag.api:create_app --factory --host 127.0.0.1 --port 8001` | Extras Dense/Reranker, cấu hình LLM, chunks, hai index Team 1, Qdrant; nên có GPU, khoảng 2 GB RAM cho BGE. |

Với Hybrid, đặt `RAG_BM25_INDEX`, `RAG_DENSE_INDEX`, `RAG_QDRANT_PATH` trong `.env` (hoặc dùng
`RAG_QDRANT_URL`). Hai manifest phải cùng `index_version` và tập `chunk_ids`. Lệnh Hybrid ghi rõ
`RAG_BM25_ONLY=false` để ghi đè cấu hình BM25-only trong `.env`. Dense embedder hiện chạy CPU;
`RAG_RERANK_DEVICE` chỉ điều khiển BGE. Lệnh live sẽ gọi provider khi xử lý câu hỏi có context.

## API và kiểm tra nhanh

| Endpoint | Hành vi |
| --- | --- |
| `POST /internal/v1/query` | JSON đúng hai khóa `{question, history}`; câu hỏi 1–2000 ký tự, lịch sử là mảng. Trả `{status, answer, citations}`. |
| `GET /internal/v1/ready` | 200 `{"status":"ready"}` khi pipeline khởi tạo xong; lỗi khởi tạo trả 503 `LLM_UNAVAILABLE`. |
| `GET /internal/v1/health` | 200 `{"status":"up"}`; chỉ kiểm tra process đang phục vụ. |
| `GET /internal/v1/documents/{document_id}/articles/{article_id}` | Toàn văn Điều luật; cần `data/doanh-nghiep/processed/articles.jsonl` cho dữ liệu thật. |

Ví dụ dùng với server đang chạy (câu hỏi gửi đến live server có thể gọi LLM):

```bash
curl --fail-with-body http://127.0.0.1:8001/internal/v1/ready
curl --fail-with-body http://127.0.0.1:8001/internal/v1/health
curl --fail-with-body --max-time 50 http://127.0.0.1:8001/internal/v1/query \
  -H 'Content-Type: application/json' -H 'X-Request-ID: demo-01' \
  -d '{"question":"Ai có quyền thành lập doanh nghiệp?","history":[]}'
curl --fail-with-body http://127.0.0.1:8001/internal/v1/documents/mock_v1/articles/art1
```

`mock_v1/art1` là fixture có sẵn; với dữ liệu thật, dùng `document_id` và `article_id` từ citation.
`/ready` không kiểm tra key với provider, không thử sinh câu trả lời và không kiểm Article Store.

Mỗi process chạy **1 lượt query + tối đa 4 lượt chờ** cho toàn pipeline. Hàng đầy trả ngay 503;
thời gian chờ tính trong deadline **45 giây**. Hết hạn chờ trả 504 và không chạy pipeline; công việc
đã chạy giữ slot đến khi thực sự kết thúc dù HTTP đã quá hạn. Giữ chuỗi **45 (dịch vụ) < 50 (Java)
< 60 giây (Frontend)**. Article Viewer: Java → dịch vụ tối đa 10 giây, Frontend tối đa 15 giây.
`timeout_seconds=45`, `max_waiting=4` là tham số `create_app`, không có biến môi trường tương ứng.

| HTTP | Mã lỗi nội bộ | Thử lại |
| --- | --- | --- |
| 400 | `INVALID_REQUEST` | Không |
| 404 | `DOCUMENT_NOT_FOUND`, `ARTICLE_NOT_FOUND` | Không |
| 413 / 415 | `PAYLOAD_TOO_LARGE` / `UNSUPPORTED_MEDIA_TYPE` | Không |
| 502 | `INVALID_LLM_OUTPUT`, `CITATION_INVALID` | Không |
| 503 | `LLM_UNAVAILABLE`, `RETRIEVAL_UNAVAILABLE` | Có |
| 504 | `LLM_TIMEOUT`, `RETRIEVAL_TIMEOUT` | Có |
| 500 | `INTERNAL_ERROR` | Không |

Chi tiết envelope và ánh xạ mã công khai của Java: [hướng dẫn tích hợp giao diện](../docs/team2_rag/ui-integration-guide.md).
`insufficient_context` là kết quả HTTP 200 với citations rỗng, không phải lỗi hạ tầng.

## Lỗi thường gặp

- **Gemini 429/503:** kiểm tra quota/model và giãn lượt hỏi; giữ `LLM_RATE_LIMIT_RPM=12` (hoặc giảm).
  Giới hạn này tính cả retry; tăng RPM không tăng quota của provider. Có thể chuyển sang mock server để demo.
- **Thiếu chunks/index, `/ready` trả 503:** kiểm tra đường dẫn từ gốc repo. BM25-only chỉ cần chunks;
  Hybrid cần cả manifest, index, cùng phiên bản chunk và Qdrant tương ứng. Thiếu `articles.jsonl` chỉ được
  phát hiện khi mở Điều luật và trả 503 `RETRIEVAL_UNAVAILABLE`.
- **BGE trên CPU chậm:** dùng `RAG_RERANK_DEVICE=cuda` khi có GPU và bản torch phù hợp; máy CPU chọn
  BM25-only hoặc tắt `RAG_RERANK`. Đặt `RAG_STRICT_RERANK=true` nếu cần phát hiện lỗi thay vì giữ thứ hạng cũ.

## Kiểm thử

```bash
.venv/bin/python scripts/harness_verify.py
.venv/bin/python -m pytest team2_rag/tests -q
.venv/bin/python -m pytest tests -q
.venv/bin/python -m team2_rag --scenario answered
```

Harness chạy bốn cổng kiểm tra và gồm cả hai bộ pytest; xem số test bị bỏ qua khi thiếu phụ thuộc tùy chọn.
Hướng dẫn đóng gói cho Team 3: [bàn giao dịch vụ](../docs/team2_rag/ai-service-handoff.md).
