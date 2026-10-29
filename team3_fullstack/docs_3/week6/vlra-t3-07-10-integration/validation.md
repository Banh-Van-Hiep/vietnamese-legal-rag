# Validation — tuần6, VLRA-T3-07–10

**Ngày:**29/10/2026. [Spec](spec.md), [plan](plan.md), [tasks](tasks.md),
[analyze](analysis.md). Source: `26c4649478956fd588a7f2d165cccbb33ac2f541`; develop đã fetch: `eea5604251afd4d8605fed510d6bf4de31d629bb`.
Không đổi app/test/schema/corpus hoặc triển khai thay Team1/2.

## Expected / Actual

| AC | Kiểm chứng thực tế | Kết luận |
| --- | --- | --- |
| AC07 HTTP/timeout/lỗi/trace | HttpAiClientTests7/7; StreamApiTests12/12. Query chỉ question/history, trace theo attempt;8 mapping lỗi/không retry; timeout đọc body được kiểm. Source connect2s/wait≤50s, store.accept commit trước khi worker gọi AI. | Đạt adapter/error path; query pipeline thật chưa đạt |
| AC08 mapping/nguồn | AiResponseValidatorTests43/43 và HTTP tests kiểm9 field citation/6 field article, IDs/URL/null/sai phiên bản. E03/E06 kiểm Viewer FastAPI mock thật qua Java. | Đạt mapping/mock; proxy article thật thiếu route Python |
| AC09 PostgreSQL/history | H2 16/16, PostgreSQL16/16: atomic state/citations/snapshot, rollback, failed/insufficient excluded, max5 cặp/20000 code point, chronological/replay. Lượt gọi factory thật lỗi lưu user completed/assistant failed. | Đạt persistence/history |
| AC10 UI | FE72/72, build đạt; browser10/10: URL/history/reload/citation/thiếu căn cứ/lỗi/thử lại,0 uncaught exception. Parser unit test fragmented UTF8/CRLF/multiline/timeout/abort; HTML được giữ như text. | Đạt kỹ thuật UI/mock |
| AC-G3 | Factory thật health200, ready/query503; không có route article trong OpenAPI, article404 NOT_FOUND. Java trả meta→error SERVICE_UNAVAILABLE, replay503; Viewer502 UPSTREAM_CONTRACT_ERROR. | Chưa đạt dữ liệu thật |

Tổng Maven5 suite là94, không cộng lại các nhóm con. Không tái sử dụng tổng125 tuần5
như thể đã chạy125 trong lượt này. Mapping/transaction boundary có phần đối chiếu
source; không đo DB pool riêng trong lúc một provider thật chạy. Không đo55s manual,
mobile/latency benchmark hoặc streaming token provider trong lượt kiểm tra này.
Java hiện phát1 delta chứa answer đã validate; không gọi đó là streaming từng token.

## Readiness thật và hai phụ thuộc bàn giao

1. `team2_rag.runtime.build_runtime`: RAG_BM25_INDEX/RAG_DENSE_INDEX không được cấu
   hình trong process + root dotenv mà runtime đọc. Startup ghi ConfigError. Đây là
   thiếu bàn giao/cấu hình ở môi trường kiểm tra, không chứng minh module retrieval
   chưa viết. Chưa đi xa đến xác minh model/provider; không kết luận API key sai.
2. `team2_rag.api.app.create_app`/OpenAPI chỉ có health/ready/query, thiếu
   GET /internal/v1/documents/{document_id}/articles/{article_id}. Gọi một ID thật
   trả404 NOT_FOUND. Java từ chối lỗi ngoài mã404 được thỏa thuận và trả502
   UPSTREAM_CONTRACT_ERROR; không tráo nguồn hoặc trả nguyên văn giả.

Team1 cần bàn giao index BM25/Dense cùng index_version/chunk_ids và article snapshot;
Team2 cấu hình runtime/model/provider và bổ sung proxy article theo interface đã có.
Team3 tiếp tục AC-G3 sau ready200 và article hoạt động, không sửa code bên họ.

## Lệnh, môi trường, evidence

[Quickstart](quickstart.md) ghi lệnh Maven/FE/factory. JDK25, Node24.21, Python3.12
venv kiểm thử riêng, PostgreSQL18 cluster local test cổng55442. Database:
legal_rag_week6_20261029. FE15173, Java18043, FastAPI mock18044, Edge CDP19242;
factory probe18049. HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE bật để không tải model;
index key thiếu xảy ra trước khâu model. Không sửa .env hoặc in secret.

Evidence ignored: backend/target/week6-acceptance-20261029/ gồm summary.json,
backend-package.log, frontend-unit.json/log, frontend-build.log, e2e/results.json,
e2e/browser.png và logs, live-readiness.json, live-runtime.log, live-through-java.json,
live-through-java-stream.txt, process-cleanup.json, preservation.json.
Runners probe-live.py/run-integration.py là helper ignored của lần kiểm tra, không
thêm dependency/script nguồn vào project. Surefire XML ghi kết quả5 suite đã chạy.

## Bàn giao

Nguồn đã hash không đổi (bỏ cache Python biên dịch); tất cả tiến trình audit mở và
cluster test riêng đã dừng.6 cổng test đóng. Không đụng dịch vụ/database thật.
W6-01–05 hoàn thành sau kiểm link/diff; W6-06 còn mở vì phụ thuộc runtime/article thật.
Không có xung đột API cần tự chọn; không tự hạ G3 hoặc báo mock thành live.

Kiểm bàn giao: 9 file Markdown/33 tham chiếu local không lỗi; diff --check PASS.
W6-01–05 đã đánh dấu theo evidence thực tế; W6-06 giữ mở.
