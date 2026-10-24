# Frontend Team 3

React + TypeScript + Vite + **Tailwind CSS v4** (plugin `@tailwindcss/vite`, không cần file cấu hình riêng).
Main chat dùng API public SSE v2.0 theo [Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0). Hồ sơ: [VLRA42](../../specs/team3/week-04/002-vlra-42-fe-be-integration/verification.md), [VLRA43](../../specs/team3/week-04/003-vlra-43-answer-citation-viewer/verification.md).

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
| `/documents/:documentId?articleId=...[&clause=...&point=...&cite=C2]` | Nguyên văn theo v2.0, mở và tải lại được; `clause`/`point`/`cite` chỉ để tô sáng phần được trích. Route nested cũ vẫn là alias |
| `/try-backend` | Trang thử backend tạm của Team 3, không thuộc UI chính thức |

Bấm số tham chiếu `[C1]` trong câu trả lời hoặc nút "Xem nguyên văn" trên thẻ căn cứ để mở điều luật ở ngăn bên phải
mà không rời hội thoại; "Mở trang riêng" trong ngăn mở cùng điều luật ở trang có link chia sẻ được.

## Hiển thị câu trả lời và căn cứ (VLRA-43)

- Câu trả lời được phân tích ở `src/utils/answerFormat.ts` rồi render bằng React, không chèn HTML: đoạn, tiêu đề
  `**...**`, danh sách `- `, `1. `, `a) ` (kể cả có một dòng dẫn phía trước), chữ đậm và dấu `[Cn]`.
- `[Cn]` chỉ mở citation có trong array đã kiểm tra; marker và thẻ của căn cứ đang mở được đánh dấu.
- Thẻ căn cứ: số Cn, "Điều …, Khoản …, Điểm …", tên văn bản, "Xem nguyên văn" và "Nguồn chính thức" (`sourceUrl`).
- Viewer kiểm tra ID trả về khớp yêu cầu (adapter VLRA42), tô sáng khoản/điểm được trích khi nhãn chuẩn
  ("Khoản 2", "Điểm a") và vị trí là duy nhất trong nguyên văn (`src/utils/legalCitation.ts`); nếu không chắc chắn thì
  báo người dùng đối chiếu toàn Điều, không tô đoán. 404 vẫn giữ câu trả lời và cho mở nguồn chính thức của citation.
- Ngăn xem là hộp thoại modal: focus ở trong ngăn, Escape đóng và trả focus về nút đã mở.
- Nút sao chép lấy câu trả lời kèm danh sách căn cứ và nguồn.
- Màn hình chào có "Phạm vi dữ liệu": lĩnh vực (`VITE_CORPUS_SCOPE`), bản dữ liệu (`VITE_CORPUS_SNAPSHOT`, trống thì
  "Chưa công bố") và chế độ thử nghiệm/thật theo `VITE_MOCK_MODE`.

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

- Vitest kiểm SSE framing/UTF8/contracts/timeout/retry/adapters/receipt. Browser harness ở `tests/browser/` dùng Edge/Chrome CDP; đọc quickstart VLRA42. Kết quả dùng HTTP fixture, chưa phải live RAG. UI câu trả lời/căn cứ/Viewer của VLRA43 mới kiểm bằng dữ liệu giả lập; E2E pipeline thật/VLRA44 vẫn riêng.
- Chưa cấu hình nginx cho tải lại các route con trong Docker (`Dockerfile` hiện chỉ phục vụ file tĩnh);
  `npm run dev` và `npm run preview` tải lại được.
- Chưa build thử image Docker sau khi thêm Tailwind (máy kiểm tra không chạy Docker). `package-lock.json` đã có
  gói native cho Alpine (`@tailwindcss/oxide-linux-x64-musl`, `lightningcss-linux-x64-musl`) và Node 20 đáp ứng
  yêu cầu `>= 20`, nhưng cần chạy `docker build` một lần để chắc chắn.
- Chưa có đăng nhập hoặc đính kèm tệp. Streaming SSE đã được tích hợp; chưa nghiệm thu RAG thật vì Team2 chưa bàn giao HTTP service.
