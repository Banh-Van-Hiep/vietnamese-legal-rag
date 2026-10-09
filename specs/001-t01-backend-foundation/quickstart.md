# Quickstart validation — Task01

**Trạng thái:** hướng dẫn lập ở vòng plan; đã thực hiện kiểm chứng T01 ngày 2026-10-09,
xem [báo cáo mục 6](../../docs/team3_fullstack/t01-backend-foundation.md#6-kiểm-chứng-spec-t01-riêng-ngày-09102026).
Runner hiện đã tuân thủ Q2; các ghi chú “chưa chạy trong lượt plan” bên dưới mô tả thời điểm lập kế hoạch.
Tham chiếu [plan hiện tại](plan.md), [tasks hiện tại](tasks.md), [data model](data-model.md)
và [interfaces](contracts/README.md). Các ca U1/C1 dưới đây vẫn là hướng dẫn chưa thực hiện.

## 1. Điều kiện và chuẩn bị

Dùng Windows PowerShell 5.1 hoặc môi trường PowerShell tương thích runner hiện tại, JDK 25
và Maven Wrapper đi kèm. Không cần AI/key thật, Docker hoặc PostgreSQL cho profile mock.
Lần đầu build cần mạng để Maven lấy dependency. Không thêm package vào POM để chạy hướng dẫn.

Từ gốc repo, mở một terminal dành riêng cho kiểm tra:

```powershell
git status --short
git diff --stat
Set-Location .\team3_fullstack\backend
$env:JAVA_HOME = 'D:\Java\jdk-25'
& (Join-Path $env:JAVA_HOME 'bin\javac.exe') -version
New-Item -ItemType Directory -Path .\target\t01 -Force | Out-Null
@(
  'SPRING_PROFILES_ACTIVE=mock'
  'SERVER_PORT=18081'
  'CORS_ALLOWED_ORIGINS=http://127.0.0.1:55173'
  'MOCK_ANSWER_STATUS=answered'
) | Set-Content -LiteralPath .\target\t01\run.env -Encoding UTF8
```

JAVA_HOME là ví dụ của máy Tuấn, thay bằng đường dẫn JDK 25 thật. Không chỉ dựa `java` trên
PATH; Maven dùng JAVA_HOME. Không copy/ghi đè `.env` đang có. Fixture trong target được Git bỏ qua.

## 2. Kiểm tra runner và build

Sau khi harness được triển khai theo plan:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\src\test\powershell\RunLocalConfigurationTests.ps1
```

Harness chưa tồn tại ở lượt plan. Expected: từng case ở bảng dưới có expected/actual,
thành công/lỗi đúng và env/location được khôi phục. Maven stub không chạy AI hay build thật.

| Case | Expected |
| --- | --- |
| Explicit Port/AllowedOrigins khác terminal/file | Giá trị explicit thắng |
| Terminal khác file, không có argument tương ứng | Terminal thắng; hiện runner cũ sẽ không đạt |
| Terminal/argument vắng | File được dùng |
| Cả argument/terminal/file key vắng | Không gán env để che default Spring; JAVA_HOME vẫn bắt buộc riêng |
| Giá trị được chọn sai/rỗng đã khai báo | Lỗi, không fallback để che lỗi |
| Giá trị thấp hơn sai nhưng nguồn thắng hợp lệ | Giữ nguồn thắng; không ghi đè bằng nguồn thấp |
| File chỉ định không tồn tại, cú pháp sai, runtime/profile sai, Maven nonzero | Lỗi, không thông báo sẵn sàng; env/location được khôi phục |
| Kết thúc thành công | Khôi phục cả key có sẵn và key trước đó vắng |

Chạy test Java trong môi trường có origin mặc định mà các test hiện có chờ; lấy fixture
riêng cho build thay vì thay cấu hình người dùng:

```powershell
@(
  'SPRING_PROFILES_ACTIVE=mock'
  'CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173'
  'MOCK_ANSWER_STATUS=answered'
) | Set-Content -LiteralPath .\target\t01\build.env -Encoding UTF8
$env:SPRING_PROFILES_ACTIVE = 'mock'
$env:CORS_ALLOWED_ORIGINS = 'http://localhost:5173,http://127.0.0.1:5173'
$env:MOCK_ANSWER_STATUS = 'answered'
powershell -NoProfile -ExecutionPolicy Bypass -File .\run-local.ps1 `
  -Task package -EnvFile .\target\t01\build.env
```

Expected: BUILD SUCCESS, không test fail/error; JAR được đóng gói. Không cố định số test 24.
Test kiểm tra mock không có DataSource, health, header/lỗi 400/404/405/413/415 và test-only
500/503/504; không cần thêm endpoint lỗi public hoặc kiểm tra contract 406 mới.

## 3. Smoke hai bộ cấu hình

Kiểm tra port chọn chưa có tiến trình khác. Không dừng Backend đang chạy của người dùng.
Tiến trình smoke cần được xác định đúng PID/port; health từ tiến trình cũ không là PASS.

**Bộ A — chứng minh terminal thắng file.** Trong terminal Backend:

```powershell
$env:SERVER_PORT = '18082'
$env:CORS_ALLOWED_ORIGINS = 'http://localhost:55174'
$env:MOCK_ANSWER_STATUS = 'insufficient_context'
powershell -NoProfile -ExecutionPolicy Bypass -File .\run-local.ps1 `
  -EnvFile .\target\t01\run.env
```

Expected sau sửa Q2: chạy port 18082, cho origin localhost:55174, trả trạng thái mẫu
insufficient_context. File vẫn có port 18081/origin 55173/answered, không được ghi đè terminal.

**Bộ B — chứng minh explicit thắng và file fallback.** Dừng đúng smoke A bằng Ctrl+C,
giữ SERVER_PORT/origin terminal như cũ, xóa chỉ biến mock status của terminal kiểm tra:

```powershell
Remove-Item -LiteralPath Env:MOCK_ANSWER_STATUS -ErrorAction SilentlyContinue
powershell -NoProfile -ExecutionPolicy Bypass -File .\run-local.ps1 `
  -EnvFile .\target\t01\run.env -Port 18083 -AllowedOrigins 'http://localhost:55175'
```

Expected: port 18083/origin localhost:55175 từ arguments; answered từ file. Không thêm
mode hoặc argument mới. Ghi `.env`/fixture hash trước và sau để xác nhận không bị ghi đè.

## 4. Kiểm tra health, CORS và header

Trong terminal thứ hai, chọn đúng bộ đang chạy:

```powershell
$baseUrl = 'http://127.0.0.1:18082'
$origin = 'http://localhost:55174'
Invoke-RestMethod "$baseUrl/api/v1/health"
$preflight = Invoke-WebRequest -UseBasicParsing -Method Options `
  -Uri "$baseUrl/api/v1/query" -Headers @{
    Origin = $origin
    'Access-Control-Request-Method' = 'POST'
    'Access-Control-Request-Headers' = 'content-type'
  }
$preflight.StatusCode
$preflight.Headers
$body = @{ client_request_id = [guid]::NewGuid().ToString(); question = 'T01 smoke check' } | ConvertTo-Json
$response = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$baseUrl/api/v1/query" `
  -ContentType 'application/json' -Headers @{ Origin = $origin } -Body ([Text.Encoding]::UTF8.GetBytes($body))
$response.Headers
$json = [Text.Encoding]::UTF8.GetString($response.RawContentStream.ToArray()) | ConvertFrom-Json
$json.status
$json.citations.Count
```

Bộ B đổi baseUrl thành port 18083 và origin localhost:55175. Expected: health up; preflight
thành công, Allow-Origin đúng origin và method/header JSON được cho phép; query có request/conversation
ID và expose header theo interface. Bộ A status=insufficient_context/citations=[]; bộ B
answered có citation fixture hiện có. Đây chỉ chứng minh cấu hình mock, không nghiệm thu toàn T02.

Kiểm tra origin ngoài danh sách trên preflight và actual request:

```powershell
try {
  Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/api/v1/health" `
    -Headers @{ Origin = 'http://localhost:59999' }
} catch {
  if (!$_.Exception.Response) { throw }
  [int]$_.Exception.Response.StatusCode
  $_.Exception.Response.Headers['Access-Control-Allow-Origin']
}
```

Expected: không cấp Allow-Origin cho origin ngoài danh sách; code hiện thường trả 403.
Không kiểm tra hoặc bắt JSON body 403. Các test Java bao phủ cả preflight bị từ chối.
Location thực tế khi tạo conversation và lỗi có Origin/header được kiểm tra trong test Java;
nếu thiếu assertion thì bổ sung ở bước triển khai, dùng endpoint có sẵn.

## 5. Lỗi, default và cleanup

- Dùng `/api/v1/unknown`, GET vào `/api/v1/query`, POST media type sai/JSON sai/body trên
  16 KiB để kiểm tra các mã tại [interfaces](contracts/README.md); không đưa 406 vào tiêu chí.
- Với 500/503/504, dùng probe/test hiện có để xác nhận envelope, retryable, không answer/status,
  không lộ chi tiết. T018 bổ sung riêng RuntimeException sau khi service tiếp nhận lượt trong
  MockQueryServiceTests và ca HTTP trên POST /api/v1/query hiện có trong BackendConfigurationTests:
  500/INTERNAL_ERROR, retryable=false, conversation ID đúng lượt và X-Conversation-ID tương ứng,
  X-Request-ID, message an toàn/không rỗng và không lộ chi tiết lỗi gốc. AI gây lỗi chỉ nằm trong
  cấu hình test, không thêm endpoint hoặc scenario public; probe 500 chưa tiếp nhận lượt không
  thay bằng chứng này. T019 chạy kiểm chứng các ca; chưa thực hiện trong lượt sửa tài liệu.
  Trên ứng dụng thật `/api/v1/t01-error-probe/timeout` phải không tồn tại.

**Ca default (T012):** Dừng đúng smoke trước đó, kiểm tra port 8080 rảnh. Trong terminal
kiểm tra Backend, giữ JAVA_HOME JDK 25 hợp lệ; bỏ cả profile/port/origin/status ở process.
Fixture riêng dưới target chỉ có comment, không chứa bất kỳ key override nào, đặc biệt
không có SPRING_PROFILES_ACTIVE. Không dùng build.env/run.env cho ca này.

```powershell
Remove-Item -LiteralPath Env:SPRING_PROFILES_ACTIVE -ErrorAction SilentlyContinue
Remove-Item -LiteralPath Env:SERVER_PORT -ErrorAction SilentlyContinue
Remove-Item -LiteralPath Env:CORS_ALLOWED_ORIGINS -ErrorAction SilentlyContinue
Remove-Item -LiteralPath Env:MOCK_ANSWER_STATUS -ErrorAction SilentlyContinue
& (Join-Path $env:JAVA_HOME 'bin\javac.exe') -version
'# Default smoke: no profile, port, origin or answer-status overrides.' |
  Set-Content -LiteralPath .\target\t01\default.env -Encoding UTF8
powershell -NoProfile -ExecutionPolicy Bypass -File .\run-local.ps1 `
  -Task run -EnvFile .\target\t01\default.env
```

Không truyền tham số profile, Port/AllowedOrigins hoặc tùy chọn Spring/Maven ép profile.
Log của **tiến trình mới** phải cho biết không có active profile được ép và default profile
thực tế là `mock`; ghi đoạn log này với PID/command vào config-smoke.log. Sau đó kiểm tra
health 200/up, port 8080, cả hai origin `http://localhost:5173` và `http://127.0.0.1:5173`
bằng preflight/actual theo mục 4, và query status=answered. Health một mình không chứng minh
profile mock. Nếu port 8080 bị chiếm, ghi chưa đạt ca default, không đọc health server cũ.


- Port bận: giữ smoke đang chạy, khởi động thêm smoke trên cùng port; tiến trình thứ hai phải
  báo lỗi/thoát nonzero, không được coi response của tiến trình thứ nhất là readiness thứ hai.
- Dừng đúng tiến trình kiểm tra bằng Ctrl+C; harness tạo helper nền phải dùng cửa sổ Hidden
  và cleanup chỉ PID/descendants do nó tạo. Không kill theo tên java/node hoặc sửa service người dùng.

## 6. Ghi nghiệm thu

Đối chiếu từng AC trong [plan](plan.md), lưu log ở `target/t01/` và surefire-reports; ghi commit,
working tree, environment, command, expected/actual và giới hạn. Báo cáo lịch sử ngày 07/10
được giữ rõ; chỉ thêm kết quả mới sau khi đã chạy. Cuối cùng kiểm tra git status/diff, không
commit `.env`, target, node_modules hoặc secret. Build/test Backend không xác nhận UI T03/T04.
