# Caption Studio Desktop 2.1 — Free, Open Source

A Windows desktop **app** built using Python + FastAPI + pywebview (Edge WebView2). The editing UI runs inside its own desktop window. AI subtitles are generated locally with faster-whisper. **No Render deployment and no paid API required.**

## Run locally on Windows

1. Install Python **3.12** if necessary. On Windows 11 ensure Edge WebView2 Runtime is installed (normally bundled).
2. Extract the complete ZIP. Double-click **START_DESKTOP_WINDOWS.bat**.
3. A standalone Caption Studio window opens; it only uses localhost and not the public Render site.
4. Import a video; generate and edit captions; export SRT or rendered MP4.

The first model use downloads Whisper weights once from Hugging Face and caches them locally; running fully offline requires that model to have been downloaded. SRT doesn't alter the original video. Burning captions into MP4 re-encodes video and is not mathematically lossless.

## Make an EXE

Double-click **BUILD_EXE_WINDOWS.bat** after extracting the source. Build may take several minutes and requires disk space for native AI libraries. After build the executable is `dist\CaptionStudio\CaptionStudio.exe`. **Distribute the whole `dist\CaptionStudio` folder** (zip it for GitHub Releases), not only the `.exe`. This is an unsigned community build and may show Windows SmartScreen warnings. PyInstaller Windows builds must be made on Windows; this source package does not include a precompiled EXE.

## Push to your existing GitHub repository

Copy `desktop.py`, `requirements-desktop.txt`, `START_DESKTOP_WINDOWS.bat`, and `BUILD_EXE_WINDOWS.bat` into your already cloned `caption-studio-web` repository; the existing backend and `static` folder are reused. Commit and push. Keep the web Render deployment only if you still want a hosted demo; it is NOT needed for desktop use.

## Privacy and limitations

Local video processing happens on your computer. Video files/job results are temporarily stored in your system temporary folder and expire opportunistically after two hours (or may disappear on reboot). Caption projects are not persisted across app restarts. The editor UI is an embedded webview, not a Tkinter native UI. Localhost is bound to 127.0.0.1 and a random port. EXE builds and full AI model downloading have not been tested on a physical Windows machine in this environment.
