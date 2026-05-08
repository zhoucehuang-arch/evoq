$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$pythonCandidates = @(
    (Join-Path $repoRoot ".venv\Scripts\python.exe"),
    $env:PYTHON,
    "python3",
    "python"
) | Where-Object { $_ -and $_.Trim() }

$python = $null
foreach ($candidate in $pythonCandidates) {
    $command = Get-Command $candidate -ErrorAction SilentlyContinue
    if (-not $command) {
        continue
    }
    $source = $command.Source
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $source -c "import sys, pytest; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
    $ErrorActionPreference = $previousErrorActionPreference
    if ($LASTEXITCODE -eq 0) {
        $python = $source
        break
    }
}

if (-not $python) {
    throw "No usable Python executable found. Install Python >= 3.11 or update ops/tools/run_tests.ps1."
}

$tmpRoot = Join-Path $repoRoot ".tmp\pytest"
New-Item -ItemType Directory -Force -Path $tmpRoot | Out-Null

$env:PYTHONPATH = "ops/tools/pytest_sitecustomize;src"
$env:TMP = $tmpRoot
$env:TEMP = $tmpRoot

$stamp = Get-Date -Format "yyyyMMddHHmmss"
$baseTemp = Join-Path $tmpRoot "pytest-$stamp"

& $python -m pytest @args --basetemp $baseTemp -p no:cacheprovider
