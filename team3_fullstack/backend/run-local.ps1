param(
    [ValidateSet('run', 'test', 'package')][string]$Task = 'run',
    [string]$Maven = '.\mvnw.cmd',
    [string]$EnvFile = '.env',
    [ValidateRange(1, 65535)][int]$Port,
    [string]$AllowedOrigins
)

$ErrorActionPreference = 'Stop'
$savedEnvironment = @{}
$supportedKeys = @('JAVA_HOME', 'SPRING_PROFILES_ACTIVE', 'SERVER_PORT', 'CORS_ALLOWED_ORIGINS', 'MOCK_ANSWER_STATUS', 'MOCK_QUERY_SCENARIO', 'MOCK_ARTICLE_SCENARIO')
foreach ($key in $supportedKeys) {
    $savedEnvironment[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
}
Push-Location $PSScriptRoot
try {
    # Parse without changing process values: explicit arguments > terminal > file > Spring defaults.
    $fileValues = @{}
    $dotenvPath = if ([IO.Path]::IsPathRooted($EnvFile)) { $EnvFile } else { Join-Path $PSScriptRoot $EnvFile }
    if ($PSBoundParameters.ContainsKey('EnvFile') -and !(Test-Path -LiteralPath $dotenvPath -PathType Leaf)) {
        throw 'The specified environment file does not exist.'
    }
    if (Test-Path -LiteralPath $dotenvPath) {
        foreach ($line in Get-Content -LiteralPath $dotenvPath -Encoding UTF8) {
            $entry = $line.Trim()
            if (!$entry -or $entry.StartsWith('#')) { continue }
            if ($entry -notmatch '^([A-Z][A-Z0-9_]*)=(.*)$') {
                throw 'Invalid .env entry. Use KEY=value, without shell expressions.'
            }
            $key = $Matches[1]
            $value = $Matches[2].Trim()
            if ($key -notin $supportedKeys) {
                throw "Unsupported backend .env key: $key"
            }
            if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            $fileValues[$key] = $value
        }
    }
    # Only explicitly supplied Port/AllowedOrigins override the corresponding settings.
    $overrides = @{}
    if ($PSBoundParameters.ContainsKey('Port')) { $overrides['SERVER_PORT'] = $Port.ToString() }
    if ($PSBoundParameters.ContainsKey('AllowedOrigins')) { $overrides['CORS_ALLOWED_ORIGINS'] = $AllowedOrigins }
    foreach ($key in $supportedKeys) {
        $supplied = $true
        if ($overrides.ContainsKey($key)) {
            $value = $overrides[$key]
        } elseif ($null -ne $savedEnvironment[$key]) {
            $value = $savedEnvironment[$key]
        } elseif ($fileValues.ContainsKey($key)) {
            $value = $fileValues[$key]
        } else {
            $supplied = $false
        }
        if ($supplied) {
            # Windows PowerShell removes an env key when assigned an empty string.
            # Reject a supplied blank value before that can silently activate a Spring default.
            if ([string]::IsNullOrWhiteSpace($value)) { throw "$key cannot be blank when supplied." }
            [Environment]::SetEnvironmentVariable($key, $value, 'Process')
        }
    }
    if ($env:SPRING_PROFILES_ACTIVE -and $env:SPRING_PROFILES_ACTIVE -ne 'mock') {
        throw 'Only the mock profile is implemented. Use SPRING_PROFILES_ACTIVE=mock.'
    }
    if (!$env:JAVA_HOME -or !(Test-Path -LiteralPath (Join-Path $env:JAVA_HOME 'bin\javac.exe'))) {
        throw 'Set JAVA_HOME to a JDK 25 installation (in backend/.env or the current terminal).'
    }
    $javaVersion = & (Join-Path $env:JAVA_HOME 'bin\javac.exe') -version 2>&1
    if ($javaVersion -notmatch '^javac 25(?:\.|$)') {
        throw 'This pom.xml requires JDK 25. Set JAVA_HOME accordingly.'
    }
    $goal = switch ($Task) {
        'run' { 'spring-boot:run' }
        'test' { 'test' }
        'package' { 'package' }
    }
    $mavenCommand = Get-Command -Name $Maven -ErrorAction Stop
    # PowerShell 5.1 turns native stderr into ErrorRecords when output is redirected.
    # Maven/JVM warnings on stderr are not failures: use the command's exit code.
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $mavenCommand -B -ntp $goal
        $mavenExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($mavenExitCode -ne 0) { throw "Maven failed with exit code $mavenExitCode." }
}
finally {
    foreach ($key in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($key, $savedEnvironment[$key], 'Process')
    }
    Pop-Location
}
