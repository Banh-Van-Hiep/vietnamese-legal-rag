# Kiến Trúc Tổng Thể Hệ Thống (System Architecture Specification - Baseline v2.0)

> **Dự án:** Vietnamese Legal RAG Assistant (Project 1 · Pháp luật Doanh nghiệp Việt Nam)
> **Tài liệu tham chiếu:** Baseline v2.0 hợp nhất BRD -> FRD -> NFR -> System Design -> App Design
> **Lịch trình học phần:** 9 tuần thực hiện (Tuần 4 đến Tuần 12 theo quy đổi: Tuần mới = Tuần cũ + 3)
> **Vai trò nguồn, xác nhận 28/10/2026:** Đây là đặc tả chính hiện hành về yêu cầu, hành vi và kiến trúc hệ thống. Quy chuẩn triển khai/nghiệm thu tại [CODING_CONVENTIONS.md](CODING_CONVENTIONS.md); tài liệu nhiệm vụ theo tuần phải bám đặc tả này. Nội dung thiết kế không tự chứng minh đã triển khai hoặc đã được nghiệm thu.

---

## 1. Tổng Quan Bài Toán & Phạm Vi Hệ Thống (Scope & BRD)

### 1.1. Mục tiêu Nghiệp vụ
Cung cấp giải pháp hỏi đáp pháp luật doanh nghiệp tiếng Việt có căn cứ kiểm chứng (grounded answer), cho phép truy hồi nguyên văn Điều luật theo đúng phiên bản áp dụng (snapshot) và minh bạch từ chối (`insufficient_context`) khi chưa đủ dữ liệu kết luận.

### 1.2. Phân định Phạm vi Pháp luật
* **Phạm vi trọng tâm (P0 - Bắt buộc MVP):**
  * Thành lập và đăng ký doanh nghiệp.
  * Vốn, thành viên góp vốn và quyền/nghĩa vụ cổ đông.
  * Quản trị nội bộ, cơ cấu quản lý và người đại diện theo pháp luật.
  * Tổ chức lại (chia, tách, hợp nhất, sáp nhập) và giải thể doanh nghiệp.
  * *Nguồn luật khởi tạo (đối chiếu 07/10/2026):* Luật 59/2020/QH14 [L1], Luật 03/2022/QH15 [L2], Luật 76/2025/QH15 [L3], NĐ 168/2025/NĐ-CP [L4], NĐ 296/2026/NĐ-CP [L5], TT 68/2025/TT-BTC [L6], TT 121/2026/TT-BTC [L7].
* **Phạm vi mở rộng (P1 - Target System):** Hợp đồng dân sự/thương mại, điều kiện đầu tư kinh doanh, thuế - kế toán, lao động & BHXH, phá sản. Nhánh P1 chỉ được tích hợp khi đã có corpus, ground truth và kiểm chứng hiệu lực pháp lý độc lập.
* **Ngoài phạm vi MVP:** Nộp hồ sơ hành chính, ký số, tự động tính thuế, dự đoán kết quả tố tụng tòa án, reasoning đa bước chuyên sâu (Project 10).

---

## 2. Kiến Trúc Mục Tiêu & Ranh Giới Trách Nhiệm (System Design)

Hệ thống được thiết kế theo kiến trúc tách biệt giữa lớp quản trị hội thoại/public gateway (Java / Spring Boot) và lớp tính toán AI RAG (Python FastAPI). Thư viện retrieval của Team 1 được đóng gói tích hợp trực tiếp vào AI Service của Team 2 nhằm tối ưu độ trễ.

### 2.1. Sơ đồ luồng dữ liệu (Data Pipeline Flow)

[React + TypeScript + Tailwind (T3)] (Port: 5173)
       │ ▲
       │ │ (1) Public Chat SSE: POST /api/v1/chat/stream (camelCase)
       │ │ (2) REST Management: Conversations, Messages, Viewer (camelCase)
       ▼ │
[Java Spring Boot Backend (T3)] (Port: 8080)
  - Quản lý Session, Idempotency, State Machine, Tracing
  - Database: PostgreSQL (Port: 5432) lưu Hội thoại, messages, receipts, citations
       │ ▲
       │ │ (3) Internal HTTP JSON: POST /internal/v1/query (snake_case)
       │ │     Lookup Điều: GET /internal/v1/documents/.../articles/...
       │ │     Header bắt buộc: X-Request-ID
       ▼ │
