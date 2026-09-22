<#
.SYNOPSIS
    Run the whole app — API, web, browser — from one command.

.DESCRIPTION
    Three things this exists to get right, because each has already cost an hour.

    NEXT_PUBLIC_API_BASE and WEB_ORIGINS must agree. The first is baked into the
    web bundle, the second is the API's CORS list. Set one and not the other and
    you get a page that renders and then fetches nothing, with the only evidence
    in the browser console.

    A busy port is found before anything starts, rather than after one process
    is up and the other is confused.

    Both processes die together. A launcher that exits leaving uvicorn on port
    8000 makes the next run fail for a reason that looks unrelated.

    Credentials come from a .env file beside the repository, which is never
    committed. Nothing here prints or forwards a value.

.EXAMPLE
    .\scripts\start.ps1
    .\scripts\start.ps1 -ApiPort 8080 -WebPort 3001 -NoBrowser
#>
[CmdletBinding()]
param(
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Say($text) { Write-Host $text }
function Die($text) { Write-Host "오류: $text" -ForegroundColor Red; exit 1 }

function Get-FreePort([int]$start) {
    foreach ($port in $start..($start + 40)) {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
        try { $listener.Start(); $listener.Stop(); return $port } catch { } finally { }
    }
    Die "$start 부근에 빈 포트가 없다."
}

# --- credentials -------------------------------------------------------------
$envFile = Join-Path $root '.env'
if (Test-Path $envFile) {
    Say '· .env 읽는 중'
    foreach ($line in Get-Content $envFile) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $split = $trimmed.IndexOf('=')
        if ($split -lt 1) { continue }
        $name = $trimmed.Substring(0, $split).Trim()
        $value = $trimmed.Substring($split + 1).Trim().Trim('"').Trim("'")
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}

# --- prerequisites -----------------------------------------------------------
# `??` is PowerShell 7 only, and start.cmd runs Windows PowerShell 5.1.
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) { Die 'python이 없다. 3.10 이상을 설치한다: winget install Python.Python.3.12' }
& $python.Source -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) { Die 'Python 3.10 이상이 필요하다.' }

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Die 'node가 없다. LTS를 설치한다: winget install OpenJS.NodeJS.LTS'
}
$nodeVersion = [version]((node --version).TrimStart('v'))
$nodeOk = ($nodeVersion -ge [version]'20.0.0') -or
          ($nodeVersion -ge [version]'18.18.0' -and $nodeVersion -lt [version]'19.0.0') -or
          ($nodeVersion -ge [version]'19.8.0' -and $nodeVersion -lt [version]'20.0.0')
if (-not $nodeOk) {
    Die "Node $nodeVersion 는 Next.js가 받지 않는다. 20 LTS 이상을 설치한다: winget install OpenJS.NodeJS.LTS"
}

& $python.Source -c "import fastapi, uvicorn" 2>$null
if ($LASTEXITCODE -ne 0) { Die 'API 의존성이 없다: pip install -r apps/api/requirements.txt' }

if (-not (Test-Path (Join-Path $root 'apps/web/node_modules'))) {
    Say '· 웹 의존성 설치 (npm ci) — 처음 한 번만 걸린다'
    Push-Location (Join-Path $root 'apps/web')
    try { npm ci } finally { Pop-Location }
}

# --- ports -------------------------------------------------------------------
$ApiPort = Get-FreePort $ApiPort
$WebPort = Get-FreePort $WebPort
$apiBase = "http://127.0.0.1:$ApiPort"
$webUrl = "http://localhost:$WebPort"
# The two variables that have to agree, set in one place.
$env:WEB_ORIGINS = "http://localhost:$WebPort,http://127.0.0.1:$WebPort"
$env:NEXT_PUBLIC_API_BASE = $apiBase

# --- run ---------------------------------------------------------------------
$api = $null
$web = $null

function Stop-Tree($process) {
    if (-not $process -or $process.HasExited) { return }
    # /T because `npx next dev` runs the server in a child of its own.
    & taskkill /PID $process.Id /T /F *> $null
}

try {
    Say "· API   $apiBase"
    $api = Start-Process -FilePath $python.Source -PassThru -NoNewWindow `
        -ArgumentList '-m', 'uvicorn', 'apps.api.main:app', '--host', '127.0.0.1', '--port', "$ApiPort"

    $ready = $false
    foreach ($attempt in 1..60) {
        if ($api.HasExited) { Die 'API가 시작하지 못했다. 위 로그를 본다.' }
        try {
            Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "$apiBase/api/health" | Out-Null
            $ready = $true; break
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $ready) { Die 'API가 60초 안에 응답하지 않았다.' }

    Say "· 웹    $webUrl"
    $web = Start-Process -FilePath 'npx.cmd' -PassThru -NoNewWindow `
        -WorkingDirectory (Join-Path $root 'apps/web') `
        -ArgumentList 'next', 'dev', '-p', "$WebPort"

    foreach ($attempt in 1..90) {
        if ($web.HasExited) { Die '웹이 시작하지 못했다. 위 로그를 본다.' }
        try {
            Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 $webUrl | Out-Null
            break
        } catch { Start-Sleep -Seconds 1 }
    }

    Say ''
    Say "  열림: $webUrl/pipeline"
    Say '  끄려면 이 창에서 Ctrl+C (또는 창을 닫는다)'
    Say ''
    if (-not $NoBrowser) { Start-Process "$webUrl/pipeline" }

    while (-not $api.HasExited -and -not $web.HasExited) { Start-Sleep -Seconds 1 }
}
finally {
    Say ''
    Say '· 종료 중'
    Stop-Tree $web
    Stop-Tree $api
}
