# Biên bản kiểm chứng nhiệm vụ Team 3 — Tuần 6

**Ngày kiểm tra:**29/10/2026 (Asia/Saigon), thay kết quả tổng hợp28/10.
**Nguồn:** [ARCHITECTURE](../../../docs/ARCHITECTURE.md),
[CODING_CONVENTIONS](../../../docs/CODING_CONVENTIONS.md), [tasks](tasks.md).
**Source:** `26c4649478956fd588a7f2d165cccbb33ac2f541`; **develop đã fetch:** `eea5604251afd4d8605fed510d6bf4de31d629bb`.
Code Team3/Team2 HTTP/runtime/contracts liên quan không khác develop; không merge
worktree. Thay đổi tuần5 là dữ liệu và hồ sơ, không đổi implementation được kiểm tra.
[Hồ sơ chi tiết](vlra-t3-07-10-integration/spec.md),
[validation](vlra-t3-07-10-integration/validation.md).

## 1. Kết luận

**Tuần6 chưa đủ điều kiện nghiệm thu G3 dữ liệu thật.** Phần adapter/mapping,
persistence/history và UI đã đạt kiểm chứng độc lập với mock. Hai phụ thuộc thật còn
thiếu: runtime chưa có đường dẫn index hợp lệ và app Team2 chưa có route đọc Điều luật.
Không có lỗi test mới ở code Team3 trong các suite đã chạy; không tự chốt toàn bộ
07/08 bằng kết quả mock. Không sửa app Team1/2, schema, corpus hoặc cấu hình shared.

**Phân định trách nhiệm theo xác nhận người dùng29/10:** phần implementation Team3
được kiểm tra đã hoàn tất và sẵn sàng nhận bàn giao; không có hạng mục sửa code
Team3 mới được xác định trong lượt rà này. Các phần còn thiếu của Team1/2 để team
sở hữu tự triển khai, Team3 không làm thay. Sau khi họ bàn giao, Team3 còn bước
kiểm thử tích hợp live W6-06; giữ07/08 và G3 ở trạng thái chờ phụ thuộc, không đánh
dấu toàn bộ nghiệm thu live đã hoàn tất. T3-09/10 đã đạt kỹ thuật theo evidence.

## 2. Expected / Actual theo task

| Task | Expected / DoD | Actual29/10 | Kết luận |
| --- | --- | --- | --- |
| VLRA-T3-07 | Java gọi FastAPI thật thành công; trace/timeouts/error mapping/không giữ DB tx | HttpAiClient7/7 và StreamHTTP12/12; source connect2s/wait≤50s, transaction kết thúc trước HTTP. Factory thật query503; qua Java meta→error SERVICE_UNAVAILABLE, lưu failed và replay503. | Adapter/xử lý lỗi đạt; còn chờ pipeline thật để nghiệm thu toàn task |
| VLRA-T3-08 | Citation/article map đủ trường, giữ ID/URL, proxy article đúng snapshot | Validator43/43 và HTTP tests/FE adapters đạt; Viewer E03/E06 mock đạt. Factory thật không có route article; upstream404 NOT_FOUND → Java502 UPSTREAM_CONTRACT_ERROR. | Mapping đạt; proxy dữ liệu thật còn chờ endpoint Team2 |
| VLRA-T3-09 | State/citations nhất quán PostgreSQL; history chỉ5 cặp answered/completed≤20000 code point | PostgreSQL16/16 và H2 16/16; chronological/whole pairs/rollback/terminal/replay đạt; E2E tiếp nối/reload đạt. Factory thật lỗi vẫn lưu completed/failed đúng. | Đủ điều kiện chốt kỹ thuật persistence/history |
| VLRA-T3-10 | URL từ meta, khóa pending, delta, render an toàn, insufficient không citation rỗng | FE72/72/build; E2E10/10 và0 exception. Parser unit kiểm UTF8/frame/error/timeout/abort; output HTML là text. | Đủ điều kiện chốt kỹ thuật UI trong phạm vi đã kiểm; không chứng minh chất lượng live |