[Python AI Service - FastAPI (T2)] (Port: 8001)
  - Query Rewrite, Reranker, Prompt, LLM Adapter, Citation Validator, Mock Engine
       │ ▲
       │ │ (4) Direct Python Library Call: retrieve(), get_article()
       ▼ │
[Thư viện Data & Retrieval (T1)]
  - bm25s + Underthesea (Lexical search)
  - Qdrant Vector DB (Port: 6333) (Dense embedding)
  - Fusion: Reciprocal Rank Fusion (RRF, k=60)
  - Storage: Raw store, Registry, chunks.jsonl, articles.jsonl

### 2.2. Phân công Trách nhiệm Mô-đun (Module Ownership)

| Phân hệ / Thành phần | Team sở hữu | Công nghệ Baseline | Trách nhiệm cốt lõi |
| :--- | :---: | :--- | :--- |
| **Data Pipeline & Retrieval** | **Team 1** | Python, bm25s, Underthesea, Qdrant, RRF (k=60) | Thu thập raw, làm sạch, tách Điều/Khoản/Điểm, quản lý unit_applicability. Cung cấp hàm retrieve(question, top_k) và get_article(doc_id, art_id) dưới dạng thư viện dùng chung. |
| **AI Service & RAG Engine** | **Team 2** | Python package team2_rag, FastAPI HTTP adapter | Tiếp nhận internal query, giải tham chiếu từ history, điều phối retrieval, reranking (chọn <= 5 chunks), build prompt theo ngân sách token, gọi LLM, validate output/citation, phục vụ chế độ Mock song song Live. |
| **Backend Gateway & State** | **Team 3** | Java/Spring Boot, Maven, PostgreSQL | Quản lý hội thoại, kiểm soát đồng thời & idempotency bằng clientRequestId, duy trì state machine, ánh xạ snake_case <-> camelCase, điều phối SSE streaming. |
| **Frontend Web Client** | **Team 3** | React 18, TypeScript, Vite, Router, Tailwind | Giao diện Chat, xử lý phân giải frame SSE (meta/delta/complete/error), bảng trích dẫn citation nhấp mở Document Viewer nguyên văn Điều luật. |
| **Golden Dataset & Benchmark** | **Cả 3 Team** (T3 điều phối) | JSON Schema, Scikit-learn/Pandas, Pytest | Xây dựng tập test đóng băng (Phase 1: 30–50 câu; v1: 100–150 câu), thực hiện benchmark độc lập và phân tích lỗi. |

---

## 3. Đặc Tả Giao Diện Tích Hợp (Interface & Contract Baseline)

Quy ước chuẩn: Public API giao tiếp ngoài dùng camelCase và ID số; Internal API và dữ liệu tầng dưới dùng snake_case và định danh chuỗi ASCII. Tầng Java Backend thực hiện ánh xạ hai chiều.

### 3.1. Public Client API (Team 3 Frontend <-> Team 3 Backend)

#### A. Chat Streaming (POST /api/v1/chat/stream)
- **Request Header:** Content-Type: application/json, Accept: text/event-stream
- **Request Body (ChatRequest):**
  - question (string bắt buộc): 1 - 2.000 code point.
  - clientRequestId (UUID v4 bắt buộc): Dùng để bảo đảm idempotency.
  - conversationId (integer/Long, tùy chọn): Null/bỏ qua nếu mở hội thoại mới.
- **Giao thức SSE Stream (Server-Sent Events):**
  1. event: meta (1 lần đầu): Chứa conversationId, clientRequestId, userMessageId, assistantMessageId, createdAt.
  2. : heartbeat (Định kỳ 10 giây): Giữ kết nối trong lúc chờ AI xử lý.
  3. event: delta (0..N lần): Chứa {"text": "..."} gửi từng mảnh câu trả lời khi trạng thái là answered.
  4. event: complete (Terminal Event thành công - 8 trường): conversationId, clientRequestId, userMessageId, assistantMessageId, status (answered / insufficient_context), answer, citations, createdAt.
  5. event: error (Terminal Event lỗi): Chứa error object {code, message, retryable}.

