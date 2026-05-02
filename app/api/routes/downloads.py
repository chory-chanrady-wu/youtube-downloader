from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.schemas import DownloadRequest, DownloadStartResponse, FormatRequest, FormatsResponse, ProgressResponse
from app.services.downloader import DownloadAccessRestrictedError, DownloadRateLimitedError, DownloadServiceError

router = APIRouter(prefix="/api", tags=["downloads"])


def get_service(request: Request):
    return request.app.state.download_service


def get_store(request: Request):
    return request.app.state.progress_store


async def rate_limit_dep(request: Request) -> None:
    limiter = request.app.state.rate_limiter
    result = limiter.check(request.client.host if request.client else "unknown")
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(result.retry_after_seconds)},
        )


@router.post("/formats", response_model=FormatsResponse)
async def get_formats(payload: FormatRequest, service=Depends(get_service), _=Depends(rate_limit_dep)):
    try:
        result = service.fetch_formats(payload.url)
        return result
    except HTTPException:
        raise
    except DownloadRateLimitedError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except DownloadAccessRestrictedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except DownloadServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/download", response_model=DownloadStartResponse)
async def start_download(
    payload: DownloadRequest,
    service=Depends(get_service),
    _=Depends(rate_limit_dep),
):
    try:
        job = await service.queue_download(
            payload.url,
            format_type=payload.format_type,
            quality=payload.quality,
            output_dir=payload.output_dir,
        )
    except HTTPException:
        raise
    except DownloadRateLimitedError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except DownloadAccessRestrictedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except DownloadServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    job_id = job["job_id"]
    return DownloadStartResponse(
        job_id=job_id,
        status=job["status"],
        progress_url=f"/api/progress/{job_id}",
        download_url=f"/api/download/{job_id}/file",
    )


@router.get("/progress/{job_id}", response_model=ProgressResponse)
async def get_progress(job_id: str, store=Depends(get_store)):
    job = store.to_dict(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return ProgressResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        title=job.get("title"),
        file_name=job.get("file_name"),
        error=job.get("error"),
        downloaded_bytes=job.get("downloaded_bytes"),
        total_bytes=job.get("total_bytes"),
    )


@router.get("/download/{job_id}/file")
async def stream_download(job_id: str, store=Depends(get_store)):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    if job.status != "ready" or not job.file_path:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File is not ready yet.")

    file_path = Path(job.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Downloaded file is no longer available.")

    media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    headers = {"Content-Disposition": f'attachment; filename="{job.file_name or file_path.name}"'}

    async def file_iterator():
        with file_path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk

    def cleanup():
        file_path.unlink(missing_ok=True)

    return StreamingResponse(file_iterator(), media_type=media_type, headers=headers, background=BackgroundTask(cleanup))



