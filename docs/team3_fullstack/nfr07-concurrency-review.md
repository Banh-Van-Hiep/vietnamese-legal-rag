# Giới hạn xử lý đồng thời của AI Service và bài tải NFR-07

- **Ngày đối chiếu:** 20/11/2026.
- **Nguồn hiện trạng:** source workspace `440296c`, phục vụ trao đổi Team 3 ↔ Team 2 về [VLRA-80](https://banhvanhiep.atlassian.net/browse/VLRA-80).
- **Trạng thái:** Phân tích tĩnh và đề xuất thảo luận; chưa phải thiết kế đã phê duyệt hoặc kết quả benchmark.
- **Quyết định kiểm thử đã xác nhận:** Giữ 50 query / 5 người dùng đồng thời, giữ slot hiện hành, tính mọi 503 vào tỷ lệ lỗi. Cách kết luận NFR-07 dưới tải này vẫn chờ nhóm chốt; không thay bài tải bằng chạy tuần tự.

## 1. Vấn đề cần thống nhất

VLRA-80 yêu cầu đo p50/p95 trên 50 truy vấn hợp lệ với 5 người dùng đồng thời sau warm-up. [AGENTS.md §2.3](../../AGENTS.md) quy định chỉ một lượt suy luận tại một thời điểm. [ADR 0004](../decisions/0004-single-llm-slot.md) còn **Proposed**, chưa chốt hướng xử lý khác biệt này.

[ARCHITECTURE §8.1](../ARCHITECTURE.md) quy định NFR-07 p95 qua `RAGPipeline.query` ≤ 45 giây và chuỗi timeout AI 45 s < Java 50 s < Frontend 60 s. Thời gian hàng đợi, HTTP và hiển thị UI cần ghi riêng để không nhầm phạm vi đo.

**50/5** là tổng 50 query từ 5 người dùng/session độc lập, tối đa 5 lượt đang xử lý; không phải gửi cả 50 cùng lúc. Mỗi người gửi lượt tiếp theo sau khi lượt trước kết thúc. Bài tải không yêu cầu bổ sung đăng nhập/tài khoản vào MVP.

## 2. Hành vi hiện tại trong mã nguồn

| Vị trí | Hành vi từ source | Hệ quả |
| --- | --- | --- |
| [api/app.py](../../team2_rag/api/app.py), `create_app` / `query` | `threading.Lock()` và `acquire(blocking=False)` trước `active.query(...)` | Khóa bao quanh toàn pipeline query, không chỉ LLM. Lượt đến lúc bận bị từ chối ngay, không xếp hàng |
| Cùng file, hàm `run` | Nhả khóa trong `finally` khi công việc thực sự kết thúc | HTTP timeout không tự giải phóng slot trong lúc thread còn chạy |
| Cùng file, chờ kết quả | `asyncio.to_thread`, `asyncio.shield`, `asyncio.wait_for` | Bảo vệ khỏi việc liên tục tạo thêm công việc nền sau timeout |
| [pipeline.py](../../team2_rag/pipeline.py), `query` | Tạo deadline khi bắt đầu pipeline, tính thời gian còn lại sau retrieval/rerank | Thêm hàng đợi ngoài pipeline không tự trừ thời gian chờ vào deadline hiện tại |
| [llm/service.py](../../team2_rag/llm/service.py), `generate` | Tạm sửa `self.provider.timeout_seconds`, sau đó phục hồi | Nếu dùng chung provider song song, có nguy cơ ghi đè timeout của nhau; đây là rủi ro tĩnh, chưa phải lỗi race đã tái hiện |
| [application-rag.properties](../../team3_fullstack/backend/src/main/resources/application-rag.properties) | Java có `app.chat.workers=8`, query timeout 50 s | Worker Java và slot Python là hai giới hạn khác nhau; tăng worker Java không tự tăng khả năng xử lý RAG |

Slot thuộc từng instance/process AI Service, không phải toàn deployment. Tăng số process có thể tăng tổng slot nhưng cũng nhân bản model/tài nguyên và dùng chung quota provider.

Health, ready và Article Viewer không lấy khóa query này. Đây là lựa chọn triển khai bảo vệ tài nguyên, không phải RAG hoặc Gemini bắt buộc chỉ phục vụ một người dùng.

## 3. Ảnh hưởng đến bài tải 50/5

- Khi nhiều query cùng đến một instance, một lượt lấy khóa; các lượt khác có thể nhận **HTTP 503 / LLM_UNAVAILABLE / retryable=true**. Số lỗi phụ thuộc lịch đến và thời gian xử lý, không mặc định mọi đợt luôn có bốn lỗi.
- Java ánh xạ lỗi này sang public `SERVICE_UNAVAILABLE`. Không đổi lỗi kỹ thuật thành `insufficient_context`; thiếu context hợp lệ vẫn là kết quả nghiệp vụ completed.
- Lỗi 503 trả nhanh có thể làm phân vị toàn bộ phản hồi thấp. Cần báo riêng latency thành công, thời gian kết thúc lượt lỗi, tỷ lệ lỗi/timeout và số mẫu; không kết luận đạt chỉ vì p95 thấp.
- Bài 50/5 vẫn dùng để quan sát hành vi dưới tải; chưa tự chứng minh xử lý thành công năm query đồng thời hoặc đạt đầy đủ mục tiêu nghiệm thu.

## 4. Các phương án cân nhắc

| Phương án | Lợi ích | Giới hạn |
| --- | --- | --- |
| Giữ một slot, từ chối ngay | Giới hạn công việc chặt, ít thay đổi | Nhiều 503 khi tải chồng lấp |
| Một worker và hàng đợi giới hạn | Hấp thụ đợt request ngắn thay vì từ chối ngay | Chờ nối tiếp có thể vượt deadline; không tăng năng lực xử lý |
| N lượt chạy và hàng đợi giới hạn | Cân bằng song song với bảo vệ tài nguyên | Cần an toàn đồng thời, deadline chung, kiểm quota và benchmark |
| Nhiều process/instance | Có thể cô lập trạng thái provider giữa process | Tăng RAM/model/index, cần kiểm tổng tải/quota; chưa được thống nhất |

Ví dụ minh họa, không phải số đo: năm query cùng đến, một worker mất đều 15 s/query thì thời gian hoàn tất khoảng 15/30/45/60/75 s, chưa tính overhead. Hàng đợi không bảo đảm deadline. Nếu query rất nhanh, một worker có thể phục vụ tải tốt hơn; cần đo thực tế.

## 5. Đề xuất thử nghiệm có kiểm soát

Đề xuất để nhóm thảo luận: **concurrency giới hạn kết hợp hàng đợi ngắn**. Có thể bắt đầu thử **N=2**, tối đa **3 lượt chờ**, rồi đo đúng bài 50/5. Các con số này là điểm thử nghiệm, không phải cấu hình chuẩn hay cam kết đạt NFR-07.

```text
5 người dùng/session → kiểm request và giới hạn tiếp nhận
                     → hàng đợi ngắn có hạn chờ
                     → tối đa N công việc RAG thực sự đang chạy
                     → validate → JSON nội bộ → Java/SSE → UI
```

Các điều kiện cần xem xét trước khi áp dụng:

1. **Deadline tính cả chờ.** Tính từ tiếp nhận tại AI Service; chờ + chạy nằm trong ngân sách AI 45 s. Pipeline/LLM nhận thời gian còn lại, không cấp thêm 45 s khi rời hàng đợi. Báo riêng queue wait, pipeline time và toàn tuyến.
2. **Không tích tụ sau timeout.** Chỉ chạy khi có slot thật, không tạo vô hạn thread chờ slot. Request quá hạn khi chưa chạy phải rời hàng đợi. Công việc đã chạy giữ slot đến lúc thật sự kết thúc dù HTTP đã timeout; không giả định cancel coroutine sẽ dừng thread/provider.
3. **An toàn trạng thái theo request.** Xử lý nguy cơ sửa `provider.timeout_seconds` dùng chung; rà soát model fallback/metadata và khả năng gọi song song của retrieval/reranker/client. Có thể cân nhắc timeout theo lời gọi hoặc cô lập provider theo worker; thiết kế cụ thể cần Team 2 đánh giá.
4. **Giới hạn mọi tầng.** Hàng đợi đầy từ chối có kiểm soát; hết hạn trả timeout theo contract đã thống nhất. Không tự thêm mã lỗi/status/endpoint public; thay mapping phải thống nhất liên team.
5. **Tôn trọng quota/tài nguyên.** Tăng N không tăng quota provider. Gemini xét RPM/TPM/RPD, quota theo project chứ không theo từng API key; cần kiểm hạn mức thực tế và ghi rate-limit error. [Tài liệu Gemini](https://ai.google.dev/gemini-api/docs/rate-limits).
6. **Giữ idempotency/hội thoại.** Năm session dùng hội thoại độc lập; giữ một pending mỗi hội thoại, không retry ngầm hoặc đổi UUID để che lỗi. Kết quả muộn không ghi đè lượt đã recovery.

Tăng N không bảo đảm tăng thông lượng nếu CPU/GPU/model hoặc quota là nút thắt. Chọn cấu hình theo tỷ lệ thành công, p50/p95 và tài nguyên, không chỉ số request được nhận.

## 6. Bằng chứng cần có nếu chọn thay đổi

| Nhóm kiểm chứng | Nội dung cần xác nhận |
| --- | --- |
| Giới hạn công việc | Tác vụ thực chạy không vượt N, lượt chờ không vượt giới hạn; lượt bị từ chối không tạo công việc mới |
| Deadline và cleanup | Chờ + chạy không cấp lại ngân sách; hết hạn trước chạy không gọi AI; timeout khi chạy không nhả slot sớm; kết thúc/lỗi nhả slot đúng |
| An toàn đồng thời | Request ID/timeout khác nhau không làm lẫn cấu hình/kết quả/provider metadata; lỗi một lượt không làm kẹt slot khác |
| Contract và DB | HTTP/SSE/error đúng schema, receipt/state nhất quán, không mất/trùng message/citation; recovery pending > 60 s và loại kết quả muộn |
| Tải thực | Cùng tập 50 query, 5 người dùng, warm-up/snapshot; raw result đủ từng lượt; p50/p95, lỗi/timeout, quota, config/phần cứng rõ |

Fixture kiểm giới hạn/hàng đợi/timeout có thể tái lập. Năng lực RAG thật cần dịch vụ/model/index thực tế; mock không thay benchmark live. Ngưỡng tỷ lệ lỗi chấp nhận và cách chốt NFR-07 cần nhóm xác nhận, không tự đặt trong báo cáo này.

## 7. Quyết định còn chờ và ranh giới phối hợp

- Giữ một slot chính thức hay cho phép thử N slot + hàng đợi?
- Nếu thử: giới hạn chạy/chờ, deadline, điều kiện quá tải và cấu hình được chọn sau đo là gì?
- Với tải 50/5: phạm vi latency và tỷ lệ lỗi nào được chấp nhận để nghiệm thu?
- Sau khi chốt, cập nhật đồng bộ ADR 0004, AGENTS, ARCHITECTURE và test; đề xuất này không tự thay baseline.

**Team 2** phụ trách đánh giá thiết kế AI Service/pipeline/provider và an toàn đồng thời trong phạm vi nhóm duyệt. **Team 3** giữ bài 50/5, thu kết quả public API/UI, kiểm state/idempotency/recovery và PostgreSQL. Báo cáo không tạo thêm Jira task hoặc cho phép tự sửa code Team 2.

Hiện tại giữ slot như đã thống nhất cho VLRA-80, ghi lỗi thực tế và chờ cách nghiệm thu được chốt. Chưa chạy bài tải hoặc triển khai phương án mới trong lượt lập báo cáo.
