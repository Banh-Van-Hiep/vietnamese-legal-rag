# Bàn giao AI Service cho Team 3 — VLRA-T2-48 / VLRA-84

Team 3 viết Dockerfile và ghép hệ thống. **Trạng thái: chưa kiểm trong container**; các lệnh dưới là
hướng dẫn dựa trên code hiện tại, chưa phải nghiệm thu live hoặc Hybrid trên GPU.
Chế độ triển khai mặc định của bàn giao là **BM25-only**, đặt rõ `RAG_BM25_ONLY=true` vì code mặc định `false`.

## Image, cài đặt và khởi động

Gợi ý base image `python:3.12-slim`, thư mục làm việc `/app`. Copy repo gồm `pyproject.toml`, README gốc,
`team1_data/`, `team2_rag/` và `contracts/v0.1/`; API đọc JSON Schema trực tiếp từ repo.
Cài và chạy từ `/app`, không đặt thư mục làm việc vào `/app/team2_rag` vì `types.py` che module chuẩn:

```bash
pip install -r team2_rag/requirements.txt && pip install -e .
RAG_BM25_ONLY=true python -m uvicorn team2_rag.api:create_app --factory --host 0.0.0.0 --port 8001 --workers 1
```

**Giữ `--workers 1` và một replica**: slot khóa và hàng đợi nằm trong từng process, không chia sẻ giữa
workers/replicas. Tăng số process sẽ tăng số query chạy đồng thời, phá giới hạn chung 1 lượt chạy + 4 lượt chờ.
Không bật reload trong container triển khai.

Bản khóa được lấy trên Python 3.12.15 ở môi trường hiện tại; chưa xác minh khả năng cài wheel trên Linux slim.
Hybrid + Rerank cài thêm `pip install -e '.[dense,reranker]'`; đây là extras khoảng phiên bản của
`pyproject.toml`, chưa khóa GPU. Nếu chạy CUDA, Team 3 cần chọn image/runtime và bản torch phù hợp GPU.

## Biến môi trường

Không đưa secret vào image. Khi chạy local, key chỉ ở `.env` (sao chép từ
`configs/team2-api.env.example`); trong container, cấp qua biến môi trường lúc chạy hoặc mount `.env`
chỉ đọc tại `/app/.env`. Không ghi key vào Dockerfile, tài liệu hay log.

| Biến | Bắt buộc / mặc định bàn giao | Ý nghĩa |
| --- | --- | --- |
| `RAG_BM25_ONLY` | `true` | BM25 + LLM, không Dense/Qdrant/BGE; code tự mặc định `false` nếu bỏ biến. |
| `LLM_PROVIDER` | Bắt buộc chọn, ví dụ `gemini` | Code mặc định `openai`; phải khớp key và model. |
| `LLM_MODEL` | Bắt buộc, không có mặc định | Tên model được cấp cho project. |
| `GEMINI_API_KEY` | Bắt buộc khi chọn `gemini` | Với provider khác dùng `OPENAI_API_KEY` / `QWEN_API_KEY`; Ollama không cần key. |
| `RAG_CHUNKS` | `data/doanh-nghiep/processed/chunks.jsonl` | Chunks đã kiểm duyệt; BM25 dựng index trong RAM khi khởi động. |
| `LLM_TIMEOUT_SECONDS` | Tùy chọn, `30.0` | Hạn gọi provider; deadline API vẫn tối đa 45 giây. |
| `LLM_RATE_LIMIT_RPM` | Tùy chọn, `12` | Giới hạn Gemini, tính cả retry; `0` tắt giới hạn. |
| `LLM_ALLOW_FALLBACK` | Tùy chọn, `true` | Cho Gemini dùng model dự phòng; benchmark đặt `false`. |
| `LLM_CONTEXT_WINDOW_TOKENS` | Tùy chọn; bắt buộc với Ollama | Khớp cửa sổ model; nếu bỏ, code dùng ngân sách ký tự xấp xỉ. |
| `RAG_TOP_K`, `RAG_VERIFY_CLAIMS` | Tùy chọn, `10`, `false` | Số kết quả truy xuất và kiểm tra claims. |

Với Hybrid + Rerank, bổ sung:

| Biến | Giá trị / yêu cầu |
| --- | --- |
| `RAG_BM25_ONLY` | `false` |
| `RAG_BM25_INDEX` | Bắt buộc; ví dụ `data/index/bm25/week4-v1`. |
| `RAG_DENSE_INDEX` | Bắt buộc; ví dụ `data/index/dense/week4-v1`. |
| `RAG_QDRANT_PATH` | Đường dẫn Qdrant local có volume ghi được; ưu tiên hơn URL nếu được đặt. |
| `RAG_QDRANT_URL` | Dùng khi không đặt path; mặc định `http://localhost:6333`, đổi sang tên service Qdrant trong mạng container. |
| `RAG_RERANK`, `RAG_RERANK_DEVICE` | `true`, `cuda` khi GPU sẵn sàng; mặc định code là `false`, `cpu`. |
| `RAG_BM25_WEIGHT`, `RAG_DENSE_WEIGHT` | Tùy chọn, mặc định `0.5`, `1.0`. |
| `RAG_RETRIEVAL_TIMEOUT` | Tùy chọn, mặc định `10` giây. |
| `RAG_RERANK_TIMEOUT_SECONDS`, `RAG_STRICT_RERANK` | Tùy chọn, mặc định `4` giây, `false`; lỗi rerank có thể giữ thứ hạng Hybrid. |

