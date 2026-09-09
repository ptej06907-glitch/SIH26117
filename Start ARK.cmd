@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo The local Python environment is missing. See README.md.
  pause
  exit /b 1
)
echo ARK is starting at http://127.0.0.1:8765
echo Keep this window open while using the workbench.
".venv\Scripts\python.exe" -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
pause
