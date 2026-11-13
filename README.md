# Caption Studio

**Free, open-source AI caption editor for Windows.** Make clean, editable captions with local Whisper transcription, export SRT subtitles, or render a captioned MP4. No account, watermark, or paid API key.

[**Download for Windows**](https://github.com/Kunal17711/caption-studio-web/releases/latest/download/CaptionStudio-Windows.zip) · [**Releases**](https://github.com/Kunal17711/caption-studio-web/releases) · [**Website**](https://kunal17711.github.io/caption-studio-web/) · [**Web demo**](https://caption-studio-web.onrender.com)

> **Release status:** The Windows ZIP link works after a GitHub Actions Windows build succeeds and publishes the first release. The app is unsigned and Windows SmartScreen might warn. No prebuilt EXE is included in the source.

## Features

- **Offline-capable local AI transcription:** faster-whisper with tiny/base models; first use downloads the selected AI model.
- **Caption customization:** edit words and timestamps, choose size, color and vertical position.
- **Two export formats:** SRT subtitles (original video unchanged) or burned-in MP4 (requires re-encoding).
- **Desktop window:** pywebview + local FastAPI, bound to `127.0.0.1`; Render isn't required.
- **Optional web demo:** publicly hosted FastAPI app on Render. The demo is not an offline application and can sleep on a free instance.

## Windows: run from source

Requires **Python 3.12** and Windows 10/11 (Edge WebView2 Runtime).

1. Clone this repository or download its source ZIP.
2. Double-click `START_DESKTOP_WINDOWS.bat` and let dependencies install.
3. Open a video, click Auto Captions, edit the subtitles and export.

## Build Windows EXE locally

Double-click `BUILD_EXE_WINDOWS.bat`, then use `dist/CaptionStudio/CaptionStudio.exe`. Distribute the **entire** `dist/CaptionStudio` folder, not the EXE alone. Builds may require significant disk space because AI runtimes are included.

## Publish a download ZIP (maintainers)

1. Open **GitHub → Actions → Build Windows app and publish release**.
2. Click **Run workflow**, choose `main`, enter a version such as `v2.1.0`, and run.
3. Once the workflow is successful, it creates a GitHub Release with `CaptionStudio-Windows.zip`. The homepage's Download button links to the latest release asset.

The workflow creates a Windows build and releases it; it does **not** run a full on-device transcription/export verification test. Smoke-test the downloadable EXE on Windows before widely distributing it.

## Publish the one-page website (maintainers)

The static landing page is in `site/`. Enable **GitHub Pages → Build and deployment → Source: GitHub Actions** in repository Settings. On the next push modifying `site/`, the `Deploy download website to GitHub Pages` workflow publishes it at `https://kunal17711.github.io/caption-studio-web/`. A manually triggered Pages workflow also works.

## Project structure

| Path | Purpose |
|---|---|
| `desktop.py` | Native desktop window around a localhost FastAPI server |
| `server.py` | Upload, transcription, subtitle and MP4 export API |
| `static/` | Web editor shared by the desktop window and hosted demo |
| `site/` | Marketing and download landing page (GitHub Pages) |
| `.github/workflows/` | Windows Release and Pages automation |
| `render.yaml` | Optional hosted demo deployment |

## Privacy & limitations

Desktop video processing happens locally; the Whisper model is downloaded the first time it is needed. The hosted demo processes uploads on Render, not on the user's computer. Source video and generated media are saved temporarily by the backend, and job state is not durable across restarts. Exported MP4 is compressed/re-encoded, so absolute zero quality loss cannot be guaranteed. This is a beta project and has not had a full Windows installation/security audit. Do not upload sensitive content to the public demo.

Open-source contributions and bug reports are welcome via GitHub Issues. Licensed under the MIT License; see [LICENSE](LICENSE).
