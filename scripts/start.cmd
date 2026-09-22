@echo off
rem Double-click this. It runs start.ps1 without changing the machine's
rem execution policy, because asking somebody to loosen a security setting to
rem launch an app is not a reasonable thing to ask.
setlocal
set "HERE=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%start.ps1" %*
if errorlevel 1 (
  echo.
  echo 위 오류를 확인한 뒤 아무 키나 누르면 창이 닫힌다.
  pause >nul
)
endlocal
