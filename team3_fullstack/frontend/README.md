# Frontend Team 3

React + TypeScript + Vite + **Tailwind CSS v4** (plugin `@tailwindcss/vite`, không cần file cấu hình riêng).
Gọi backend qua API Team 3 v1.2 ([docs/team3_fullstack/team3.md](../../docs/team3_fullstack/team3.md)).

## Style

- Màu, font và hiệu ứng (đóng dấu, chấm chờ, ngăn trượt) khai báo một lần ở khối `@theme` trong
  [src/styles/global.css](src/styles/global.css); mỗi biến `--color-*` thành class như `bg-ink-900`, `text-muted`, `border-line`.
  Không còn CSS viết tay cho từng thành phần: style nằm ngay trong `className`.
- Đoạn lặp lại được gom thành thành phần hoặc hằng số: `Notice` (lỗi / thông tin), `IconButton`, và
  `components/common/classes.ts` (thẻ căn cứ, liên kết "Xem nguyên văn điều luật").
- Dùng cỡ chữ dạng `text-[14px]`, không dùng `text-sm`/`text-lg`: class có tên của Tailwind đặt luôn chiều cao dòng
  và làm lệch bố cục so với thiết kế (body dùng line-height 1.6).
- Điểm ngắt màn hình dùng `max-[860px]:` (thanh bên thành ngăn trượt) và `max-[600px]:` (điện thoại).
- `data-testid` trên các phần tử chính (`msg-assistant`, `suggestion`, `notice-error`…) là móc cho kiểm thử tự động,
  không phải style. Đừng xóa khi sửa giao diện.
- Trang thử `/try-backend` của Team 3 vẫn dùng CSS riêng ở `styles/backend-playground.css`. Reset của Tailwind xóa lề
  `<p>`/`<h*>` và gạch chân liên kết nên đầu file đó có khối `revert` để trang giữ nguyên hình dạng cũ.

## Chạy

```bash
cd team3_fullstack/frontend
cp .env.example .env        # đặt VITE_API_URL nếu backend không ở http://localhost:8080
npm ci
npm run dev                 # http://localhost:5173
npm run build               # kiểm tra kiểu + build
npm test                    # test đơn vị (vitest), không cần backend
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
- **Thử lại** (quy tắc ở `src/api/retryPolicy.ts`): chưa chắc server đã xử lý lượt cũ thì gửi lại *đúng*
  `client_request_id`, vì backend trả kết quả đã lưu và không tạo lượt trùng. Gồm: mất kết nối, quá 60 giây,
  server đã trả 2xx nhưng FE không đọc được body, và mọi lỗi không rõ nguồn. Chỉ khi server đã báo rõ lượt đó
  thất bại (ví dụ 503, 504) mới hỏi lại bằng ID mới, thành một lượt mới trong lịch sử.
- `insufficient_context` hiện là thông báo "Chưa đủ căn cứ", tách khỏi lỗi hệ thống.
- Nhãn "Dữ liệu thử nghiệm" hiện khi `VITE_MOCK_MODE` khác `false`.
- Mục "Điều 404" trong trang tra cứu cố ý không có ở backend, để thử đường "không tìm thấy".

## Giới hạn

- Test trong repo mới là test đơn vị cho lớp API (`client.test.ts`, `retryPolicy.test.ts`). Các luồng giao diện
  (gửi, thử lại, viewer, Search, mobile) đã được kiểm thử bằng trình duyệt tự động nhưng kịch bản nằm ngoài repo.
- Chưa cấu hình nginx cho tải lại các route con trong Docker (`Dockerfile` hiện chỉ phục vụ file tĩnh);
  `npm run dev` và `npm run preview` tải lại được.
- Chưa build thử image Docker sau khi thêm Tailwind (máy kiểm tra không chạy Docker). `package-lock.json` đã có
  gói native cho Alpine (`@tailwindcss/oxide-linux-x64-musl`, `lightningcss-linux-x64-musl`) và Node 20 đáp ứng
  yêu cầu `>= 20`, nhưng cần chạy `docker build` một lần để chắc chắn.
- Không có streaming, đăng nhập, đính kèm tệp: backend chưa hỗ trợ.
