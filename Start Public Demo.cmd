@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo The local Python environment is missing. See README.md.
  pause
  exit /b 1
)
if "%~1"=="" (
  echo Usage: Start Public Demo.cmd https://YOUR-TAILSCALE-HOST.ts.net
  pause
  exit /b 1
)
set "ARK_DB_PATH=%CD%\demo-data\workbench.sqlite3"
if not exist "%ARK_DB_PATH%" (
  echo The isolated demo database does not exist. Run Start Demo Setup.cmd first.
  pause
  exit /b 1
)
if not exist "demo-data\.encrypted-storage" (
  echo Encrypt the stopped demo first: python scripts\encrypt_local_data.py --directory demo-data
  pause
  exit /b 1
)
if not exist "demo-data\.require-antivirus" (
  echo Mandatory upload scanning is not enabled for the demo.
  pause
  exit /b 1
)
set "ARK_PUBLIC_DEMO_ORIGIN=%~1"
echo Public synthetic demo starting on local port 8766.
echo Keep this window open while judges may use the link.
".venv\Scripts\python.exe" -m uvicorn backend.app:app --host 127.0.0.1 --port 8766 --workers 1
pause
