# 0004. Mỗi lúc chỉ một lượt gọi LLM trong AI service

- Ngày: 2026-11-16 (ghi lại) · Trạng thái: **Proposed — cần Team 2, Team 3 và nhóm trưởng chốt**
- Nguồn: bất biến số 3 trong `AGENTS.md`; `team2_rag/api/app.py` (`slot = threading.Lock()`); test NFR-08 trong `team2_rag/tests/`.

## Bối cảnh
AI service dùng một `threading.Lock()` không chờ. Khi đang có một lượt suy luận, request thứ hai nhận ngay HTTP 503 `LLM_UNAVAILABLE` (`retryable: true`).
Google Doc v2.0 lại đặt điều kiện đo NFR-07 là "50 query hợp lệ, 5 người dùng đồng thời". Với một slot, 4 trên 5 request đồng thời sẽ nhận 503.

## Các phương án
1. **Giữ một slot** (hiện trạng). Điều kiện đo NFR-07 đổi thành chạy tuần tự, và đo riêng tỷ lệ 503 khi có tải đồng thời. Phù hợp quota provider miễn phí và máy demo yếu.
2. **Cho N slot hoặc một hàng đợi có giới hạn**, ví dụ N = 2 và hàng đợi 5 với deadline chung 45 s. Đáp ứng điều kiện đo nguyên bản nhưng tốn quota và phải kiểm lại chuỗi timeout NFR-08.
3. **Một slot và hàng đợi có giới hạn** (Team 3 nêu trong `docs/team3_fullstack/nfr07-concurrency-review.md`). Vẫn chỉ 1 lượt chạy, thêm tối đa 4 lượt chờ; hàng đầy thì 503, chờ quá hạn thì 504.

## Đề xuất của Team 2 (22/11/2026)
Chọn phương án 3, đã có code (`create_app(max_waiting=4)`):
- Đủ chỗ cho 5 người dùng đồng thời của VLRA-80 mà không cần thêm RAM hay quota Gemini chạy song song.
- Giữ an toàn chỗ `llm/service.py` sửa tạm `provider.timeout_seconds` dùng chung; chỗ này chỉ đúng khi mỗi lúc một lượt chạy.
- Thời gian chờ nằm trong hạn 45 giây (deadline tính lúc request đến), nên chuỗi NFR-08 45 < 50 < 60 giữ nguyên, không thêm mã lỗi.
- Giới hạn: không tăng năng lực xử lý. Gemini chậm thì lượt cuối hàng có thể nhận 504. Thứ tự vào slot không bảo đảm FIFO.

Trạng thái vẫn là Proposed đến khi Team 3 và nhóm trưởng đồng ý.

## Cần chốt
Nhóm chọn một phương án, đổi trạng thái thành Accepted, rồi sửa cho khớp `AGENTS.md`, `docs/ARCHITECTURE.md` mục 8.1 và báo cáo NFR-07 của Team 2.
