from pathlib import Path

from app.core.config import get_settings
from app.core.progress import ProgressStore
from app.services.downloader import (
    DownloadAccessRestrictedError,
    DownloadRateLimitedError,
    DownloadService,
    DownloadServiceError,
)


def make_service() -> DownloadService:
    return DownloadService(get_settings(), ProgressStore())


def test_default_temp_dir_uses_downloads_folder(monkeypatch):
    monkeypatch.delenv("YT_DOWNLOAD_TEMP_DIR", raising=False)
    settings = get_settings()
    assert settings.temp_dir == Path.home() / "Downloads" / "youtube_downloads"


def test_classifier_maps_rate_limit_to_429_message():
    service = make_service()
    error = service._friendly_yt_dlp_error("HTTP Error 429: Too Many Requests")
    assert isinstance(error, DownloadRateLimitedError)
    assert error.status_code == 429


def test_classifier_maps_bot_check_to_403_message():
    service = make_service()
    error = service._friendly_yt_dlp_error("Sign in to confirm you’re not a bot")
    assert isinstance(error, DownloadAccessRestrictedError)
    assert error.status_code == 403


def test_classifier_maps_missing_js_runtime_to_500_message():
    service = make_service()
    error = service._friendly_yt_dlp_error("No supported JavaScript runtime could be found")
    assert isinstance(error, DownloadServiceError)
    assert error.status_code == 500


def test_sanitize_filename_removes_invalid_windows_characters():
    service = make_service()
    assert service._sanitize_filename('My / Cool: Video? *Title*') == 'My Cool Video Title'


def test_download_name_uses_sanitized_title_and_extension():
    service = make_service()
    title = service._sanitize_filename('Sample <Video> Title')
    assert service._build_download_name(title, 'video') == 'Sample Video Title.mp4'
    assert service._build_download_name(title, 'audio') == 'Sample Video Title.mp3'


def test_resolve_output_dir_creates_custom_folder(tmp_path):
    service = make_service()
    custom_dir = tmp_path / "outside-project" / "downloads"
    resolved = service._resolve_output_dir(str(custom_dir))
    assert resolved == custom_dir.resolve()
    assert resolved.exists()


