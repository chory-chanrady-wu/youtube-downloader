from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass(slots=True)
class Settings:
    app_name: str = "YouTube Downloader"
    max_file_size_mb: int = 200
    rate_limit_requests: int = 5
    rate_limit_window_seconds: int = 60
    progress_ttl_seconds: int = 60 * 60
    temp_dir: Path = field(default_factory=lambda: Path(os.getenv("YT_DOWNLOAD_TEMP_DIR", Path.cwd() / "tmp_downloads")))
    cookies_file: Path | None = None
    allowed_hosts: tuple[str, ...] = (
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
    )

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


def get_settings() -> Settings:
    cookies_file = os.getenv("YT_DLP_COOKIES_FILE")
    return Settings(
        app_name=os.getenv("APP_NAME", "YouTube Downloader"),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "200")),
        rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "5")),
        rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        progress_ttl_seconds=int(os.getenv("PROGRESS_TTL_SECONDS", str(60 * 60))),
        temp_dir=Path(os.getenv("YT_DOWNLOAD_TEMP_DIR", str(Path.cwd() / "tmp_downloads"))),
        cookies_file=Path(cookies_file) if cookies_file else None,
    )

