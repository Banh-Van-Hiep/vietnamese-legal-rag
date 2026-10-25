# Tích hợp Team 2 theo đặc tả v2.0

Phạm vi: VLRA-38/VLRA-45 và hai điểm nối với VLRA-39/VLRA-47. Module cung cấp
HTTP mock để Team 3 tích hợp độc lập, cùng contract với live. Kiểm thử live toàn
luồng còn chờ dữ liệu/index/article store của Team 1 và cấu hình model thực tế.

## Đối chiếu yêu cầu

| Đặc tả v2.0 | Implementation | Bằng chứng |
| --- | --- | --- |
| 7.6, 9.9: status, marker, citation/provenance | `models.response.RAGResponse`; generation và mọi nhánh pipeline dùng validator chung | Model, generation, pipeline và HTTP regressions |
| 9.14: Python trả mã nội bộ, Java ánh xạ public | `errors.classify_internal`, `api.handlers` | Test cũ và mới dùng cùng bảng mã |
| NFR-13, 5.6: không log raw question/answer/prompt/secret | Handler chỉ ghi request ID, code, tên exception; startup không ghi exception text | Kiểm tra log bằng chuỗi giả |
| 7.7-7.8: HTTP mock độc lập | `api.mock_app.create_mock_app` | Query và Viewer cùng routes với live, không tải runtime/models |
| 7.2, 9.11-9.12: mở toàn Điều đúng phiên bản | `articles.ArticleRepository`, `JsonlArticleStore` | Source lookup, 404/503/504, version, newline và schema tests |
| 9.8, 9.12: internal schemas | `contracts/v0.1/internal_query_request.schema.json`, `internal_article.schema.json` | JSON Schema và semantic validation |

## Điểm vào và API

- `RAGPipeline.query(question, history, request_id=...)`: retrieval → strict rerank → context → generation → shared validation.
- `build_runtime()`: tải các index/model theo cấu hình; không tự rebuild collection.
- `create_app()`: live FastAPI factory; luôn gọi `install_error_handlers(app)` và dùng `RAGResponse` mặc định.
- `create_mock_app()`: HTTP mock được chọn tường minh bằng lệnh chạy riêng; không có fallback từ live sang mock.
- `service.query()` là mock thư viện cũ, không phải handler live.

| Method | Path | Kết quả |
| --- | --- | --- |
| POST | `/internal/v1/query` | `{question, history}` → `{status, answer, citations}` |
| GET | `/internal/v1/documents/{document_id}/articles/{article_id}` | ArticleResponse đủ 6 field, toàn Điều |
| GET | `/internal/v1/health` | Liveness; không chứng minh models đã sẵn sàng |
| GET | `/internal/v1/ready` | Query runtime sẵn sàng; 503 khi khởi động thất bại |

Python không lưu hội thoại hoặc cấp public IDs. Public SSE, camelCase mapping,
idempotency và DB thuộc Team 3. Query chỉ nhận `question` và `history`; scenario,
model, context và public IDs không được gửi trong request. Các giới hạn là 2000
code point sau trim, tối đa 5 cặp history/20000 ký tự và body 256 KiB.

## Chạy HTTP mock cho Team 3

Từ gốc repo, Python 3.12 được khuyến nghị:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test,api]"
python -m uvicorn team2_rag.api.mock_app:create_mock_app --factory --host 127.0.0.1 --port 8001
```

```bash
curl -i http://127.0.0.1:8001/internal/v1/ready
curl -i http://127.0.0.1:8001/internal/v1/query -H 'Content-Type: application/json' -H 'X-Request-ID: mock-query-1' -d '{"question":"Kiểm thử tích hợp","history":[]}'
curl -i http://127.0.0.1:8001/internal/v1/documents/mock_v1/articles/art1 -H 'X-Request-ID: mock-article-1'
```

Java đặt `RAG_BASE_URL=http://localhost:8001`. Fixture trả `mock_v1/art1`, nguồn
HTTPS `example.com`, nội dung ghi rõ giả lập và header `X-RAG-Mode: mock`.
Fixture article là dữ liệu kiểm thử riêng, không phải bản ghép chunk hay văn bản
pháp luật. Team 3 cần hiển thị nhãn môi trường mock trong demo.

Để thử `insufficient_context`, khởi động lại server với cấu hình môi trường:

```bash
RAG_MOCK_SCENARIO=insufficient_context python -m uvicorn team2_rag.api.mock_app:create_mock_app --factory --host 127.0.0.1 --port 8001
```

Mock chỉ có hai tình huống này theo mục 7.7; không bổ sung field scenario hoặc
backdoor gây lỗi vào request. Các nhánh lỗi kỹ thuật được kiểm thử bằng dependency
injection. Fixture không được tính vào Golden Dataset hoặc chất lượng pháp lý.

## Mã lỗi nội bộ

| Python HTTP/code | Java public code | Retryable |
| --- | --- | --- |
| 502 `INVALID_LLM_OUTPUT` / `CITATION_INVALID` | `UPSTREAM_INVALID_RESPONSE` | false |
| 503 `RETRIEVAL_UNAVAILABLE` / `LLM_UNAVAILABLE` | `SERVICE_UNAVAILABLE` | true |
| 504 `RETRIEVAL_TIMEOUT` / `LLM_TIMEOUT` | `UPSTREAM_TIMEOUT` | true |
| 404 `DOCUMENT_NOT_FOUND` / `ARTICLE_NOT_FOUND` | Giữ nguyên khi lookup article | false |

