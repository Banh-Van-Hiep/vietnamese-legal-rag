# Quickstart — VLRA-42

FE chính dùng Backend profile rag v2.0; /try-backend giữ trang JSON v1.2 lịch sử.

```powershell
cd team3_fullstack/frontend
npm test
npm run build
npm run dev
```

Backend: theo [quickstart VLRA41](../001-vlra-41-rag-query/quickstart.md), PostgreSQL riêng,
RAG_BASE_URL trỏ service Team2 khi bàn giao. FE dùng VITE_API_URL Backend, không gọi Python.
VITE_MOCK_MODE=true khi dùng fixture/stub; không tắt banner để giả nghiệm thu live.

Kiểm tra: gửi câu hỏi → URL conv từ meta → answer/citation từ complete; reload không
query AI lại; request gián đoạn retry cùng UUID; failed xác định retry UUID mới;
đổi conv không nhận response cũ; mở nguồn đúngIDs, lỗi nguồn không xóa answer.
Chưa có service thật thì lỗi rõ ràng, không tự fallback đáp án mock.

Kết quả chi tiết tại verification.md; cách tái chạy browser smoke ở các mục bên dưới.

## Stack fixture để kiểm tra độc lập khi chờ Team2

Đây là **TEST ONLY**, không phải RAG thật. Cần Node24 (WebSocket builtin), JDK25,
PostgreSQL database test riêng và Edge/Chrome đã cài. Không dùng database production.
Mở các terminal riêng từ repository root; thay credential database bằng cấu hình test
của bạn, không commit password hoặc .env thật.

Terminal1 — fixture:

```powershell
cd team3_fullstack/frontend
node tests/browser/rag-stub.mjs
```

Terminal2 — Java:

```powershell
cd team3_fullstack/backend
$env:JAVA_HOME='D:/Java/jdk-25'
$env:SPRING_PROFILES_ACTIVE='rag'
$env:SPRING_DATASOURCE_URL='jdbc:postgresql://127.0.0.1:5432/legal_rag_test'
$env:SPRING_DATASOURCE_USERNAME='<test-user>'
$env:SPRING_DATASOURCE_PASSWORD='<test-password>'
$env:RAG_BASE_URL='http://127.0.0.1:18042'
$env:SERVER_PORT='18043'
$env:CORS_ALLOWED_ORIGINS='http://127.0.0.1:15173'
.\mvnw.cmd spring-boot:run
```

Terminal3 — Frontend:

```powershell
cd team3_fullstack/frontend
$env:VITE_API_URL='http://127.0.0.1:18043'
$env:VITE_MOCK_MODE='true'
npm run dev -- --host 127.0.0.1 --port 15173 --strictPort
```

Mở http://127.0.0.1:15173 để thử. VITE_MOCK_MODE chỉ là nhãn dữ liệu, không chọn API
hoặc bật mock Backend. Không đưa fixture này vào deployment live.

## Chạy browser smoke

Từ frontend, mở Edge headless bằng profile riêng, không dùng profile cá nhân:

```powershell
$edgeProfile=(New-Item -ItemType Directory -Force ../backend/target/vlra42-browser/edge-profile).FullName
$edgeArgs='--headless=new --disable-gpu --disable-background-networking --no-first-run --remote-debugging-address=127.0.0.1 --remote-debugging-port=19242 --user-data-dir="'+$edgeProfile+'" about:blank'
$edge=Start-Process 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' -ArgumentList $edgeArgs -WindowStyle Hidden -PassThru
node tests/browser/vlra42-smoke.mjs
Stop-Process -Id $edge.Id -ErrorAction SilentlyContinue
```

Điều chỉnh đường dẫn Edge theo máy. Mặc định FE15173/BE18043/stub18042/CDP19242;
có thể đổi qua FE_URL, BE_URL, STUB_URL, CDP_URL và EVIDENCE_DIR. Fixture hỗ trợ
STUB_PORT; đổi cổng phải đồng bộ Java/FE/CORS. Chạy fixture riêng cho mỗi suite vì ca
lỗi lần đầu phụ thuộc counter của fixture, không dùng chung với người khác.

Expected:11ca PASS,0uncaught JS exception. Evidence trong backend/target/vlra42-browser;
không commit log/browser profile/build. Sau test, dừng fixture/Vite/Java bằng Ctrl+C
và dừng đúng PostgreSQL cluster test nếu bạn đã tạo riêng.

## Live và rollback

**Bổ sung W4-Q2 (23/10):** người dùng cho phép lấy câu hỏi đầu làm title, thay quy tắc
không tự đổi title của Docs v2.0 §9.2; quyết định chi tiết trong spec.md. Bấm Câu hỏi mới,
gửi câu đầu → sidebar/header hiển thị câu đầu (tối đa 100 code point). Hỏi tiếp và reload
→ giữ title đó. Không dùng LLM đặt tên; tên custom giữ nguyên. Các hội thoại cũ không
tự đổi hàng loạt; chỉ database preview local đã được cập nhật riêng theo verification.md.

Khi Team2 bàn giao, giữ public contract và đổi RAG_BASE_URL sang service thật; cấu hình
retrieval/model/key bên Team2. Chạy lại AC41/44; VITE_MOCK_MODE=false chỉ khi dữ liệu
đã là thật. T014 live vẫn mở; xem [verification.md](verification.md).

Commit theo thứ tự transport(d561f7f)→adapters(b632265)→UI(b695277)→hồ sơ. Khi cần,
revert từ cuối về đầu vì UI import các module trước; không reset/force push. Revert UI
khôi phục luồng JSON v1.2 cần backend profile mock. Chưa push các commit của lượt này.
