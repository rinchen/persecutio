#!/usr/bin/env python3
"""Fetch Christian persecution news from Christian Solidarity Worldwide (CSW)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import (
    FETCHED,
    USER_AGENT,
    build_news_result,
    ensure_fetched_dir,
    exit_for_status,
    fetch_text,
    load_json_cache,
    parse_html_news_listing,
    write_json,
    write_status,
)

ensure_fetched_dir()

CSW_NEWS_URL = "https://www.csw.org.uk/news"
OUTPUT = FETCHED / "csw.json"


def parse_articles(html: str) -> list[dict]:
    return parse_html_news_listing(
        html,
        source_label="Christian Solidarity Worldwide",
        relative_link_re=r'href="(/news/[^"]+)"',
        link_base="https://www.csw.org.uk",
        fallback_link_re=r'<a[^>]*href="(/news/[^"]+)"[^>]*>(.*?)</a>',
    )


def main():
    print("Fetching Christian Solidarity Worldwide news...")
    cached = load_json_cache(OUTPUT)

    html, err = fetch_text(CSW_NEWS_URL, user_agent=USER_AGENT)
    if html is None:
        if cached:
            print("  fetch failed, using cached data")
            cached["status"] = "cached"
            write_json(OUTPUT, cached)
            write_status("csw", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        result = build_news_result(
            source="Christian Solidarity Worldwide",
            source_url=CSW_NEWS_URL,
            status="fetch_failed",
            articles=[],
        )
        write_json(OUTPUT, result)
        write_status("csw", "failed", "fetch failed, no cache")
        exit_for_status("failed")

    articles = parse_articles(html)
    print(f"  found {len(articles)} persecution-related articles")
    result = build_news_result(
        source="Christian Solidarity Worldwide",
        source_url=CSW_NEWS_URL,
        status="ok",
        articles=articles,
        previous=cached,
    )
    write_json(OUTPUT, result)
    print(f"  wrote {OUTPUT} ({result['total_articles']} accumulated)")
    write_status("csw", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
