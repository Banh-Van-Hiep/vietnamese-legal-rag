# Research — VLRA-42

- Quyết định: fetch POST + ReadableStream + TextDecoder streaming, không EventSource.
  SSE UTF8, data multiline và comments theo [MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events).
- Quyết định: abort và operation token/epoch bảo vệ phản hồi cũ theo
  [React useEffect](https://react.dev/reference/react/useEffect); abort nhận không hủy AI.
- Quyết định: giữ view model UI hiện có, thêm wire types/adapter rõ ràng; tránh sửa
  toàn bộ Citation UI trong VLRA42. Wire contract vẫn camelCase/ID integer.
- Không còn câu hỏi contract: user chốt v2.0 và triển khai42, chờ Team2. Viewer backend
  rag thiếu route: bổ sung proxy tối thiểu, không tự tạo source/corpus.
- Edge đã có trong máy, Node24 có WebSocket; browser smoke không cần thêm dependency.
- Lần baseline npm test/build bị sandbox spawn EPERM từ esbuild; chạy lại ngoài sandbox.
