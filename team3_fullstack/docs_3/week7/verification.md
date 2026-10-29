# Biên bản nghiệm thu lại Team 3 — Tuần7

**Ngày:**29/10/2026 (Asia/Saigon), thay tổng hợp28/10. Source `d67f36acf615956728838a005ec8758d13a9a74a`;
develop đã fetch `eea5604251afd4d8605fed510d6bf4de31d629bb`. Code liên quan không đổi; bảo toàn hồ sơ tuần6 chưa commit.
Căn cứ [ARCHITECTURE](../../../docs/ARCHITECTURE.md),
[CODING_CONVENTIONS](../../../docs/CODING_CONVENTIONS.md), [tasks tuần7](tasks.md).
[Hồ sơ chi tiết](vlra-t3-11-14-acceptance/spec.md),
[validation](vlra-t3-11-14-acceptance/validation.md).

## 1. Kết luận

**Chưa đủ điều kiện nghiệm thu toàn tuần7 hoặc G4.** T3-11 đạt hành vi idempotency;
T3-12 đạt UI/mock local, còn nguồn/hiệu năng thật. T3-13 đã có công cụ chia tập,
chờ nguồn150; T3-14 chưa có demo live và phê duyệt G4. Không sửa app để đổi kết quả.

Phân công T3-13 được người dùng chốt29/10: Team1 bổ sung đủ150 câu, Team2 kiểm
chứng; Team3 chỉ chia90 Dev/60 Test. Không tự tạo/review/phê duyệt hoặc freeze.
Team3 vẫn tổ chức demo theo T3-14 sau bàn giao. Công cụ T3-13 mới nằm trong worktree;
phần source ứng dụng dùng để nghiệm thu các mục khác vẫn không đổi.

## 2. Expected / Actual từng task

| Task | Expected / DoD | Actual29/10 | Trạng thái |
| --- | --- | --- | --- |
| T3-11 | IDEM01–12, concurrent requests không tạo trùng, snapshot replay không gọi lại AI |3 suite44 test đã PASS29/10; hash source khớp, đủ12 tình huống,32 ca store có16 PostgreSQL thật; đối chiếu matrix §3 | Đạt hành vi/đủ điều kiện chốt kỹ thuật |
| T3-12 | Viewer đúng ID/version/nguyên văn,404, nguồn an toàn, responsive và<1s |7 kiểm tra Viewer hiệu lực đạt;360/768px không tràn;20 click→DOM ready p95=54.30ms local mock. LinkHTTPS/_blank/rel đạt với fixture; chưa nguồn nhà nước/article thật | Đạt phần UI/mock; còn chờ nghiệm thu dữ liệu/hiệu năng thật |
| T3-13 | Phân công mới: Team1 đủ150, Team2 kiểm chứng, Team3 chia90 Dev/60 Test giữ nguyên record và thống kê/SHA256 | Công cụ stdlib đã có,13 test PASS trên Python3.12 và3.14; kiểm làm tròn/tái lập/no-overwrite/hash. Nguồn thật hiện50 bị từ chối exit2, không sinh tập v1 | Công cụ hoàn tất; chờ bộ150 để chia dữ liệu thật, không tự freeze |
| T3-14 | Demo live P0+citation/Viewer, insufficient và replay UUID, ảnh/video và3 team duyệt G4 |G2 mock đã đạt ở tuần6; factory thật cùng source/config còn503/404; không có demo/phê duyệt G4 trong lượt này | Chờ bàn giao liên team và tổ chức nghiệm thu live |

Không yêu cầu tạo class IdempotencyIntegrationTest trùng nếu behavioral suite đã
kiểm đủ. Không lấy benchmark mock hoặc sample5qa làm corpus/release Golden v1 thật.

## 3. Ma trận IDEM01–12

Dùng lại kết quả chạy thực tế29/10 của ChatStoreTests16, PostgresChatStoreTests16 và
StreamApiTests12 vì source hash không đổi; không tính thành44 test mới chạy.

| IDEM | Testcase bằng chứng | Kết quả |
| --- | --- | --- |
|IDEM-01|persistsPairReplaysWithAnotherRepositoryAndStableTimestamp; sseHasNumericCamelCaseIdsCanonicalCitationAndReplay|PASS evidence29/10|
|IDEM-02|historyOnlyAnsweredPairsAtMostFiveInChronologicalOrder|PASS evidence29/10|
|IDEM-03|pendingConflictBusyAndFailureReplayDoNotAddMessages; metaIsSentAfterAcceptanceWhilePendingAndBusyIsRejected|PASS evidence29/10|
|IDEM-04|persistsPairReplaysWithAnotherRepositoryAndStableTimestamp; sseHasNumericCamelCaseIdsCanonicalCitationAndReplay|PASS evidence29/10|
|IDEM-05|pendingConflictBusyAndFailureReplayDoNotAddMessages; upstreamErrorsTerminateStreamAndReplayLogicalHttpStatus|PASS evidence29/10|
|IDEM-06|pendingConflictBusyAndFailureReplayDoNotAddMessages|PASS evidence29/10|
|IDEM-07|pendingConflictBusyAndFailureReplayDoNotAddMessages|PASS evidence29/10|
|IDEM-08|persistsPairReplaysWithAnotherRepositoryAndStableTimestamp|PASS evidence29/10|
|IDEM-09|duplicateFirstRequestsAcrossRepositoryInstancesCreateOnePair|PASS evidence29/10|
|IDEM-10|differentRequestsForSameConversationAcrossInstancesAllowOnlyOnePending|PASS evidence29/10|
|IDEM-11|deleteRemovesContentAndKeepsOnlyTombstone|PASS evidence29/10|
|IDEM-12|queryAndDeleteShareDatabaseLock; completedReplayWaitsForDeleteLockAndDoesNotReturnDeletedSnapshot|PASS evidence29/10|

