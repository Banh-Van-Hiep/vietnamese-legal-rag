<#
VLRA-44 - chạy E2E React -> Java (profile rag) -> FastAPI của Team 2 (HTTP mock) trên Windows.

Chạy từ thư mục gốc repo:
  powershell -ExecutionPolicy Bypass -File team3_fullstack\run-vlra44-e2e.ps1 -UseDocker
hoặc với PostgreSQL đã cài sẵn (database test riêng, không dùng database thật):
  powershell -ExecutionPolicy Bypass -File team3_fullstack\run-vlra44-e2e.ps1 -DbUser postgres -DbPassword <mật khẩu> -CreateDb

Script tự dừng các tiến trình nó đã mở. Evidence: team3_fullstack\backend\target\vlra44-e2e\
Đây là kiểm thử với HTTP mock (mốc G2), chưa phải RAG thật.
#>
param(
  [string]$JavaHome = $env:JAVA_HOME,
  [string]$Python = "python",
  [switch]$UseDocker,
  [string]$DbUrl = "jdbc:postgresql://127.0.0.1:5432/legal_rag_e2e",
  [string]$DbUser = "postgres",
  [string]$DbPassword = "",
  [switch]$CreateDb,
  [string]$EdgePath = "",
  [switch]$SkipInstall
)
# "Continue": Windows PowerShell 5.1 coi stderr của lệnh native là lỗi khi đặt "Stop"; lỗi được kiểm tra bằng $LASTEXITCODE và Fail.
$ErrorActionPreference = "Continue"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Backend = Join-Path $Root "team3_fullstack\backend"
$Frontend = Join-Path $Root "team3_fullstack\frontend"
$Evidence = Join-Path $Backend "target\vlra44-e2e"
New-Item -ItemType Directory -Force $Evidence | Out-Null
$FePort = 15173; $BePort = 18043; $RagPort = 18044; $CdpPort = 19242
$started = @()

