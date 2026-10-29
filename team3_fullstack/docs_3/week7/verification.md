# Biên bản nghiệm thu Team 3 — Tuần 7

**Ngày kiểm chứng:** 30/10/2026. **Nhiệm vụ:** [tasks.md](tasks.md).

## 1. Kết luận

**Chưa đạt nghiệm thu G4 của tuần 7.**

T3-11 đạt idempotency; T3-12 đạt Viewer với mock; công cụ T3-13 đạt kiểm thử.
Còn thiếu kiểm chứng Viewer thật, bộ150 câu đã kiểm chứng để chia90/60 và
ba kịch bản demo live được các team nghiệm thu theo T3-14.

## 2. Expected / Actual từng task

| Task | Expected / DoD | Actual30/10 | Trạng thái |
| --- | --- | --- | --- |
| T3-11 | IDEM01–12, concurrent requests không tạo trùng, snapshot replay không gọi lại AI | 3 suite44 test chạy trong package125/125, đủ12 tình huống;32 ca store gồm16 PostgreSQL thật; đối chiếu matrix §3 | Đạt hành vi/đủ điều kiện chốt kỹ thuật |
| T3-12 | Viewer đúng ID/version/nguyên văn,404, nguồn an toàn, responsive và<1s | 7 kiểm tra Viewer hiệu lực đạt;360/768px không tràn;20 click→DOM ready p95=56.0ms local mock. LinkHTTPS/_blank/rel đạt với fixture; chưa nguồn nhà nước/article thật | Đạt phần UI/mock; còn chờ nghiệm thu dữ liệu/hiệu năng thật |
| T3-13 | Phân công mới: Team1 đủ150, Team2 kiểm chứng, Team3 chia90 Dev/60 Test giữ nguyên record và thống kê/SHA256 | Công cụ stdlib đã có,13 test PASS trên Python3.12.15; kiểm làm tròn/tái lập/no-overwrite/hash. Nguồn thật hiện50 bị từ chối exit2, không sinh tập v1 | Công cụ hoàn tất; chờ bộ150 để chia dữ liệu thật, không tự freeze |
| T3-14 | Demo live P0+citation/Viewer, insufficient và replay UUID, ảnh/video và3 team duyệt G4 | Luồng mock đạt; runtime thật còn503/404; chưa đủ demo và xác nhận G4 | Chờ bàn giao liên team và tổ chức nghiệm thu live |

## 3. Ma trận IDEM01–12

44 test store/HTTP đạt, gồm16 H2,16 PostgreSQL và12 HTTP/SSE.

| IDEM | Testcase bằng chứng | Kết quả |
| --- | --- | --- |
| IDEM-01 | persistsPairReplaysWithAnotherRepositoryAndStableTimestamp; sseHasNumericCamelCaseIdsCanonicalCitationAndReplay | Đạt |
| IDEM-02 | historyOnlyAnsweredPairsAtMostFiveInChronologicalOrder | Đạt |
| IDEM-03 | pendingConflictBusyAndFailureReplayDoNotAddMessages; metaIsSentAfterAcceptanceWhilePendingAndBusyIsRejected | Đạt |
| IDEM-04 | persistsPairReplaysWithAnotherRepositoryAndStableTimestamp; sseHasNumericCamelCaseIdsCanonicalCitationAndReplay | Đạt |
| IDEM-05 | pendingConflictBusyAndFailureReplayDoNotAddMessages; upstreamErrorsTerminateStreamAndReplayLogicalHttpStatus | Đạt |
| IDEM-06 | pendingConflictBusyAndFailureReplayDoNotAddMessages | Đạt |
| IDEM-07 | pendingConflictBusyAndFailureReplayDoNotAddMessages | Đạt |
| IDEM-08 | persistsPairReplaysWithAnotherRepositoryAndStableTimestamp | Đạt |
| IDEM-09 | duplicateFirstRequestsAcrossRepositoryInstancesCreateOnePair | Đạt |
| IDEM-10 | differentRequestsForSameConversationAcrossInstancesAllowOnlyOnePending | Đạt |
| IDEM-11 | deleteRemovesContentAndKeepsOnlyTombstone | Đạt |
| IDEM-12 | queryAndDeleteShareDatabaseLock; completedReplayWaitsForDeleteLockAndDoesNotReturnDeletedSnapshot | Đạt |

Recovery định kỳ còn thiếu; hiện có recovery khi khởi động hoặc có thao tác gọi vào.

## 4. Viewer: kiểm tra và số đo

| Kiểm tra | Kết quả |
| --- | --- |
| Nội dung/ID và link HTTPS, target/rel an toàn | Đạt với fixture |
| Focus, Tab loop và Escape | Đạt |
| Viewport360px/768px | Không tràn ngang |
| Document/article404 | Hiển thị đúng, không thay nội dung |
| 20 lượt mở: median / p95 / max | 39.2 /56.0 /91.5 ms, đo click→DOM ready với mock |
| Tổng số ca | 7/7,0 lỗi JavaScript chưa xử lý |

## 5. T3-13: phân chia Golden

- **Team1:** bổ sung150 câu. **Team2:** kiểm chứng nội dung. **Team3:** chia90 Dev/60 Test.
- Công cụ giữ nguyên record/ID, phân tầng theo expected_status, tái lập theo seed và xuất SHA-256.
- 13/13 test đạt trên Python3.12.15. Bộ hiện tại50 câu bị từ chối đúng yêu cầu150.
- Output: golden_dataset_v1.dev.json, golden_dataset_v1.test.json và golden_dataset_v1.split.json.
- Còn chờ bộ150 đã kiểm chứng để thực hiện chia thật.

[Kiểm chứng công cụ](vlra-t3-13-golden-split/validation.md).

## 6. Bằng chứng, môi trường và bước tiếp

Môi trường: JDK25, Node24.21, Python3.12, PostgreSQL18 và Edge headless.
Kết quả tại `backend/target/final-acceptance-20261030/`: junit/, viewer/results.json,
viewer/viewer-timing.json, ảnh360/768, golden-split-tests.log và summary.json.

1. **Team1/2:** bàn giao query/article thật và Golden150 đã kiểm chứng.
2. **Team3:** chia90/60, kiểm Viewer/hiệu năng thật và tổ chức3 demo live của G4.
3. **Team3:** bổ sung job recovery định kỳ theo baseline.
4. **Nhóm:** xác nhận ảnh/video và nghiệm thu G4.

[Kiểm chứng idempotency/Viewer](vlra-t3-11-14-acceptance/validation.md).