Không bắt buộc thêm class/libraries trùng ví dụ: JDK HttpClient, DTO/controller và
ChatStore đã thực hiện trách nhiệm. Không phát sinh thay đổi công nghệ/API.

## 3. Readiness thật và trách nhiệm bàn giao

| Kiểm tra app factory thật | Kết quả |
| --- | --- |
| GET /internal/v1/health |200 up |
| GET /internal/v1/ready |503 LLM_UNAVAILABLE |
| POST /internal/v1/query |503 LLM_UNAVAILABLE, không có answer giả |
| Runtime config |RAG_BM25_INDEX/RAG_DENSE_INDEX chưa cấu hình; startup ConfigError |
| OpenAPI |Chỉ health/ready/query; thiếu endpoint article |
| GET article với ID snapshot thật |404 NOT_FOUND |
| Java gọi query factory thật |SSE200 meta→error SERVICE_UNAVAILABLE; DB user completed/assistant failed; replay503 |
| Java proxy article factory thật |502 UPSTREAM_CONTRACT_ERROR, không thay phiên bản hoặc tạo nguyên văn |

Mã LLM_UNAVAILABLE không đủ để kết luận thiếu/sai API key: startup dừng ở cấu hình
index trước khi kiểm model/provider. Probe bật offline guard, không tải model/index.
Cần Team1 bàn giao index/snapshot tương thích; Team2 cấu hình runtime và phục vụ
article theo hợp đồng. Đây là khoảng thiếu bàn giao, không phải xung đột yêu cầu.
Không tự triển khai bên họ. Golden đã chuyển Team2 kiểm chứng, không lẫn vào audit này.

## 4. Kiểm thử và evidence

- Maven Wrapper package: **94/94**,0 fail/error/skip;5 suite liên quan, bao gồm16 ca
  PostgreSQL thật và16 H2. Không cộng các nhóm con vào tổng94.
- Frontend: **72/72**, tsc/Vite build PASS.
- Browser E2E: **10/10**,0 uncaught exception, React→Java→PostgreSQL→FastAPI HTTP mock.
- Factory probe và Java gọi factory thật đã chạy riêng; kết quả503/404 là bằng chứng
  blocker G3, không ghi thành ca trả lời thành công hoặc fallback mock.

Lệnh/setup tại [quickstart](vlra-t3-07-10-integration/quickstart.md).
DB test legal_rag_week6_20261029 ở127.0.0.1:55442; Java18043/FE15173/Python18044,
factory probe18049/CDP19242. Python venv riêng, JDK25, Node24.21, PostgreSQL18.
Không thay .env, không in credential/danh tính. Không đo mobile/latency/token-stream
provider hoặc chờ55s manual lần này; không lấy kết quả cũ gán PASS mới.

Evidence ignored: backend/target/week6-acceptance-20261029/ có summary.json,
backend-package.log, frontend-unit.json/log, frontend-build.log, e2e/results.json,
ảnh browser và logs, live-readiness.json, live-through-java.json/stream.txt,
live-runtime.log, preservation.json, process-cleanup.json.
Đã dừng đúng tiến trình/cluster test audit mở;6 cổng đã đóng, không đụng dịch vụ thật.

## 5. Điều kiện khép tuần6

1. Team1/2 bàn giao index BM25/Dense cùng phiên bản/chunk IDs, article snapshot và
   cấu hình runtime/model/provider dùng được; ready200.
2. Team2 bổ sung endpoint article đúng6 field và mã404 DOCUMENT_NOT_FOUND/
   ARTICLE_NOT_FOUND; không dùng NOT_FOUND cho lookup cần phân biệt này.
3. Team3 chạy lại query thật qua Java/UI→Answer+Citation, click Viewer đúng document/
   article/version, kiểm nối tiếp/history và lỗi liên quan. Sau đó mới nghiệm thu G3.

