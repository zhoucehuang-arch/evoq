param(
    [int]$ApiPort = 8000,
    [int]$DashboardPort = 3000,
    [string]$DashboardToken = "local-dev-token",
    [string]$DatabasePath = ".runtime/evoq-local.db"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$LogDir = Join-Path $RuntimeDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-PortOpen {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    return $null -ne $connection
}

function Resolve-Python {
    $candidates = @(
        $env:PYTHON,
        "C:\Users\hzc_\AppData\Local\Programs\Python\Python313\python.exe",
        "python"
    ) | Where-Object { $_ -and $_.Trim() }

    foreach ($candidate in $candidates) {
        try {
            $version = & $candidate -c "import sys; print(sys.version_info.major)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $version.Trim() -eq "3") {
                return $candidate
            }
        } catch {
        }
    }
    throw "No usable Python 3 interpreter found. Set PYTHON to a valid python.exe path."
}

$Python = Resolve-Python
$DbFullPath = Join-Path $RepoRoot $DatabasePath
$DbDir = Split-Path $DbFullPath -Parent
New-Item -ItemType Directory -Force -Path $DbDir | Out-Null

$BackendLog = Join-Path $LogDir "local-backend.log"
$DashboardLog = Join-Path $LogDir "local-dashboard.log"
$PidPath = Join-Path $RuntimeDir "local-pids.json"

$backendStarted = $false
$dashboardStarted = $false

if (Test-PortOpen -Port $ApiPort) {
    Write-Host "API port $ApiPort is already in use. Reusing the existing process."
} else {
    $backendCommand = @"
`$env:PYTHONPATH='src'
`$env:QE_REPO_ROOT='$RepoRoot'
`$env:QE_POSTGRES_URL='sqlite+pysqlite:///$DbFullPath'
`$env:QE_DASHBOARD_API_TOKEN='$DashboardToken'
Set-Location '$RepoRoot'
& '$Python' -m uvicorn quant_evo_nextgen.api.main:app --host 127.0.0.1 --port $ApiPort *> '$BackendLog'
"@
    $backend = Start-Process -FilePath powershell.exe -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand) -WindowStyle Hidden -PassThru
    $backendStarted = $true
}

if (Test-PortOpen -Port $DashboardPort) {
    Write-Host "Dashboard port $DashboardPort is already in use. Reusing the existing process."
} else {
    $dashboardCommand = @"
`$env:NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:$ApiPort'
`$env:QE_DASHBOARD_API_TOKEN='$DashboardToken'
Set-Location '$RepoRoot\apps\dashboard-web'
npm run dev -- --hostname 127.0.0.1 --port $DashboardPort *> '$DashboardLog'
"@
    $dashboard = Start-Process -FilePath powershell.exe -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $dashboardCommand) -WindowStyle Hidden -PassThru
    $dashboardStarted = $true
}

@{
    api_port = $ApiPort
    dashboard_port = $DashboardPort
    dashboard_token = $DashboardToken
    database = $DbFullPath
    backend_pid = if ($backendStarted) { $backend.Id } else { $null }
    dashboard_pid = if ($dashboardStarted) { $dashboard.Id } else { $null }
    backend_log = $BackendLog
    dashboard_log = $DashboardLog
    started_at = (Get-Date).ToString("o")
} | ConvertTo-Json | Set-Content -Encoding UTF8 -Path $PidPath

Write-Host "EvoQ local runtime is starting."
Write-Host "Dashboard: http://127.0.0.1:$DashboardPort"
Write-Host "API health: http://127.0.0.1:$ApiPort/healthz"
Write-Host "Logs: $LogDir"
Write-Host "Run smoke: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1"
