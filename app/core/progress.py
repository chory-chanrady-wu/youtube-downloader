from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class DownloadJob:
    job_id: str
    status: str
    url: str
    format_type: str
    quality: str
    progress: float = 0.0
    title: str | None = None
    file_name: str | None = None
    file_path: str | None = None
    size_bytes: int | None = None
    downloaded_bytes: int | None = None
    total_bytes: int | None = None
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""


class ProgressStore:
    def __init__(self) -> None:
        self._jobs: dict[str, DownloadJob] = {}
        self._lock = Lock()

    def create_job(self, *, url: str, format_type: str, quality: str) -> DownloadJob:
        timestamp = datetime.now(timezone.utc).isoformat()
        job = DownloadJob(
            job_id=uuid4().hex,
            status="queued",
            url=url,
            format_type=format_type,
            quality=quality,
            created_at=timestamp,
            updated_at=timestamp,
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def update_job(self, job_id: str, **changes: Any) -> DownloadJob:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
            job.updated_at = datetime.now(timezone.utc).isoformat()
            return job

    def get_job(self, job_id: str) -> DownloadJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def to_dict(self, job_id: str) -> dict[str, Any] | None:
        job = self.get_job(job_id)
        return asdict(job) if job else None

    def complete(self, job_id: str, *, title: str, file_name: str, file_path: str, size_bytes: int | None) -> DownloadJob:
        return self.update_job(
            job_id,
            status="ready",
            title=title,
            file_name=file_name,
            file_path=file_path,
            size_bytes=size_bytes,
            progress=1.0,
            downloaded_bytes=size_bytes,
            total_bytes=size_bytes,
            error=None,
        )

    def fail(self, job_id: str, error: str) -> DownloadJob:
        return self.update_job(job_id, status="failed", error=error)


