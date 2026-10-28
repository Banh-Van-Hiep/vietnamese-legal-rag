# Biên bản kiểm chứng nhiệm vụ Team 3 — Tuần 7

**Ngày kiểm tra:** 28/10/2026 (Asia/Saigon).
**Căn cứ hiện hành:** [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) (đặc tả chính),
[CODING_CONVENTIONS.md](../../../docs/CODING_CONVENTIONS.md) (quy chuẩn/DoD),
[tasks.md](tasks.md) (phân rã nhiệm vụ tuần). Jira phục vụ theo dõi công việc.
**Source kiểm tra:** `62c3556bab16e106e2e6ff29b0280a96fb738146` cùng thay đổi tài liệu chưa commit; không sửa code nghiệp vụ/test hoặc dataset để làm kết quả đạt.
**Môi trường:** Windows, JDK25/Spring Boot4.1.1, Maven Wrapper3.9.16, Node24.21,
Python3.12 trong venv kiểm thử riêng, PostgreSQL18 database riêng, Edge headless profile riêng.
**Phạm vi kết luận:** kiểm chứng kỹ thuật; chưa thay phê duyệt nhóm/gate hoặc trạng thái Jira.

**Đối chiếu nguồn ngày 28/10:** ARCHITECTURE §3/§6/§8.2 cho Viewer, idempotency và dataset/evaluation; CODING_CONVENTIONS §4/§7 cho bất biến/DoD. G4 là mốc kế hoạch tuần7, không thay các chỉ tiêu Recall@5/Citation Correctness/Answer Quality/an toàn của đặc tả chính.
Kết luận dựa trên baseline/quy chuẩn/task hiện hành, không loại tiêu chí chỉ vì Jira cũ
chưa ghi. Lượt cập nhật nguồn này không chạy lại build/test hoặc thay số liệu đã đo.

## 1. Kết luận

**Chưa đạt Gate G4 hoặc nghiệm thu trọn tuần7.** Idempotency được kiểm chứng; Viewer/G2
đạt với mock. Chưa đủ dataset v1, manifest/split/review và môi trường RAG live.

## 2. Đối chiếu từng task

| Task | Expected / DoD | Actual và căn cứ | Kết luận |
| --- | --- | --- | --- |
| VLRA-T3-11 | IDEM01–12, không AI/message trùng, snapshot replay | 16 ca store chạy lại cả H2/PostgreSQL và12 ca StreamApiTests đạt; ma trận mapping dưới đây đủ12 tình huống. Không có lớp tên `IdempotencyIntegrationTest`; tái sử dụng behavioral tests hiện có. | Đạt hành vi idempotency |
| VLRA-T3-12 | Viewer đúng phiên bản/IDs,404, nguồnHTTPS, mobile và<1s | E03/E06 và tests saiIDs/version đạt. Edge360px/768px hiển thị nguồn an toàn, không tràn ngang;20 lookup mock p95≈10.16ms. Chưa đo p95UI/nguồn corpus thật và tra nguồn nhà nước live. | Đạt mock; chưa xác minh đầy đủ live |
| VLRA-T3-13 |100–150 câu, 75/25 answered/unanswerable,60/40 Dev/Test,freeze+SHA256,review | Hai file hiện có tổng53mẫu riêng biệt (52 answered/1 insufficient); filePhase1 có40. Không có `golden_dataset_v1.manifest.json`, chưa có bằng chứng stratified split/freeze/ký review. Validator enum answered hiện đã đúng và chạy đạt; lưu ý sửa enum trong ARCHITECTURE §8.2.A là phần đã được đáp ứng, không giao làm lại. | Chưa đạt dataset v1 |
| VLRA-T3-14 | Demo3luồng pipeline thật, cả 3 team duyệt G4, ảnh/video | G2 E2E 10/10 có screenshot, nhưng live ready/query 503; không có demo đủ retrieval→rerank→LLM/source thật và biên bản duyệt G4 trong lượt này. | Bị chặn G4 |

## 3. Ma trận IDEM01–12 đã đối chiếu

Các test dưới đều có trong lượt package 125/125 mới chạy; store tests kế thừa trên PostgreSQL thật.

