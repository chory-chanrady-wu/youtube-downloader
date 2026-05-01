from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from fastapi import HTTPException, status


def sanitize_user_input(value: str) -> str:
    return (value or "").strip()


def _host_matches_youtube(host: str, allowed_hosts: tuple[str, ...]) -> bool:
    host = host.lower().strip(".")
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in allowed_hosts)


def validate_youtube_url(raw_url: str, allowed_hosts: tuple[str, ...]) -> str:
    url = sanitize_user_input(raw_url)
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="YouTube URL is required.")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL must start with http:// or https://")

    if not parsed.netloc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid YouTube URL.")

    if not _host_matches_youtube(parsed.hostname or "", allowed_hosts):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only YouTube URLs are allowed.")

    if parsed.hostname in {"youtu.be"} and not parsed.path.strip("/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid YouTube short link.")

    normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    return normalized