Unready/busy trả `LLM_UNAVAILABLE`; lỗi retrieval/reranker trả
`RETRIEVAL_UNAVAILABLE`; hết deadline xử lý AI 45 giây trả `LLM_TIMEOUT`.
Request sai trả 400/413/415, route/method sai trả 404/405; lỗi ngoài dự kiến trả
500. Envelope chỉ có `error.code/message/retryable`, kèm `X-Request-ID`.
Các helper mã public cũ vẫn được giữ cho compatibility, nhưng không dùng làm wire
code của service nội bộ Python.

## ArticleRepositoryPort và bàn giao Team 1

Team 1 cung cấp `get_article(document_id, article_id)` hoặc snapshot articles
JSONL. Truyền repository qua `create_app(article_store=repository)`, hoặc cấu hình
`RAG_ARTICLES` trỏ tới snapshot có nguyên văn Điều. Mặc định là
`data/doanh-nghiep/processed/articles.jsonl`.

Mỗi record có `document_id`, `document_title`, `article_id`, `article`, `content`,
`source_url`; metadata lưu trữ bổ sung được bỏ khỏi HTTP response. Nội dung giữ
nguyên xuống dòng. Store nạp snapshot hợp lệ một lần, giữ phiên bản bất biến;
khởi động lại service khi chuyển snapshot. Cùng identity bị trùng hoặc source
hỏng/thiếu → 503; không tự đọc chunks để thay thế. Source chưa sẵn sàng không bị
báo nhầm là document/article không tồn tại. Khi đã có source, thiếu document và
thiếu article được phân biệt bằng hai mã 404. Lookup không gọi LLM; deadline 10s.

Chưa tạo corpus/articles thay Team 1. Trong lúc chờ, Team 3 dùng HTTP mock ở trên.

## Chạy live

```bash
python -m pip install -e ".[test,api,rag,retrieval,dense,reranker]"
python -m team1_data.retrieval build --out data/index/bm25/week4-v1
python -m team1_data.retrieval dense-build --out data/index/dense/week4-v1
python -m team2_rag.run_query "Công ty cổ phần có bắt buộc phải có cổ phần phổ thông không?"
python -m uvicorn team2_rag.api:create_app --factory --host 127.0.0.1 --port 8001 --workers 1
```

Copy các biến cần thiết từ `configs/team2-api.env.example` vào `.env` hiện có,
không ghi đè API key của người khác. BM25/Dense phải cùng version/chunk IDs;
Qdrant và embedding phải khớp manifest. `BM25SearchAdapter` tương thích envelope
hiện tại của Team 1 tại biên Hybrid; không sửa thuật toán ranking Team 1.

LLM provider/model/window/key do cấu hình quyết định. Ollama có hướng dẫn riêng
trong README; smoke Ollama chỉ chứng minh đoạn Context → LLM, không chứng minh
retrieval/BGE live. Ngân sách target là retrieval 5s, rerank 5s, LLM 30s và AI 45s.
API deadline 45s không hủy được thread CPU/provider đang chạy; slot giữ đến khi
công việc thật sự kết thúc. Chọn timeout LLM ≤30s khi nghiệm thu live; Ollama
120s chỉ phục vụ smoke/dev riêng. Chưa có bằng chứng benchmark latency target.

History không được dùng làm chứng cứ. Tham chiếu mơ hồ yêu cầu làm rõ; query
rewriting tổng quát và applicability theo đơn vị luật còn chờ các lớp tương ứng,
không tính là đã hoàn tất target system.

## Kiểm thử và giới hạn nghiệm thu

```bash
python -m pip install -r team2_rag/requirements-dev.txt
python -m pytest team2_rag/tests tests/test_team2_mock.py tests/test_team2_reranker.py tests/test_team2_pipeline.py tests/test_team2_api.py -q
python -m team2_rag.validate_golden
```

Bộ test gồm cả các TestCase cũ và pytest mới. Các test về generation/retrieval
boundary dùng scorer/provider giả; không tính thành chất lượng AI thật. Golden
chính có 40 mẫu, 10 mẫu `gold_031`–`gold_040` giữ nguyên; 5 mẫu evaluation fixture
riêng tái dùng 4 câu cũ và thêm `gold_041`, không được báo là 5 QA mới đã gộp.

Kiểm tra bản sửa ngày 25/10/2026, nền `feature/team2-rag` tại `beae8ee`:

- 415 test pass, 147 subtest pass, không skip trong lệnh Team 2 ở trên.
- HTTP qua socket/Uvicorn thật ở loopback: query 200, citation → article 200,
  đúng 6 field và giữ newline; document/article vắng trả đúng hai mã 404;
  request thêm scenario bị chặn 400; request ID và header mock được giữ.
- OpenAPI hiển thị question/history và model response; HTTP mock không tải
  retrieval, BGE hoặc provider. Kiểm tra này không phải Java/React end-to-end.
- Golden chính 40 mẫu giữ nguyên và vượt qua validator. Không phát sinh QA
  luật mới từ fixture hoặc kết quả fake-provider.

Chưa nghiệm thu VLRA-38 live toàn luồng, chỉ tiêu citation/answer/latency hoặc
báo cáo benchmark VLRA-40. Các lỗi BM25/preprocessing đã tái hiện ở baseline
`develop` cần Team 1 sửa; không đưa mock/fake vào báo cáo như live thành công.
