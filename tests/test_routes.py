
from fastapi.testclient import TestClient

from app.main import app
from app.services.downloader import DownloadAccessRestrictedError, DownloadRateLimitedError


class FakeService:
    def __init__(self):
        self.last_output_dir = None

    def fetch_formats(self, url: str):
        return {
            "title": "Sample video",
            "thumbnail": None,
            "available_qualities": ["720p", "360p"],
            "audio_available": True,
            "duration": 123,
        }

    async def queue_download(self, url: str, *, format_type: str, quality: str, output_dir: str | None = None):
        self.last_output_dir = output_dir
        job = app.state.progress_store.create_job(url=url, format_type=format_type, quality=quality)
        temp_file = app.state.settings.temp_dir / f"{job.job_id}.mp4"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.write_bytes(b"video-bytes")
        app.state.progress_store.complete(
            job.job_id,
            title="Sample video",
            file_name="Sample video.mp4",
            file_path=str(temp_file),
            size_bytes=temp_file.stat().st_size,
        )
        return app.state.progress_store.to_dict(job.job_id)


class RestrictedService:
    def fetch_formats(self, url: str):
        raise DownloadAccessRestrictedError(
            "YouTube requires sign-in for this video. Try a different video, or provide a cookies file via YT_DLP_COOKIES_FILE."
        )


class RateLimitedService:
    def fetch_formats(self, url: str):
        raise DownloadRateLimitedError(
            "YouTube rate-limited this request. Please wait a bit and try again, or use cookies if this video requires sign-in."
        )


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_formats_endpoint(monkeypatch):
    monkeypatch.setattr(app.state, "download_service", FakeService())
    response = client.post("/api/formats", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert response.status_code == 200
    assert response.json()["title"] == "Sample video"


def test_formats_endpoint_restricted(monkeypatch):
    monkeypatch.setattr(app.state, "download_service", RestrictedService())
    response = client.post("/api/formats", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert response.status_code == 403
    assert "sign-in" in response.json()["detail"].lower()


def test_formats_endpoint_rate_limited(monkeypatch):
    monkeypatch.setattr(app.state, "download_service", RateLimitedService())
    response = client.post("/api/formats", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert response.status_code == 429
    assert "rate-limited" in response.json()["detail"].lower()


def test_download_and_stream_endpoint(monkeypatch):
    fake_service = FakeService()
    monkeypatch.setattr(app.state, "download_service", fake_service)
    output_dir = str(app.state.settings.temp_dir / "outside-project")
    response = client.post(
        "/api/download",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "format_type": "video",
            "quality": "720p",
            "output_dir": output_dir,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert fake_service.last_output_dir == output_dir

    file_response = client.get(payload["download_url"])
    assert file_response.status_code == 200
    assert file_response.content == b"video-bytes"

