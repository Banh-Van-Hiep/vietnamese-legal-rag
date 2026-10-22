# Frontend Team 3

React + TypeScript + Vite + **Tailwind CSS v4** (plugin `@tailwindcss/vite`, không cần file cấu hình riêng).
Main chat dùng API public SSE v2.0 theo [Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0). Hồ sơ: [VLRA42](../../specs/team3/week-04/002-vlra-42-fe-be-integration/verification.md).

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

Main UI cần Backend profile `rag` v2.0 và PostgreSQL: xem [quickstart VLRA41](../../specs/team3/week-04/001-vlra-41-rag-query/quickstart.md). Backend mock cũ trả JSON v1.2 chỉ phù hợp trang `/try-backend`, không dùng cho main chat mới. Service thật còn chờ Team2; cách kiểm thử bằng fixture tại [quickstart VLRA42](../../specs/team3/week-04/002-vlra-42-fe-be-integration/quickstart.md).

## Các trang

| Đường dẫn | Chức năng |
| --- | --- |
| `/` | Hỏi đáp, hội thoại mới |
| `/c/:conversationId` | Mở lại hội thoại đã lưu |
| `/search` | Tra cứu (khung): tìm trong vài mục mẫu, chưa có API Search |
| `/documents/:documentId?articleId=...` | Nguyên văn theo v2.0, mở và tải lại được; route nested cũ vẫn là alias |
| `/try-backend` | Trang thử backend tạm của Team 3, không thuộc UI chính thức |

Bấm số tham chiếu `[C1]` trong câu trả lời hoặc nút "Xem nguyên văn điều luật" để mở điều luật ở ngăn bên phải
mà không rời hội thoại.

## Hành vi cần biết

- Lượt đầu gửi thẳng `POST /api/v1/chat/stream`, không tạo hội thoại trước. Backend tạo conv
  trong transaction nhận lượt; FE lấy ID số từ meta, đổi URL sang `/c/:conversationId`.
  Public fields camelCase; adapter chuyển sang presentation model cũ trong component.
- Mỗi lượt có `clientRequestId` UUID v4 mới. Chặn câu hỏi rỗng, quá 2000 ký tự và gửi trùng khi đang chờ.
- **Thử lại** (quy tắc ở `src/api/retryPolicy.ts`): chưa chắc server đã xử lý lượt cũ thì gửi lại *đúng*
  `clientRequestId`, vì backend trả kết quả đã lưu và không tạo lượt trùng. Gồm: mất kết nối, quá 60 giây,
  server đã trả 2xx nhưng FE không đọc được body, và mọi lỗi không rõ nguồn. Chỉ khi server đã báo rõ lượt đó
  thất bại (ví dụ 503, 504) mới hỏi lại bằng ID mới, thành một lượt mới trong lịch sử.
- SSE parser đọc meta/delta/complete/error; complete thay bằng full answer/citation chuẩn.
- Dừng nhận chỉ dừng stream phía FE, không hủy AI. Retry chưa rõ reset buffer và giữ UUID.
- Pending trên server chặn gửi mới; reload lấy history, có nút tải lại trạng thái. Receipt
  chưa rõ được giữ tối thiểu trong sessionStorage của tab và xóa question sau terminal;
  nếu storage bị chặn, không cam kết phục hồi UUID khi reload trước meta.
- `insufficient_context` hiện là thông báo "Chưa đủ căn cứ", tách khỏi lỗi hệ thống.
- Nhãn "Dữ liệu thử nghiệm" hiện khi `VITE_MOCK_MODE` khác `false`.
- Mục "Điều 404" trong trang tra cứu cố ý không có ở backend, để thử đường "không tìm thấy".

## Giới hạn

- Vitest kiểm SSE framing/UTF8/contracts/timeout/retry/adapters/receipt. Browser harness ở `tests/browser/` dùng Edge/Chrome CDP; đọc quickstart VLRA42. Kết quả dùng HTTP fixture, chưa phải live RAG. Thiết kế UI đầy đủ/VLRA43 và E2E pipeline thật/VLRA44 vẫn riêng.
- Chưa cấu hình nginx cho tải lại các route con trong Docker (`Dockerfile` hiện chỉ phục vụ file tĩnh);
  `npm run dev` và `npm run preview` tải lại được.
- Chưa build thử image Docker sau khi thêm Tailwind (máy kiểm tra không chạy Docker). `package-lock.json` đã có
  gói native cho Alpine (`@tailwindcss/oxide-linux-x64-musl`, `lightningcss-linux-x64-musl`) và Node 20 đáp ứng
  yêu cầu `>= 20`, nhưng cần chạy `docker build` một lần để chắc chắn.
- Chưa có đăng nhập hoặc đính kèm tệp. Streaming SSE đã được tích hợp; chưa nghiệm thu RAG thật vì Team2 chưa bàn giao HTTP service.