#### B. REST Management Endpoints & Frontend Routes
- **REST Endpoints (Backend API):**
  - GET /api/v1/conversations: Trả về danh sách Conversation[] (sắp xếp updatedAt DESC, id ASC).
  - GET /api/v1/conversations/{conversationId}/messages: Trả về danh sách Message[] (sequenceNo ASC).
  - DELETE /api/v1/conversations/{conversationId}: Trả về HTTP 204 No Content khi xóa thành công (chặn xóa khi đang pending, lưu tombstone clientRequestId).
  - GET /api/v1/documents/{documentId}?articleId={articleId}: Trả về PublicArticleResponse (gồm 6 trường: documentId, documentTitle, articleId, article, content, sourceUrl) để xem toàn văn Điều.
- **Frontend Client Routes (React Router):**
  - `/`: Màn hình Chat chính khởi tạo hội thoại mới.
  - `/c/:conversationId`: Xem lịch sử và tiếp tục phiên hỏi đáp đã có.
  - `/documents/:documentId?articleId={articleId}`: Màn hình Document Viewer xem nguyên văn Điều luật (hỗ trợ hiển thị độc lập hoặc nhúng slide-over panel trong Chat).

### 3.2. Internal API (Team 3 Backend -> Team 2 AI Service)

#### A. RAG Query (POST /internal/v1/query)
- **Header:** X-Request-ID (UUID truy vết log)
- **Input (QueryRequest):**
  - question (string): 1 - 2.000 code point.
  - history (array): Tối đa 5 cặp completed + answered gần nhất ({role, content}), tổng content <= 20.000 code point.
- **Output (RagResponse):**
  - status: "answered" hoặc "insufficient_context".
  - answer: Nội dung trả lời (1 - 12.000 code point).
  - citations: Mảng citation_id, chunk_id, document_id, article_id, document_title, article, clause, point, source_url (rỗng nếu insufficient_context).

#### B. Internal Article Lookup (GET /internal/v1/documents/{document_id}/articles/{article_id})
- **Output (ArticleResponse):** Trả về đủ 6 trường snake_case từ Article Store. Không tìm thấy trả HTTP 404.

### 3.3. Python Library Interface (Team 2 AI Service <-> Team 1 Retrieval)
- retrieve(question: str, top_k: int = 20) -> dict: Trả về dict tuân thủ retrieval_output.schema.json gồm question và results (tối đa 50 phần tử, mỗi phần tử đủ 12 trường snake_case).
- get_article(document_id: str, article_id: str) -> dict: Trả về toàn văn Điều từ Article Store; ném exception nếu lỗi hoặc không tìm thấy.

---

## 4. Đặc Tả Dữ Liệu & Tiền Xử Lý (Data & Retrieval - Team 1)

### 4.1. Quy ước Định danh Khóa (ID Conventions)
- document_key: Loại văn bản + số hiệu chuẩn hóa (VD: luat-59-2020-qh14).
- document_id: document_key + content version (VD: luat-59-2020-qh14-v1).
- article_id: dieu- + số hiệu Điều (VD: dieu-12, dieu-12a).
- chunk_id: {document_id}__{article_id}__k{khoản}__{chunk_index} (VD: luat-59-2020-qh14-v1__dieu-12__k1__0; không có khoản ghi k0).

### 4.2. Quy tắc Chunking Văn bản Pháp luật
- R1 (Cả Điều): Điều không có Khoản và vừa giới hạn -> toàn bộ Điều (clause = null, point = null).
- R2 (Theo Khoản): Mỗi Khoản tách thành một chunk độc lập (không gộp các Khoản ngắn).
- R3 (Khoản dài có Điểm): Nhóm các Điểm liên tiếp nhưng phải lặp lại câu dẫn nguyên văn của Khoản ở đầu mỗi chunk.
- R4 (Cắt theo câu): Nếu vượt ngưỡng, cắt câu trọn vẹn với OVERLAP_TOKENS = 64 (không vượt ranh giới Khoản/Điểm khác).
- Ngân sách Token: MAX_TOKENS = 512 (context_header + content), TARGET_TOKENS = 384, MIN_TOKENS = 20 (cảnh báo).
- Search Text: Search Text = context_header + "\n" + content.