W6-06 trong [tasks kiểm chứng](vlra-t3-07-10-integration/tasks.md) còn mở.
Không tự sửa Jira, xác nhận nhóm đã duyệt gate, hoặc báo tuần6 hoàn tất khi thiếu
luồng thật. Phần độc lập09/10 có thể chốt kỹ thuật theo bằng chứng trên.

## 6. Rà toàn tuyến mã nguồn liên team — bổ sung29/10

**Source:** `d67f36acf615956728838a005ec8758d13a9a74a`; **develop:** `eea5604251afd4d8605fed510d6bf4de31d629bb` đã fetch lại.
Phạm vi: code được gọi trên tuyến UI→Java SSE/store→FastAPI→runtime→Hybrid→rerank→
context/prompt→LLM→citation validator và tuyến citation→Viewer→article store. Đã đọc
các điểm nối/DTO/config/test liên quan; không khẳng định mọi thuật toán/nhánh trong
repository hoặc provider/model thật đã được kiểm chứng. Không sửa code Team1/2/3.

### 6.1. Những điểm đã nối bằng code

- FE sendQuery/streamChat gọi POST /api/v1/chat/stream; Java StreamService gọi
  HttpAiClient, gửi question/history theo internal contract và map camelCase.
- Runtime Team2 đã dựng BM25/Dense→Hybrid→BGE scorer→RAGPipeline; pipeline gọi
  generate_answer→LLMService→provider rồi validate citation membership/metadata.
- Đã có adapter OpenAI/Gemini/Qwen/Ollama; không còn kết luận thiếu code gọi LLM.
- Query/history/persistence/UI và error path đã được kiểm ở tuần6 §2–4. Bằng chứng
  mock không tự xác nhận chất lượng retrieval, model hay hiệu lực pháp lý.

### 6.2. Phần thiếu và chủ sở hữu

| ID | Phát hiện/căn cứ source | Ảnh hưởng và phần cần bàn giao |
| --- | --- | --- |
| S1 | runtime.py cần index manifests/Qdrant/embedder/BGE/settings. Trong process + root dotenv hiện chưa có đường dẫn BM25/Dense, model/key hoặc context window. Venv test cũng chưa có bm25s/underthesea/qdrant-client/sentence-transformers/torch/transformers/tiktoken. | Chặn live query trong môi trường kiểm tra. Team1 bàn giao index tương thích, Team2 hoàn thiện môi trường/config provider. Không kết luận máy/nhánh khác cũng thiếu dependency. |
| S2 | Tìm get_article/ArticleStore trong source Python chỉ thấy route của mock_app; data không có articles.jsonl. App thật/OpenAPI thiếu route article. | Thiếu code/snapshot phục vụ Viewer: Team1 cung cấp lookup nguyên Điều bất biến; Team2 bọc endpoint6 field và mã404 đúng contract. Không dựng nguyên văn từ các chunk rời để giả làm Article Store. |
| S3 | retrieval/common.py filter_chunks chỉ kiểm legal_status, cho con_hieu_luc/het_hieu_luc_mot_phan; Dense cũng lọc trạng thái cấp văn bản. Không thấy unit_applicability.jsonl hoặc kiểm verified_current trong đường retrieval/context. | Chưa đạt quy tắc dữ liệu cấp Điều/Khoản của ARCHITECTURE §4.3. Team1 chủ trì registry/filter/snapshot, Team2 bảo toàn điều kiện khi dựng context. Metadata hiện có không đủ khẳng định1083 chunk thuộc văn bản hết hiệu lực một phần đều sai; từng đơn vị cần xác minh. |
| S4 | pipeline.py dòng94 trả insufficient ngay khi regex gặp tham chiếu như công ty đó/công ty này, không xét history để viết lại query. Probe với1 cặp history rõ ngữ cảnh vẫn không gọi retrieval. | Nối tiếp hội thoại chưa đầy đủ theo §5.1: Team2 cần giải tham chiếu/rewrite hoặc làm rõ khi không xác định được. Không phải lỗi FE không gửi conversationId/history. |
| S5 | runtime.py dòng48 chỉ tạo TokenBudget nếu context_window_tokens có giá trị; answer.py cho budget ký tự khi None. Config mẫu chưa nêu LLM_CONTEXT_WINDOW_TOKENS. | Có thể chạy nhưng chưa đạt token-budget baseline. Team2 cần chốt/cấu hình window và tokenizer của model, chặn chế độ ký tự trong cấu hình nghiệm thu live; không phải mọi provider đều cần API key (Ollama là ngoại lệ). |
| S6 | application.properties/.env.example Backend mặc định mock legacy, main UI dùng SSE profile rag. docker-compose.yml chỉ là placeholder. | Muốn chạy thủ công phải chọn profile rag, PostgreSQL, RAG_BASE_URL/CORS/VITE_API_URL đúng và tắt nhãn mock khi dùng dữ liệu thật. Không thể dùng docker compose hiện tại để bật đủ hệ thống; Compose chưa là điều kiện bắt buộc riêng của tuần6. |

