# Feature Specification: VLRA-28 — Kiểm thử BM25 Retrieval

**Feature Branch**: nhánh hiện tại `feature/team3/*`, giữ nguyên; không tạo/chuyển nhánh.
**Feature Directory**: `specs/team3/week-03/001-vlra-28-bm25-tests`.
**Created**: 2026-10-19. **Status**: Draft — đã đặc tả, chưa kiểm thử/nghiệm thu.
**Input**: VLRA-28 do người dùng cung cấp: kiểm thử độc lập index/query BM25 trên corpus
hiện có; bàn giao unit tests, Top-K/chunk_id, pass/fail và danh sách lỗi.
**Phân công**: thành viên Team 3 kiểm thử chức năng Team 1 theo nhiệm vụ tuần 3.

## Clarifications

### Session 2026-10-19

- Nguồn bổ sung: người dùng yêu cầu triển khai theo [hướng dẫn tester](https://velvetforest.github.io/minh-hoa-BTL/minh-hoa-cong-viec.html), cập nhật 17/10; không thay contract hoặc giao xây Hybrid.
- Dùng golden Team 2 hiện có làm baseline; thêm bộ mẫu riêng và file phân nhóm theo ID, không đổi định dạng/file gốc Team 2 khi chưa phối hợp owner. Mẫu mới là nhãn retrieval draft, chưa phê chuẩn pháp lý.
- Script đánh giá và mixin contract được xây một lần trong VLRA-28, VLRA-29 tái sử dụng. Recall@20 ≥ 0.90 là ngưỡng Hybrid theo Retrieval Design §5; không áp làm gate unit test BM25.
- Không có câu hỏi làm rõ quan trọng còn chặn phần độc lập. Model/Docker/Hybrid chưa sẵn sàng phải ghi trạng thái thực tế, không thay bằng số minh họa trên trang.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Kiểm tra index và truy vấn độc lập (Priority: P1)

Người kiểm thử xác định BM25 có khởi tạo/nạp index và trả các chunk đúng với dữ liệu,
câu hỏi và số lượng yêu cầu hay không, trước khi dùng kết quả làm đầu vào cho RAG.

**Why this priority**: Index hoặc mapping ID sai làm mọi bước sau tìm nhầm căn cứ.
**Independent Test**: Dùng bộ chunk kiểm soát được cùng câu hỏi có nhãn đối chiếu;
kiểm tra build, lưu/nạp lại và output mà không cần Dense, Hybrid, LLM hoặc FE/BE.

**Acceptance Scenarios**:

1. **Given** corpus kiểm thử có chunk IDs duy nhất và nhãn hợp lệ, **When** tạo index
   và truy vấn câu khớp đoạn đã biết, **Then** chunk dự kiến xuất hiện đúng vị trí đã
   xác định trước, output không đổi ID/content/metadata từ nguồn.
2. **Given** một index đã lưu cùng corpus/version, **When** nạp lại và chạy cùng query,
   **Then** kết quả tương đương trước lưu, có evidence về ID/rank/score và manifest.
3. **Given** query có nhiều ứng viên, **When** đổi Top-K trong khoảng được chấp nhận,
   **Then** số kết quả không vượt K hoặc số ứng viên dương, ID không trùng, rank liên tục.

### User Story 2 - Kiểm tra câu hỏi dựa trên corpus thật (Priority: P1)

Người kiểm thử có bảng Top-K/chunk_id truy vết được về corpus đang có, tách khỏi
fixture nhỏ để thấy những trường hợp query thực tế tìm đúng hoặc chưa phù hợp.

**Why this priority**: Unit fixture không thay yêu cầu Jira dùng câu hỏi từ corpus hiện có.
**Independent Test**: Chọn câu hỏi và expected chunk IDs từ corpus, cố định trước chạy;
ghi bộ câu hỏi, nhãn/căn cứ chọn, phiên bản và expected/actual cho từng query.

**Acceptance Scenarios**:

1. **Given** câu hỏi có tham chiếu Điều/số hiệu hoặc thuật ngữ trong corpus, **When**
   query BM25 với K công bố, **Then** báo ID/rank/score thực tế, đối chiếu nhãn và ghi
   PASS/FAIL có lý do; không chọn expected từ output vừa nhận.
2. **Given** một câu không có token khớp, **When** query thành công, **Then** results rỗng;
   không nhầm kết quả rỗng với index hỏng, cũng không tự suy kết luận pháp lý.
3. **Given** corpus/index khác snapshot, **When** đối chiếu kết quả, **Then** ghi sự khác
   biệt và không cộng các kết quả khác snapshot thành một báo cáo so sánh.

### User Story 3 - Kiểm tra lỗi và bàn giao kết quả (Priority: P2)

Người phụ trách Team 1 nhận được lỗi tái hiện được, còn người tổng hợp biết phần nào
đã chạy, bị lỗi hoặc chưa đủ điều kiện; test có sẵn không bị tính lại thành công việc mới.

**Why this priority**: Báo cáo có thể kiểm tra lại cần cả nhánh lỗi và giới hạn môi trường.
**Independent Test**: Kiểm tra input/index/corpus không hợp lệ và đối chiếu trạng thái
trong report với kết quả test thật; không phải khởi động toàn hệ thống.

**Acceptance Scenarios**:

1. **Given** question rỗng/sai kiểu/quá dài hoặc K sai, **When** query, **Then** bị từ chối
   theo interface; không biến lỗi thành danh sách kết quả hợp lệ.
2. **Given** index thiếu/hỏng hoặc chunk store không khớp, **When** load/query, **Then**
   lỗi được ghi cùng bước tái hiện, expected/actual và ảnh hưởng; không báo index sẵn sàng.
3. **Given** môi trường thiếu dependency làm suite skip, **When** báo kết quả, **Then**
   ghi SKIP/BLOCKED và nguyên nhân; không báo kiểm thử BM25 đã PASS toàn bộ.

### Edge Cases

- Question null/sai kiểu/blank; 4000 và 4001 Unicode code point; dấu câu hoặc token ngoài từ vựng.
- Unicode NFC/NFD, hoa/thường, kiểu đặt dấu, cụm Điều/Khoản/Điểm/Chương và số hiệu văn bản.
- K=1/50, 0/51, bool/số thực; K lớn hơn corpus hoặc số chunk có điểm dương.
- Corpus rỗng/sau lọc không còn chunk, duplicate ID, index thiếu/hỏng hoặc lệch IDs.
- Chunk ngoài bộ lọc thiết kế; ID/metadata bị đổi; rank không liên tục, score không hữu hạn.
- Điểm bằng nhau: ghi hành vi/tính lặp lại; không tự đặt tie-break BM25 chưa được nguồn chốt.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Phải kiểm kê và tái sử dụng test BM25 hiện có; xác định rõ yêu cầu đã được
  bao phủ và phần cần bổ sung. Test tồn tại hoặc số lượng test không là evidence PASS.
- **FR-002**: Phải kiểm tra build/save/load index, tập IDs và khả năng truy vấn lại cùng
  dữ liệu; index/store không tương thích phải có kết quả lỗi quan sát được.
- **FR-003**: Phải kiểm tra question sau trim dài 1–4000 code point, K là số nguyên
  1–50, không chấp nhận bool; không đổi giới hạn của retrieval thành giới hạn public chat.
- **FR-004**: Phải kiểm tra chuẩn hóa query/cụm pháp lý theo thiết kế BM25, output dùng
  question đã trim, score hữu hạn/dương, `retrieval_method=bm25`; loại điểm 0.
- **FR-005**: Mỗi output phải khớp RetrievalOutput v0.1: question/results và đủ 12 field
  của candidate; IDs tồn tại, không trùng; rank 1..N, score giảm dần và N≤K.
- **FR-006**: Phải kiểm tra provenance/content khớp chunk nguồn, cùng corpus/version.
  Bộ lọc legal_status đang có không chứng minh unit applicability đã được xác minh.
- **FR-007**: Phải có bảng chạy câu hỏi từ corpus thật: question/case ID, K, snapshot/hash,
  expected chunk IDs và căn cứ nhãn, actual IDs/rank/score, kết luận/lý do từng case.
- **FR-008**: Phải kiểm tra input/corpus/index lỗi và query không khớp; lỗi kỹ thuật
  không được dùng thay kết quả tìm kiếm thành công/rỗng.
- **FR-009**: Báo cáo phải có commit/working tree, môi trường, cách tái hiện, pass/fail/
  error/skip/not-run, lỗi/thiếu hụt và giới hạn; không suy test được skip là PASS.
- **FR-010**: Chỉ kiểm thử và bàn giao lỗi. Không tự sửa implementation/corpus/contract,
  thay tham số để che lỗi hoặc copy output làm expected; giữ thay đổi local có sẵn.
- **FR-011**: Cung cấp script đánh giá chung nhận object có retrieve(question, top_k):
  Recall@5/20 macro theo gold IDs, MRR@10, p50/p95 của retrieve; lưu từng query/rank/score,
  snapshot/hash, index_version, model/revision, môi trường và lỗi. Gold rỗng không được
  tính thành Recall=1 hoặc suy kết quả retrieval rỗng là phân loại thiếu căn cứ.
- **FR-012**: Tạo mixin contract tái dùng cho BM25/Dense và Hybrid sau này: schema,
  IDs duy nhất, rank 1..N, score giảm không tăng, giới hạn K, trim và tám input lỗi;
  giữ kiểm tra đặc thù từng method, chỉ bỏ kiểm tra bị trùng hoàn toàn.
- **FR-013**: Bổ sung mẫu retrieval có căn cứ từ corpus, nhóm tham chiếu pháp lý/
  diễn đạt đời thường/ngoài corpus; dùng validator Team 2 cho baseline và mẫu mới,
  ghi giới hạn validator, lưu nhóm ở sidecar để không đổi schema nguồn.

### Key Entities

- **Retrieval test case**: câu hỏi, K, nguồn/căn cứ nhãn, expected/actual và trạng thái.
- **Corpus/index identity**: hash/version, tập chunk IDs và thông tin tái hiện index.
- **Candidate**: chunk/provenance từ corpus, score kỹ thuật, rank và phương pháp.
- **Issue**: bước tái hiện, expected/actual, evidence, phạm vi ảnh hưởng và owner.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Mọi FR-001..013 truy vết tới case/evidence hoặc trạng thái chưa kiểm chứng
  có lý do; không có yêu cầu được đánh dấu đạt chỉ từ việc đọc source.
- **SC-002**: Tất cả case đã thực thi có kết quả quan sát được; số pass/fail/error/skip
  và tổng case khớp báo cáo. Bàn giao đủ các case bắt buộc đã chốt, ghi rõ phần chưa chạy.
  Nhiệm vụ kiểm thử cho phép phát hiện/bàn giao lỗi, không yêu cầu sửa production hoặc
  đổi FAIL thành PASS; kết luận module đạt phải tách khỏi kết luận đã làm đủ công việc kiểm thử.
- **SC-003**: 100% query corpus thật trong bộ đã công bố có expected/actual Top-K/IDs,
  snapshot và căn cứ nhãn; mọi ID output đối chiếu được về corpus tương ứng.
- **SC-004**: Mọi sai khác được phát hiện có ca tái hiện và evidence; người khác có thể
  chạy lại theo báo cáo hoặc nhận được lý do cụ thể nếu thiếu tài nguyên.

Không tự đặt số câu tối thiểu, SLA, Recall threshold hoặc coverage gate ngoài Jira.
Đánh giá so sánh theo hướng dẫn đã được giao; metric không thay nghiệm thu unit test.

## Assumptions

- T1 giữ quyền sở hữu module; người dùng giao quyền kiểm thử/bổ sung test, chưa giao sửa production.
- Bộ case/nhãn được cố định trước chạy; corpus thật là bản có trong repo, hash không là
  phê chuẩn hiệu lực pháp luật. Nhãn chưa đủ căn cứ phải ghi cần review, không tự bịa ID.
- Dùng môi trường/index tạm cô lập khi thực hiện; không ghi đè snapshot/index đang phục vụ.
- Nhánh/phạm vi đã hợp nhất ở HEAD 5a9af42; các file tài liệu chưa commit phải được giữ.

## Scope and Dependencies

Trong phạm vi: BM25/tokenizer/index/query, contract, script đánh giá dùng chung, mẫu/nhóm golden riêng và test/report/issues.
Ngoài phạm vi: xây Dense/Hybrid, RAG/LLM/SSE, đổi model/retrieval algorithm, benchmark toàn dự án,
review pháp lý toàn corpus, auth/FE/BE, sửa code production và cập nhật Jira/commit/push.

Phụ thuộc: corpus/chunk metadata/nhãn đối chiếu, dependency BM25 và schema validator.
Lọc legal_status/applicability còn khác baseline C5 là giới hạn phải báo; không sửa nguồn
hoặc mặc định toàn bộ corpus đủ điều kiện pháp lý vì test khởi tạo index đạt.

## Sources and Current State

- [Nhiệm vụ tuần](../requirements.md) là nguồn Jira/phạm vi; [phân rã](../tasks.md) giữ dependency cấp tuần.
- [Retrieval Design](../../../../docs/team1_data/retrieval-design.md) §4;
  [BM25 Proposal](../../../../docs/team1_data/bm25-proposal.md) §3–4;
  [Contract](../../../../contracts/v0.1/CONTRACT.md) và [schema](../../../../contracts/v0.1/retrieval_output.schema.json).
- Đã đọc [BM25 module](../../../../team1_data/retrieval/bm25.py),
  [common](../../../../team1_data/retrieval/common.py), [tokenizer](../../../../team1_data/retrieval/tokenizer.py)
  và [18 định nghĩa test](../../../../tests/test_bm25_retrieval.py). Đây là source inventory ngày19/10, chưa là kết quả chạy.
- Thiết kế minh họa facade Retriever, còn code dùng BM25Retriever; không tạo facade chỉ để test.
  Đổi tokenizer/tham số để tối ưu là công việc khác; script đo chung thuộc hướng dẫn bổ sung đã giao.
- Code có filter cấp văn bản; yêu cầu unit applicability từ [C5](../../README.md#3-quyết-định-kế-thừa-và-ranh-giới)
  vẫn cần đối chiếu khi chọn dữ liệu/giải thích kết quả.

## Readiness

Clarify → plan → tasks → analyze và sửa vấn đề đã thực hiện riêng ngày 19/10.
Checklist chất lượng 16/16; chưa có quyết định thiết kế chặn phần độc lập.
Trạng thái triển khai/nghiệm thu xem tasks.md và verification.md; model/server/Hybrid
phải có bằng chứng thực thi riêng. Không có extension hooks.
