# Validation — nghiệm thu tuần7, VLRA-T3-11–14

**Ngày:**29/10/2026. [Spec](spec.md), [plan](plan.md), [tasks](tasks.md),
[analyze](analysis.md). HEAD `d67f36acf615956728838a005ec8758d13a9a74a`, develop `eea5604251afd4d8605fed510d6bf4de31d629bb` đã fetch.
Bảo toàn3 file tuần6 chưa commit; không sửa code/test/schema/corpus/dataset các team.

## Expected / Actual

| AC | Actual | Kết luận |
| --- | --- | --- |
| AC11 | Hash source khớp evidence tuần6;3 suite store H2/PostgreSQL/HTTP tổng44 PASS đã chạy29/10, đủ12 tình huống IDEM | Đạt hành vi idempotency; không tính44 là chạy mới |
| AC12 |7 kiểm tra Viewer hiệu lực đạt,0 exception;360/768px không tràn; nguyên văn/HTTPS target+rel và404 đúng;20 lượt mở DOM p95=54.30ms, median=30.20ms | Đạt UI/mock local; chưa đo nguồn/hiệu năng corpus thật |
| AC13 | T3-13 theo phân công mới chỉ chia150→90/60; tool13test đã đạt, Phase1 thật50 bị từ chối và giữ nguyên | Công cụ sẵn sàng; chạy dữ liệu thật chờ Team1/2, không tự freeze |
| AC14 | Evidence factory thật29/10 ready/query503, article404; chưa có buổi demo live/ảnh-video/phê duyệt G4 | Chờ bàn giao và nghiệm thu chung, chưa đạt G4 |

## Ma trận IDEM và evidence giữ nguyên

Source hash khớp trước khi dùng lại; XML3 suite đã sao chép vào evidence tuần7 để
không bị Maven clean ghi đè. Các testcase dùng chung nhiều nhánh, không tạo thêm12
case trùng chỉ để đúng tên lớp. Kiểm cả32 test store (16H2/16PostgreSQL) và12 HTTP.

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

IDEM09 kiểm race khi lượt đầu còn pending; nếu completed trước khi request sau quan
sát receipt thì replay đúng cũng hợp lệ theo thiết kế hội thoại. Không suy direct
recover test chứng minh đã có recovery scheduler định kỳ; source chưa có job này.

## Probe Viewer mới

- V01: đúng nội dung/ID fixture và external link HTTPS, target_blank/noopener/noreferrer.
- V02: focus trong drawer, Tab loop, Escape đóng và trả focus về citation.
- V03/V04: viewport360px/768px không tràn ngang drawer/trang; có ảnh tương ứng.
- V05:20 click→article DOM ready, p95=54.30ms, max=89.20ms.
- V06/V07: UI article/document404, không hiện nội dung thay thế.

Lần đầu6/7: V02 không thấy focus trở lại vì helper mở drawer bằng DOM.click() mà
không đặt focus opener; không phải bằng chứng lỗi của thao tác người dùng thật.
Giữ nguyên raw results.json. Chỉ chạy lại V02 bằng CDP mousePressed/mouseReleased:
1/1 PASS, Tab loop/Escape/focus restore đạt. Không sửa ứng dụng hoặc xóa evidence lỗi
helper. Summary hợp nhất6 ca đạt ban đầu với1 ca keyboard đã kiểm lại thành7 ca hiệu lực.

Timing là DOM ready, không phải visual paint/FPS, mạng3G, p95production hoặc nguồn
nhà nước thật. Java gọi FastAPI HTTP mock; fixture example.com không là chứng cứ
đã mở URL cơ quan nhà nước. Chưa kiểm p95<200ms Article Store thật của Team1.

## Môi trường, lệnh và giới hạn

Windows/JDK25/Node24.21/Python3.12/PostgreSQL18/Edge headless. Database test riêng
legal_rag_week7_20261029, port55442; FE15173/Java18043/mock18044/CDP19242.
[Quickstart](quickstart.md) ghi cách tái lập suites khi code đổi. Lượt này dùng JAR
đã package tuần6 đúng source hash; không build/test lại toàn bộ app khi chưa đổi code.
Helper ignored chạy bằng Python venv kiểm thử riêng; Node CDP probe với env FE_URL/
BE_URL/CDP_URL/EVIDENCE_DIR, không profile cá nhân hoặc secret. Không gọi provider thật.

Evidence ignored backend/target/week7-acceptance-20261029/:
summary.json, dataset-inventory.json, idempotency-evidence.json, XML3 suite,
viewer/results.json, viewer/viewer-timing.json, viewer/viewer-360.png/768.png,
focus-rerun/viewer/focus-results.json, process-cleanup.json, focus-rerun/process-cleanup.json,
logs và helper. Cả6 cổng audit đã đóng; dừng đúng tiến trình/cluster audit mở.
Dataset giữ nguyên hash. Không tự commit/push hoặc xác nhận nhóm đã phê duyệt.

## Phần còn lại

Team1/2 tự hoàn thiện runtime/index/article/review nội dung. Team3 chỉ chia150→90/60 theo phân công T3-13 mới; tích hợp Viewer và tổ chức G4 sau
bàn giao vẫn thuộc các task khác. Không tự tạo/review/freeze Golden. Recovery scheduler là backlog
Team3 theo baseline, không được coi đã đạt từ direct recover hoặc12 tình huống IDEM.

Đã xem ảnh360/768 và kiểm 9 file Markdown/34 tham chiếu local, không lỗi.
Diff --check PASS; W7-01–04 hoàn thành theo evidence, W7-05 còn mở.

T3-13 đã có [validation công cụ riêng](../vlra-t3-13-golden-split/validation.md);
Team1 bổ sung150, Team2 kiểm chứng, Team3 chỉ chia. Số liệu freeze thiếu trong
kiểm kê cũ là tình trạng release chung, không còn là nhiệm vụ tool Team3 tự xác nhận.