S1/S2 chặn chạy trọn vẹn ngay; S3 chặn khẳng định đáp ứng nguồn luật được duyệt.
S4/S5 là phần chưa đáp ứng đầy đủ hành vi/budget theo đặc tả. Đây là khoảng thiếu
implementation/config so với nguồn chuẩn; lượt review không tự thay contract hoặc
quyết định phương án triển khai cho team sở hữu.

**Lưu ý nhánh:** BM25Retriever.retrieve ở checkout hiện tại còn lồng envelope của
_search vào results; develop đã sửa _search trả list. Runtime Team2 có BM25SearchAdapter
nhận cả list/envelope, nên không coi lỗi standalone cũ này là blocker mới của tuyến
runtime. Chưa merge develop hoặc chạy BM25 thật vì venv thiếu dependencies; không
báo thuật toán BM25/Dense hoặc chất lượng topK đã đạt từ unit test với nhánh giả.

### 6.3. Kiểm chứng bổ sung và giới hạn

- Mới chạy6 module test pipeline/API/runtime/answer Team2: **125 test và40 subtest
  PASS**,0 fail. Chạy3 test Hybrid: **3/3 PASS**. Các dependency bên ngoài được giả
  lập trong test; không gọi LLM/Qdrant thật.
- Probe filter trong bộ nhớ: chunk có legal_status được phép và thuộc tính bổ sung
  unit_applicability=pending_review vẫn được filter giữ. Đây là probe minh họa filter
  không xét cấp đơn vị, không khẳng định corpus hiện có bản ghi pending_review thật.
- Probe follow-up có2 history item: insufficient,0 retrieval call. Không sửa corpus
  hoặc history thật; không dùng probe này thay đánh giá chất lượng rewrite.
- Kết quả FastAPI thật503/404 và Java error path tại §3 đã chạy29/10 vẫn áp dụng vì
  code/config liên quan không đổi; không chạy lại các suite FE/Java đã PASS chỉ để
  cộng số test. Không tải model, build index hay dùng API key/provider bên ngoài.
- Evidence bổ sung ignored: backend/target/source-audit-20261029/checks.json,
  summary.json, team2-tests.log, team2-boundaries.xml, hybrid-tests.log, hybrid-unit.xml.
  Môi trường/config chỉ ghi trạng thái có/không; không in secret/danh tính.

**Kết luận toàn tuyến:** phần khung tích hợp đã có, chưa có bằng chứng chạy trọn
UI→RAG thật→Answer/Citation→Viewer. Cần xử lý S1/S2 và đối chiếu S3–S5 trước khi
khẳng định hoàn thiện đúng đặc tả; không chỉ thêm API key là đủ. Hồ sơ này chưa thay
nghiệm thu Golden của Team2 hoặc xác nhận G3 đã được nhóm phê duyệt.

## 7. Đối chiếu phần thiếu với nhiệm vụ theo tuần của Team1/2

