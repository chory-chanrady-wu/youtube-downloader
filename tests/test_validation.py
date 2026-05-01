from fastapi import HTTPException
import pytest

from app.core.config import get_settings
from app.utils.validation import validate_youtube_url


def test_validate_youtube_url_accepts_standard_watch_url():
    settings = get_settings()
    result = validate_youtube_url(" https://www.youtube.com/watch?v=dQw4w9WgXcQ ", settings.allowed_hosts)
    assert result.startswith("https://www.youtube.com/watch")


@pytest.mark.parametrize(
    "url",
    [
        "",
        "ftp://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://example.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/",
    ],
)
def test_validate_youtube_url_rejects_bad_urls(url):
    settings = get_settings()
    with pytest.raises(HTTPException):
        validate_youtube_url(url, settings.allowed_hosts)

