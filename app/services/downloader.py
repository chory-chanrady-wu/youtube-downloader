from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.progress import ProgressStore
from app.utils.validation import validate_youtube_url


class DownloadTooLargeError(RuntimeError):
    pass


class DownloadServiceError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class DownloadAccessRestrictedError(DownloadServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=403)


class DownloadRateLimitedError(DownloadServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=429)


class DownloadService:
    def __init__(self, settings: Settings, progress: ProgressStore) -> None:
        self.settings = settings
        self.progress = progress
        self.settings.temp_dir.mkdir(parents=True, exist_ok=True)

    def _load_yt_dlp(self):
        try:
            from yt_dlp import YoutubeDL
            from yt_dlp.utils import DownloadError
        except ImportError as exc:  # pragma: no cover - dependency missing in runtime only
            raise RuntimeError("yt-dlp is not installed. Install dependencies with pip install -r requirements.txt") from exc
        return YoutubeDL, DownloadError

    def _friendly_yt_dlp_error(self, error: Exception | str) -> DownloadServiceError:
        text = str(error)
        lowered = text.lower()

        if "http error 429" in lowered or "too many requests" in lowered:
            return DownloadRateLimitedError(
                "YouTube rate-limited this request. Please wait a bit and try again, or use cookies if this video requires sign-in."
            )

        if "sign in to confirm you’re not a bot" in lowered or "sign in to confirm you're not a bot" in lowered or "not a bot" in lowered:
            return DownloadAccessRestrictedError(
                "YouTube requires sign-in for this video. Try a different video, or provide a cookies file via YT_DLP_COOKIES_FILE."
            )

        if "no supported javascript runtime could be found" in lowered:
            return DownloadServiceError(
                "yt-dlp needs a JavaScript runtime for this video. Install Deno or another supported runtime, then try again.",
                status_code=500,
            )

        # ffmpeg is required for merging video+audio and audio extraction
        if "requested merging of multiple formats" in lowered or "ffmpeg is not installed" in lowered or "ffmpeg" in lowered:
            return DownloadServiceError(
                "ffmpeg is required to merge video and audio or extract audio. Install ffmpeg and ensure it's on your PATH, then try again.",
                status_code=500,
            )

        if "video is unavailable" in lowered or "this video is unavailable" in lowered:
            return DownloadServiceError("This video is unavailable or has been removed.", status_code=404)

        return DownloadServiceError(text, status_code=400)

    def _yt_dlp_base_options(self) -> dict[str, Any]:
        opts: dict[str, Any] = {"quiet": True, "nocheckcertificate": True}
        if self.settings.cookies_file:
            if not self.settings.cookies_file.exists():
                raise DownloadServiceError(
                    f"Cookies file not found: {self.settings.cookies_file}",
                    status_code=400,
                )
            opts["cookiefile"] = str(self.settings.cookies_file)
        return opts

    def _quality_to_height(self, quality: str) -> int:
        return int(quality.rstrip("p"))

    def _sanitize_filename(self, name: str, default: str = "video") -> str:
        cleaned = re.sub(r'[\\/:*?"<>|]+', "_", name).strip(" ._")
        return cleaned or default

    def _pick_stream(self, info: dict[str, Any], *, format_type: str, quality: str) -> tuple[int | None, int | None]:
        formats = info.get("formats", []) or []
        height = self._quality_to_height(quality)

        if format_type == "audio":
            audio_formats = [f for f in formats if f.get("vcodec") == "none" and f.get("acodec") != "none"]
            if not audio_formats:
                return None, None
            best = max(audio_formats, key=lambda f: (f.get("abr") or 0, f.get("filesize") or f.get("filesize_approx") or 0))
            size = best.get("filesize") or best.get("filesize_approx")
            return None, int(size) if size else None

        video_formats = [
            f for f in formats
            if f.get("vcodec") != "none"
            and (f.get("height") or 0) <= height
        ]
        if not video_formats:
            return None, None
        best_video = max(
            video_formats,
            key=lambda f: (
                f.get("height") or 0,
                f.get("tbr") or 0,
                f.get("filesize") or f.get("filesize_approx") or 0,
            ),
        )
        best_audio_candidates = [f for f in formats if f.get("vcodec") == "none" and f.get("acodec") != "none"]
        best_audio = max(
            best_audio_candidates,
            key=lambda f: (f.get("abr") or 0, f.get("filesize") or f.get("filesize_approx") or 0),
            default=None,
        )

        size = (best_video.get("filesize") or best_video.get("filesize_approx") or 0) or 0
        if best_audio is not None:
            size += int(best_audio.get("filesize") or best_audio.get("filesize_approx") or 0)
        return int(best_video.get("height") or height), int(size) if size else None

    def _build_format_selector(self, format_type: str, quality: str) -> tuple[str, list[dict[str, str]]]:
        height = self._quality_to_height(quality)
        if format_type == "audio":
            return "bestaudio/best", [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
        return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]", []

    def _progress_hook(self, job_id: str):
        def hook(data: dict[str, Any]) -> None:
            status = data.get("status")
            downloaded = data.get("downloaded_bytes") or 0
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            progress = float(downloaded / total) if total else 0.0
            if total and downloaded > self.settings.max_file_size_bytes:
                raise DownloadTooLargeError(
                    f"Download exceeds the maximum allowed size of {self.settings.max_file_size_mb} MB."
                )
            if status == "downloading":
                self.progress.update_job(
                    job_id,
                    status="downloading",
                    progress=min(progress, 0.99),
                    downloaded_bytes=int(downloaded),
                    total_bytes=int(total) if total else None,
                )
            elif status == "finished":
                self.progress.update_job(job_id, status="processing", progress=0.99)

        return hook

    def fetch_formats(self, raw_url: str) -> dict[str, Any]:
        YoutubeDL, DownloadError = self._load_yt_dlp()
        url = validate_youtube_url(raw_url, self.settings.allowed_hosts)
        opts = {
            **self._yt_dlp_base_options(),
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except DownloadError as exc:
            raise self._friendly_yt_dlp_error(exc) from exc
        except Exception as exc:
            raise self._friendly_yt_dlp_error(exc) from exc

        title = info.get("title") or "Unknown title"
        thumbnail = info.get("thumbnail")
        formats = info.get("formats", []) or []
        qualities = sorted({f.get("height") for f in formats if f.get("vcodec") != "none" and f.get("height")}, reverse=True)
        allowed = [q for q in (1080, 720, 360, 144) if q in qualities or any((f.get("height") or 0) >= q for f in formats if f.get("vcodec") != "none")]
        return {
            "title": title,
            "thumbnail": thumbnail,
            "available_qualities": [f"{q}p" for q in allowed] or ["144p"],
            "audio_available": any(f.get("acodec") != "none" for f in formats),
            "duration": info.get("duration"),
        }

    async def queue_download(self, raw_url: str, *, format_type: str, quality: str) -> dict[str, Any]:
        url = validate_youtube_url(raw_url, self.settings.allowed_hosts)
        job = self.progress.create_job(url=url, format_type=format_type, quality=quality)
        asyncio.create_task(self._download_worker(job.job_id, url, format_type, quality))
        return self.progress.to_dict(job.job_id) or {}

    async def _download_worker(self, job_id: str, url: str, format_type: str, quality: str) -> None:
        try:
            await asyncio.to_thread(self._download_sync, job_id, url, format_type, quality)
        except DownloadTooLargeError as exc:
            self.progress.fail(job_id, str(exc))
        except Exception as exc:  # pragma: no cover - runtime safety
            self.progress.fail(job_id, str(exc))

    def _download_sync(self, job_id: str, url: str, format_type: str, quality: str) -> None:
        YoutubeDL, DownloadError = self._load_yt_dlp()
        format_selector, postprocessors = self._build_format_selector(format_type, quality)
        opts = {
            **self._yt_dlp_base_options(),
            "outtmpl": str(self.settings.temp_dir / f"{job_id}.%(ext)s"),
            "restrictfilenames": True,
            "noplaylist": True,
            "progress_hooks": [self._progress_hook(job_id)],
            "format": format_selector,
            "quiet": True,
            "no_warnings": True,
        }
        if postprocessors:
            opts["postprocessors"] = postprocessors
        if format_type == "video":
            opts["merge_output_format"] = "mp4"

        with YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except DownloadError as exc:
                raise self._friendly_yt_dlp_error(exc) from exc
            except Exception as exc:
                raise self._friendly_yt_dlp_error(exc) from exc

        title = self._sanitize_filename(info.get("title") or "video")
        final_path = self._find_output_file(job_id)
        if final_path is None or not final_path.exists():
            raise RuntimeError("The downloader could not produce an output file.")

        size_bytes = final_path.stat().st_size
        if size_bytes > self.settings.max_file_size_bytes:
            final_path.unlink(missing_ok=True)
            raise DownloadTooLargeError(
                f"Downloaded file exceeds the maximum allowed size of {self.settings.max_file_size_mb} MB."
            )

        download_name = self._build_download_name(title, format_type)
        self.progress.complete(
            job_id,
            title=title,
            file_name=download_name,
            file_path=str(final_path),
            size_bytes=size_bytes,
        )

    def _find_output_file(self, job_id: str) -> Path | None:
        candidates = [p for p in self.settings.temp_dir.glob(f"{job_id}.*") if not p.name.endswith(".part")]
        if not candidates:
            return None
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0]

    def _build_download_name(self, title: str, format_type: str) -> str:
        extension = "mp3" if format_type == "audio" else "mp4"
        return f"{title}.{extension}"


