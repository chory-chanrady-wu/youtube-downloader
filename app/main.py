from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes.downloads import router as downloads_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.progress import ProgressStore
from app.core.rate_limit import RateLimiter
from app.services.downloader import DownloadService

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.state.settings = settings
app.state.progress_store = ProgressStore()
app.state.rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
app.state.download_service = DownloadService(settings, app.state.progress_store)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(health_router)
app.include_router(downloads_router)



@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "app_name": settings.app_name,
            "rate_limit": settings.rate_limit_requests,
            "quality_options": ["144p", "360p", "720p", "1080p"],
            "format_options": ["video", "audio"],
        },
    )

