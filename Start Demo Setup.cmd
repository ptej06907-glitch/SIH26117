@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo The local Python environment is missing. See README.md.
  pause
  exit /b 1
)
set "ARK_DB_PATH=%CD%\demo-data\workbench.sqlite3"
set "ARK_PUBLIC_DEMO_ORIGIN="
echo Isolated synthetic demo setup: http://127.0.0.1:8767
echo Create demo accounts and upload only synthetic or public materials.
echo Stop this server before enabling Tailscale Funnel.
".venv\Scripts\python.exe" -m uvicorn backend.app:app --host 127.0.0.1 --port 8767 --workers 1
pause
