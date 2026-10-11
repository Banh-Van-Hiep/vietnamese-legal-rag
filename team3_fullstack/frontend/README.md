# Frontend Team 3

React + TypeScript + Vite, CSS thuần (không dùng thư viện UI). Gọi backend qua API Team 3 v1.2
([docs/team3_fullstack/team3.md](../../docs/team3_fullstack/team3.md)).

## Chạy

```bash
cd team3_fullstack/frontend
cp .env.example .env        # đặt VITE_API_URL nếu backend không ở http://localhost:8080
npm ci
npm run dev                 # http://localhost:5173
npm run build               # kiểm tra kiểu + build
```

Backend mock (cổng 8080, cho phép origin `http://localhost:5173`): xem
[quickstart T02](../../specs/002-t02-mock-api/quickstart.md). Backend lưu trong bộ nhớ, **mất dữ liệu khi khởi động lại**.

## Các trang

| Đường dẫn | Chức năng |
| --- | --- |
| `/` | Hỏi đáp, hội thoại mới |
| `/c/:conversationId` | Mở lại hội thoại đã lưu |
| `/search` | Tra cứu (khung): tìm trong vài mục mẫu, chưa có API Search |
| `/documents/:documentId/articles/:articleId` | Nguyên văn điều luật, mở và tải lại được |
| `/try-backend` | Trang thử backend tạm của Team 3, không thuộc UI chính thức |

Bấm số tham chiếu `[C1]` trong câu trả lời hoặc nút "Xem nguyên văn điều luật" để mở điều luật ở ngăn bên phải
mà không rời hội thoại.

## Hành vi cần biết

- Câu hỏi đầu tiên: FE tạo hội thoại (`POST /conversations`, tên = câu hỏi, tối đa 100 ký tự) rồi gửi `POST /query`
  kèm `conversation_id`. Làm vậy để thanh bên không toàn "Hội thoại mới"; contract cho phép cách này.
- Mỗi lượt có `client_request_id` UUID v4 mới. Chặn câu hỏi rỗng, quá 2000 ký tự và gửi trùng khi đang chờ.
- **Thử lại:** mất kết nối hoặc quá 60 giây (chưa biết server đã xử lý chưa) → gửi lại *đúng* `client_request_id`.
  Server đã báo lỗi (ví dụ 503) → hỏi lại bằng ID mới, thành một lượt mới trong lịch sử.
- `insufficient_context` hiện là thông báo "Chưa đủ căn cứ", tách khỏi lỗi hệ thống.
- Nhãn "Dữ liệu thử nghiệm" hiện khi `VITE_MOCK_MODE` khác `false`.
- Mục "Điều 404" trong trang tra cứu cố ý không có ở backend, để thử đường "không tìm thấy".

## Giới hạn

- Chưa có test tự động trong repo. Luồng đã được kiểm thử bằng trình duyệt tự động ngoài repo (xem báo cáo bàn giao).
- Chưa cấu hình nginx cho tải lại các route con trong Docker (`Dockerfile` hiện chỉ phục vụ file tĩnh);
  `npm run dev` và `npm run preview` tải lại được.
- Không có streaming, đăng nhập, đính kèm tệp: backend chưa hỗ trợ.
