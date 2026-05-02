from __future__ import annotations

from pydantic import BaseModel, Field


class FormatRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")


class DownloadRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    format_type: str = Field(pattern="^(video|audio)$")
    quality: str = Field(pattern="^(144p|360p|720p|1080p)$")
    output_dir: str | None = Field(default=None, description="Optional folder where the downloaded file should be saved")


class DownloadStartResponse(BaseModel):
    job_id: str
    status: str
    progress_url: str
    download_url: str | None = None


class FormatsResponse(BaseModel):
    title: str
    thumbnail: str | None = None
    available_qualities: list[str]
    audio_available: bool
    duration: int | None = None


class ProgressResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    title: str | None = None
    file_name: str | None = None
    error: str | None = None
    downloaded_bytes: int | None = None
    total_bytes: int | None = None


