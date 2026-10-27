# Quickstart — VLRA-41

Chạy từ repository root. JDK 25; JAVA_HOME phải trỏ cùng JDK25 (lệnh java trên PATH có thể khác Maven). Dùng Maven Wrapper, không cần cài Maven.

```powershell
cd team3_fullstack/backend
.\mvnw.cmd -B -ntp test
.\mvnw.cmd -B -ntp package
```

Runtime v2.0 cần PostgreSQL database riêng và Team2 internal HTTP service đúng contract.
Spring không tự đọc .env; đặt biến process (không commit secret):

```powershell
$env:SPRING_PROFILES_ACTIVE = "rag"
$env:SPRING_DATASOURCE_URL = "jdbc:postgresql://localhost:5432/legal_rag"
$env:SPRING_DATASOURCE_USERNAME = "<local-user>"
$env:SPRING_DATASOURCE_PASSWORD = "<local-password>"
$env:RAG_BASE_URL = "http://localhost:8001"
.\mvnw.cmd spring-boot:run
```

Terminal khác, dùng curl.exe -N để thấy heartbeat/meta ngay; body UTF-8:

```powershell
'{"question":"Câu hỏi kiểm thử","clientRequestId":"44444444-4444-4444-8444-444444444444"}' | Set-Content -Encoding utf8 request.json
curl.exe -N -H "Content-Type: application/json" -H "Accept: text/event-stream" --data-binary "@request.json" http://localhost:8080/api/v1/chat/stream
```

Kỳ vọng meta, sau đó complete hoặc error; answered chỉ phát delta sau commit.
Gửi lại cùng ID/payload: completed replay không gọi AI, failed HTTP logical error.
GET /api/v1/conversations/{conversationId}/messages trả array, ID là số.
Profile mock cũ vẫn JSON v1.2, không dùng để nghiệm thu endpoint v2.0.
HTTP stub và H2 chỉ trong test; chưa có service Team2 thì không chấm live RAG PASS.
Không có server stub production trong task này. Không bật đồng thời rag và mock.

## PostgreSQL integration tests

`PostgresChatStoreTests` mặc định SKIP nếu không có test.postgres.url. Muốn chạy:
chuẩn bị PostgreSQL database test riêng, tài khoản được CREATE SCHEMA; mỗi ca tự
xóa schema vlra41_<UUID> của nó. Không trỏ URL vào database production.

```powershell
# từ backend; thay cổng/tài khoản theo database test riêng
.\mvnw.cmd -B -ntp '-Dtest=PostgresChatStoreTests' '-Dtest.postgres.url=jdbc:postgresql://127.0.0.1:55441/postgres' '-Dtest.postgres.user=vlra41' test
```

Password nếu cần qua TEST_POSTGRES_PASSWORD, không ghi vào lệnh/log. Cụm tạm trong
lần kiểm chứng đã dừng, cần chuẩn bị lại trước khi dùng URL55441 ở trên.

## Public schema

Sau StreamApiTests, từ root dùng Python đã cài test extra của repository:

```powershell
python specs/team3/week-04/001-vlra-41-rag-query/contracts/validate-examples.py
```

Bốn payload lấy từ HTTP wire và ba payload âm phải PASS. Xem [báo cáo](verification.md)
để phân biệt test stub, PostgreSQL và AC live chưa chạy.
