@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 (echo Python 3.12 required & pause & exit /b 1)
)
.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt "pyinstaller>=6.10,<7" --prefer-binary
if errorlevel 1 (echo Install failed & pause & exit /b 1)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --windowed --name CaptionStudio --add-data "static;static" --collect-all faster_whisper --collect-all ctranslate2 --collect-all tokenizers --collect-all av --collect-all imageio_ffmpeg --collect-all webview --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto --hidden-import uvicorn.protocols.http.auto --hidden-import uvicorn.protocols.websockets.auto --hidden-import uvicorn.lifespan.on --hidden-import multipart --hidden-import python_multipart desktop.py
if errorlevel 1 (echo Build failed, see the error above & pause & exit /b 1)
echo.
echo EXE READY: dist\CaptionStudio\CaptionStudio.exe
echo Keep the entire CaptionStudio folder together when sharing.
pause
