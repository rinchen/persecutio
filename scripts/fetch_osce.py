#!/usr/bin/env python3
"""Fetch FoRB-related resources from OSCE/ODIHR."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from christian_persecution import is_christian_persecution
from fetch_common import (
    FETCHED,
    USER_AGENT,
    build_news_result,
    countries_for_article,
    ensure_fetched_dir,
    exit_for_status,
    fetch_text,
    load_json_cache,
    strip_html,
    write_json,
    write_status,
)

ensure_fetched_dir()

PAGE_URL = "https://www.osce.org/odihr/freedom-of-religion-or-belief"
OUTPUT = FETCHED / "osce.json"
# Resource links on the FoRB hub page
LINK_RE = re.compile(
    r'href="((?:https://(?:www\.)?osce\.org|https://odihr\.osce\.org)?/odihr/\d+)"[^>]*>(.*?)</a>',
    re.I | re.S,
)


def parse_articles(html: str) -> list[dict]:
    articles: list[dict] = []
    seen: set[str] = set()
    for match in LINK_RE.finditer(html):
        path = match.group(1)
        url = path if path.startswith("http") else f"https://www.osce.org{path}"
        title = strip_html(match.group(2)).strip()
        if len(title) < 12 or url in seen:
            continue
        blob = f"{title}"
        if not is_christian_persecution(
            title=title,
            description=blob,
            high_trust_source=False,
        ) and not re.search(
            r"religion|belief|forb|christian|church|hate.?crime",
            blob,
            re.I,
        ):
            continue
        seen.add(url)
        articles.append({
            "title": title,
            "url": url,
            "date": None,
            "description": "",
            "countries": countries_for_article(title, ""),
            "source": "OSCE / ODIHR",
        })
    return articles


def main():
    print("Fetching OSCE/ODIHR FoRB resources...")
    cached = load_json_cache(OUTPUT)
    html, err = fetch_text(PAGE_URL, user_agent=USER_AGENT)
    if html is None:
        if cached:
            cached["status"] = "cached"
            write_json(OUTPUT, cached)
            write_status("osce", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        result = build_news_result(
            source="OSCE / ODIHR",
            source_url=PAGE_URL,
            status="fetch_failed",
            articles=[],
        )
        write_json(OUTPUT, result)
        write_status("osce", "failed", f"fetch failed: {err}")
        exit_for_status("failed")

    articles = parse_articles(html)
    print(f"  found {len(articles)} FoRB-related items")
    result = build_news_result(
        source="OSCE / ODIHR",
        source_url=PAGE_URL,
        status="ok",
        articles=articles,
        previous=cached,
    )
    write_json(OUTPUT, result)
    print(f"  wrote {OUTPUT} ({result['total_articles']} accumulated)")
    write_status("osce", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
