# YouTube Downloader Web App

A small FastAPI + yt-dlp application that lets users inspect YouTube formats, start a download job, monitor progress, and stream the finished file back to the browser from a temporary file.

> Note: downloading from YouTube may be subject to the platform's terms of service and local laws. Use this project responsibly.

## Features

- Simple HTML/CSS frontend
- FastAPI backend with async endpoints
- YouTube URL validation and sanitization
- Format inspection endpoint
- MP4 video and MP3 audio downloads
- Temporary-file streaming instead of permanent storage
- Basic in-memory rate limiting
- File-size limits to avoid oversized downloads
- Progress polling for download status

## Project Structure

```text
app/
  main.py
  schemas.py
  api/routes/
    health.py
    downloads.py
  core/
    config.py
    progress.py
    rate_limit.py
  services/
    downloader.py
  utils/
    validation.py
  templates/
    index.html
  static/
    app.js
    styles.css
tests/
  test_validation.py
  test_routes.py
requirements.txt
README.md
Dockerfile
```

## Requirements

- Python 3.10+
- `ffmpeg` installed on the system for MP3 extraction and media merging
- Internet access for `yt-dlp` to inspect and download videos

## Local Setup

### 1) Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Run the app

```powershell
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## API Endpoints

- `GET /health` — health check
- `POST /api/formats` — inspect available formats for a YouTube URL
- `POST /api/download` — start a download job
- `GET /api/progress/{job_id}` — poll download progress
- `GET /api/download/{job_id}/file` — stream the finished file

### Example payload

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_type": "video",
  "quality": "720p"
}
```

## Environment Variables

- `APP_NAME` — app title shown in the UI
- `MAX_FILE_SIZE_MB` — maximum allowed download size in MB (default `200`)
- `RATE_LIMIT_REQUESTS` — max requests per IP per window (default `5`)
- `RATE_LIMIT_WINDOW_SECONDS` — rate-limit window in seconds (default `60`)
- `PROGRESS_TTL_SECONDS` — reserved for future cleanup jobs (default `3600`)
- `YT_DOWNLOAD_TEMP_DIR` — temp directory for downloads
- `YT_DLP_COOKIES_FILE` — optional path to a Netscape cookies file exported from your browser

### Installing ffmpeg (required)

`ffmpeg` is required for merging video+audio and for MP3 extraction. On Windows you can install it with one of the following options:

- Chocolatey (admin PowerShell):

```powershell
choco install ffmpeg -y
```

- Scoop (recommended for user installs):

```powershell
iwr -useb get.scoop.sh | iex
scoop install ffmpeg
```

- winget:

```powershell
winget install gyan.ffmpeg
```

Or download a static build from https://www.gyan.dev/ffmpeg/builds/ and add the `bin` folder to your `PATH`.

Verify installation:

```powershell
ffmpeg -version
```


## Notes on Deployment

### Docker

Use the provided `Dockerfile` if you want a containerized deployment. It installs `ffmpeg` and exposes port `8000`.

### Cloud hosting

- Run behind a reverse proxy such as Nginx, Caddy, or a managed ingress.
- Keep the temp directory on writable ephemeral disk.
- Move rate limiting and progress storage to Redis or another shared store if you run multiple workers/instances.
- If deploying behind HTTPS, use a proper domain and proxy headers.

### Scaling notes

This version keeps jobs and rate limits in memory for simplicity. For production use:
- Move job state to Redis or a database
- Use a task queue such as Celery/RQ/Arq
- Add shared rate limiting
- Add cleanup for stale temp files

## Development Tips

- If MP3 downloads fail, verify that `ffmpeg` is installed and on `PATH`.
- Large downloads are rejected based on the configured file-size limit.
- `yt-dlp` can fail on restricted or age-gated videos; the API surfaces those errors to the UI.
- If YouTube returns `429` or asks you to sign in, that is a platform restriction rather than an app bug. You can try a different video or provide `YT_DLP_COOKIES_FILE`.

