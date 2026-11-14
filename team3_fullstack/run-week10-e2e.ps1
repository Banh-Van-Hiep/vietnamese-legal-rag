<# Week10 UI acceptance. Default: all18 UI states with labelled mock, isolated test DB and owned processes. #>
param(
    [ValidateSet('mock','corpus','live')][string]$Mode = 'mock',
    [string]$Python = '',
    [string]$JavaHome = $env:JAVA_HOME,
    [string]$PgBin = '',
    [string]$BrowserPath = '',
    [string]$OutputDir = '',
    [string]$RagUrl = '',
    [switch]$Bm25Only,
    [string]$Questions = ''
)
$ErrorActionPreference = 'Stop'
$week10Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $Python) {
    foreach ($candidate in @('.venv\Scripts\python.exe', '.local\team3\retrieval-audit-20261019\venv\Scripts\python.exe')) {
        $candidatePath = Join-Path $week10Root $candidate
        if (Test-Path -LiteralPath $candidatePath) { $Python = $candidatePath; break }
    }
    if (-not $Python) { $Python = 'python' }
}
if (-not $JavaHome -and (Test-Path -LiteralPath 'D:\Java\jdk-25')) { $JavaHome = 'D:\Java\jdk-25' }
Push-Location $week10Root
$week10OriginalJavaHome = $env:JAVA_HOME
$week10OriginalPath = $env:Path
try {
    if ($JavaHome) { $env:JAVA_HOME = $JavaHome; $env:Path = (Join-Path $JavaHome 'bin') + ';' + $env:Path }
    $week10Args = @('-X', 'utf8', 'team3_fullstack/tests/run_week10_acceptance.py', '--mode', $Mode)
    if ($PgBin) { $week10Args += @('--pg-bin', $PgBin) }
    if ($BrowserPath) { $week10Args += @('--browser', $BrowserPath) }
    if ($OutputDir) { $week10Args += @('--output-dir', $OutputDir) }
    if ($RagUrl) { $week10Args += @('--rag-url', $RagUrl) }
    if ($Bm25Only) { $week10Args += '--bm25-only' }
    if ($Questions) { $week10Args += @('--questions', $Questions) }
    & $Python @week10Args
    $week10ExitCode = $LASTEXITCODE
}
finally {
    $env:JAVA_HOME = $week10OriginalJavaHome
    $env:Path = $week10OriginalPath
    Pop-Location
}
exit $week10ExitCode