Dense embedder hiện cố định CPU; `RAG_RERANK_DEVICE` chỉ áp dụng BGE. Bảng đầy đủ các biến và mặc định:
[README Team 2](../../team2_rag/README.md#cấu-hình). `timeout_seconds=45` và `max_waiting=4` là tham số
factory `create_app`, không có biến môi trường để thay đổi chúng.

## Dữ liệu và volume

| Đường dẫn trong container (với `/app` là gốc) | Chế độ | Quyền / lưu ý |
| --- | --- | --- |
| `/app/data/doanh-nghiep/processed/chunks.jsonl` | Mọi chế độ live | Chỉ đọc; có thể đổi bằng `RAG_CHUNKS`. |
| `/app/data/doanh-nghiep/processed/articles.jsonl` | Article Viewer thật | Chỉ đọc; đường dẫn cố định trong `team2_rag/articles.py`, không có biến đổi đường dẫn. |
| `/app/data/index/bm25/week4-v1/` | Hybrid | Chỉ đọc; mount toàn bộ index và `index_manifest.json`, đặt `RAG_BM25_INDEX`. |
| `/app/data/index/dense/week4-v1/` | Hybrid | Chỉ đọc; mount toàn bộ snapshot và `index_manifest.json`, đặt `RAG_DENSE_INDEX`. |
| `/app/data/index/qdrant/` | Hybrid dùng Qdrant local | Đọc/ghi, volume bền vững, đặt `RAG_QDRANT_PATH`; phải chứa collection khớp Dense manifest. |

Hai manifest Hybrid phải cùng `index_version` và tập `chunk_ids`, đồng bộ với chunks. BM25-only không đọc
index BM25/Dense trên đĩa. Nếu dùng Qdrant server thì dữ liệu volume do service Qdrant quản lý.
Hybrid cần thêm model embedding/BGE và cache; chuẩn bị model/cache trước khi chạy nếu môi trường không có mạng.
Package API hiện đặt `HF_HOME`/`TORCH_HOME` mặc định theo đường dẫn Windows; container Hybrid nên đặt
hai biến này đến cache Linux có quyền ghi (ví dụ `/app/model-cache`, `/app/model-cache/torch`).

## Healthcheck và nối với Java

Healthcheck dùng **`GET /internal/v1/ready`**. Có thể dùng thư viện chuẩn Python trong image slim:

```bash
python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8001/internal/v1/ready", timeout=5).close()'
```

200 `{"status":"ready"}` nghĩa là pipeline khởi tạo xong; lỗi khởi tạo trả 503 `LLM_UNAVAILABLE`.
`GET /internal/v1/health` chỉ báo process sống. Readiness không kiểm key với provider, Article Store,
hoặc chất lượng câu trả lời; cần thử một câu hỏi và mở Điều luật riêng khi nghiệm thu live.

Phía Java đặt **`RAG_BASE_URL=http://ai-service:8001`** nếu Compose đặt tên service là `ai-service`
(đổi hostname theo Compose thực tế). Java gọi `POST /internal/v1/query` với JSON đúng hai khóa
`question`, `history` và truyền header `X-Request-ID`. Giao diện không gọi trực tiếp dịch vụ nội bộ.

Giữ chuỗi timeout **45 giây (dịch vụ) < 50 giây (Java) < 60 giây (Frontend)**; thời gian chờ hàng đợi
nằm trong 45 giây. Hàng đầy trả 503 `LLM_UNAVAILABLE`, quá hạn trả 504 `LLM_TIMEOUT`; công việc quá hạn
HTTP vẫn giữ slot đến khi kết thúc. Tra cứu Điều luật: Java → dịch vụ tối đa 10 giây, Frontend tối đa 15 giây.
Mã lỗi và mapping Java: [hướng dẫn tích hợp](ui-integration-guide.md).

## Phạm vi chưa nghiệm thu

**Chưa kiểm trong container**, chưa cài lại trong venv sạch, chưa gọi provider live trong lần bàn giao này.
Hybrid + Rerank còn cần snapshot Team 1 và kiểm trên GPU. Kiểm thử cục bộ không thay cho nghiệm thu
cài đặt Linux/container, kết nối Java hay luồng Retrieval → LLM thật.