| IDEM | Tình huống | Evidence test |
| --- | --- | --- |
|01|UUID mới, không conv|persistsPairReplaysWithAnotherRepositoryAndStableTimestamp; sseHasNumericCamelCaseIdsCanonicalCitationAndReplay|
|02|UUID mới, conv có sẵn|historyOnlyAnsweredPairsAtMostFiveInChronologicalOrder; E2E E04|
|03|UUID cũ pending|pendingConflictBusyAndFailureReplayDoNotAddMessages; metaIsSentAfterAcceptanceWhilePendingAndBusyIsRejected|
|04|Completed replay không AI|persistsPairReplaysWithAnotherRepositoryAndStableTimestamp; sseHasNumericCamelCaseIdsCanonicalCitationAndReplay|
|05|Failed replay logical error|pendingConflictBusyAndFailureReplayDoNotAddMessages; upstreamErrorsTerminateStreamAndReplayLogicalHttpStatus|
|06|Đổi question cùngUUID|pendingConflictBusyAndFailureReplayDoNotAddMessages|
|07|Đổi conv cùngUUID|pendingConflictBusyAndFailureReplayDoNotAddMessages|
|08|Retry bỏ conv, giữ binding|persistsPairReplaysWithAnotherRepositoryAndStableTimestamp|
|09|Hai request cùngUUID đua nhau|duplicateFirstRequestsAcrossRepositoryInstancesCreateOnePair|
|10|UUID mới cùng conv pending|differentRequestsForSameConversationAcrossInstancesAllowOnlyOnePending|
|11|UUID thuộcconv đã xóa|deleteRemovesContentAndKeepsOnlyTombstone|
|12|Query/delete đồng thời|queryAndDeleteShareDatabaseLock; completedReplayWaitsForDeleteLockAndDoesNotReturnDeletedSnapshot|

Cụm test đảm nhiệm nhiều tiêu chí trong một case; không tạo12case trùng chỉ để khớp mã trong bảng.
Snapshot replay không thay điều kiện recovery scheduler của tuần4/8, phần đó vẫn thiếu.

## 4. Evidence và điều kiện nghiệm thu tiếp

- [Lệnh/setup](../week5/verification.md#3-lệnh-chạy-lại): package 125/125, FE 72/72,
  build và E2E 10/10 mới chạy. UI probe thêm3 ca đạt, không là kiểm chứng legal grounding.
- Evidence local ignored tại `backend/target/week-acceptance-20261028/`:
  `e2e/{results.json,browser.png}`, `ui-probe.json`, `viewer-360.png`, `viewer-768.png`,
  `mock-performance.json`, `live-readiness.json`, `inventory.json`, surefire reports.
- Cần chốt dataset100–150 câu, split/manifest/review; cấu hình live đạt ready 200;
  chạy ba demo P0/citation, ngoài phạm vi và duplicateUUID trên pipeline thật.
- Nhóm xác nhận ảnh/video và phê duyệt G4 sau khi có kết quả; không tự đóng Jira.

## 5. Các cổng chất lượng theo đặc tả chính

ARCHITECTURE §8.2.B quy định các chỉ tiêu dưới đây, độc lập với việc gọi mốc tuần là G4.
Bộ kiểm chứng mock vừa chạy chưa đo các chỉ tiêu này trên bộ Test có nhãn/corpus thật:

| Chỉ tiêu | Mục tiêu trong đặc tả chính | Kết quả lượt kiểm tra này |
| --- | --- | --- |
| Retrieval | Recall@5 ≥85%; bổ sung Recall@20 ≥90% và MRR@20 | Chưa đo trên retrieval thật |
| Citation Correctness | ≥90%, thẩm định claim/phiên bản/nguyên văn | Chưa thẩm định pháp lý; schema/UI PASS không thay chỉ tiêu này |
| Answer Quality | Chấm mù rubric 5 tiêu chí, target ≥baseline | Chưa chạy blind evaluation trên dataset đã đóng băng |
| An toàn | Từ chối thiếu dữ kiện/ngoài snapshot, giảm hallucination | Nhánh mock insufficient được kiểm, chưa là đánh giá hallucination hoặc refusal của model thật |

Chưa đủ căn cứ nghiệm thu MVP theo đặc tả chính dù luồng G2 mock đạt.
