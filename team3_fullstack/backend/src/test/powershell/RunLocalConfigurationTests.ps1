param(
    [string]$JavaHome = $env:JAVA_HOME,
    [string]$RunnerPath = (Join-Path $PSScriptRoot '..\..\..\run-local.ps1')
)

# Maven is stubbed here; real Spring binding/defaults require separate startup smoke checks.
$ErrorActionPreference = 'Stop'
$runner = (Resolve-Path -LiteralPath $RunnerPath).Path
$backend = Split-Path -Parent $runner
$keys = @('JAVA_HOME','SPRING_PROFILES_ACTIVE','SERVER_PORT','CORS_ALLOWED_ORIGINS','MOCK_ANSWER_STATUS','MOCK_QUERY_SCENARIO','MOCK_ARTICLE_SCENARIO')
$saved = @{}
foreach ($key in ($keys + @('T01_CAPTURE_PATH','T01_STUB_EXIT','T01_STUB_WARN'))) { $saved[$key] = [Environment]::GetEnvironmentVariable($key, 'Process') }
$initialLocation = (Get-Location).Path
$initialExitCode = $global:LASTEXITCODE
$utf8 = New-Object System.Text.UTF8Encoding($false)
$fixtureRoot = Join-Path $backend ('target\t01\runner-' + [guid]::NewGuid().ToString('N'))
$results = New-Object 'System.Collections.Generic.List[object]'

function Assert-Equal($Actual, $Expected, [string]$Label) {
    if ($Actual -cne $Expected) { throw "$Label expected=[$Expected] actual=[$Actual]" }
}

function Invoke-Case {
    param(
        [string]$Name, [hashtable]$Process = @{}, [string[]]$Entries = @(),
        [hashtable]$Arguments = @{}, [hashtable]$Expected = @{},
        [string]$ErrorPattern, [int]$ExitCode = 0, [string]$TestRunner = $runner,
        [switch]$DefaultFile, [switch]$MissingFile, [switch]$Warning
    )
    $casePath = Join-Path $fixtureRoot $Name
    New-Item -ItemType Directory -Path $casePath -Force | Out-Null
    $envFile = Join-Path $casePath 'case.env'
    if (!$MissingFile) { [IO.File]::WriteAllLines($envFile, $Entries, $utf8) }
    foreach ($key in $keys) { [Environment]::SetEnvironmentVariable($key, $null, 'Process') }
    $env:JAVA_HOME = $JavaHome
    foreach ($key in $Process.Keys) { [Environment]::SetEnvironmentVariable($key, $Process[$key], 'Process') }
    $env:T01_CAPTURE_PATH = Join-Path $casePath 'capture.json'
    $env:T01_STUB_EXIT = $ExitCode.ToString()
    $env:T01_STUB_WARN = $Warning.ToString()
    $before = @{}
    foreach ($key in $keys) { $before[$key] = [Environment]::GetEnvironmentVariable($key, 'Process') }
    $locationBefore = (Get-Location).Path
    $invoke = @{ Maven = $stub; Task = 'test' }
    if (!$DefaultFile) { $invoke['EnvFile'] = $envFile }
    foreach ($key in $Arguments.Keys) { $invoke[$key] = $Arguments[$key] }
    $runnerError = $null
    try { & $TestRunner @invoke | Out-Null } catch { $runnerError = $_.Exception.Message }
    try {
        # Always check restoration, including when the outcome/exception is wrong.
        foreach ($key in $keys) { Assert-Equal ([Environment]::GetEnvironmentVariable($key, 'Process')) $before[$key] "restore $key" }
        Assert-Equal (Get-Location).Path $locationBefore 'restore location'
        if ($ErrorPattern) {
            if (!$runnerError -or $runnerError -notmatch $ErrorPattern) { throw "Expected error /$ErrorPattern/; actual=[$runnerError]" }
        } else {
            if ($runnerError) { throw "Unexpected runner error: $runnerError" }
            $capture = Get-Content -Raw -LiteralPath $env:T01_CAPTURE_PATH | ConvertFrom-Json
            foreach ($key in $Expected.Keys) { Assert-Equal $capture.Environment.$key $Expected[$key] "effective $key" }
            $expectedGoal = if ($Arguments.ContainsKey('Task')) { switch ($Arguments.Task) { 'run' { 'spring-boot:run' }; 'package' { 'package' }; default { 'test' } } } else { 'test' }
            Assert-Equal ($capture.Arguments -join ' ') "-B -ntp $expectedGoal" 'Maven arguments'
        }
        $results.Add([pscustomobject]@{ Case=$Name; Result='PASS'; Expected=$(if ($ErrorPattern) { "error /$ErrorPattern/" } else { $Expected }); Actual=$(if ($ErrorPattern) { $runnerError } else { $capture.Environment }); Restoration='PASS' })
        Write-Output "PASS $Name (including env/location restoration)"
    } catch {
        $results.Add([pscustomobject]@{ Case=$Name; Result='FAIL'; Expected=$(if ($ErrorPattern) { $ErrorPattern } else { $Expected }); Actual=$_.Exception.Message })
        Write-Output "FAIL $Name : $($_.Exception.Message)"
    }
}

