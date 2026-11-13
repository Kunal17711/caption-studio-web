# Caption Studio Web 2.0

Free, local-first video captions with browser UI, AI transcription (Whisper), editable timed captions, SRT download, and FFmpeg burn-in MP4 export. No paid API keys or account needed.

## Windows setup
1. Extract ZIP to a fresh folder.
2. Requires **Python 3.12**. Double-click `START_WINDOWS.bat`.
3. Open `http://127.0.0.1:8000` (the script tries to open it automatically).
4. Import a video, generate captions, edit styling, export SRT or MP4.

The first run downloads the open Whisper model. Subsequent transcriptions use the cache. For performance prefer small video files and `tiny` model.

## Deploy to Render (optional)
1. Push contents of this directory to a *new* GitHub repository.
2. Render → New → Blueprint, connect the repo, select `render.yaml` and deploy.
3. Render free hosting is a best-effort hobby tier; cold starts, upload timeouts, memory limitations, monthly limits and ephemeral storage apply. For real public AI usage, budget for compute/storage and implement authentication/quotas. Do not use as an unrestricted production service.

**Privacy:** When run locally, the video stays on your machine. When deployed to Render, videos are uploaded to that server, stored temporarily and deleted after two hours when a future upload triggers cleanup. Files are *not* immediately removed when browser closes. No authentication is included in this MVP: generated random job IDs serve as access tokens. Do not upload confidential videos to a public deployment.

**Quality:** SRT export preserves your original video file. Burned-in captions require lossy re-encoding at CRF 17, preserving source frame geometry by default.

**Limitations:** No accounts, payments, long-term project storage, real-time collaborative editing, or automated abuse prevention. This is a functional free MVP, not a production-ready SaaS. Concurrent processing is serialized in-process. Render services can restart and wipe temporary files. Font size and placement during MP4 export use ASS's virtual 1080×1920 canvas; best suited to portrait video.
