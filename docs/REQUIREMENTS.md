# Yêu cầu, truy vết và cổng nghiệm thu

> Chuyển ngày 16/11/2026 từ Google Doc "Legal RAG" (Đặc tả tổng thể v2.0, mục 1.7, 2.1, 3, 10.3–10.5). Từ nay file này là nguồn chuẩn cho các mã BR/FR/NFR; Google Doc là bản lưu trữ.
> File này nêu **yêu cầu**, không nêu kết quả đo. Kết quả đo nằm trong báo cáo của từng team (`docs/teamX_*/`, `evaluation/`) và trong `teamX_*/docs_X/weekN/tasks.md`.
> Kiến trúc, contract, mã lỗi và ngân sách thời gian NFR-06..09: [ARCHITECTURE.md](ARCHITECTURE.md).

## 1. Business requirements

| Mã | Yêu cầu nghiệp vụ | Tiêu chí xác nhận |
| :--- | :--- | :--- |
| BR-01 | Tra cứu đúng tình huống doanh nghiệp | Use case P0 có corpus và câu hỏi chuẩn tương ứng |
| BR-02 | Câu trả lời có căn cứ kiểm chứng được | Citation đúng nội dung, đúng đơn vị và mở được nguồn |
| BR-03 | Dùng quy định phù hợp snapshot pháp luật | Đơn vị hết hiệu lực hoặc chưa xác minh không vào context mặc định |
| BR-04 | Minh bạch khi không đủ căn cứ hoặc thiếu tình huống | Không suy đoán; có lý do và hướng bổ sung thông tin |
| BR-05 | Hỏi tiếp và theo dõi hội thoại thuận tiện | Lịch sử có thứ tự; không tạo trùng khi gửi lại |
| BR-06 | Ba team phát triển và tích hợp độc lập | Contract, mock và bộ test dùng chung |
| BR-07 | Chứng minh hiệu quả theo Project 1 | Báo cáo recall, MRR, citation, điểm câu trả lời và hallucination |

## 2. Functional requirements (P0)

| Mã | Chức năng | Điều kiện nghiệm thu | Chủ trì |
| :--- | :--- | :--- | :--- |
| FR-01 | Thu thập và chuẩn hóa corpus | Raw bất biến, text sạch, registry nguồn/phiên bản, báo cáo chất lượng | T1 |
| FR-02 | Tách Điều/Khoản/Điểm và lưu nguyên văn Điều | ID duy nhất, liên kết chunk → article; không mất điều kiện pháp lý | T1 |
| FR-03 | Hybrid retrieval BM25 + dense | Cùng snapshot, hợp nhất RRF, output đúng schema; có baseline | T1 |
| FR-04 | Xử lý câu hỏi và câu hỏi tiếp nối | Trim/validate; giải tham chiếu từ history; truy hồi lại căn cứ | T2, T3 |
| FR-05 | Reranking và xây context | Chọn chunk trong ngân sách token, không trộn phiên bản mâu thuẫn | T2 |
| FR-06 | Sinh câu trả lời grounded | Tiếng Việt, nêu điều kiện, citation từ metadata thực, không bịa ID | T2 |
| FR-07 | Xử lý thiếu căn cứ | `insufficient_context`, citations rỗng; nêu phần thiếu hoặc hỏi lại | T2 |
| FR-08 | Quản lý hội thoại và chống gửi trùng | CRUD, ID số, sequence/state; UUID v4 của lượt cho idempotency | T3 |
| FR-09 | Xem điều luật từ citation | Đúng `document_id`/`article_id`, nguyên văn đầy đủ, nguồn HTTPS | T1, T2, T3 |
| FR-10 | Mock và xác thực contract | Hai nhánh RAG hợp lệ, lỗi tích hợp có test; không cần API key | T2, T3 |
| FR-11 | Chat UI và Document Viewer | Render đủ trạng thái, citation nhấp được; không gọi LLM trực tiếp | T3 |
| FR-12 | Đánh giá và lưu bằng chứng | Golden Dataset có ground truth, báo cáo so baseline và target | Cả nhóm |

