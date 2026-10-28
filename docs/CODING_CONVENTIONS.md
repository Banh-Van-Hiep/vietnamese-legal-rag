QUY CHUẨN KỸ THUẬT, LẬP TRÌNH & QUY TRÌNH PHỐI HỢP
(Coding Conventions & Engineering Standards - Baseline v2.0)
> **Dự án:** Vietnamese Legal RAG Assistant (Project 1 · Pháp luật Doanh nghiệp Việt Nam)  
> **Căn cứ tài liệu:** Bản đặc tả thiết kế hệ thống tổng thể v2.0  
> **Phạm vi áp dụng:** Thống nhất cho cả 3 Sub-teams (Team 1 Data & Retrieval, Team 2 RAG & LLM, Team 3 Backend & Frontend)
---
1. NGUYÊN TẮC CỐT LÕI "DOCUMENTS-FIRST" & TỔ CHỨC REPO
1.1. Thứ Bậc Nguồn Chuẩn (Single Source of Truth)
Nghiệp vụ & Hành vi: [docs/ARCHITECTURE.md](ARCHITECTURE.md) là đặc tả chính hiện hành, hợp nhất BRD/FRD/NFR và thiết kế hệ thống (người dùng xác nhận ngày 28/10/2026). Không tự ý thay đổi phạm vi nghiệp vụ nếu chưa qua xét duyệt.
Tài liệu này quy định cách triển khai, phối hợp và Definition of Done. Jira quản lý công việc; `tasks.md` theo tuần cụ thể hóa mục tiêu/DoD theo đặc tả chính. Không lấy mô tả Jira hoặc Google Docs cũ để ghi đè baseline hiện hành; khi nội dung giao việc, baseline hoặc schema lệch nhau, ghi rõ khác biệt để thống nhất trước khi sửa phần phụ thuộc.
Dữ liệu luật & Provenance: File registry chính thức kèm mã băm SHA-256 từ nguồn cơ quan nhà nước là nguồn chuẩn. Không dùng bài viết tổng hợp thay thế văn bản quy phạm pháp luật.
Giao tiếp liên team: File JSON Schema (Draft 2020-12) và OpenAPI trong thư mục `contracts/` là nguồn chuẩn duy nhất về cấu trúc trao đổi máy tính. Khi có sự sai lệch giữa tài liệu Word/Markdown và Schema, tuyệt đối không tự chọn một bên để code mà phải ghi nhận discrepancy, họp thống nhất và cập nhật đồng bộ cả hai.
Mức độ hoàn thành: Test report tự động và artefact chạy thực tế là thước đo tiến độ duy nhất. Không dùng số lượng file tạo ra hay số package đã cài đặt để báo cáo hoàn thành.
1.2. Tổ Chức Thư Mục Tài Liệu Co-location
Thư mục `docs/` lưu đặc tả dùng chung của dự án, không lưu nhiệm vụ hoặc báo cáo tiến độ theo tuần. Hai tài liệu nền là:
`docs/ARCHITECTURE.md`: Kiến trúc tổng thể, luồng dữ liệu liên team và chỉ tiêu kỹ thuật.
`docs/CODING_CONVENTIONS.md`: Bộ quy chuẩn này.
`docs/README.md` là mục lục; các thư mục `docs/team1_data/`, `docs/team2_rag/`, `docs/team3_fullstack/` chứa thiết kế chức năng, interface và trách nhiệm của từng team trong hệ thống chung.
Tài liệu theo tuần của từng team được đặt ngay trong thư mục nguồn của team đó theo lộ trình học phần Tuần 4 đến Tuần 12 (`Tuần mới = Tuần cũ + 3`):
`team1_data/docs/week_XX/tasks.md`
`team2_rag/docs/week_XX/tasks.md`
`team3_fullstack/docs_3/weekN/tasks.md` (ví dụ `week4`, `week5`; theo quyết định tổ chức tài liệu ngày 28/10/2026).
Với Team 3, nhiệm vụ và bộ spec/plan/tasks/verification đặt cùng tuần trong `docs_3/`. Chỉ duy trì bộ nhiệm vụ tuần hiện hành, không giữ bản nhiệm vụ cũ song song trong `specs/`. Báo cáo nghiệm thu `verification.md` nằm ngay trong thư mục tuần tương ứng; không đánh dấu đạt chỉ bằng cách chuyển tài liệu.
Mỗi task Team 3 vẫn thực hiện theo Spec Kit: specify → clarify → plan → tasks → analyze → sửa vấn đề → implement → validate. Bộ chi tiết nằm tại `team3_fullstack/docs_3/weekN/<jira>-<chuc-nang>/`; lưu kết quả validate tại `validation.md` trong bộ task, tổng hợp nghiệm thu vào `weekN/verification.md`. Cách bố trí và nội dung validate tại [quy trình Team 3](../team3_fullstack/docs_3/README.md#quy-trình-thực-hiện-nhiệm-vụ). Đây là quy trình công việc, không yêu cầu cài Spec Kit để người khác đọc được tài liệu.
Cấu trúc bắt buộc của mỗi file `tasks.md` hàng tuần:
Task list: Ghi rõ mã Jira (ví dụ `VLRA16`), người phụ trách, mục tiêu và Definition of Done cụ thể.
Technical Details: Ý tưởng giải thuật, công thức tính toán, thư viện và tham số cấu hình.
Interface & Contracts: Định nghĩa DTO, Pydantic Schema, chữ ký hàm (`def` / method) phục vụ team phụ thuộc.
Mock Implementation: Đoạn code giả lập stub/mock trả dữ liệu mẫu chuẩn schema để team khác tích hợp ngay.
Blockers & Risks: Rủi ro và phương án giải tỏa.
---
2. QUY CHUẨN ĐẶT TÊN, KIỂU DỮ LIỆU & RANH GIỚI GIAO TIẾP
2.1. Phân Định Casing Theo Ranh Giới (Boundary Rule)
Khu vực Public Client (Frontend React <-> Backend Java):
Định dạng: JSON UTF-8, quy chuẩn `camelCase`.
Ví dụ: `conversationId`, `clientRequestId`, `userMessageId`, `assistantMessageId`, `documentTitle`, `sourceUrl`.
Khu vực Nội bộ & Dữ liệu (Backend Java <-> AI Service Python <-> Thư viện Retrieval):
Định dạng: JSON UTF-8 / Python dict, quy chuẩn `snake_case`.
Ví dụ: `document_id`, `chunk_id`, `article_id`, `source_url`, `retrieval_method`, `answer_status`.
Quy tắc chuyển đổi: Lớp Adapter của Java Backend chịu trách nhiệm chuyển đổi 2 chiều giữa `camelCase` và `snake_case`. Không ép Python đổi sang `camelCase` và không ép React đổi sang `snake_case`.
2.2. Quy Chuẩn Định Danh Khóa (ID Conventions)
Mọi ID pháp lý do Team 1 khởi tạo phải bất biến và chỉ chứa ký tự ASCII `[a-z0-9_-]`:
`document_key`: Loại văn bản + số hiệu chuẩn hóa (chữ thường, gạch ngang).
Định dạng: `{loai}-{so}-{nam}-{co_quan}`
Ví dụ: `luat-59-2020-qh14`, `nd-168-2025-nd-cp`
`document_id`: `document_key` + phiên bản nội dung bất biến (`-v{N}`).
Định dạng: `{document_key}-v{version}`
Ví dụ: `luat-59-2020-qh14-v1`
Lưu ý: `document_id` thể hiện phiên bản text trích xuất, không đại diện cho hiệu lực pháp lý vĩnh viễn.
`article_id`: `dieu-` + số/chữ của Điều.
Ví dụ: `dieu-12`, `dieu-13a`
`chunk_id`: Định danh duy nhất toàn hệ thống của một đoạn cắt.
Cú pháp: `{document_id}__{article_id}__k{khoan}__{chunk_index}`
Ví dụ: `luat-59-2020-qh14-v1__dieu-12__k1__0` (Khoản 1 Điều 12 chunk 0).
Điều không chia khoản bắt buộc ghi `k0` (ví dụ `...__dieu-1__k0__0`).
`chunk_index` bắt đầu từ `0`, tăng liên tục.
`conversationId` & `messageId` (Team 3 cấp):
Số nguyên dương an toàn (`JSON integer` trong khoảng `1` đến `9.007.199.254.740.991` - `Number.MAX_SAFE_INTEGER`).
Phía Java dùng kiểu `Long`, Database dùng `BIGINT`. Không ép kiểu về chuỗi hoặc float.
`clientRequestId` (Team 3 Frontend cấp):
Chuỗi UUID v4 chuẩn (ví dụ: `44444444-4444-4444-8444-444444444444`). Duy nhất trên toàn môi trường demo để chống gửi trùng (idempotency key).
2.3. Quy Chuẩn Xử Lý Chuỗi Unicode & Thời Gian
Bắt buộc mã hóa toàn hệ thống bằng UTF-8 (chuẩn NFC). Không xóa dấu tiếng Việt, không làm biến dạng ký tự pháp lý.
Kiểm tra độ dài văn bản bằng Unicode code point count (trong Java dùng `codePointCount`, Python dùng `len(str)`), không đo theo byte mảng để tránh lỗi với ký tự đa byte.
Toàn bộ timestamp trao đổi qua API phải tuân thủ chuẩn RFC 3339 UTC (ví dụ: `2026-10-07T04:00:00Z`).
---
3. QUY CHUẨN LẬP TRÌNH CHO TỪNG SUB-TEAM
3.1. Team 1: Data & Retrieval (Python)
Môi trường & Ngôn ngữ: Python `>= 3.10`, quản lý gói qua file cấu hình cố định phiên bản (lockfile), không ghi `"latest"`.
Thư viện chuẩn: `bm25s`, `underthesea` (tách từ tiếng Việt), `qdrant-client`.
Quy tắc làm sạch dữ liệu (Cleaning):
Không xóa dấu câu pháp lý, số thứ tự, tỷ lệ %, ngày tháng, chữ số La Mã.
Giữ liên kết bảng biểu (hàng/cột); tách chú thích sửa đổi ra metadata nhưng không làm mất căn cứ đối chiếu.
Chỉ lọc bỏ header/footer/menu trang web; không áp dụng quy tắc "xóa mọi ký tự lạ".
Quy tắc Chunking:
`R1`: Điều không có Khoản -> Cả Điều là 1 chunk (`clause = null`, `point = null`).
`R2`: Điều có Khoản -> Mỗi Khoản là 1 chunk. Tuyệt đối không gộp các Khoản ngắn.
`R3`: Khoản dài có Điểm -> Gom nhóm Điểm liên tiếp nhưng bắt buộc lặp lại nguyên văn câu dẫn của Khoản ở đầu mỗi chunk.
`R4`: Vẫn vượt ngưỡng token -> Cắt câu trọn vẹn, cấu hình `OVERLAP_TOKENS = 64` (overlap chỉ diễn ra trong cùng đơn vị, không lan sang Khoản khác).
Giới hạn: `MAX_TOKENS = 512` (`context_header + content`), `TARGET_TOKENS = 384`, `MIN_TOKENS = 20`.
Search Text: Luôn tạo theo công thức `Search Text = context_header + "\n" + content` để đảm bảo retriever nắm trọn ngữ cảnh phân cấp của văn bản luật.
Registry & Applicability: Quản lý hiệu lực đến từng đơn vị Khoản/Điểm trong `data/registry/unit_applicability.jsonl`. Chỉ nạp vào index các chunk có trạng thái `verified_current`. Các chunk thuộc diện `pending_review` hoặc bị sửa đổi phải bị loại khỏi context mặc định.
3.2. Team 2: RAG & LLM (Python FastAPI)
Môi trường: Package `team2_rag` chạy trên nền Python `>= 3.10`, bọc ngoài bằng FastAPI adapter.
Context Builder Invariants:
Ngân sách Token: `LEGAL_CONTEXT <= 3000 tokens`, `output reserve = 1500 tokens`, `safety margin = 256 tokens`.
Chọn trọn vẹn từng chunk, tối đa 5 chunks sau reranking. Không cắt vụn làm mất câu điều kiện hoặc ngoại lệ pháp lý.
Prompting & LLM Invariants:
System prompt quy định rõ vai trò, bắt buộc trả lời bằng tiếng Việt và chỉ suy diễn từ `LEGAL_CONTEXT`.
Đánh nhãn tạm các candidate là `[C1]`, `[C2]`... LLM chỉ được phép trích dẫn nhãn này trong bài viết.
Cấm tuyệt đối: Không cho phép LLM tự bịa đặt ID, `chunk_id`, `document_id` hay đường link `source_url`. Bộ parser của code sẽ tự động remap nhãn `[Cn]` thành object citation đầy đủ metadata.
Output Parsing & Citation Validation:
Chuỗi chấp nhận: Parse JSON -> Validate Schema -> Kiểm tra Marker -> Kiểm tra Membership trong context -> Chấp nhận.
Mọi marker `[Cn]` xuất hiện trong `answer` phải tương ứng với đúng 1 citation object hợp lệ trong mảng `citations`.
Thứ tự citation trong mảng phải liên tục và tăng dần theo lần xuất hiện đầu tiên của marker trong câu trả lời.
Nếu LLM sinh câu trả lời bịa đặt nguồn hoặc vi phạm schema, ném lỗi upstream (`502 UPSTREAM_INVALID_RESPONSE`), không tự động chèn nguồn giả để "sửa" câu trả lời.
3.3. Team 3: Backend & Frontend (Java & React)
Backend Stack: Java 25, Spring Boot 4.1.1, Maven Wrapper, PostgreSQL.
*(Quyết định ngày 28/10/2026: giữ Java 25 / Spring Boot 4.1.1 theo `team3_fullstack/backend/pom.xml`; sửa quy chuẩn và kế hoạch cho thống nhất, không hạ phiên bản hoặc sửa code trong đợt chuẩn hóa tài liệu này. JAVA_HOME phải trỏ JDK 25 khi chạy Maven Wrapper.)*
Quản lý cấu hình: Đọc từ biến môi trường (`.env`), không commit credential mật vào code/repo.
Database Transaction: Tuyệt đối không giữ DB connection/transaction trong lúc đang gọi HTTP xuống AI Service để tránh làm cạn kiệt connection pool.
Transport SSE: Sử dụng `SseEmitter` bất đồng bộ, thiết lập worker pool có giới hạn, async timeout 55 giây, `Cache-Control: no-store`.
Idempotency: Khóa theo `conversationId` và đối chiếu `clientRequestId` trên bảng `RequestReceipt`. Đảm bảo hai request gửi tới đồng thời không tạo trùng dữ liệu.
Frontend Stack: React 18, TypeScript, Tailwind CSS, Vite.
Giao tiếp SSE: Dùng `fetch` + `ReadableStream` để gửi POST body kèm `clientRequestId`. Xử lý trọn vẹn việc chia tách buffer, hỗ trợ UTF-8 nhiều mảnh.
UI State Machine: Phân biệt rõ các trạng thái `idle`, `submitting/pending`, `answered`, `insufficient_context`, `failed`.
Security: Escape toàn bộ output hiển thị, cấm render HTML tùy ý từ LLM (sử dụng Markdown renderer an toàn).
Document Viewer: Nhấp vào citation `[Cn]` phải gọi API mở đúng văn bản theo `documentId` và `articleId` tương ứng.
---
4. BẤT BIẾN NGHIỆP VỤ & QUY CHUẨN XỬ LÝ LỖI (INVARIANTS & ERROR HANDLING)
4.1. Bộ Quy Tắc Nghiệp Vụ Bất Biến (Business Rules)
BIZ-01 (Căn cứ pháp lý): Mỗi kết luận pháp lý trong câu trả lời bắt buộc phải có căn cứ rõ ràng từ context. Kiến thức nội tại của mô hình, nội dung trong câu hỏi của người dùng hoặc tin nhắn cũ không được dùng thay cho chứng cứ pháp luật.
BIZ-02 (Phân biệt thiếu dữ kiện và lỗi kỹ thuật):
Thiếu thông tin tình huống hoặc không tìm thấy điều luật phù hợp trong snapshot -> Trả về HTTP 200 / Complete event với `status = "insufficient_context"` và `citations = []`.
Vector DB sập, timeout, LLM sinh JSON sai định dạng -> Là lỗi kỹ thuật, bắt buộc trả về mã lỗi `5xx` tương ứng. Tuyệt đối không chuyển lỗi kỹ thuật thành `insufficient_context`.
BIZ-03 (Toàn vẹn Snapshot): Mọi truy vấn chỉ được tìm kiếm trên snapshot dữ liệu đã được kiểm duyệt và công bố. Cấm âm thầm tìm kiếm web thời gian thực trong lúc đang phục vụ lượt chat.
BIZ-04 (Phiên bản bất biến): Trích dẫn citation và Document Viewer phải trỏ cùng phiên bản văn bản. Nếu phiên bản cũ đã bị lưu kho không còn phục vụ, trả về HTTP 404 rõ ràng, không được tự động chuyển sang phiên bản mới.
BIZ-05 (Idempotency): Một lượt hỏi được chấp nhận chỉ tạo ra chính xác 1 `user message` và 1 `assistant message`. Gửi lại cùng `clientRequestId` phải phát lại kết quả cũ (replay), không tạo lượt mới.
4.2. Chuẩn Hóa Phản Hồi Sự Cố (Error Envelope & Mapping)
Mọi lỗi (REST JSON hoặc SSE `event: error`) phải sử dụng cấu trúc envelope thống nhất:
```json
{
  "error": {
    "code": "STRING_ERROR_CODE",
    "message": "Thông báo lỗi bằng tiếng Việt rõ ràng, dễ hiểu.",
    "retryable": false
  }
}
```
Bảng ánh xạ mã lỗi giữa các tầng hệ thống:

| Tình huống lỗi | HTTP Code | Public Error Code | Thuộc tính `retryable` | Hành vi hệ thống |
| :--- | :---: | :--- | :---: | :--- |
| Tham số sai, ID âm, chuỗi quá dài | 400 | `INVALID_REQUEST` | `false` | Chặn ngay tại tầng Controller. |
| Hội thoại không tồn tại | 404 | `CONVERSATION_NOT_FOUND` | `false` | Báo không tìm thấy session. |
| Không tìm thấy văn bản / Điều luật | 404 | `DOCUMENT_NOT_FOUND` / `ARTICLE_NOT_FOUND` | `false` | Trả về khi tra cứu Document Viewer. |
| UUID lượt hỏi đã bị xóa | 404 | `REQUEST_NOT_FOUND` | `false` | Khớp với tombstone đã lưu. |
| Lượt hỏi / Hội thoại đang bận xử lý | 409 | `REQUEST_IN_PROGRESS` / `CONVERSATION_BUSY` | `true` | Client giữ nguyên giao diện, không spam. |
| Cùng UUID nhưng đổi câu hỏi / hội thoại | 409 | `REQUEST_ID_CONFLICT` | `false` | Yêu cầu Frontend đổi UUID mới. |
| LLM sinh sai JSON / Bịa trích dẫn | 502 | `UPSTREAM_INVALID_RESPONSE` | `false` | Ghi log phân tích prompt, hủy kết quả. |
| Request nội bộ gửi sang AI sai schema | 502 | `UPSTREAM_CONTRACT_ERROR` | `false` | Lỗi tích hợp giữa Backend và AI. |
| Index / Qdrant / LLM mất kết nối | 503 | `SERVICE_UNAVAILABLE` | `true` | Báo dịch vụ tạm thời gián đoạn. |
| Database lỗi không đọc/ghi được | 503 | `PERSISTENCE_UNAVAILABLE` | `true` | Lỗi tầng lưu trữ dữ liệu. |
| Lượt xử lý bị treo quá 60 giây | 503 | `PROCESSING_INTERRUPTED` | `true` | Background recovery tự động giải phóng. |
| Toàn trình vượt quá thời gian tối đa | 504 | `UPSTREAM_TIMEOUT` | `true` | Quá deadline 45s-50s, ngắt kết nối an toàn. |
---
5. QUY CHUẨN TÍCH HỢP ĐỘC LẬP BẰNG MOCK (MOCK PROTOCOL)
Để đảm bảo 3 team làm việc song song mà không bị phụ thuộc vào tiến độ của nhau, chế độ Mock phải tuân thủ nghiêm ngặt các quy tắc sau:
Khả năng hoạt động độc lập: Mock của Team 2 và Team 3 phải chạy được mà không cần API Key LLM và không cần chờ Team 1 hoàn thành toàn bộ corpus.
Tuân thủ triệt để Contract: Mock data phải vượt qua 100% các bài test của JSON Schema tương ứng (`rag_response.schema.json`, `retrieval_output.schema.json`).
Cung cấp đủ 2 kịch bản nghiệp vụ:
Kịch bản Answered: Trả về `status = "answered"`, trong câu trả lời có chứa marker `[C1]`, mảng `citations` có 1 phần tử trỏ tới fixture hợp lệ trong Article Store thử nghiệm (ví dụ `document_id = "mock_v1"`, `article_id = "art1"`).
Kịch bản Insufficient Context: Trả về `status = "insufficient_context"`, câu trả lời giải thích lý do thiếu dữ liệu, mảng `citations = []` và không có bất kỳ marker trích dẫn nào.
Cô lập dữ liệu Mock: Dữ liệu Mock chỉ phục vụ tích hợp giao diện và kiểm thử luồng. Tuyệt đối không đưa fixture mock vào corpus thật hoặc bộ dữ liệu đánh giá Golden Dataset.
---
6. QUY TRÌNH GIT & QUẢN LÝ PHIÊN BẢN
6.1. Quy Ước Nhánh (Branching Strategy)
`main`: Nhánh ổn định cao nhất, chỉ merge khi có bản phát hành được nghiệm thu qua các Gate.
`develop`: Nhánh tích hợp chung toàn dự án.
Nhánh tính năng (Feature branches):
Cú pháp: `feature/<team_name>/week-<XX>-<task-short-name>`
Ví dụ: `feature/team1-data/week-05-chunking`, `feature/team2-rag/week-06-reranker`, `feature/team3-fullstack/week-05-sse-stream`
Quy tắc bất di bất dịch: Tuyệt đối không commit hoặc push trực tiếp lên `main` và `develop`. Mọi thay đổi bắt buộc phải đi qua Pull Request (PR) có ít nhất 1 thành viên khác review.
6.2. Quy Chuẩn Commit Message
Áp dụng chuẩn Conventional Commits:
`feat: <nội dung>` (Thêm tính năng hoặc mô-đun mới)
`fix: <nội dung>` (Sửa lỗi logic, sửa bug tích hợp)
`docs: <nội dung>` (Cập nhật tài liệu, cập nhật task tuần)
`refactor: <nội dung>` (Cấu trúc lại code nhưng không đổi hành vi)
`test: <nội dung>` (Thêm unit test, dữ liệu test hoặc cấu hình benchmark)
`chore: <nội dung>` (Cập nhật dependency, cấu hình build/tooling)
---
7. ĐỊNH NGHĨA HOÀN THÀNH (DEFINITION OF DONE - DOD)
Một task hoặc Pull Request chỉ được coi là hoàn thành (Done) khi thỏa mãn toàn bộ 6 tiêu chí sau:
Version Control: Code nằm trên đúng nhánh tính năng, lịch sử commit rõ ràng và đã mở PR vào `develop`.
Tiêu chí Nghiệp vụ: Đáp ứng đầy đủ các yêu cầu chức năng (FR) và phi chức năng (NFR) được giao cho task đó.
Kiểm thử & Bằng chứng: Toàn bộ Unit Test và Schema Validation Test chạy thành công cục bộ; có log hoặc ảnh chụp màn hình làm bằng chứng.
Đồng bộ Tài liệu: Tài liệu tuần (`tasks.md`), tài liệu thiết kế liên quan và JSON Schema được cập nhật đồng bộ với code thực tế.
Sẵn sàng Tích hợp: Team nhận ở khâu tiếp theo đã được bàn giao interface, hướng dẫn chạy và dữ liệu mock hoạt động ổn định.
Minh bạch Tiến độ: Ghi nhận trung thực các giới hạn kỹ thuật (limitations) và tồn đọng (backlog). Không báo cáo một khung code rỗng hoặc mock là tính năng live đã hoàn chỉnh.
