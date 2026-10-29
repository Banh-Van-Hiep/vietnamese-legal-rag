# Validation — tuần7, T3-11–14

**Ngày kiểm chứng:**30/10/2026. **Kết quả:** idempotency đạt; Viewer/tool Golden đạt phần độc lập; G4 còn mở.

## Expected / Actual

| AC | Actual | Kết luận |
| --- | --- | --- |
| AC11 | 3 suite store H2/PostgreSQL/HTTP tổng44 PASS trong package125/125, đủ12 tình huống IDEM | Đạt hành vi idempotency;44 là nhóm con của125 |
| AC12 | 7 kiểm tra Viewer hiệu lực đạt,0 exception;360/768px không tràn; nguyên văn/HTTPS target+rel và404 đúng;20 lượt mở DOM p95=56.0ms, median=39.2ms | Đạt UI/mock local; chưa đo nguồn/hiệu năng corpus thật |
| AC13 | T3-13 theo phân công mới chỉ chia150→90/60; tool13test đã đạt, Phase1 thật50 bị từ chối và giữ nguyên | Công cụ sẵn sàng; chạy dữ liệu thật chờ Team1/2, không tự freeze |
| AC14 | Evidence factory thật30/10 ready/query503, article404; chưa có buổi demo live/ảnh-video/phê duyệt G4 | Chờ bàn giao và nghiệm thu chung, chưa đạt G4 |

## Ma trận IDEM và bằng chứng

44 test gồm16 H2,16 PostgreSQL và12 HTTP/SSE đạt.

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

## Kiểm tra Viewer

| Ca | Nội dung | Kết quả |
| --- | --- | --- |
| V01 | Nguyên văn/ID fixture, nguồn HTTPS và rel an toàn | Đạt |
| V02 | Focus, Tab loop và Escape trả focus | Đạt |
| V03 | Viewport360px | Không tràn ngang |
| V04 | Viewport768px | Không tràn ngang |
| V05 | 20 lượt click→DOM ready | Median39.2ms; p95=56.0ms; max91.5ms với mock |
| V06 | Article404 | Đúng thông báo, không thay nội dung |
| V07 | Document404 | Đúng thông báo, không thay nội dung |

## Môi trường và bằng chứng

JDK25, Node24.21, Python3.12, PostgreSQL18, Edge headless và FastAPI HTTP mock.

Bằng chứng tại
`backend/target/final-acceptance-20261030/`, gồm kết quả, ảnh360/768 và số đo Viewer.

## Phần còn lại

1. **Team1/2:** bàn giao query/article thật và Golden150 đã kiểm chứng.
2. **Team3:** chia90/60, kiểm Viewer thật và tổ chức demo G4.
3. **Team3:** hoàn thiện recovery định kỳ theo baseline.

[Kiểm chứng công cụ chia Golden](../vlra-t3-13-golden-split/validation.md) ·
[Nghiệm thu tuần7](../verification.md).