### 4.3. Quản lý Hiệu lực Từng Đơn vị (Unit Applicability)
Team 1 duy trì file data/registry/unit_applicability.jsonl kiểm soát trạng thái áp dụng đến cấp Khoản/Điểm: verified_current, verified_historical, pending_review. Chỉ các bản ghi verified_current mới được đưa vào index truy vấn mặc định.

---

## 5. RAG Pipeline & Thẩm Tra Trích Dẫn (RAG & LLM - Team 2)

### 5.1. Luồng Xử Lý Trực Tuyến (Online Flow)
1. Query Processing: Chuẩn hóa text, giải tham chiếu từ history, sinh câu hỏi truy hồi độc lập (<= 4.000 code points).
2. Hybrid Retrieval: Gọi retrieve(question, top_k=20) kết hợp bm25s và Qdrant qua RRF (k=60).
3. Reranking: Dùng Cross-Encoder (BAAI/bge-reranker-v2-m3) chấm lại điểm, chọn tối đa 5 chunk tốt nhất.
4. Context Injection: Đóng gói System Prompt, History và LEGAL_CONTEXT (gán nhãn tạm [C1], [C2]...).
5. LLM Generation: Gọi LLM qua Adapter.
6. Verification: Parse JSON đầu ra, kiểm tra marker [Cn] ánh xạ chính xác với context metadata, kiểm tra trích dẫn. Nếu thiếu thông tin, xuất status = insufficient_context và citations = [].

---

## 6. Xử Lý Đồng Thời, Trạng Thái & Chống Trùng (Backend State - Team 3)

### 6.1. State Machine Tin Nhắn
- Mỗi lượt hỏi sinh ra 1 cặp: 1 user message (completed) + 1 assistant message.
- assistant message bắt đầu ở trạng thái pending.
- Thành công: chuyển sang completed (answerStatus là answered hoặc insufficient_context).
- Thất bại: chuyển sang failed (kèm errorCode và cờ retryable).
- Recovery: Nếu pending > 60 giây, background job tự động chuyển thành failed (mã PROCESSING_INTERRUPTED).

### 6.2. Ma Trận Idempotency (RequestReceipt)

| Tình huống kiểm tra | Trạng thái hiện tại | Phản hồi của Hệ thống |
| :--- | :--- | :--- |
| ID mới, không kèm conversationId | Chưa có | Tạo mới cuộc hội thoại và cặp message trong 1 transaction. |
| Cùng ID, đang xử lý | pending | Trả về HTTP 409 Conflict (REQUEST_IN_PROGRESS), không gọi thêm AI. |
| Cùng ID, đã hoàn thành | completed | Mở SSE replay lại đúng kết quả meta -> delta -> complete từ DB. |
| Cùng ID, đã thất bại | failed | Trả lại lỗi logic đã lưu dưới dạng HTTP tương ứng. |
| Cùng ID nhưng khác câu hỏi | - | Trả về HTTP 409 Conflict (REQUEST_ID_CONFLICT). |
| ID mới nhưng hội thoại đang bận | pending | Trả về HTTP 409 Conflict (CONVERSATION_BUSY). |

---

## 7. Bảng Mã Lỗi & Ánh Xạ Chuẩn Hóa (Standard Error Mapping)

Cấu trúc JSON phản hồi sự cố:
{"error": {"code": "STRING_CODE", "message": "Thông báo tiếng Việt", "retryable": true/false}}