Không cần12 testcase lặp lại cùng một invariant;1 test có thể kiểm nhiều nhánh.
Recovery stale trực tiếp có test, nhưng chưa có job recovery định kỳ như baseline
ARCHITECTURE §6.1. Đây là backlog Team3, không gán Team1/2 hoặc tuyên bố12case đã
chứng minh scheduler. Lượt này chỉ nghiệm thu, chưa sửa code phần đó.

## 4. Viewer: kiểm mới và số đo

7 kiểm tra hiệu lực: nguyên văn/ID/HTTPS link an toàn; keyboard/focus/Escape;
360px/768px;20 lượt mở; UI404 cho document/article. Không uncaught JS exception.
Median=30.20ms, p95=54.30ms, max=89.20ms, đo click→DOM ready,
không giả lập mạng chậm. Không thay p95 nguồn luật thật bằng độ trễ fixture.

Lần đầu6/7 do helper DOM.click không đặt focus opener; raw evidence được giữ.
Chỉ chạy lại keyboard bằng click chuột CDP thực:1/1 PASS. Không sửa app để làm test
đạt; chi tiết và giới hạn tại [validation](vlra-t3-11-14-acceptance/validation.md).
Fixture nguồn example.com không chứng minh URL nhà nước/corpus thật đã hoạt động.

## 5. T3-13: phân chia Golden theo phân công mới

- Team1 bổ sung đủ150; Team2 kiểm chứng nội dung; Team3 chỉ chia. Quyết định29/10
  thay phần Team3 tự thu thập/phê duyệt/freeze đã ghi trước đây trong nhiệm vụ này.
- Công cụ: team3_fullstack/tools/split_golden_dataset.py,13 test PASS trên Python3.12
  và3.14 (cùng13 ca, không cộng thành26). Chia90/60 theo expected_status với seed;
  giữ toàn bộ field/ID, không trùng giữa2 tập, xuất SHA256/seed/phân bố.
- Output tương lai: golden_dataset_v1.dev.json, golden_dataset_v1.test.json và
  golden_dataset_v1.split.json. Báo cáo ghi split_only, không phải manifest freeze.
- File Phase1 hiện50 mẫu49/1 giữ nguyên hash; tool từ chối exit2, không tự tạo thêm
  câu hoặc sinh Dev/Test thật. Không cộng sample5qa vào nguồn v1.
- [Spec/plan/tasks](vlra-t3-13-golden-split/spec.md),
  [validation](vlra-t3-13-golden-split/validation.md),
  [lệnh chạy sau bàn giao](vlra-t3-13-golden-split/quickstart.md).
- T3-14 vẫn cần demo live/ảnh-video/xác nhận nhóm sau bàn giao; không suy gate đã
  được duyệt hoặc source đã đúng luật từ công cụ chia tập.

## 6. Evidence, môi trường và bước tiếp

Bộ [SpecKit/validation](vlra-t3-11-14-acceptance/validation.md) ghi lệnh/tên testcase,
expected/actual và nguồn evidence. JDK25, Node24.21, Python3.12 venv riêng, PostgreSQL18,
Edge headless. Database legal_rag_week7_20261029 trên55442; các port web test
15173/18043/18044/19242. JAR/source giữ nguyên, không build/test toàn app lại sau PASS.

Evidence ignored: backend/target/week7-acceptance-20261029/ gồm summary.json,
idempotency-evidence.json, XML3 suite, dataset-inventory.json, viewer/results.json,
viewer/viewer-timing.json, ảnh360/768, focus-rerun/viewer/focus-results.json,
process-cleanup.json, logs/helpers. Nguồn G2/live đã chạy29/10 được tham chiếu từ
week6-acceptance-20261029, không ghi thành phép thử mới của tuần7.
Đã dừng đúng tiến trình/cluster test audit mở, cả6 cổng test đóng. Không sửa .env,
app/test/schema/corpus/dataset hoặc code team khác; chưa commit/push.

Các chỉ tiêu Recall/Citation Correctness/Answer Quality trong đặc tả chung vẫn chưa
đo bằng model/dataset thật. Không gán toàn bộ benchmark các tuần sau thành điều kiện
mới cho từng task tuần7, cũng không coi G2 mock chứng minh chất lượng pháp lý.

**Việc cần làm tiếp:** nhận bàn giao live/article và nguồn150 từ Team1 sau Team2
kiểm chứng; Team3 chạy công cụ chia90/60, kiểm Viewer/hiệu năng thật, xử lý backlog
recovery theo baseline và tổ chức demo G4. Không tự review/freeze thay các team.
W7-05 và T008 của bộ task T3-13 giữ mở vì chưa có dữ liệu thật150.

Kiểm chứng công cụ T3-13 và evidence riêng: backend/target/t3-13-golden-split-20261029/.
Không chạy lại Maven/FE do không sửa app/config. Shared Phase1/corpus/validator giữ
nguyên hash. Người dùng đã yêu cầu commit/push đợt hồ sơ và công cụ lên nhánh Team3;
việc bàn giao code không thay xác nhận nghiệm thu live/G4.
