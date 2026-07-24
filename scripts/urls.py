"""Shared URL allowlisting for fetch construction and HTML render."""
from __future__ import annotations

from urllib.parse import urlparse


def is_safe_url(url: str | None) -> bool:
    """True only for absolute http(s) URLs with a network location."""
    if not url or not isinstance(url, str):
        return False
    parsed = urlparse(url.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def safe_url(url: str | None, fallback: str = "#") -> str:
    """Return the URL if http(s), else fallback. Does not HTML-escape."""
    if is_safe_url(url):
        return url.strip()  # type: ignore[union-attr]
    return fallback


def http_url(base: str, *parts: str) -> str | None:
    """Join base + path parts and return only if the result is a safe http(s) URL."""
    base = (base or "").rstrip("/")
    path = "/".join(p.strip("/") for p in parts if p)
    url = f"{base}/{path}" if path else base
    return url if is_safe_url(url) else None
