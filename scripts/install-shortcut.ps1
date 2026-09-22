<#
.SYNOPSIS
    Put a launcher icon on the Desktop (and optionally the Start menu).

.DESCRIPTION
    The shortcut points at start.cmd, so a double-click runs the same launcher
    a terminal would. It changes nothing else on the machine: no service, no
    registry key, no startup entry. Removing it is deleting the file.

.EXAMPLE
    .\scripts\install-shortcut.ps1
    .\scripts\install-shortcut.ps1 -StartMenu
    .\scripts\install-shortcut.ps1 -Remove
#>
[CmdletBinding()]
param(
    [string]$Name = 'Outlier Expectation Gap',
    [switch]$StartMenu,
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$targets = @([IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), "$Name.lnk"))
if ($StartMenu) {
    $programs = [Environment]::GetFolderPath('Programs')
    $targets += [IO.Path]::Combine($programs, "$Name.lnk")
}

if ($Remove) {
    foreach ($path in $targets) {
        if (Test-Path $path) { Remove-Item $path -Force; Write-Host "삭제: $path" }
        else { Write-Host "없음: $path" }
    }
    exit 0
}

$launcher = Join-Path $root 'scripts\start.cmd'
if (-not (Test-Path $launcher)) { Write-Host "오류: $launcher 가 없다" -ForegroundColor Red; exit 1 }

$icon = Join-Path $root 'assets\harness.ico'
if (-not (Test-Path $icon)) {
    # The icon is generated, not committed as an opaque blob, so it can be
    # rebuilt on a checkout that has not run the generator.
    Write-Host '· 아이콘 생성 중 (scripts/make_icon.py)'
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
    if ($python) { & $python.Source (Join-Path $root 'scripts\make_icon.py') | Out-Null }
}

$shell = New-Object -ComObject WScript.Shell
foreach ($path in $targets) {
    $link = $shell.CreateShortcut($path)
    $link.TargetPath = $launcher
    $link.WorkingDirectory = $root
    $link.Description = '장기 아웃라이어 기대차 투자 하네스 — API와 웹을 함께 실행한다'
    if (Test-Path $icon) { $link.IconLocation = $icon }
    $link.Save()
    Write-Host "만듦: $path"
}
Write-Host ''
Write-Host '아이콘을 더블클릭하면 API와 웹이 함께 뜨고 브라우저가 열린다.'
Write-Host '창을 닫으면 둘 다 종료된다.'
