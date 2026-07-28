#!/usr/bin/env python3
"""Fetch FoRB news from IPPFoRB (RSS with HTML fallback)."""
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
from rss_news_fetcher import parse_rss_items

ensure_fetched_dir()

RSS_URL = "https://ippforb.com/feed/"
NEWS_URL = "https://ippforb.com/"
OUTPUT = FETCHED / "ippforb.json"
LINK_RE = re.compile(
    r'href="(https://ippforb\.com/[^"]+)"[^>]*>(.*?)</a>',
    re.I | re.S,
)


def parse_html(html: str) -> list[dict]:
    articles: list[dict] = []
    seen: set[str] = set()
    for match in LINK_RE.finditer(html):
        url = match.group(1).split("#")[0]
        title = strip_html(match.group(2)).strip()
        if len(title) < 16 or url in seen or url.rstrip("/") == "https://ippforb.com":
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
            "source": "IPPFoRB",
        })
    return articles


def main():
    print("Fetching IPPFoRB...")
    cached = load_json_cache(OUTPUT)
    articles: list[dict] = []
    source_url = RSS_URL

    xml, err = fetch_text(RSS_URL, user_agent=USER_AGENT)
    if xml:
        articles, _ = parse_rss_items(xml, source_label="IPPFoRB", high_trust=True)
    if not articles:
        source_url = NEWS_URL
        html, err2 = fetch_text(NEWS_URL, user_agent=USER_AGENT)
        if html is None and not cached:
            result = build_news_result(
                source="IPPFoRB",
                source_url=NEWS_URL,
                status="fetch_failed",
                articles=[],
            )
            write_json(OUTPUT, result)
            write_status("ippforb", "failed", f"fetch failed: {err or err2}")
            exit_for_status("failed")
        if html:
            articles = parse_html(html)

    if not articles and cached:
        cached["status"] = "cached"
        write_json(OUTPUT, cached)
        write_status("ippforb", "cached", "empty fetch, using cache")
        exit_for_status("cached")

    print(f"  found {len(articles)} FoRB-related articles")
    result = build_news_result(
        source="IPPFoRB",
        source_url=source_url,
        status="ok",
        articles=articles,
        previous=cached,
    )
    write_json(OUTPUT, result)
    print(f"  wrote {OUTPUT} ({result['total_articles']} accumulated)")
    write_status("ippforb", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
