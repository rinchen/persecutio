#!/usr/bin/env python3
"""Fetch Christian persecution news from Barnabas Aid."""
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

NEWS_URL = "https://www.barnabasaid.org/us/news/"
OUTPUT = FETCHED / "barnabas.json"
LINK_RE = re.compile(
    r'href="(https://www\.barnabasaid\.org/us/news/[a-z0-9][^"]+/)"[^>]*>(.*?)</a>',
    re.I | re.S,
)


def parse_articles(html: str) -> list[dict]:
    articles: list[dict] = []
    seen: set[str] = set()
    for match in LINK_RE.finditer(html):
        url = match.group(1).rstrip("/") + "/"
        if url.rstrip("/").endswith("/us/news") or "/page/" in url:
            continue
        title = strip_html(match.group(2)).strip()
        if len(title) < 20 or url in seen:
            continue
        if not is_christian_persecution(title=title, description="", high_trust_source=True):
            continue
        seen.add(url)
        articles.append({
            "title": title,
            "url": url,
            "date": None,
            "description": "",
            "countries": countries_for_article(title, ""),
            "source": "Barnabas Aid",
        })
    return articles


def main():
    print("Fetching Barnabas Aid news...")
    cached = load_json_cache(OUTPUT)
    html, err = fetch_text(NEWS_URL, user_agent=USER_AGENT)
    if html is None:
        if cached:
            cached["status"] = "cached"
            write_json(OUTPUT, cached)
            write_status("barnabas", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        result = build_news_result(
            source="Barnabas Aid",
            source_url=NEWS_URL,
            status="fetch_failed",
            articles=[],
        )
        write_json(OUTPUT, result)
        write_status("barnabas", "failed", f"fetch failed: {err}")
        exit_for_status("failed")

    articles = parse_articles(html)
    print(f"  found {len(articles)} persecution-related articles")
    result = build_news_result(
        source="Barnabas Aid",
        source_url=NEWS_URL,
        status="ok",
        articles=articles,
        previous=cached,
    )
    write_json(OUTPUT, result)
    print(f"  wrote {OUTPUT} ({result['total_articles']} accumulated)")
    write_status("barnabas", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