try {
    if (!$JavaHome -or !(Test-Path -LiteralPath (Join-Path $JavaHome 'bin\javac.exe'))) { throw 'Provide -JavaHome pointing to an installed JDK 25.' }
    $version = & (Join-Path $JavaHome 'bin\javac.exe') -version 2>&1
    if ($version -notmatch '^javac 25(?:\.|$)') { throw 'Harness requires JDK 25.' }
    New-Item -ItemType Directory -Path $fixtureRoot -Force | Out-Null
    $stub = Join-Path $fixtureRoot 'maven-stub.ps1'
    $stubText = @'
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
if ($env:T01_STUB_WARN -eq 'True') { & (Join-Path $PSScriptRoot 'stderr.cmd') 2>&1 | Out-Null }
$values = [ordered]@{}
foreach ($key in @('JAVA_HOME','SPRING_PROFILES_ACTIVE','SERVER_PORT','CORS_ALLOWED_ORIGINS','MOCK_ANSWER_STATUS','MOCK_QUERY_SCENARIO','MOCK_ARTICLE_SCENARIO')) {
    $values[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
}
[IO.File]::WriteAllText($env:T01_CAPTURE_PATH, (@{ Environment=$values; Arguments=$Arguments } | ConvertTo-Json -Depth 4), (New-Object System.Text.UTF8Encoding($false)))
$global:LASTEXITCODE = [int]$env:T01_STUB_EXIT
'@
    [IO.File]::WriteAllText($stub, $stubText, $utf8)
    [IO.File]::WriteAllText((Join-Path $fixtureRoot 'stderr.cmd'), "@echo Controlled native warning 1>&2`r`n@exit /b 0`r`n", $utf8)
    Invoke-Case 'explicit-wins' -Process @{ SERVER_PORT='18082'; CORS_ALLOWED_ORIGINS='http://localhost:55174' } -Entries @('SERVER_PORT=18081','CORS_ALLOWED_ORIGINS=http://127.0.0.1:55173') -Arguments @{ Port=18083; AllowedOrigins='http://localhost:55175' } -Expected @{ SERVER_PORT='18083'; CORS_ALLOWED_ORIGINS='http://localhost:55175' }
    Invoke-Case 'terminal-port-wins' -Process @{ SERVER_PORT='18082' } -Entries @('SERVER_PORT=18081') -Expected @{ SERVER_PORT='18082' }
    Invoke-Case 'terminal-origin-wins' -Process @{ CORS_ALLOWED_ORIGINS='http://localhost:55174' } -Entries @('CORS_ALLOWED_ORIGINS=http://127.0.0.1:55173') -Expected @{ CORS_ALLOWED_ORIGINS='http://localhost:55174' }
    Invoke-Case 'terminal-status-wins' -Process @{ MOCK_ANSWER_STATUS='insufficient_context' } -Entries @('MOCK_ANSWER_STATUS=answered') -Expected @{ MOCK_ANSWER_STATUS='insufficient_context' }
    Invoke-Case 'terminal-query-scenario-wins' -Process @{ MOCK_QUERY_SCENARIO='upstream_timeout' } -Entries @('MOCK_QUERY_SCENARIO=answered') -Expected @{ MOCK_QUERY_SCENARIO='upstream_timeout' }
    Invoke-Case 'terminal-article-scenario-wins' -Process @{ MOCK_ARTICLE_SCENARIO='service_unavailable' } -Entries @('MOCK_ARTICLE_SCENARIO=success') -Expected @{ MOCK_ARTICLE_SCENARIO='service_unavailable' }
    Invoke-Case 'file-scenario-fallback' -Entries @('MOCK_QUERY_SCENARIO=internal_error','MOCK_ARTICLE_SCENARIO=upstream_timeout') -Expected @{ MOCK_QUERY_SCENARIO='internal_error'; MOCK_ARTICLE_SCENARIO='upstream_timeout' }
    Invoke-Case 'invalid-winning-scenarios-not-masked' -Process @{ MOCK_QUERY_SCENARIO='bad'; MOCK_ARTICLE_SCENARIO='wrong' } -Entries @('MOCK_QUERY_SCENARIO=answered','MOCK_ARTICLE_SCENARIO=success') -Expected @{ MOCK_QUERY_SCENARIO='bad'; MOCK_ARTICLE_SCENARIO='wrong' }
    Invoke-Case 'terminal-profile-wins' -Process @{ SPRING_PROFILES_ACTIVE='mock' } -Entries @('SPRING_PROFILES_ACTIVE=unsupported') -Expected @{ SPRING_PROFILES_ACTIVE='mock' }
    Invoke-Case 'terminal-java-wins' -Entries @('JAVA_HOME=Z:/missing-low-priority-jdk') -Expected @{ JAVA_HOME=$JavaHome }
    Invoke-Case 'file-fallback' -Entries @('SPRING_PROFILES_ACTIVE=mock','SERVER_PORT=18081','CORS_ALLOWED_ORIGINS="http://127.0.0.1:55173"',"MOCK_ANSWER_STATUS='answered'") -Expected @{ SPRING_PROFILES_ACTIVE='mock'; SERVER_PORT='18081'; CORS_ALLOWED_ORIGINS='http://127.0.0.1:55173'; MOCK_ANSWER_STATUS='answered' }
    Invoke-Case 'file-java-fallback' -Process @{ JAVA_HOME=$null } -Entries @("JAVA_HOME=$JavaHome") -Expected @{ JAVA_HOME=$JavaHome }
    Invoke-Case 'spring-defaults-unmasked' -Expected @{ SPRING_PROFILES_ACTIVE=$null; SERVER_PORT=$null; CORS_ALLOWED_ORIGINS=$null; MOCK_ANSWER_STATUS=$null; MOCK_QUERY_SCENARIO=$null; MOCK_ARTICLE_SCENARIO=$null }
    foreach ($taskGoal in @('run','package')) { Invoke-Case "goal-$taskGoal" -Arguments @{ Task=$taskGoal } }
    Invoke-Case 'valid-terminal-masks-invalid-file-value' -Process @{ SERVER_PORT='18082'; CORS_ALLOWED_ORIGINS='http://localhost:55174'; MOCK_ANSWER_STATUS='answered' } -Entries @('SERVER_PORT=not-a-port','CORS_ALLOWED_ORIGINS=*','MOCK_ANSWER_STATUS=wrong') -Expected @{ SERVER_PORT='18082'; CORS_ALLOWED_ORIGINS='http://localhost:55174'; MOCK_ANSWER_STATUS='answered' }
    # Semantic errors pass unchanged to Spring; real startup smoke must reject them.
    Invoke-Case 'invalid-winning-server-values-not-masked' -Process @{ SERVER_PORT='not-a-port'; CORS_ALLOWED_ORIGINS='*'; MOCK_ANSWER_STATUS='wrong' } -Entries @('SERVER_PORT=18081','CORS_ALLOWED_ORIGINS=http://localhost:5173','MOCK_ANSWER_STATUS=answered') -Expected @{ SERVER_PORT='not-a-port'; CORS_ALLOWED_ORIGINS='*'; MOCK_ANSWER_STATUS='wrong' }
    foreach ($key in $keys) { Invoke-Case "blank-file-$key" -Process @{ JAVA_HOME=$(if ($key -eq 'JAVA_HOME') { $null } else { $JavaHome }) } -Entries @("$key=") -ErrorPattern 'cannot be blank|JDK 25' }
    Invoke-Case 'explicit-blank-origin' -Process @{ CORS_ALLOWED_ORIGINS='http://localhost:5173' } -Arguments @{ AllowedOrigins='' } -Entries @('CORS_ALLOWED_ORIGINS=http://localhost:5173') -ErrorPattern 'cannot be blank'
    Invoke-Case 'bad-winning-java' -Process @{ JAVA_HOME=(Join-Path $fixtureRoot 'missing-winning-jdk') } -Entries @("JAVA_HOME=$JavaHome") -ErrorPattern 'JDK 25'
    Invoke-Case 'missing-java' -Process @{ JAVA_HOME=$null } -ErrorPattern 'JDK 25'
    Invoke-Case 'bad-winning-profile' -Process @{ SPRING_PROFILES_ACTIVE='unsupported' } -Entries @('SPRING_PROFILES_ACTIVE=mock') -ErrorPattern 'Only the mock profile'
    Invoke-Case 'missing-explicit-file' -MissingFile -ErrorPattern 'specified environment file does not exist'
    Invoke-Case 'syntax-error-after-valid-key' -Entries @('SERVER_PORT=18081','export WRONG=yes') -ErrorPattern 'Invalid .env entry'
    Invoke-Case 'unsupported-key' -Entries @('SERVER_PORT=18081','OTHER_KEY=value') -ErrorPattern 'Unsupported backend .env key'
    Invoke-Case 'maven-nonzero' -Entries @('SERVER_PORT=18081') -ExitCode 7 -ErrorPattern 'Maven failed with exit code 7'
    Invoke-Case 'native-stderr-zero-exit-is-not-failure' -Warning
    Invoke-Case 'missing-maven-command' -Arguments @{ Maven=(Join-Path $fixtureRoot 'missing-maven.cmd') } -ErrorPattern 'not recognized|not found'
    Invoke-Case 'invalid-explicit-port' -Arguments @{ Port=0 } -ErrorPattern 'validation|range|greater than'
    $jdk24 = Join-Path (Split-Path -Parent $JavaHome) 'jdk-24.0.2'
    if (Test-Path -LiteralPath (Join-Path $jdk24 'bin\javac.exe')) { Invoke-Case 'jdk24-winner-not-masked' -Process @{ JAVA_HOME=$jdk24 } -Entries @("JAVA_HOME=$JavaHome") -ErrorPattern 'requires JDK 25' }
    $isolatedRunner = Join-Path $fixtureRoot 'run-local.ps1'
    Copy-Item -LiteralPath $runner -Destination $isolatedRunner
    Invoke-Case 'optional-default-file-absent' -TestRunner $isolatedRunner -DefaultFile -Process @{ SERVER_PORT='18082' } -Expected @{ SERVER_PORT='18082' }
    $report = Join-Path $fixtureRoot 'results.json'
    [IO.File]::WriteAllText($report, (ConvertTo-Json -InputObject @($results.ToArray()) -Depth 6), $utf8)
    Write-Output "Evidence: $report"
    $failed = @($results | Where-Object Result -eq 'FAIL')
    Write-Output "Runner cases: $($results.Count); failures: $($failed.Count)"
    if ($failed.Count) { throw "$($failed.Count) runner configuration cases failed." }
}
finally {
    foreach ($key in $saved.Keys) { [Environment]::SetEnvironmentVariable($key, $saved[$key], 'Process') }
    Set-Location -LiteralPath $initialLocation
    $global:LASTEXITCODE = $initialExitCode
}
