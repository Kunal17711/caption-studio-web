@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 (
    echo Please install Python 3.12, then retry.
    pause
    exit /b 1
  )
)
.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt --prefer-binary
if errorlevel 1 (
  echo Install failed. Check internet, then retry.
  pause
  exit /b 1
)
.venv\Scripts\python.exe desktop.py
if errorlevel 1 pause
