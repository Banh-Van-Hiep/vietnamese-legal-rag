# Plan — VLRA-42

**Ngày:** 23/10/2026. Theo Docs v2.0 §8.6–8.7/§9 và yêu cầu người dùng: FE–BE SSE,
chờ Team2, commit nhỏ trên nhánh bàn giao; không push. Kế thừa React18/TS/Vite/Vitest,
Spring MVC/JDBC của VLRA-41 (841280d), không thêm framework hoặc dependency runtime.

## Constitution check

Contract v2.0 đã chốt. Chỉ ai/ Java gọi Python; không sửa Team1/2/shared contracts.
Giữ component/cấu trúc hiện tại; kiểm chứng parser + API + browser/Backend thật.
HTTP stub chỉ dùng kiểm thử và phải nhận diện là dữ liệu thử, không đạt live RAG.

## Thành phần và hiện trạng

Đã có client HTTP/timeout, retry policy, UI/Citation/Viewer và epoch guard một phần.
Hiện transport snake_case/UUID/JSON cũ; tải lịch sử còn pagination; FE tạo conv trước
khi query nên dễ lặp conv khi phản hồi tạo bị mất. Chưa có parser SSE.

Bổ sung public wire types + validators + incremental parser + streamChat trong
frontend/src/{types/publicApi.ts,api/publicContract.ts,api/sse.ts,api/chatStream.ts}.
Adapter ánh xạ public ID số/camelCase sang view model UI hiện có tại api/publicApi.ts;
không ép kiểu field sai từ response. URL route trong browser vẫn là string, không
coi đó là kiểu ID JSON. conversationApi/documentApi chuyển arrays/route v2.0.

useChat dùng meta để gắn conv, không POST create trước lượt đầu; complete là bản chuẩn,
retry chưa rõ giữ UUID và cùng placeholder/buffer reset; failed đã biết dùng UUID mới.
Giữ pending khi reload, cho refresh/reconcile; đổi route/hủy/unmount abort nhận và bỏ
response cũ, không hủy AI. Lưu pending receipt tối thiểu trong sessionStorage để không
mất UUID lúc chưa nhận meta và reload; bỏ question sau terminal. Không ghi key/secret.

useArticle/AppContext thêm guards cho response cũ; getArticle xác minh response IDs.
Bổ sung proxy Java GET /documents/{documentId}?articleId=... bằng DocumentService/AiClient
đã có, trả 6 camelCase fields; đây là wiring tối thiểu, không dựng lại UI VLRA-43.

## Kiểm chứng và chia commit

1. feat(frontend): thêm SSE transport/validators/tests; chưa đổi UI callers. Build được.
2. feat(api): thêm adapter v2.0 và Java Viewer proxy/tests; giữ wrappers cũ đến bước3.
3. feat(frontend): nối hook/context/API với v2.0, retry/reload/abort/stale response,
   cập nhật thông báo cần thiết, không đổi thiết kế UI; kiểm thử browser thật.
4. docs(team3): hồ sơ VLRA-42, evidence/quickstart và thứ tự revert 4→3→2→1.
Mỗi bước chỉ commit khi kiểm tra tương ứng đạt; identity GitHub đã xác minh từ connector,
không sửa commit cũ. Những sửa tài liệu chung/VLRA43/44 hiện có không gom vào commit.

Vitest: frame/UTF8/CRLF/multiline/chunks/meta/terminal/shape/ID/budget/timeout/abort;
API mapping/errors và nguồn khớp IDs. Maven: Viewer mapping + error + regression.
Browser Edge riêng qua DevTools Protocol có sẵn, Node builtin WebSocket; không thêm
công cụ E2E runtime. Chạy Vite + Java rag + PostgreSQL riêng + HTTP stub (không Python
service giả production), kiểm success/insufficient/error/retry/reload/switch/source/CORS.
Live pipeline của Team2/AC VLRA44 giữ mở.

## Bổ sung W4-Q2 — tiêu đề từ câu hỏi đầu

Quyết định người dùng trong spec thay quy định không tự đổi title tại Docs v2.0 §9.2.
Sửa `backend/.../conversation/persistence/ChatStore.java` trong transaction accept có
khóa conversation: tạo title từ câu đầu, chỉ đổi default khi sequence đầu tiên, giữ
title custom/follow-up/replay. Giới hạn 100 code point; không thêm API/dependency/LLM.
Tận dụng `ChatStoreTests` (kế thừa trên PostgreSQL) để kiểm Unicode, persistence, retry,
failure và tên custom/cũ; mở rộng assertion B01/B02 của browser harness hiện có.
Build/package bằng Maven Wrapper, chạy lại browser với Java mới; ghi evidence và tạo
một commit riêng sau khi pass. Dữ liệu preview local được xử lý riêng, không có migration
ngầm cho database khác. T014 live không phụ thuộc thay đổi title và vẫn mở.
