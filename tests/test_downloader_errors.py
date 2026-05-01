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

