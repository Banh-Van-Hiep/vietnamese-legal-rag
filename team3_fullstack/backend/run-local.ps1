param(
    [ValidateSet('run', 'test', 'package')][string]$Task = 'run',
    [string]$Maven = '.\mvnw.cmd'
)

$ErrorActionPreference = 'Stop'
$savedEnvironment = @{}
Push-Location $PSScriptRoot
try {
    $dotenvPath = Join-Path $PSScriptRoot '.env'
    if (Test-Path -LiteralPath $dotenvPath) {
        foreach ($line in Get-Content -LiteralPath $dotenvPath -Encoding UTF8) {
            $entry = $line.Trim()
            if (!$entry -or $entry.StartsWith('#')) { continue }
            if ($entry -notmatch '^([A-Z][A-Z0-9_]*)=(.*)$') {
                throw 'Invalid .env entry. Use KEY=value, without shell expressions.'
            }
            $key = $Matches[1]
            $value = $Matches[2].Trim()
            if ($key -notin @('JAVA_HOME', 'SPRING_PROFILES_ACTIVE', 'SERVER_PORT', 'CORS_ALLOWED_ORIGINS', 'MOCK_ANSWER_STATUS')) {
                throw "Unsupported backend .env key: $key"
            }
            if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            if (!$savedEnvironment.ContainsKey($key)) {
                $savedEnvironment[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
            }
            [Environment]::SetEnvironmentVariable($key, $value, 'Process')
        }
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
    & $Maven $goal
    if ($LASTEXITCODE -ne 0) { throw "Maven failed with exit code $LASTEXITCODE." }
}
finally {
    foreach ($key in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($key, $savedEnvironment[$key], 'Process')
    }
    Pop-Location
}
