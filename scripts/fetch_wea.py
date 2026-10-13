#!/usr/bin/env python3
"""Fetch Christian persecution / FoRB news (wea).

worldea.org/feed/ now returns HTTP 500, but the WordPress REST API still
serves posts, so read structured JSON instead of RSS.
"""
import json
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
    normalize_date,
    strip_html,
    write_json,
    write_status,
)

ensure_fetched_dir()

SOURCE_LABEL = "WEA"
API_URL = (
    "https://worldea.org/wp-json/wp/v2/posts"
    "?per_page=30&_fields=link,date,title,excerpt"
)
OUTPUT = FETCHED / "wea.json"


def _rendered(value) -> str:
    if isinstance(value, dict):
        return value.get("rendered") or ""
    return value or ""


def parse_posts(text: str) -> list[dict]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return []
    if not isinstance(data, list):
        return []

    articles: list[dict] = []
    for post in data:
        if not isinstance(post, dict):
            continue
        title = strip_html(_rendered(post.get("title"))).strip()
        excerpt = strip_html(_rendered(post.get("excerpt"))).strip()
        url = (post.get("link") or "").strip()
        if not title or not url:
            continue
        if not is_christian_persecution(
            title=title, description=excerpt, high_trust_source=True
        ):
            continue
        date = post.get("date")
        articles.append({
            "title": title,
            "url": url,
            "date": normalize_date(date) or date,
            "description": excerpt[:500],
            "countries": countries_for_article(title, excerpt),
            "source": SOURCE_LABEL,
        })
    return articles


def main():
    print("Fetching WEA...")
    cached = load_json_cache(OUTPUT)

    text, err = fetch_text(API_URL, user_agent=USER_AGENT)
    if text is None:
        if cached:
            cached["status"] = "cached"
            write_json(OUTPUT, cached)
            write_status("wea", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        result = build_news_result(
            source=SOURCE_LABEL,
            source_url=API_URL,
            status="fetch_failed",
            articles=[],
        )
        write_json(OUTPUT, result)
        write_status("wea", "failed", f"fetch failed: {err}")
        exit_for_status("failed")

    articles = parse_posts(text)
    if not articles and cached:
        cached["status"] = "cached"
        write_json(OUTPUT, cached)
        write_status("wea", "cached", "empty fetch, using cache")
        exit_for_status("cached")

    print(f"  found {len(articles)} FoRB-related articles")
    result = build_news_result(
        source=SOURCE_LABEL,
        source_url=API_URL,
        status="ok",
        articles=articles,
        previous=cached,
    )
    write_json(OUTPUT, result)
    print(f"  wrote {OUTPUT} ({result['total_articles']} accumulated)")
    write_status("wea", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