## 3. Non-functional requirements

### 3.1. Chất lượng pháp lý và AI (NFR-01..05)

| Mã | Yêu cầu và mục tiêu | Cách đo |
| :--- | :--- | :--- |
| NFR-01 Retrieval | Recall@5 ≥ 85% (cổng MVP); báo thêm MRR; Recall@20 ≥ 90% là mục tiêu bổ sung | Cùng corpus và golden relevance, macro-average trên câu answerable; không đổi K sau khi xem kết quả |
| NFR-02 Citation | Citation correctness ≥ 90%; ID, schema và khả năng truy vết hợp lệ 100% ở output được chấp nhận | Review cả claim–citation và hiệu lực/phiên bản; validator có test riêng |
| NFR-03 Answer | Điểm câu trả lời target ≥ baseline; ghi hallucination rate | Chấm mù cùng rubric, cùng test set |
| NFR-04 Provenance | 100% chunk phát hành có source, version, liên kết article và bằng chứng kiểm tra hiệu lực | Validator dữ liệu, mẫu đối chiếu nguyên văn, test amendment |
| NFR-05 Contract | 100% response trả cho client đúng schema và invariant nghiệp vụ | Test schema và semantic validator ở biên T1/T2/T3 |

### 3.2. Hiệu năng (NFR-06..09)

Xem bảng ở [ARCHITECTURE.md mục 8.1](ARCHITECTURE.md). Không chép lại ở đây để tránh hai nguồn lệch nhau.

### 3.3. Tin cậy, bảo mật và vận hành (NFR-10..16)

| Mã | Yêu cầu | Kiểm tra nghiệm thu |
| :--- | :--- | :--- |
| NFR-10 | Nhất quán dữ liệu và idempotency | Hai request đồng thời không tạo trùng; một lượt pending mỗi hội thoại; lỗi ghi DB không báo thành công |
| NFR-11 | Khôi phục sau gián đoạn | Pending > 60 giây chuyển failed với `PROCESSING_INTERRUPTED`; không gọi lại LLM ngầm; kết quả muộn bị bỏ |
| NFR-12 | Bí mật và bề mặt truy cập | API key chỉ ở AI service; `.env` không commit; CORS allowlist; internal API không public; không lộ stack trace |
| NFR-13 | Dữ liệu người dùng và chống prompt injection | Không log câu hỏi/answer thô mặc định; context là dữ liệu, không phải chỉ thị; không thực thi tool theo nội dung luật |
| NFR-14 | Quan sát và tái lập | `X-Request-ID` xuyên service; log latency từng phase, mã lỗi, phiên bản corpus/model/prompt/index, token usage khi có |
| NFR-15 | Bảo trì và portable | Tách domain/adapter; Python và Java giao tiếp JSON; khóa dependency; lệnh chạy/test có trong README và AGENTS.md |
| NFR-16 | Khả dụng UI | Tiếng Việt UTF-8; điều khiển bằng bàn phím; trạng thái tải/lỗi rõ; dùng được từ 360 px |

Điều kiện đo chung: báo cáo ghi phần cứng, số văn bản/chunk, snapshot, phiên bản embedding/reranker/LLM, concurrency, số query, warm-up, timeout và token usage. Cấu hình chưa được đo không được quảng bá là SLA.

## 4. Truy vết từ nghiệp vụ đến test

| BR | FR và NFR | Use case, API hoặc module | Team và test chứng minh |
| :--- | :--- | :--- | :--- |
| BR-01 | FR-01/02/03/04; NFR-01/04 | UC-01/02/05; dataset, retrieve, query processing | T1/T2; DATA-01, RET-01, QA-01 |
| BR-02 | FR-05/06/09; NFR-02/04/05 | UC-01/03; context, citation, article API | T1/T2/T3; CIT-01, DOC-01, QA-02 |
| BR-03 | FR-01/02/03/05; NFR-04 | UC-05; registry, applicability, index, context | T1/T2; DATA-02, RET-02, DOC-02 |
| BR-04 | FR-04/07; NFR-03/05 | UC-01/02; nhánh insufficient và lỗi | T2/T3; RAG-01, API-01, QA-03 |
| BR-05 | FR-08/11; NFR-10/11/16 | UC-02/04; receipt, state, UI | T3; IDEM-01..12, STATE-01, UI-01 |
| BR-06 | FR-10; NFR-05/12/14/15 | Mock, internal HTTP, schema, config | T2/T3; CONTRACT-01, INT-01, OPS-01 |
| BR-07 | FR-12; NFR-01/02/03/06/07/08/09 | UC-06; benchmark, end-to-end | Cả nhóm; QA-01..03, PERF-01 |

