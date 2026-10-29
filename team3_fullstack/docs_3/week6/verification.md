# Biên bản nghiệm thu Team 3 — Tuần 6

**Ngày kiểm chứng:** 30/10/2026. **Nhiệm vụ:** [tasks.md](tasks.md).

## 1. Kết luận

**Chưa đạt nghiệm thu G3 của tuần 6.**

T3-09/10 đạt kỹ thuật; adapter và mapping của T3-07/08 đạt kiểm thử độc lập.
Query thật trả503 và endpoint article chưa có trong baseline nghiệm thu;
cần bàn giao dịch vụ/dữ liệu và kiểm thử thành công toàn tuyến để chốt.

## 2. Expected / Actual theo task

| Task | Expected / DoD | Actual30/10 | Kết luận |
| --- | --- | --- | --- |
| VLRA-T3-07 | Java gọi FastAPI thật thành công; trace/timeouts/error mapping/không giữ DB tx | HttpAiClient7/7 và StreamHTTP12/12; source connect2s/wait≤50s, transaction kết thúc trước HTTP. Factory thật query503; qua Java meta→error SERVICE_UNAVAILABLE, lưu failed và replay503. | Adapter/xử lý lỗi đạt; còn chờ pipeline thật để nghiệm thu toàn task |
| VLRA-T3-08 | Citation/article map đủ trường, giữ ID/URL, proxy article đúng snapshot | Validator43/43 và HTTP tests/FE adapters đạt; Viewer E03/E06 mock đạt. Factory thật không có route article; upstream404 NOT_FOUND → Java502 UPSTREAM_CONTRACT_ERROR. | Mapping đạt; proxy dữ liệu thật còn chờ endpoint Team2 |
| VLRA-T3-09 | State/citations nhất quán PostgreSQL; history chỉ5 cặp answered/completed≤20000 code point | PostgreSQL16/16 và H2 16/16; chronological/whole pairs/rollback/terminal/replay đạt; E2E tiếp nối/reload đạt. Factory thật lỗi vẫn lưu completed/failed đúng. | Đủ điều kiện chốt kỹ thuật persistence/history |
| VLRA-T3-10 | URL từ meta, khóa pending, delta, render an toàn, insufficient không citation rỗng | FE72/72/build; E2E10/10 và0 exception. Parser unit kiểm UTF8/frame/error/timeout/abort; output HTML là text. | Đủ điều kiện chốt kỹ thuật UI trong phạm vi đã kiểm; không chứng minh chất lượng live |

## 3. Readiness thật và trách nhiệm bàn giao

| Kiểm tra app factory thật | Kết quả |
| --- | --- |
| GET /internal/v1/health | 200 up |
| GET /internal/v1/ready | 503 LLM_UNAVAILABLE |
| POST /internal/v1/query | 503 LLM_UNAVAILABLE, không có answer giả |
| Runtime config | RAG_BM25_INDEX/RAG_DENSE_INDEX chưa cấu hình; startup ConfigError |
| OpenAPI | Chỉ health/ready/query; thiếu endpoint article |
| GET article với ID snapshot thật | 404 NOT_FOUND |
| Java gọi query factory thật | SSE200 meta→error SERVICE_UNAVAILABLE; DB user completed/assistant failed; replay503 |
| Java proxy article factory thật | 502 UPSTREAM_CONTRACT_ERROR, không thay phiên bản hoặc tạo nguyên văn |

## 4. Kiểm thử và bằng chứng

| Kiểm tra | Kết quả |
| --- | --- |
| Backend | 125/125 package; trong đó94 ca adapter/validator/store/HTTP đều đạt, gồm16 H2 +16 PostgreSQL |
| Frontend | 72/72, TypeScript/Vite build đạt |
| E2E HTTP mock | 10/10,0 lỗi JavaScript chưa xử lý |

Bằng chứng tại `backend/target/final-acceptance-20261030/`.

## 5. Điều kiện khép tuần6

1. **Team1:** bàn giao index BM25/Dense cùng phiên bản, registry hiệu lực và Article Store.
2. **Team2:** bàn giao runtime/model/provider chạy được, query/article đúng contract và token budget.
3. **Team3:** kiểm query thật → Answer/Citation → Viewer, history và các nhánh lỗi để chốt G3.

## 6. Rà toàn tuyến mã nguồn liên team

