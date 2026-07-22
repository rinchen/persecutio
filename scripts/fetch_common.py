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
    countries_for_article,
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
# Cap accumulated news articles per source (daily merges otherwise grow forever).
DEFAULT_ARTICLE_CAP = 500
# 0 disables age pruning; count cap alone bounds growth.
DEFAULT_ARTICLE_MAX_AGE_DAYS = 0

__all__ = [
    "ROOT",
    "DATA",
    "FETCHED",
    "USER_AGENT",
    "KNOWN_COUNTRIES",
    "COUNTRY_ALIASES",
    "DEFAULT_ARTICLE_CAP",
    "DEFAULT_ARTICLE_MAX_AGE_DAYS",
    "ensure_fetched_dir",
    "write_status",
    "exit_for_status",
    "fetch_bytes",
    "fetch_text",
    "fetch_json_to_path",
    "atomic_write_text",
    "strip_html",
    "detect_countries",
    "countries_for_article",
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
    "fetch_or_use_cache",
    "parse_html_news_listing",
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
        return None, f"{type(e).__name__}: {e}"


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


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Write text via a sibling temp file then replace (avoids truncated caches)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding=encoding)
    tmp.replace(path)


def fetch_json_to_path(
    url: str,
    path: Path,
    name: str,
    *,
    skip: bool = False,
    timeout: int = 30,
    user_agent: str = USER_AGENT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fetch JSON with size cap; parse before writing so bad bodies cannot poison cache.

    Returns (data, status_dict) where status_dict has name/url/status/fetched_at/message.
    """
    status: dict[str, Any] = {
        "name": name,
        "url": url,
        "status": "ok",
        "fetched_at": None,
        "message": None,
    }
    if path.exists() and skip:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            status["status"] = "cached"
            status["fetched_at"] = datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc
            ).isoformat()
            return (data if isinstance(data, dict) else {}), status
        except Exception as e:
            status["status"] = "failed"
            status["message"] = f"corrupt cache: {type(e).__name__}: {e}"
            return {}, status

    text, err = fetch_text(url, timeout=timeout, user_agent=user_agent)
    if text is None:
        status["status"] = "failed"
        status["message"] = err
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                status["status"] = "partial"
                status["fetched_at"] = datetime.fromtimestamp(
                    path.stat().st_mtime, tz=timezone.utc
                ).isoformat()
                return (data if isinstance(data, dict) else {}), status
            except Exception as e2:
                print(f"  warning: corrupt cache {path.name}: {type(e2).__name__}: {e2}")
                status["message"] = f"{err}; corrupt cache: {type(e2).__name__}"
        return {}, status

    stripped = text.lstrip()
    if not stripped or stripped[:1] not in ("{", "["):
        status["status"] = "failed"
        status["message"] = "response is not JSON"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                status["status"] = "partial"
                return (data if isinstance(data, dict) else {}), status
            except Exception as e2:
                print(f"  warning: corrupt cache {path.name}: {type(e2).__name__}: {e2}")
        return {}, status

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        status["status"] = "failed"
        status["message"] = f"JSONDecodeError: {e}"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                status["status"] = "partial"
                return (data if isinstance(data, dict) else {}), status
            except Exception as e2:
                print(f"  warning: corrupt cache {path.name}: {type(e2).__name__}: {e2}")
        return {}, status

    atomic_write_text(path, json.dumps(parsed, indent=2, ensure_ascii=False) + "\n")
    status["fetched_at"] = datetime.now(timezone.utc).isoformat()
    if isinstance(parsed, dict):
        return parsed, status
    # Some endpoints return a top-level list; wrap for callers expecting a dict.
    return {"_list": parsed}, status


def fetch_or_use_cache(
    url: str,
    output: Path,
    name: str,
    *,
    user_agent: str = USER_AGENT,
    timeout: int = 30,
) -> tuple[str | None, dict[str, Any], str | None]:
    """Fetch text or fall back to cached JSON. Returns (text, cached, fatal_status).

    If fatal_status is set, caller should exit with that status (cache already rewritten).
    """
    cached = load_json_cache(output)
    text, err = fetch_text(url, timeout=timeout, user_agent=user_agent)
    if text is not None:
        return text, cached, None
    if cached:
        print("  fetch failed, using cached data")
        cached["status"] = "cached"
        write_json(output, cached)
        write_status(name, "cached", f"fetch failed, using cache: {err}")
        return None, cached, "cached"
    write_status(name, "failed", f"fetch failed: {err}")
    return None, cached, "failed"


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
    atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


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
    *,
    max_articles: int = DEFAULT_ARTICLE_CAP,
    max_age_days: int = DEFAULT_ARTICLE_MAX_AGE_DAYS,
) -> list[dict[str, Any]]:
    """Union articles by canonical URL; newer/richer fields win. Newest first.

    Caps retained articles by count and optional age window so daily merges
    do not grow without bound on CI runners.
    """
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
    dated = [a for a in articles if normalize_date(a.get("date"))]
    undated = [a for a in articles if not normalize_date(a.get("date"))]
    dated.sort(key=lambda a: normalize_date(a.get("date")), reverse=True)

    if max_age_days and max_age_days > 0:
        cutoff = datetime.now(timezone.utc).date().toordinal() - max_age_days
        kept: list[dict[str, Any]] = []
        for a in dated:
            d = normalize_date(a.get("date"))
            try:
                y, m, day = (int(x) for x in d.split("-", 2))
                if datetime(y, m, day).date().toordinal() >= cutoff:
                    kept.append(a)
            except (ValueError, TypeError):
                kept.append(a)
        dated = kept

    merged_list = dated + undated
    if max_articles and max_articles > 0 and len(merged_list) > max_articles:
        # Prefer dated newest; then undated up to the remaining slots
        merged_list = merged_list[:max_articles]
    return merged_list


def group_articles_by_country(articles: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_country: dict[str, list[dict[str, Any]]] = {}
    for a in articles:
        # Always re-detect so stale pronoun/alias false positives are not kept,
        # and secondary description mentions do not override title/category.
        countries = countries_for_article(
            a.get("title") or "",
            a.get("description") or "",
            a.get("categories") or [],
        )
        a["countries"] = countries
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


def parse_html_news_listing(
    html: str,
    *,
    source_label: str,
    absolute_link_re: str | None = None,
    relative_link_re: str = r'href="(/news/[^"]+)"',
    link_base: str = "",
    fallback_link_re: str | None = None,
    min_fallback_title_len: int = 20,
) -> list[dict[str, Any]]:
    """Shared <article> listing scrape used by CSW/ICC-style HTML news pages."""
    articles: list[dict[str, Any]] = []
    article_pattern = re.compile(r"<article[^>]*>(.*?)</article>", re.DOTALL | re.IGNORECASE)
    for match in article_pattern.finditer(html):
        article_html = match.group(1)
        title_match = re.search(r"<h[23][^>]*>(.*?)</h[23]>", article_html, re.DOTALL | re.IGNORECASE)
        if not title_match:
            continue
        title = strip_html(title_match.group(1)).strip()
        if not title:
            continue

        url = None
        if absolute_link_re:
            link_match = re.search(absolute_link_re, article_html)
            if link_match:
                url = link_match.group(1)
        if not url:
            link_match = re.search(relative_link_re, article_html)
            if link_match:
                path = link_match.group(1)
                url = path if path.startswith("http") else f"{link_base}{path}"

        date_match = re.search(r'<time[^>]*datetime="([^"]+)"', article_html)
        date = date_match.group(1) if date_match else None
        if not date:
            date_match = re.search(r"(\w+ \d{1,2},?\s*\d{4})", article_html)
            date = date_match.group(1) if date_match else None

        excerpt = ""
        p_match = re.search(r"<p[^>]*>(.*?)</p>", article_html, re.DOTALL | re.IGNORECASE)
        if p_match:
            excerpt = strip_html(p_match.group(1)).strip()[:500]

        if not is_christian_persecution(title=title, description=excerpt):
            continue

        countries = countries_for_article(title, excerpt)
        articles.append({
            "title": title,
            "url": url,
            "date": normalize_date(date) or date,
            "description": excerpt[:300],
            "countries": countries,
            "source": source_label,
        })

    if articles or not fallback_link_re:
        return articles

    for match in re.finditer(fallback_link_re, html, re.DOTALL | re.IGNORECASE):
        raw_url = match.group(1)
        title = strip_html(match.group(2)).strip()
        if not title or len(title) < min_fallback_title_len:
            continue
        if not is_christian_persecution(title=title, description=""):
            continue
        url = raw_url if raw_url.startswith("http") else f"{link_base}{raw_url}"
        countries = countries_for_article(title, "")
        articles.append({
            "title": title,
            "url": url,
            "date": None,
            "description": "",
            "countries": countries,
            "source": source_label,
        })
    return articles