**Đối chiếu:**29/10/2026, các file tasks tuần4–8 trong docs_1/docs_2, không sửa tài
liệu của team khác và không suy trạng thái Jira từ kế hoạch. Mã VLRA-T1-*/VLRA-T2-*
là mã phân rã đang ghi trong repo; chưa xác minh ánh xạ sang ticket Jira gốc.

| Phần thiếu từ §6 | Tuần/task trong tài liệu | Ranh giới nghiệm thu |
| --- | --- | --- |
| S1: index BM25/Dense/Qdrant bàn giao thật | [Team1 tuần6](../../../team1_data/docs_1/week6/tasks.md) VLRA-T1-06 (BM25),07 (Dense),09 (interface/tests); §5 bàn giao index thực. [Team2 tuần6](../../../team2_rag/docs_2/week6/tasks.md) VLRA-T2-06 tích hợp retrieval,07 nạp BGE,09 chạy Live. | Thuộc G3 tuần6. Có source build/load không chứng minh artifact/runtime đã bàn giao; venv test thiếu dependency không chứng minh máy team sở hữu chưa cài. |
| S2: articles.jsonl và get_article thật | [Team1 tuần4](../../../team1_data/docs_1/week4/tasks.md) VLRA-T1-04 thiết kế; [tuần5](../../../team1_data/docs_1/week5/tasks.md) VLRA17 sinh articles, VLRA18 mock; [tuần6 §5](../../../team1_data/docs_1/week6/tasks.md) yêu cầu hoàn thiện lookup đọc dữ liệu thật. | Cần lookup cơ bản thật cho bàn giao tuần6. Tuần7 VLRA-T1-10/11 mới đóng băng/tối ưu, không đồng nghĩa tuần6 chỉ cần mock. |
| S2: endpoint HTTP proxy article | [Team2 tuần6](../../../team2_rag/docs_2/week6/tasks.md) VLRA-T2-09 ghi rõ GET /internal/v1/documents/{document_id}/articles/{article_id}; §5 bàn giao đủ query/article cho Team3. | Phần thiếu code trực tiếp của nhiệm vụ tuần6 Team2, phụ thuộc lookup của Team1. |
| S3: registry và eligibility theo đơn vị | [Team1 tuần5](../../../team1_data/docs_1/week5/tasks.md) VLRA17 tạo unit_applicability.jsonl, §3.2 chỉ verified_current được index; [tuần6](../../../team1_data/docs_1/week6/tasks.md) VLRA-T1-07 filter snapshot/verified_current và08 Eligibility Filter. | Tạo dữ liệu từ tuần5, áp vào retrieval tuần6. Tuần7 freeze manifest không thay việc lọc trước index/context. |
| S1: cấu hình provider/model, chạy LLM thật | [Team2 tuần5](../../../team2_rag/docs_2/week5/tasks.md) VLRA20 xây adapter và test LLM cô lập; [tuần6](../../../team2_rag/docs_2/week6/tasks.md) VLRA-T2-09 nối Live LLM với FastAPI. | Adapter đã có code. Điều còn chưa chứng minh tại môi trường audit là runtime cấu hình được và query dữ liệu thật thành công, thuộc tuần6. |
| S5: đếm token/budget live | [Team2 tuần4](../../../team2_rag/docs_2/week4/tasks.md) VLRA-T2-02 thiết kế ngân sách; [tuần6](../../../team2_rag/docs_2/week6/tasks.md) VLRA-T2-08 lập trình tokenizer/Context Builder≤3000 token. | Thiết kế tuần4, thực thi đúng ngân sách khi nghiệm thu live thuộc tuần6. Code hỗ trợ TokenBudget đã có nhưng cấu hình None vẫn cho phép budget ký tự. |
| S4: giải tham chiếu/rewrite dựa history | [Team2 tuần4](../../../team2_rag/docs_2/week4/tasks.md) VLRA-T2-01 ghi thiết kế Query Coreference Resolution, sơ đồ §3.1 có bước này. Chưa thấy task triển khai riêng rõ ràng trong bảng tuần5–8. | Là yêu cầu chung còn thiếu triển khai/coverage phân công; không tự gán tuần6 hoặc kết luận một task tuần6 đã quá hạn vì phần này. Cần team sở hữu xác nhận task/mốc thực hiện. |
| S6: cấu hình chạy local và Compose | Team2 tuần4 VLRA-T2-04 cấu hình môi trường/skeleton, tuần5 VLRA19 hướng dẫn cài đặt; tuần6 VLRA-T2-09 chạy server thật. Team1 tuần4 VLRA-T1-05 yêu cầu mẫu Compose Qdrant. | Mẫu Compose Qdrant không tương đương giao full-stack Compose. Chưa thấy task riêng yêu cầu đủ4 service Compose trong tuần4–8; không tự thêm điều kiện Docker vào G3 khi có thể chạy local thủ công. |
| E2E/demo trọn vẹn và freeze | [Team1 tuần7](../../../team1_data/docs_1/week7/tasks.md) VLRA-T1-10 freeze,11 tối ưu Article Store,13 demo G4; [Team2 tuần7](../../../team2_rag/docs_2/week7/tasks.md) VLRA-T2-13 E2E Live/G4. Team3 [tuần7](../week7/tasks.md) VLRA-T3-14 điều phối G4. | Buổi demo/acceptance toàn tuyến G4 thuộc tuần7. Tuần6 vẫn phải bàn giao retrieval/query/article thật để tuần7 có thể tích hợp. |

