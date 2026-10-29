# Validation — tuần6, T3-07–10

**Ngày kiểm chứng:**30/10/2026. **Kết quả:** phần Team3 đạt với mock; G3 chờ dữ liệu thật.

## Expected / Actual

| AC | Kiểm chứng thực tế | Kết luận |
| --- | --- | --- |
| AC07 HTTP/timeout/lỗi/trace | HttpAiClientTests7/7; StreamApiTests12/12. Query chỉ question/history, trace theo attempt;8 mapping lỗi/không retry; timeout đọc body được kiểm. Source connect2s/wait≤50s, store.accept commit trước khi worker gọi AI. | Đạt adapter/error path; query pipeline thật chưa đạt |
| AC08 mapping/nguồn | AiResponseValidatorTests43/43 và HTTP tests kiểm9 field citation/6 field article, IDs/URL/null/sai phiên bản. E03/E06 kiểm Viewer FastAPI mock thật qua Java. | Đạt mapping/mock; proxy article thật thiếu route Python |
| AC09 PostgreSQL/history | H2 16/16, PostgreSQL16/16: atomic state/citations/snapshot, rollback, failed/insufficient excluded, max5 cặp/20000 code point, chronological/replay. Lượt gọi factory thật lỗi lưu user completed/assistant failed. | Đạt persistence/history |
| AC10 UI | FE72/72, build đạt; browser10/10: URL/history/reload/citation/thiếu căn cứ/lỗi/thử lại,0 uncaught exception. Parser unit test fragmented UTF8/CRLF/multiline/timeout/abort; HTML được giữ như text. | Đạt kỹ thuật UI/mock |
| AC-G3 | Factory thật health200, ready/query503; không có route article trong OpenAPI, article404 NOT_FOUND. Java trả meta→error SERVICE_UNAVAILABLE, replay503; Viewer502 UPSTREAM_CONTRACT_ERROR. | Chưa đạt dữ liệu thật |

## Readiness thật và phụ thuộc bàn giao

| Kiểm tra | Kết quả |
| --- | --- |
| FastAPI health | 200 |
| FastAPI ready/query | 503 LLM_UNAVAILABLE; runtime thiếu đường dẫn index |
| FastAPI article | 404 NOT_FOUND; lookup chưa được tích hợp |
| Java query | Meta→error SERVICE_UNAVAILABLE; lưu user completed/assistant failed; replay503 |
| Java Viewer | 502 UPSTREAM_CONTRACT_ERROR |

## Môi trường và bằng chứng

JDK25, Node24.21, Python3.12, PostgreSQL18 và Edge headless.

Bằng chứng tại `backend/target/final-acceptance-20261030/`.

## Bàn giao

- **Team1:** index/snapshot cùng phiên bản, registry hiệu lực và Article Store nguyên văn.
- **Team2:** runtime/model/provider, query/article đúng contract và token budget.
- **Team3:** kiểm query/history/Viewer trên dịch vụ thật để chốt G3.

## Rà toàn tuyến

Nhóm API/mock/pipeline/reranker/Hybrid:48 test +81 subtest đạt với dependency giả.
Bộ mở rộng Team2:388 đạt,1 lỗi Golden gold_041,147 subtest đạt; theo dõi tại tuần5.
Còn thiếu unit applicability, giải tham chiếu history và bảo đảm token budget của cấu hình live.

[Phần thiếu và phụ trách](../verification.md#6-rà-toàn-tuyến-mã-nguồn-liên-team).
Bằng chứng tại `backend/target/final-acceptance-20261030/`.

## Đối chiếu mốc tuần liên team

- Registry/articles: Team1 tuần5; lookup/index/filter thật: Team1 tuần6.
- Live query/article/token budget: Team2 tuần6.
- Query coreference: có thiết kế Team2 tuần4, chưa có task triển khai riêng rõ ràng.
- Tổng duyệt E2E/G4: tuần7.

[Nghiệm thu tuần6](../verification.md) · [Tasks](tasks.md).