### 6.1. Những điểm đã nối bằng code

- FE gọi public SSE; Java truyền question/history/trace sang FastAPI.
- Runtime có BM25/Dense → Hybrid → BGE rerank → context/prompt → LLM → citation validation.
- Có adapter OpenAI/Gemini/Qwen/Ollama; persistence/history và UI đã hoạt động với mock.

### 6.2. Phần thiếu và chủ sở hữu

| Mã | Phần thiếu | Phụ trách |
| --- | --- | --- |
| S1 | Môi trường kiểm tra thiếu index, cấu hình model/provider và dependency chạy retrieval/model thật | Team1 bàn giao index; Team2 cấu hình runtime |
| S2 | Article Store/lookup thật và endpoint proxy chưa được tích hợp trong nhánh nghiệm thu | Team1/2 |
| S3 | Retrieval chưa lọc theo unit_applicability/verified_current cấp đơn vị | Team1, Team2 tích hợp |
| S4 | Câu tham chiếu như “công ty đó” bị từ chối trước retrieval dù có history | Team2 |
| S5 | Thiếu context window vẫn cho phép budget ký tự thay vì token | Team2 |
| S6 | Cấu hình local cần profile rag, PostgreSQL và URL dịch vụ phù hợp; Compose chưa có full stack | Các team phối hợp cấu hình chạy |
| S7 | ID gold_041 chỉ hai câu hỏi khác nhau giữa Phase1/fixture;1 test hồi quy lỗi | Team3/Team2 phối hợp; theo dõi tuần5 |

### 6.3. Kiểm chứng bổ sung

- Nhóm API/mock/pipeline/reranker/Hybrid: **48 test +81 subtest** đạt, dùng dependency giả.
- Bộ mở rộng Team2: **388 đạt,1 lỗi Golden gold_041,147 subtest đạt**; lỗi theo dõi tại tuần5.
- Probe history2 item: insufficient_context,0 retrieval call.
- Probe filter giữ candidate có legal_status được phép dù bổ sung trạng thái đơn vị pending_review.

Bằng chứng tại `backend/target/final-acceptance-20261030/`.

## 7. Đối chiếu phần thiếu với nhiệm vụ theo tuần của Team1/2

| Phần việc | Tuần/task |
| --- | --- |
| Index BM25/Dense và retrieval thật | [Team1 tuần6](../../../team1_data/docs_1/week6/tasks.md): T1-06/07/09; [Team2 tuần6](../../../team2_rag/docs_2/week6/tasks.md): T2-06/07/09 |
| Sinh articles và registry | [Team1 tuần5](../../../team1_data/docs_1/week5/tasks.md): VLRA17 |
| Lookup nguyên văn cơ bản | [Team1 tuần6](../../../team1_data/docs_1/week6/tasks.md): ma trận bàn giao §5; [tuần7](../../../team1_data/docs_1/week7/tasks.md): T1-10/11 đóng băng/tối ưu |
| Endpoint article | [Team2 tuần6](../../../team2_rag/docs_2/week6/tasks.md): T2-09 |
| Eligibility filter | [Team1 tuần6](../../../team1_data/docs_1/week6/tasks.md): T1-07/08 |
| Live LLM | [Team2 tuần5](../../../team2_rag/docs_2/week5/tasks.md): VLRA20; [tuần6](../../../team2_rag/docs_2/week6/tasks.md): T2-09 tích hợp live |
| Token budget | [Team2 tuần4](../../../team2_rag/docs_2/week4/tasks.md): T2-02 thiết kế; [tuần6](../../../team2_rag/docs_2/week6/tasks.md): T2-08 triển khai |
| Query coreference | [Team2 tuần4](../../../team2_rag/docs_2/week4/tasks.md): T2-01 thiết kế; chưa có task triển khai riêng rõ ở tuần5–8 |
| Demo toàn tuyến G4 | Team1 T1-13, Team2 T2-13 và Team3 T3-14 ở tuần7 |

## 8. Trạng thái nhánh liên quan

| Baseline đã nghiệm thu | Nội dung | Còn cần kiểm chứng |
| --- | --- | --- |
| `ac35828` | Factory hiện hành chỉ có health/ready/query; chưa có route article | Tích hợp bàn giao query/article và snapshot/index để chạy live |

[Kiểm chứng chi tiết](vlra-t3-07-10-integration/validation.md).