| Tình huống lỗi | HTTP Code | Public Error Code | retryable | Hành vi xử lý |
| :--- | :---: | :--- | :---: | :--- |
| Payload sai cấu trúc / vượt giới hạn | 400 | INVALID_REQUEST | false | Bị chặn ngay tại Controller. |
| Hội thoại không tồn tại | 404 | CONVERSATION_NOT_FOUND | false | Không tìm thấy trong DB. |
| Không tìm thấy văn bản / Điều luật | 404 | DOCUMENT_NOT_FOUND / ARTICLE_NOT_FOUND | false | Trả về khi xem Document Viewer. |
| Đang có request xử lý dở | 409 | REQUEST_IN_PROGRESS / CONVERSATION_BUSY | true | Frontend giữ nguyên trạng thái chờ. |
| Xung đột UUID giữa các câu hỏi | 409 | REQUEST_ID_CONFLICT | false | Bắt buộc client đổi UUID mới. |
| LLM trả sai cấu trúc JSON/Citation | 502 | UPSTREAM_INVALID_RESPONSE | false | AI Service chặn, không lưu completed. |
| AI Service/Vector DB ngừng hoạt động | 503 | SERVICE_UNAVAILABLE | true | Báo hệ thống bận, cho phép thử lại. |
| Treo xử lý quá 60 giây | 503 | PROCESSING_INTERRUPTED | true | Tự động hủy bởi background recovery. |
| Timeout toàn trình vượt 45s - 50s | 504 | UPSTREAM_TIMEOUT | true | Ngắt kết nối và đóng stream có kiểm soát. |

---

## 8. Ngân Sách Hiệu Năng & Mục Tiêu Nghiệm Thu (NFRs & Verification)

### 8.1. Ngân sách Thời gian Toàn trình (Latency Budget)
- Tổng thời gian xử lý AI (Deadline): <= 45 giây (Retrieval <= 5s, Rerank <= 5s, LLM <= 30s, Overhead <= 5s).
- Retrieval p95: <= 1 giây (Đo sau warm-up trên phần cứng tiêu chuẩn).
- Timeout giao tiếp: Backend chờ AI tối đa 50 giây; Frontend chờ Backend tối đa 60 giây.

### 8.2. Tiêu chuẩn Đánh giá Chất lượng (Project 1 Evaluation Gates)

#### A. Cấu trúc Golden Dataset
- **Quy mô:** Tuần 5 có 30–50 câu (khởi đầu); Tuần 7 đóng băng Golden Dataset v1 gồm 100–150 câu. Phân tầng xấp xỉ 60% Dev / 40% Test (tỷ lệ khoảng 75% answerable, 25% unanswerable).
- **Cấu trúc bản ghi (File `golden_phase1_30cai.json` hiện hữu gồm 8 trường):**
  - `id`: Định danh duy nhất và ổn định (cho phép tiền tố đóng góp, VD: `gold_team3_001`; ví dụ công khai không dùng danh tính cá nhân).
  - `question`: Câu hỏi tiếng Việt thực tế từ người dùng.
  - `expected_status`: `"answered"` hoặc `"insufficient_context"`.
  - `ground_truth`: Đáp án chuẩn mực hoặc lý do giải thích thiếu căn cứ.
  - `gold_chunk_ids`: Mảng các `chunk_id` thật làm căn cứ (rỗng nếu `insufficient_context`).
  - `citation`: Nhãn trích dẫn kỳ vọng (VD: `Điều 12 Luật Doanh nghiệp 2020`).
  - `category`: Nhóm chủ đề (thành lập, vốn, quản trị, giải thể, ngoài phạm vi...).
  - `author`: Thành viên đóng góp câu hỏi.
- **Lưu ý kỹ thuật:** Script validator tự động hiện tại của nhóm đang kiểm tra nhầm enum `answerable` thay vì `answered` -> Cần sửa lại validator cho khớp với cấu trúc `answered` của dataset để tránh báo lỗi giả.

#### B. Các Cổng Chất lượng Bắt buộc (Evaluation Gates)
1. Retrieval Recall@5: >= 85% (Bắt buộc cho MVP trên tập câu hỏi answerable). Đánh giá bổ sung Recall@20 >= 90% và MRR@20.
2. Citation Correctness: >= 90% (Thẩm định chéo: trích dẫn phải hỗ trợ claim, đúng phiên bản và mở được nguyên văn Điều).
3. Answer Quality: Chấm mù theo Rubric 5 tiêu chí (0–10 điểm), đảm bảo điểm của Target System (Hybrid + Rerank) >= Baseline (BM25-only).
4. An toàn & Minh bạch: Giảm thiểu hallucination rate; bắt buộc từ chối trả lời (`insufficient_context`) khi câu hỏi thiếu dữ kiện hoặc nằm ngoài snapshot dữ liệu.
