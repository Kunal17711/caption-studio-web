@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (py -3.12 -m venv .venv)
.venv\Scripts\python.exe -m pip install -r requirements.txt --prefer-binary
start "" http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
pause
