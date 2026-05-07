param(
    [int]$ApiPort = 8000,
    [int]$DashboardPort = 3000,
    [string]$DashboardToken = "local-dev-token"
)

$ErrorActionPreference = "Stop"
$failures = New-Object System.Collections.Generic.List[string]
$headers = @{ "X-Quant-Evo-Dashboard-Token" = $DashboardToken }

function Test-JsonEndpoint {
    param(
        [string]$Name,
        [string]$Url,
        [hashtable]$Headers = @{}
    )
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -Headers $Headers -TimeoutSec 10
        if ($response.StatusCode -ne 200) {
            $failures.Add("${Name}: HTTP $($response.StatusCode)")
            return
        }
        $null = $response.Content | ConvertFrom-Json
        Write-Host "ok $Name"
    } catch {
        $failures.Add("${Name}: $($_.Exception.Message)")
    }
}

function Test-Page {
    param(
        [string]$Path
    )
    $url = "http://127.0.0.1:$DashboardPort$Path"
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 15
        if ($response.StatusCode -ne 200) {
            $failures.Add("page ${Path}: HTTP $($response.StatusCode)")
            return
        }
        if ($response.Content.Length -lt 1000) {
            $failures.Add("page ${Path}: response too small")
            return
        }
        Write-Host "ok page $Path"
    } catch {
        $failures.Add("page ${Path}: $($_.Exception.Message)")
    }
}

Test-JsonEndpoint -Name "healthz" -Url "http://127.0.0.1:$ApiPort/healthz"
Test-JsonEndpoint -Name "doctor" -Url "http://127.0.0.1:$ApiPort/api/v1/system/doctor" -Headers $headers
Test-JsonEndpoint -Name "strategy hypotheses" -Url "http://127.0.0.1:$ApiPort/api/v1/strategy/hypotheses" -Headers $headers
Test-JsonEndpoint -Name "strategy factor replay backtests" -Url "http://127.0.0.1:$ApiPort/api/v1/strategy/backtests" -Headers $headers
Test-JsonEndpoint -Name "market data providers" -Url "http://127.0.0.1:$ApiPort/api/v1/market-data/providers" -Headers $headers
Test-JsonEndpoint -Name "market data factors" -Url "http://127.0.0.1:$ApiPort/api/v1/market-data/factors" -Headers $headers
Test-JsonEndpoint -Name "live readiness report" -Url "http://127.0.0.1:$ApiPort/api/v1/execution/live-readiness-report" -Headers $headers
Test-JsonEndpoint -Name "approvals" -Url "http://127.0.0.1:$ApiPort/api/v1/approvals" -Headers $headers

@("/", "/research", "/strategy", "/data", "/trading", "/learning", "/evolution", "/system", "/incidents") | ForEach-Object {
    Test-Page -Path $_
}

if ($failures.Count -gt 0) {
    Write-Host "EvoQ local smoke failed:"
    $failures | ForEach-Object { Write-Host "fail $_" }
    exit 1
}

Write-Host "EvoQ local smoke passed."
