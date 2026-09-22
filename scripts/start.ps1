<#
    THIS FILE MUST STAY UTF-8 **WITH BOM**.

    Windows PowerShell 5.1 — which start.cmd runs — decodes a BOM-less .ps1 as
    the system ANSI code page. On Korean Windows that is CP949, where the third
    byte of 중 (EC A4 91) is a valid lead byte and swallows the ' that follows
    it. The string then never closes and the parse fails many lines later, at a
    brace that has nothing wrong with it. tests/test_launcher.py asserts the BOM
    so an editor cannot quietly drop it again.

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

function Invoke-Native([string]$File, [string[]]$Arguments, [switch]$Show) {
    # Windows PowerShell turns a native command's *stderr* into a terminating
    # error when $ErrorActionPreference is 'Stop'. pip, npm and python all
    # write perfectly ordinary progress there, so every external call goes
    # through here with the preference relaxed and the exit code checked
    # explicitly — which is the thing we actually care about.
    #
    # -Show keeps the output. A silent `npm ci` looks like a hung launcher for
    # the several minutes it takes the first time.
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        if ($Show) { & $File @Arguments 2>&1 | Out-Host }
        else { & $File @Arguments 2>&1 | Out-Null }
        return $LASTEXITCODE
    } finally { $ErrorActionPreference = $previous }
}

function Get-FreePort([int]$start) {
    foreach ($port in $start..($start + 40)) {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
        try { $listener.Start(); $listener.Stop(); return $port } catch { }
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
if ((Invoke-Native $python.Source @('-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)')) -ne 0) {
    Die 'Python 3.10 이상이 필요하다: winget install Python.Python.3.12'
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Die 'node가 없다. LTS를 설치한다: winget install OpenJS.NodeJS.LTS'
}
$nodeRaw = (node --version).Trim().TrimStart('v')
$nodeVersion = $null
# A nightly or release-candidate build carries a suffix [version] refuses.
[void][version]::TryParse(($nodeRaw -split '-')[0], [ref]$nodeVersion)
if (-not $nodeVersion) { Die "Node 버전을 읽지 못했다: $nodeRaw" }
$nodeOk = ($nodeVersion -ge [version]'20.0.0') -or
          ($nodeVersion -ge [version]'18.18.0' -and $nodeVersion -lt [version]'19.0.0') -or
          ($nodeVersion -ge [version]'19.8.0' -and $nodeVersion -lt [version]'20.0.0')
if (-not $nodeOk) {
    Die "Node $nodeRaw 는 Next.js가 받지 않는다. 20 LTS 이상을 설치한다: winget install OpenJS.NodeJS.LTS"
}

if ((Invoke-Native $python.Source @('-c', 'import fastapi, uvicorn')) -ne 0) {
    Die 'API 의존성이 없다: pip install -r apps/api/requirements.txt'
}

if (-not (Test-Path (Join-Path $root 'apps/web/node_modules'))) {
    Say '· 웹 의존성 설치 (npm ci) — 처음 한 번만 걸린다'
    Push-Location (Join-Path $root 'apps/web')
    try {
        if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
            Die 'npm이 없다. Node LTS를 설치하면 함께 들어온다.'
        }
        if ((Invoke-Native $env:ComSpec @('/c', 'npm', 'ci') -Show) -ne 0) {
            Die 'npm ci 실패 — 위 로그를 본다.'
        }
    } finally { Pop-Location }
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
    Invoke-Native 'taskkill' @('/PID', "$($process.Id)", '/T', '/F') | Out-Null
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
    if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
        Die 'npx가 없다. Node LTS를 설치하면 함께 들어온다.'
    }
    # Through cmd.exe, never through a resolved path. Node ships both `npx`
    # (an extensionless shim) and `npx.cmd`; Get-Command returns the first,
    # and Start-Process cannot execute it — "올바른 Win32 응용 프로그램이 아닙니다".
    # cmd.exe applies PATHEXT and finds the .cmd, and taskkill /T still reaches
    # the node process underneath it.
    $web = Start-Process -FilePath $env:ComSpec -PassThru -NoNewWindow `
        -WorkingDirectory (Join-Path $root 'apps/web') `
        -ArgumentList '/c', 'npx', 'next', 'dev', '-p', "$WebPort"

    $webReady = $false
    foreach ($attempt in 1..90) {
        if ($web.HasExited) { Die '웹이 시작하지 못했다. 위 로그를 본다.' }
        try {
            Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 $webUrl | Out-Null
            $webReady = $true; break
        } catch { Start-Sleep -Seconds 1 }
    }
    # Without this the script would announce the URL and open a browser at a
    # page that never came up, which reads as the app being broken rather than
    # as the build still failing.
    if (-not $webReady) { Die '웹이 90초 안에 응답하지 않았다. 위 로그를 본다.' }

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
