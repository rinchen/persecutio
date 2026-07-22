"""Shared helpers for scripts/fetch_*.py."""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from christian_persecution import is_christian_persecution, is_persecution_article
from country_registry import (
    COUNTRY_ALIASES,
    KNOWN_COUNTRIES,
    detect_countries,
    resolve_country_name,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FETCHED = DATA / "fetched"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_MAX_BYTES = 20 * 1024 * 1024  # 20 MiB

__all__ = [
    "ROOT",
    "DATA",
    "FETCHED",
    "USER_AGENT",
    "KNOWN_COUNTRIES",
    "COUNTRY_ALIASES",
    "ensure_fetched_dir",
    "write_status",
    "exit_for_status",
    "fetch_bytes",
    "fetch_text",
    "strip_html",
    "detect_countries",
    "resolve_country_name",
    "is_persecution_article",
    "is_christian_persecution",
    "load_json_cache",
    "write_json",
    "normalize_date",
    "canonical_url",
    "merge_articles",
    "group_articles_by_country",
    "build_news_result",
]


def ensure_fetched_dir() -> Path:
    FETCHED.mkdir(parents=True, exist_ok=True)
    return FETCHED


def write_status(name: str, status: str, message: str | None = None, path: Path | None = None) -> Path:
    ensure_fetched_dir()
    status_path = path or (FETCHED / f"{name}_status.json")
    payload = {
        "name": name,
        "status": status,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "message": message,
    }
    status_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return status_path


def exit_for_status(status: str) -> None:
    """Exit non-zero when the fetch logically failed."""
    if status == "failed":
        sys.exit(1)
    sys.exit(0)


def fetch_bytes(
    url: str,
    *,
    timeout: int = 30,
    max_bytes: int = DEFAULT_MAX_BYTES,
    user_agent: str = USER_AGENT,
) -> tuple[bytes | None, str | None]:
    """Fetch URL body with size cap. Returns (data, error)."""
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            length = resp.headers.get("Content-Length")
            if length is not None:
                try:
                    if int(length) > max_bytes:
                        return None, f"content-length {length} exceeds max {max_bytes}"
                except ValueError:
                    pass
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    return None, f"response exceeded max {max_bytes} bytes"
                chunks.append(chunk)
            return b"".join(chunks), None
    except Exception as e:
        return None, f"{type(e).__name__}"


def fetch_text(
    url: str,
    *,
    timeout: int = 30,
    max_bytes: int = DEFAULT_MAX_BYTES,
    user_agent: str = USER_AGENT,
) -> tuple[str | None, str | None]:
    data, err = fetch_bytes(url, timeout=timeout, max_bytes=max_bytes, user_agent=user_agent)
    if err:
        print(f"  fetch error: {err}")
        return None, err
    assert data is not None
    return data.decode("utf-8", errors="replace"), None


def strip_html(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_json_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"  warning: corrupt cache {path.name}: {type(e).__name__}")
        return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_fetched_dir()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def canonical_url(url: str | None) -> str:
    if not url:
        return ""
    u = url.strip()
    # Drop common tracking fragments
    u = u.split("#")[0]
    if u.endswith("/"):
        u = u[:-1]
    return u


def normalize_date(value: str | None) -> str:
    """Normalize assorted date strings to YYYY-MM-DD when possible."""
    if not value or not isinstance(value, str):
        return ""
    raw = value.strip()
    if not raw:
        return ""
    # Already ISO-ish
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", raw)
    if m:
        return m.group(1)
    # GDELT seendate: 20260115T120000Z
    m = re.match(r"^(\d{4})(\d{2})(\d{2})", raw)
    if m and len(raw) >= 8 and raw[:8].isdigit():
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    try:
        dt = parsedate_to_datetime(raw)
        if dt is not None:
            return dt.date().isoformat()
    except Exception:
        pass
    # Month Day, Year
    m = re.search(
        r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s+(\d{1,2}),?\s+(\d{4})",
        raw,
        re.I,
    )
    if m:
        months = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        mon = months[m.group(1)[:3].lower()]
        return f"{int(m.group(3)):04d}-{mon:02d}-{int(m.group(2)):02d}"
    return raw


def merge_articles(
    existing: list[dict[str, Any]],
    new_articles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Union articles by canonical URL; newer/richer fields win. Newest first."""
    by_url: dict[str, dict[str, Any]] = {}
    for art in list(existing or []) + list(new_articles or []):
        if not isinstance(art, dict):
            continue
        url = canonical_url(art.get("url"))
        if not url:
            # Keep undated URL-less items keyed by title
            key = f"title:{(art.get('title') or '').strip().lower()}"
            if key == "title:":
                continue
        else:
            key = url
        prev = by_url.get(key)
        normalized = dict(art)
        normalized["url"] = url or art.get("url") or ""
        normalized["date"] = normalize_date(art.get("date")) or art.get("date") or ""
        if prev is None:
            by_url[key] = normalized
            continue
        # Prefer longer description / keep countries union
        merged = dict(prev)
        for field in ("title", "description", "source", "date"):
            new_val = normalized.get(field) or ""
            old_val = merged.get(field) or ""
            if len(str(new_val)) > len(str(old_val)):
                merged[field] = new_val
        if normalized.get("date") and (
            not merged.get("date")
            or str(normalized["date"]) > str(merged.get("date") or "")
        ):
            merged["date"] = normalized["date"]
        old_countries = set(merged.get("countries") or [])
        new_countries = set(normalized.get("countries") or [])
        # Prefer newly fetched country tags when present (fixes WP description mis-tags)
        if new_countries:
            merged["countries"] = sorted(new_countries)
        elif old_countries:
            merged["countries"] = sorted(old_countries)
        by_url[key] = merged

    articles = list(by_url.values())

    def sort_key(a: dict[str, Any]):
        d = normalize_date(a.get("date")) or ""
        # Empty dates sort last
        return (0 if d else 1, d)

    articles.sort(key=sort_key, reverse=False)
    # Newest first: reverse chronological among dated; undated at end
    dated = [a for a in articles if normalize_date(a.get("date"))]
    undated = [a for a in articles if not normalize_date(a.get("date"))]
    dated.sort(key=lambda a: normalize_date(a.get("date")), reverse=True)
    return dated + undated


def group_articles_by_country(articles: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_country: dict[str, list[dict[str, Any]]] = {}
    for a in articles:
        countries = a.get("countries") or []
        if not countries and a.get("title"):
            countries = detect_countries(f"{a.get('title', '')} {a.get('description', '')}")
        for country in countries:
            canonical = resolve_country_name(country) or country
            entry = {
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "date": normalize_date(a.get("date")) or a.get("date") or "",
                "description": (a.get("description") or "")[:300],
                "source": a.get("source", ""),
            }
            by_country.setdefault(canonical, []).append(entry)
    for country, arts in by_country.items():
        by_country[country] = merge_articles([], arts)
    return by_country


def build_news_result(
    *,
    source: str,
    source_url: str,
    status: str,
    articles: list[dict[str, Any]],
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prev_articles = []
    if previous and isinstance(previous.get("articles"), list):
        prev_articles = previous["articles"]
    merged = merge_articles(prev_articles, articles)
    by_country = group_articles_by_country(merged)
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "source_url": source_url,
        "status": status,
        "articles": merged,
        "countries": by_country,
        "total_articles": len(merged),
        "countries_with_articles": len(by_country),
    }
