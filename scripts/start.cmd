@echo off
rem Double-click this. It runs start.ps1 without changing the machine's
rem execution policy: asking somebody to loosen a machine-wide security
rem setting in order to open an app is not a reasonable thing to ask.
rem
rem ASCII only, on purpose. cmd.exe decodes this file in the console's OEM
rem code page, which is neither UTF-8 nor what the .ps1 files use, and a
rem mis-decoded batch file fails in ways that look like something else.
setlocal
set "HERE=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%start.ps1" %*
if errorlevel 1 (
  echo.
  echo Startup failed. Read the error above, then press any key to close.
  pause >nul
)
endlocal
