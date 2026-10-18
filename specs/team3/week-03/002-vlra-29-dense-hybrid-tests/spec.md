# Feature Specification: VLRA-29 — Kiểm thử Dense và Hybrid Retrieval

**Feature Branch**: nhánh hiện tại `feature/team3/*`, giữ nguyên; không tạo/chuyển nhánh.
**Feature Directory**: `specs/team3/week-03/002-vlra-29-dense-hybrid-tests`.
**Created**: 2026-10-19. **Status**: Draft — đã đặc tả, chưa kiểm thử/nghiệm thu.
**Input**: VLRA-29 do người dùng cung cấp: kiểm thử embedding/vector, hợp nhất RRF,
rank/chunk_id/dedup; bàn giao bộ test, kết quả similarity/RRF, pass/fail và lỗi.
**Phân công**: thành viên Team 3 kiểm thử chức năng Team 1 theo nhiệm vụ tuần 3.

## Clarifications

### Session 2026-10-19

- Người dùng giao triển khai theo [hướng dẫn tester](https://velvetforest.github.io/minh-hoa-BTL/minh-hoa-cong-viec.html). Phần xây Hybrid/factory/candidate API/Compose thuộc người làm VLRA-27; không sửa production trong task kiểm thử.
- Tái dùng script đánh giá, mixin và golden/nhóm do VLRA-28 tạo; phần Dense độc lập không chờ Hybrid. Model thật dùng AITeamVN/Vietnamese_Embedding theo adapter hiện tại, cố định commit revision khi tải được.
- Kiểm tra model thật và Qdrant server phải ghi riêng; thiếu dịch vụ/tài nguyên ghi BLOCKED/NOT RUN. FakeEmbedder và Qdrant in-memory không chứng minh model thật hoặc server đã đạt.
- Recall@20 ≥ 0.90 và không thấp hơn nhánh tốt nhất theo Retrieval Design §5 là gate benchmark Hybrid, không là unit-test gate. Baseline 30 câu và bộ mở rộng báo riêng, không so trực tiếp khác dataset/model/snapshot.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Kiểm tra embedding và Dense độc lập (Priority: P1)

Người kiểm thử xác định chuỗi chunk/query → embedding → vector search → chunk/rank/score
có đúng thiết kế, không cần chờ Hybrid hoặc gọi LLM.

**Why this priority**: Vector/ID sai làm kết quả retrieval sai dù report có điểm similarity.
**Independent Test**: Dữ liệu/vector kiểm soát được để kiểm tra chuẩn hóa, chiều,
cosine, payload và truy vấn; phân biệt test double với embedding model thật.

**Acceptance Scenarios**:

1. **Given** vector hữu hạn/không zero và chunk có ID duy nhất, **When** tạo index và
   query bằng vector đã biết, **Then** thứ tự/similarity khớp giá trị tính độc lập,
   IDs/metadata còn nguyên, không dùng output vừa chạy làm expected.
2. **Given** model/prefix/revision/dimension cố định, **When** encode query/chunk,
   **Then** ghi cấu hình và xác nhận preprocessing, chiều/giá trị chuẩn hóa theo thiết kế;
   lỗi vector/model được ghi thành lỗi, không trả thành kết quả tìm kiếm hợp lệ.
3. **Given** corpus/query không liên quan nhưng index hợp lệ, **When** Dense tìm hàng xóm,
   **Then** báo score/IDs thật; không áp quy tắc BM25 “không trùng token thì phải rỗng”.
4. **Given** test đang dùng embedding giả, **When** báo PASS, **Then** ghi phạm vi vector
   plumbing, không suy đã kiểm chứng model thật hoặc semantic relevance của corpus.

### User Story 2 - Kiểm tra hợp nhất Hybrid/RRF (Priority: P1)

Người kiểm thử kiểm tra chunk ở một/hai nhánh được gộp đúng ID, điểm RRF và thứ tự;
không đánh đồng cosine với RRF hoặc lỗi một nhánh với nhánh tìm thành công nhưng rỗng.

**Why this priority**: Hợp nhất sai hoặc đếm trùng làm xếp hạng và dữ liệu đưa vào RAG sai.
**Independent Test**: Cố định hai ranked lists và oracle RRF tính tay từ thiết kế,
sau đó so output module Hybrid thật; oracle không thay module được kiểm thử.

**Acceptance Scenarios**:

1. **Given** hai ranked lists có chunk chung/riêng và tham số công bố, **When** hợp nhất,
   **Then** một row cho mỗi ID, score bằng tổng đóng góp rank, output rank liên tục và N≤K.
2. **Given** hai chunk bằng điểm RRF, **When** xếp hạng, **Then** ưu tiên best rank nhỏ hơn,
   rồi chunk_id theo từ điển; lặp lại trên cùng dữ liệu có kết quả xác định.
3. **Given** một nhánh thành công/rỗng hoặc cả hai rỗng, **When** hợp nhất, **Then** đóng góp
   nhánh rỗng là 0; cả hai rỗng trả results=[] và vẫn phân biệt với lỗi nguồn.
4. **Given** một nhánh lỗi hoặc snapshot/tập IDs không tương thích, **When** query Hybrid,
   **Then** báo lỗi theo interface; không âm thầm trả nhánh còn lại với nhãn hybrid_rrf.
5. **Given** chưa có module Hybrid, **When** bàn giao, **Then** ghi phần Hybrid BLOCKED,
   dependency/owner rõ; chạy công thức minh họa hoặc skip không được tính là Hybrid PASS.

### User Story 3 - Query corpus thật và bàn giao có thể tái hiện (Priority: P2)

Người tổng hợp có kết quả Dense và Hybrid tách riêng, biết model/nguồn nào được chạy
và mỗi lỗi/giới hạn ảnh hưởng tới kết luận nào.

**Why this priority**: Unit test vector giả không thay yêu cầu xác nhận embedding và retrieval thực tế.
**Independent Test**: Cố định corpus/hash, query/expected IDs và profile; báo expected/actual,
cấu hình, cách tái hiện và trạng thái cho từng lớp, không cần FE/BE.

**Acceptance Scenarios**:

1. **Given** model thật và corpus/nhãn đã sẵn sàng, **When** chạy query kiểm thử thực tế,
   **Then** ghi model/revision, K, IDs/rank/cosine, nhãn/căn cứ chọn và verdict; không dùng
   kết quả model giả để thay evidence này.
2. **Given** Hybrid và hai nhánh cùng snapshot đã sẵn sàng, **When** chạy bộ query,
   **Then** lưu candidate IDs/rank từng nhánh, điểm RRF cuối, dedup và metadata tương ứng.
3. **Given** thiếu model/dịch vụ/module, **When** báo kết quả, **Then** ghi NOT RUN/BLOCKED
   và nguyên nhân; tiếp tục phần độc lập, không kết luận toàn VLRA-29 đạt.

### Edge Cases

- Question blank/sai kiểu/quá 4000 code point; K ngoài 1–50, bool/số thực; Unicode NFC/NFD.
- Vector zero/NaN/Inf, sai số chiều/số lượng, shape query/chunk không tương thích.
- Collection thiếu/mất sau connect, manifest lỗi/hash/IDs/model-revision không khớp.
- Score cosine âm hoặc đồng hạng; sai số số thực không bị nhầm thành xác suất hay lỗi thứ hạng.
- Hai ranked lists rỗng, một nhánh rỗng, trùng ID giữa nhánh, ID trùng trong một input vi phạm contract.
- RRF tie, ID không có ở một nhánh, K lớn hơn số ID hợp lệ, metadata/version không nhất quán.
- Một nhánh lỗi; không truy xuất được dependency/model; test suite skip vì thiếu package.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Phải kiểm kê/tái sử dụng test Dense hiện có; tách test double, model thật,
  vector service thật/local và Hybrid. Không coi một lớp PASS là các lớp còn lại đã chạy.
- **FR-002**: Phải kiểm tra preprocessing query/chunk, prefix theo model, vector hữu hạn,
  không zero, đúng dimension/count và chuẩn hóa; so expected từ oracle độc lập.
- **FR-003**: Phải kiểm tra lưu/query/nạp kết nối index, named cosine vector, mapping
  chunk IDs/payload/version, tính nhất quán manifest; lỗi không được che thành success.
- **FR-004**: Dense output theo RetrievalOutput v0.1: 12 field/candidate, ID thật/duy nhất,
  rank 1..N, N≤K, `retrieval_method=dense`, score cosine hữu hạn trong [-1,1] theo sai số số thực.
  Không tự thêm ngưỡng cosine để loại kết quả hoặc coi score là độ tin cậy pháp lý.
- **FR-005**: Phải có kiểm chứng model thật trên câu hỏi/corpus được cố định trước chạy;
  model/revision/cấu hình, expected IDs/căn cứ nhãn và actual scores được ghi đầy đủ.
  Chưa đủ tài nguyên ghi NOT RUN/BLOCKED; fixture embedding giả không thay kết quả đó.
- **FR-006**: Hybrid phải được đối chiếu với công thức `Σ w_i/(rrf_k+rank_i)`, rank bắt đầu
  từ 1, nhánh không chứa ID góp 0; cấu hình mặc định đề xuất k=60 và weights=1/1 có nguồn.
  Tham số sử dụng phải công bố, không cộng điểm BM25 trực tiếp với cosine.
- **FR-007**: Hợp nhất chỉ một candidate mỗi chunk_id, score/rank/tie-break đúng thiết kế
  best rank rồi ID từ điển, cắt Top-K sau hợp nhất, `retrieval_method=hybrid_rrf`.
  Input trùng ID trong cùng nhánh là vi phạm cần ghi/test, không lấy double count làm expected.
- **FR-008**: Phải kiểm tra rỗng/lỗi từng nhánh, corpus/index lệch và metadata/ID không tồn tại.
  Nhánh lỗi không được giả nhãn hybrid_rrf bằng kết quả nhánh còn lại.
- **FR-009**: Query thực tế của Dense/Hybrid lưu snapshot, query/K, expected/căn cứ nhãn,
  actual IDs/rank/similarity/RRF và contributor lists khi Hybrid được chạy; report theo từng phương pháp.
- **FR-010**: Phải bàn giao test/report/issue list, commit/working tree, môi trường, command,
  expected/actual, tổng pass/fail/error/skip/not-run và dependency chưa đủ.
- **FR-011**: Module Hybrid chưa có phải ghi BLOCKED phần phụ thuộc; được tiếp tục Dense.
  Không tự viết implementation Hybrid, lấy phác thảo docs làm production hoặc báo skip là PASS.
- **FR-012**: Không đổi model/schema/algorithm/corpus hoặc sửa production để test đạt;
  lỗi có ca tái hiện bàn giao T1, quyết định thay interface/model cần owner/phạm vi riêng.
- **FR-013**: Dùng script/mixin VLRA-28 để đánh giá cùng snapshot và bộ nhãn; ghi
  Recall@5/20, MRR@10, p50/p95, nhóm câu hỏi, model/revision và từng query/score.
  Gold rỗng tách khỏi mẫu tính Recall/MRR; không tự đặt cosine threshold.
- **FR-014**: Khi có runtime Hybrid, kiểm tra cả timeout theo cấu hình thiết kế,
  lỗi một nhánh, lệch version/IDs, RRF/dedup/tie-break; chưa có runtime ghi BLOCKED
  và bàn giao interface retrieve/question/results, vị trí mixin, oracle/case cho owner.

### Key Entities

- **Embedding run**: model/revision/prefix/dimension, profile giả/thật và nguồn dữ liệu.
- **Ranked list**: method, snapshot, K, IDs/rank/score và metadata gốc.
- **Fusion case**: contributor ranks, k/weights, oracle RRF/tie-break và kết quả thực tế.
- **Evidence/issue**: yêu cầu/case, cách tái hiện, expected/actual, trạng thái và owner/dependency.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Mọi FR-001..014 có mapping tới case/evidence hoặc phần chưa kiểm chứng có lý do;
  không đánh dấu một method đạt chỉ vì method khác có test chạy được.
- **SC-002**: Tất cả case đã thực thi có verdict và tổng số khớp report; lỗi phát hiện được
  bàn giao với expected/actual và bước tái hiện. Hoàn thành công việc kiểm thử không đồng nghĩa
  module không có lỗi hoặc buộc người kiểm thử sửa production.
- **SC-003**: 100% output đã kiểm tra truy vết được IDs về corpus/snapshot tương ứng;
  bảng Dense ghi similarity, bảng Hybrid ghi RRF/contributor ranks và dedup.
- **SC-004**: Tất cả ca RRF bắt buộc có expected tính độc lập trước chạy; sai khác được ghi FAIL,
  chưa có runtime ghi BLOCKED/NOT RUN. Không thay production evidence bằng oracle hoặc skip.
- **SC-005**: Báo cáo phân biệt model giả, model thật và dependency Hybrid; chỉ kết luận
  đã kiểm chứng đủ phạm vi khi các phần bắt buộc được thực thi, kể cả khi phát hiện FAIL.
  Phần chưa chạy ghi BLOCKED/NOT RUN và bàn giao từng phần, không nâng thành toàn VLRA-29 DONE.

Không tự thêm số query tối thiểu, ngưỡng Recall, latency/coverage hoặc thay model mặc định.
Benchmark model mặc định theo hướng dẫn thuộc phạm vi; chọn model mới/tuning weights là phạm vi riêng.

## Assumptions

- T1 sở hữu Dense/Hybrid; người dùng giao kiểm thử, không giao xây module chưa có hoặc sửa production.
- Bộ query/nhãn cố định trước chạy, cùng snapshot; không dùng score/tập ID có schema hợp lệ
  làm bằng chứng relevance hoặc applicability. Bộ lọc cấp văn bản không thay unit applicability C5.
- Kiểm thử có thể dùng tài nguyên cô lập; model giả chỉ dùng cho cơ chế/vector oracle.
  Run model thật cần model/revision và tài nguyên được ghi ở plan; không tự thay model để làm test đạt.
- Input RRF hợp lệ tuân contract IDs duy nhất mỗi nhánh; case vi phạm được ghi riêng để review hành vi.

## Scope and Dependencies

Trong phạm vi: Dense embedding/index/query/cosine, Hybrid RRF/dedup/rank và lỗi, query corpus,
test/report/issues. Ngoài phạm vi: sửa production, tạo facade/retriever Hybrid, đổi model,
server fusion/Weighted Score, corpus processing/legal review toàn bộ, RAG/LLM/FE/BE và benchmark toàn dự án.

Phụ thuộc: bộ dữ liệu/nhãn/version, embedding profile/tài nguyên, vector store cô lập, hai nhánh
cùng snapshot và module Hybrid. Thiếu Hybrid chỉ chặn phần cần runtime Hybrid, không chặn Dense.
Chưa có module là gap, không là bằng chứng thuật toán lỗi; không tự đổi phạm vi để bỏ nửa nhiệm vụ.

## Sources and Current State

- [Nhiệm vụ tuần](../requirements.md), [phân rã cấp tuần](../tasks.md).
- [Retrieval Design](../../../../docs/team1_data/retrieval-design.md) §4;
  [Dense Proposal](../../../../docs/team1_data/dense-retrieval-proposal.md) §2–5;
  [Hybrid Proposal](../../../../docs/team1_data/hybrid-retrieval-proposal.md) §4–5;
  [Contract](../../../../contracts/v0.1/CONTRACT.md), [schema](../../../../contracts/v0.1/retrieval_output.schema.json).
- Đã đọc [Dense module](../../../../team1_data/retrieval/dense.py),
  [embedding adapter](../../../../team1_data/retrieval/embedding.py),
  [22 định nghĩa test](../../../../tests/test_dense_retrieval.py),
  [exports](../../../../team1_data/retrieval/__init__.py) và CLI. Đây là source inventory ngày19/10, chưa chạy.
- Test hiện có dùng FakeEmbedder và Qdrant in-memory. Model adapter có trong source,
  không suy model thật đã được kiểm chứng. Dense hiện giữ nearest neighbours khi query không trùng từ.
- Chưa có module Hybrid/RRF, facade Retriever.from_config hoặc test Hybrid runtime trong nhánh.
  Interface trong docs là thiết kế, không tự thêm production vào nhiệm vụ kiểm thử.
- Hướng dẫn bổ sung giao benchmark model mặc định; các model candidates/tham số tuning
  không là nhiệm vụ thay model. Giữ [C1–C5](../../README.md#3-quyết-định-kế-thừa-và-ranh-giới), đặc biệt C5.

## Readiness

Clarify → plan → tasks → analyze và sửa vấn đề đã thực hiện riêng ngày 19/10.
Checklist chất lượng 16/16; chưa có quyết định thiết kế chặn phần độc lập.
Trạng thái triển khai/nghiệm thu xem tasks.md và verification.md; model/server/Hybrid
phải có bằng chứng thực thi riêng. Không có extension hooks.
