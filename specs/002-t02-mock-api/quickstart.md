# T02 — Quickstart validation
**Trạng thái:** đã thực hiện local ngày 2026-10-09: wrapper package74, runner37 và HTTP8 PASS; xem [báo cáo T02](../../docs/team3_fullstack/t02-mock-api.md) và target/t02/ dưới backend. Không thay nghiệm thu nhóm.
Thư mục feature: specs/002-t02-mock-api/. Từ repository root, dùng PowerShell/JDK25 và
wrapper; không AI/key/DB thật, không sửa .env cá nhân.

    $env:JAVA_HOME = 'D:\Java\jdk-25'
    .\team3_fullstack\backend\src\test\powershell\RunLocalConfigurationTests.ps1 -JavaHome $env:JAVA_HOME
    New-Item -ItemType Directory -Path .\team3_fullstack\backend\target\t02 -Force | Out-Null
    $buildFixture = Join-Path (Get-Location) 'team3_fullstack\backend\target\t02\build.env'
    @('SPRING_PROFILES_ACTIVE=mock','CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173','MOCK_ANSWER_STATUS=answered') | Set-Content -LiteralPath $buildFixture -Encoding UTF8
    Remove-Item Env:MOCK_QUERY_SCENARIO,Env:MOCK_ARTICLE_SCENARIO -ErrorAction SilentlyContinue
    $env:SPRING_PROFILES_ACTIVE = 'mock'
    $env:CORS_ALLOWED_ORIGINS = 'http://localhost:5173,http://127.0.0.1:5173'
    $env:MOCK_ANSWER_STATUS = 'answered'
    .\team3_fullstack\backend\run-local.ps1 -Task package -EnvFile $buildFixture

Build fixture giữ profile mock, origin localhost/127.0.0.1:5173, legacy answered; query/article
selector absent để old tests giữ môi trường. Mọi test output dưới target được ignore.
Runner key mới theo Q2; nếu terminal selector có sẵn sẽ thắng file. Dùng terminal dành riêng.

## Scenario HTTP
Tạo fixture dưới backend/target/t02, JAVA_HOME hợp lệ; chọn free port 18084 hoặc cổng khác
do kiểm tra tạo. Gọi runner -EnvFile fixture -Port port; không thêm query/body field scenario.
Mỗi instance có MOCK_QUERY_SCENARIO và MOCK_ARTICLE_SCENARIO, restart khi đổi.

| Query mode | Expected |
| --- | --- |
| answered | 200, đủ 8 field, 1 citation marker C1 đúng |
| insufficient_context | 200, đủ ID/time, citations=[], không marker |
| internal_error | 500 INTERNAL_ERROR false |
| service_unavailable | 503 SERVICE_UNAVAILABLE true |
| upstream_timeout | 504 UPSTREAM_TIMEOUT true |

Article success trả tuple mock_v1/art1, newline; error modes như query ba lỗi trên.
Mọi mode: query input {} →400; document ID sai→400, missing doc/art→404; Origin được phép
vẫn đọc trace/error. Gọi document với ?extra=1 và GET body {} đều phải 400,
kể cả scenario hệ thống. Không probe public; 502 malformed chỉ qua spy/unit test.

Ví dụ query body hợp lệ:
    {"client_request_id":"44444444-4444-4444-8444-444444444444","question":"T02 kiểm thử"}

Mỗi lượt/scenario dùng UUIDv4 mới để tránh replay kết quả trước. Hỏi tiếp đưa conversation_id
đã nhận; hỏi mới bỏ ID cũ. Mở document bằng document_id/article_id citation, không display name.

## Guard/regression/evidence
Guard tests null/status/answer/limit Unicode/nullable/citation/marker/HTTPS/tuple mismatch;
HTTP spy kiểm502 và header/failed state. Wrapper full package bao gồm old T01 tests;
harness kiểm hai key mới và core keys. Smoke legacy selector vắng và ưu tiên terminal/file.
Ghi log/command/PID/expected/actual, snapshot old code/.env/diff. Không dùng health server cũ.
Helper nền Hidden, cleanup chỉ PID/descendants do nó tạo; giữ output để review.
Theo [tasks](tasks.md) và [báo cáo T02](../../docs/team3_fullstack/t02-mock-api.md) đã cập nhật sau implement.
Kết quả cuối: final-validation.log/final-surefire/, runner-tests.log, http-smoke-results.json,
jar-review.json, process-cleanup-review.json và scope-review.json. Helper thật ở
backend/target/t02/SmokeValidation.ps1; GET body dùng curl.exe có sẵn trên Windows.