**Chỗ cần đọc cùng nhau:** ví dụ get_article trong Team1 tuần5 có comment “Tuần6–7”,
nhưng ma trận bàn giao tuần6 ghi rõ lookup dữ liệu thật; tuần7 liệt kê đóng băng/tối
ưu p95. Khi lập kế hoạch, dùng mốc lookup cơ bản tuần6 và tối ưu/freeze tuần7. Nếu
nhóm muốn dời cả lookup cơ bản, cần xác nhận lịch bàn giao liên team thay vì tự suy
comment ví dụ đã thay DoD tuần6. Lượt đối chiếu này chưa đổi lịch hoặc task nguồn.

**Điều chỉnh cách hiểu báo cáo trước:** S4 là khoảng thiếu so với đặc tả toàn hệ
thống, chưa có căn cứ gán mốc triển khai cụ thể ở tuần6. S1/S2/S3/S5 có nhiệm vụ
và bàn giao tuần5–6 rõ hơn. Không lấy yêu cầu demo G4 tuần7 để bổ sung ngược thành
điều kiện mới cho từng task tuần6; giữ riêng query/article thật của G3 và tổng duyệt
UI toàn tuyến của G4.

## 8. Cập nhật kiểm tra nhánh trước bàn giao29/10

Fetch origin không báo ref mới thay đổi. Tuy vậy, có code trên feature branch chưa
vào develop: origin/feature/team2-rag tại c947fac bổ sung endpoint article,
team2_rag/articles.py và tùy chọn strict_rerank. Các nhận định thiếu route/store ở
các mục trên áp dụng cho HEAD/develop được kiểm thử, không phủ nhận feature branch này.

Đã đọc source branch, chưa chạy test hoặc merge: articles.py ưu tiên articles.jsonl,
nhưng khi thiếu sẽ ghép lại các chunk để trả content; cần Team1/2 đối chiếu yêu cầu
nguyên văn/snapshot trước khi dùng làm bằng chứng Viewer thật. Thêm route không tự
chứng minh runtime/index/model đã sẵn sàng hoặc khép G3.

Nhánh corpus pilot của Team1 tại4ac0aaf cũng có1 commit chưa vào develop. Không tự
merge các nhánh Team1/2 theo yêu cầu kiểm tra. Việc đồng bộ nhánh Team3-fullstack
chỉ tiếp nhận baseline đã có trên nhánh đích, không chọn thêm feature commit bên ngoài.