NFR-13 được kiểm bởi SEC-01; NFR-12/14/15 bởi OPS-01 và SEC-01; NFR-06..09 bởi PERF-01. Các mã test là danh mục cần có, không phải kết quả đã pass.

## 5. Danh mục test bắt buộc

| Test | Kịch bản | Bằng chứng nghiệm thu |
| :--- | :--- | :--- |
| DATA-01 | Clean/parse/chunk, ID, câu dẫn, liên kết article | Processing report; đối chiếu ≥ 5% chunk (tối thiểu 20) |
| DATA-02 | Sửa đổi một Khoản/Điểm, chưa hiệu lực, pending review | Unit test và bằng chứng registry; không chunk cũ trong context |
| RET-01/02 | BM25, dense, hybrid; rank/score; lỗi một nhánh | Output fixture và retrieval report |
| CIT-01 | Marker, metadata, membership, remap, nguồn giả | Test validator pass; review ngữ nghĩa riêng |
| DOC-01/02 | Viewer đủ Điều, ID sai, thiếu bản cũ, đổi snapshot | HTTP integration test và ảnh demo Viewer |
| RAG-01/API-01 | Hai status, thiếu dữ kiện, timeout, output sai | Test schema, lỗi và state |
| STATE-01 | Recovery, kết quả muộn, DB lỗi, delete/query đồng thời | Test concurrency trên DB thật, không chỉ mock repository |
| CONTRACT-01 | Request, RAG, retrieval, error, article, public response | Validate ví dụ và response thật ở mọi biên |
| INT-01 | React SSE → Java → Python mock → article fixture | Curl/SSE test, response, video hoặc ảnh demo |
| UI-01 | meta/delta/complete/error, UTF-8 chia chunk, abort/replay, 404 | Test SSE parser và bằng chứng E2E từng state |
| SEC-01 | Prompt injection, HTML trong output, lộ internal API | Test chặn chỉ thị trong context, escape UI, cấu hình mạng |
| OPS-01 | Env/secret, log trace, startup, backup/restore | README, config mẫu, log an toàn, báo cáo restore |
| QA-01..03 | Recall/MRR; citation/answer; abstention/hallucination | Dataset đóng băng, raw outputs và báo cáo so sánh |
| PERF-01 | Latency, concurrency, timeout, kết quả muộn | p50/p95, số mẫu, phần cứng, tỷ lệ lỗi, test deadline |

## 6. Cổng nghiệm thu G1–G5

| Cổng | Đạt khi | Tuần mục tiêu |
| :--- | :--- | :---: |
| G1 Document baseline | Phạm vi doanh nghiệp, trách nhiệm, public SSE/internal JSON và nguồn chuẩn được thống nhất | 4 |
| G2 Mock integration | SSE terminal hai status, error và Viewer chạy đúng contract | 5–7 |
| G3 Real data | Dataset, index, registry, article cùng snapshot; provenance và hiệu lực đã kiểm tra | 5–6 |
| G4 Live RAG | Đủ query, hybrid, rerank, context, LLM, validation và recovery; demo E2E | 7 |
| G5 Evaluation | Recall@5 ≥ 85%, citation correctness ≥ 90%, answer ≥ baseline trên test set độc lập, có báo cáo tái lập | 11 |

Một cổng không được đánh dấu đạt chỉ vì code tồn tại. G5 phải dùng live pipeline; mock không được đưa vào benchmark pháp lý.