function Step($text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Fail($text) { Write-Host "LỖI: $text" -ForegroundColor Red; throw $text }
function Wait-Url($url, $seconds, $name, $proc = $null) {
  $end = (Get-Date).AddSeconds($seconds)
  while ((Get-Date) -lt $end) {
    if ($proc -and $proc.HasExited) { Fail "$name đã dừng (mã $($proc.ExitCode)) trước khi sẵn sàng. Xem log trong $Evidence" }
    try { $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 3; if ($r.StatusCode -lt 500) { return } } catch { }
    Start-Sleep -Milliseconds 500
  }
  Fail "$name chưa sẵn sàng sau $seconds giây ($url). Xem log trong $Evidence"
}
function Stop-Tree($proc) {
  if ($proc -and -not $proc.HasExited) { & taskkill /PID $proc.Id /T /F 2>$null | Out-Null }
}

try {
  Step "Kiểm tra máy"
  if ($JavaHome) { $env:JAVA_HOME = $JavaHome; $env:Path = "$JavaHome\bin;$env:Path" }
  $javaVersion = (& java -version 2>&1 | Select-Object -First 1) -as [string]
  if ($javaVersion -notmatch '"25') { Fail "Cần JDK 25 (đang có: $javaVersion). Cài JDK 25 hoặc truyền -JavaHome <thư mục JDK 25>." }
  if (-not ($javaVersion)) { Fail "Không tìm thấy java." }
  $nodeVersion = (& node -v) -as [string]
  if ([int]($nodeVersion.TrimStart('v').Split('.')[0]) -lt 22) { Fail "Cần Node 22 trở lên (đang có: $nodeVersion)." }
  & $Python --version | Out-Null
  if ($LASTEXITCODE -ne 0) { Fail "Không chạy được '$Python'. Truyền -Python py nếu máy dùng lệnh py." }
  if (-not $EdgePath) {
    $EdgePath = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
                  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
                  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
  }
  if (-not $EdgePath) { Fail "Không tìm thấy Edge/Chrome. Truyền -EdgePath." }
  Write-Host "Java: $javaVersion | Node: $nodeVersion | Trình duyệt: $EdgePath"

  Step "PostgreSQL test riêng"
  if ($UseDocker) {
    & docker rm -f vlra44-pg 2>$null | Out-Null
    & docker run -d --name vlra44-pg -e POSTGRES_PASSWORD=vlra44 -e POSTGRES_DB=legal_rag_e2e -p 55432:5432 postgres:16 | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "Không chạy được container PostgreSQL (Docker Desktop đã bật chưa?)." }
    $DbUrl = "jdbc:postgresql://127.0.0.1:55432/legal_rag_e2e"; $DbUser = "postgres"; $DbPassword = "vlra44"
    $ready = $false
    for ($i = 0; $i -lt 60 -and -not $ready; $i++) {
      & docker exec vlra44-pg pg_isready -U postgres -d legal_rag_e2e 2>$null | Out-Null
      $ready = ($LASTEXITCODE -eq 0); if (-not $ready) { Start-Sleep 1 }
    }
    if (-not $ready) { Fail "PostgreSQL trong Docker chưa sẵn sàng." }
  } elseif ($CreateDb) {
    $dbName = ($DbUrl -split '/')[-1]
    $env:PGPASSWORD = $DbPassword
    & psql -h 127.0.0.1 -U $DbUser -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$dbName'" | Set-Variable exists
    if (-not $exists) { & psql -h 127.0.0.1 -U $DbUser -d postgres -c "CREATE DATABASE $dbName" | Out-Null }
    Remove-Item Env:\PGPASSWORD
  }
  Write-Host "Database: $DbUrl"

  if (-not $SkipInstall) {
    Step "Cài thư viện Python của Team 2 (api, test) và Frontend"
    Push-Location $Root; & $Python -m pip install --quiet -e ".[api,test]"; $pipCode = $LASTEXITCODE; Pop-Location
    if ($pipCode -ne 0) { Fail "pip install lỗi." }
    if (-not (Test-Path (Join-Path $Frontend "node_modules"))) { Push-Location $Frontend; & npm ci --no-audit --no-fund; Pop-Location }
  }

  Step "Java backend (profile rag) ở cổng $BePort"
  $env:SPRING_PROFILES_ACTIVE = "rag"
  $env:SPRING_DATASOURCE_URL = $DbUrl; $env:SPRING_DATASOURCE_USERNAME = $DbUser; $env:SPRING_DATASOURCE_PASSWORD = $DbPassword
  $env:RAG_BASE_URL = "http://127.0.0.1:$RagPort"; $env:SERVER_PORT = "$BePort"
  $env:CORS_ALLOWED_ORIGINS = "http://127.0.0.1:$FePort"
  # UTC: Windows ở Việt Nam báo múi giờ "Asia/Saigon", tên cũ mà PostgreSQL 16 từ chối khi kết nối
  # (FATAL: invalid value for parameter "TimeZone"). API vẫn trả thời gian UTC như trước.
  $java = Start-Process cmd.exe -ArgumentList "/c", "mvnw.cmd -q spring-boot:run `"-Dspring-boot.run.jvmArguments=-Duser.timezone=UTC`"" -WorkingDirectory $Backend -PassThru -NoNewWindow `
    -RedirectStandardOutput (Join-Path $Evidence "backend.log") -RedirectStandardError (Join-Path $Evidence "backend.err.log")
  $started += $java
  # Lần đầu Maven tải thư viện nên có thể mất vài phút.
  Wait-Url "http://127.0.0.1:$BePort/api/v1/health" 600 "Java backend" $java

  Step "Frontend Vite ở cổng $FePort"
  $env:VITE_API_URL = "http://127.0.0.1:$BePort"; $env:VITE_MOCK_MODE = "true"
  $vite = Start-Process cmd.exe -ArgumentList "/c", "npm run dev -- --host 127.0.0.1 --port $FePort --strictPort" -WorkingDirectory $Frontend `
    -PassThru -NoNewWindow -RedirectStandardOutput (Join-Path $Evidence "vite.log") -RedirectStandardError (Join-Path $Evidence "vite.err.log")
  $started += $vite
  Wait-Url "http://127.0.0.1:$FePort/" 120 "Vite" $vite

  Step "Trình duyệt headless (profile riêng, không dùng profile cá nhân)"
  $profileDir = (New-Item -ItemType Directory -Force (Join-Path $Evidence "browser-profile")).FullName
  $edge = Start-Process $EdgePath -ArgumentList "--headless=new", "--disable-gpu", "--no-first-run", "--disable-background-networking",
    "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=$CdpPort", "--user-data-dir=`"$profileDir`"", "about:blank" -PassThru -WindowStyle Hidden
  $started += $edge
  Wait-Url "http://127.0.0.1:$CdpPort/json/version" 30 "DevTools của trình duyệt"

  Step "Chạy kịch bản VLRA-44 (FastAPI mock do kịch bản tự bật/tắt ở cổng $RagPort)"
  $env:FE_URL = "http://127.0.0.1:$FePort"; $env:BE_URL = "http://127.0.0.1:$BePort"; $env:RAG_PORT = "$RagPort"
  $env:CDP_URL = "http://127.0.0.1:$CdpPort"; $env:PYTHON = $Python; $env:REPO_ROOT = $Root; $env:EVIDENCE_DIR = $Evidence
  Push-Location $Frontend; & node tests/browser/vlra44-e2e.mjs; $e2eCode = $LASTEXITCODE; Pop-Location
  if ($e2eCode -ne 0) { Write-Host "Có kịch bản FAIL, xem $Evidence\results.json" -ForegroundColor Yellow }
  else { Write-Host "Tất cả kịch bản PASS. Evidence: $Evidence" -ForegroundColor Green }
}
finally {
  Step "Dọn dẹp"
  foreach ($p in $started) { Stop-Tree $p }
  if ($UseDocker) { & docker rm -f vlra44-pg 2>$null | Out-Null }
  Write-Host "Đã dừng các tiến trình do script mở."
}
