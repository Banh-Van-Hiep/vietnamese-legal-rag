# Kiểm thử tải 50/5 và định hướng sửa lỗi — VLRA-80

**Ngày:** 23/11/2026. **Kết luận:** chưa chốt nghiệm thu.

Code/test và cấu hình thử nghiệm bổ sung đã hoàn tác; giữ code hàng đợi đã merge. Số liệu dưới đây là kết quả đã đo trước hoàn tác, không phải kiểm chứng lại source sau hoàn tác.

## 1. Điều kiện đo

- 50 câu, 5 Locust users, hai warm-up riêng; UI → Java → Python RAG → Gemini, PostgreSQL test riêng.
- BM25-only, top_k=10, rerank=false, claims=false, fallback=false; một pipeline chạy, tối đa bốn request chờ. Deadline AI/Java/FE: 45/50/60 giây.
- R01–R08: **Gemini 3.5 Flash Lite**; R09: **Gemini 3.1 Flash Lite**. Máy Windows, 4 logical CPU, RAM 7,74 GiB.
- Gemini 3.5 Flash Lite được gọi qua alias `gemini-flash-lite-latest`; kiểm tra trực tiếp ngày 23/11/2026 trả `modelVersion=gemini-3.5-flash-lite`. Các lượt cũ chỉ lưu alias, không lưu `modelVersion` riêng.
- p95 API tính trên lượt hoàn tất, gồm thời gian chờ; không phải thời gian render UI. Các lượt khác cấu hình/thời điểm không dùng làm bằng chứng nhân quả.

## 2. Kết quả các lần chạy

| Lượt | Cấu hình | Hoàn tất/đã chạy | Lỗi hạn mức | Lỗi provider | Lỗi output | p95 API (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| M01 | Fixture | 50/50 | 0 | 0 | 0 | 0,527 |
| R01 | Gemini 3.5 Flash Lite, chưa pacing | Chưa chạy: warm-up lỗi | — | — | — | — |
| R02 | Gemini 3.5 Flash Lite, chưa pacing | 40/50 | 3 | 7 | 0 | 35,027 |
| R03 | Gemini 3.5 Flash Lite, chưa pacing | 33/50 | 16 | 1 | 0 | 23,288 |
| R04 | Gemini 3.5 Flash Lite, chưa pacing | 45/50 | 0 | 5 | 0 | 41,065 |
| R05 | Gemini 3.5 Flash Lite, chưa pacing | 45/50 | 3 | 1 | 1 | 33,935 |
| R06 | Gemini 3.5 Flash Lite, chưa pacing | 42/50 | 6 | 1 | 1 | 33,008 |
| R07 | Gemini 3.5 Flash Lite, 12/phút | 49/50 | 0 | 0 | 1 | 35,202 |
| R08 | Gemini 3.5 Flash Lite, 12/phút + schema | 46/50 | 0 | 2 | 2 | 35,896 |
| R09 | Gemini 3.1 Flash Lite, 12/phút + schema | 49/50 | 0 | 0 | 1 | 27,986 |

**R09 mới nhất:** 49/50 hoàn tất (42 `answered`, 7 `insufficient_context`), một lỗi (2%), không timeout. p50 **24,982 s**, p95 **27,986 s**. UI **2/2 PASS**; warm-up **2/2 PASS**; 42 lượt Viewer thành công.

Gemini: **54 attempt HTTP, tất cả 200**, không 429/503. Nhịp nhỏ nhất **5,000 s**, tối đa **12 lần/60 s**. DB: **50 receipt, 100 message, 49 completed, 0 pending**. Đã dừng tài nguyên test.

## 3. Lỗi, nguyên nhân và hướng sửa

| Nhóm lỗi | Bằng chứng | Nguyên nhân xác định / giới hạn bằng chứng | Hướng sửa đề xuất |
| --- | --- | --- | --- |
| Hạn mức Gemini | 28 lỗi cuối `LLMRateLimitError` ở R02–R06; bảng quota có đỉnh RPM 18/15 | Provider trả HTTP 429. Đã vượt RPM ở thời điểm bảng quota ghi nhận; log cũ chưa xác định từng lỗi thuộc RPM, TPM hay RPD | Kiểm soát nhịp mọi attempt, gồm retry; mức thử 12/phút có khoảng dự phòng so với 15/phút. Theo dõi quota; đổi key cùng project không tăng hạn mức |
| Provider không khả dụng | 17 lỗi cuối `LLMProviderError`; riêng R08 có 6 HTTP 503, trong đó hai query vẫn lỗi sau retry | R08 xác nhận 503 từ Google, không phải hàng đợi đầy: request đã lấy slot. Không có bằng chứng xác định nguyên nhân bên trong Google; các lượt cũ có thể gồm lỗi mạng hoặc 5xx | Phân biệt HTTP status với lỗi kết nối trong log; retry/backoff có giới hạn trong deadline 45 giây. Không tăng hàng đợi hoặc timeout để che lỗi provider |
| Output/citation | 6 lỗi output cuối qua các lượt. R09: `gold_006` → `CITATION_INVALID`, `citations`, HTTP public `UPSTREAM_INVALID_RESPONSE` | Gemini trả JSON đọc được nhưng vi phạm quan hệ status/citation. Parser yêu cầu `answered` có citation; `insufficient_context` không có citation/marker. Log chưa phân biệt nhánh nào bị vi phạm ở mẫu này | Ghi mã lý do riêng cho từng nhánh, kèm status/số citation/số marker; đối chiếu prompt và schema với validator. Giữ từ chối output sai, không tự vá citation |

**Chi tiết lỗi R09:** finish reason `STOP`, **92/2048 output token**, 332 ký tự phản hồi; không có dấu hiệu bị cắt vì hết token. Schema cấu trúc đã được bật nhưng không kiểm đủ quan hệ status/citation; tăng token hoặc chỉ đổi model không bảo đảm sửa lỗi này.

## 4. Thứ tự xử lý và kiểm tra lại

1. Bổ sung log lý do citation cụ thể; chạy lại `gold_006`, `gold_019`, `gold_030` để xác định nhánh sai trước khi sửa prompt/schema.
2. Khôi phục có chọn lọc pacing và chẩn đoán HTTP; giữ một worker/bốn chỗ chờ, deadline 45/50/60 giây và validator citation.
3. Chạy lại cùng bộ 50/5; báo đủ lượt lỗi, p95, HTTP status và DB pending. Chốt ngưỡng lỗi với nhóm trước khi nghiệm thu; bài BM25-only không thay kiểm chứng Hybrid/G5.

Dữ liệu từng request, warm-up, cấu hình và hash source thử nghiệm: [nfr07-concurrency-results.json](nfr07-concurrency-results.json). R01 dừng trước tải; không tính là 0% lỗi. Fixture và các ca kiểm tra riêng không cộng vào tải thật.

Tham chiếu quota: [Google Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).
