#!/usr/bin/env python3
"""Fetch Christian persecution news from International Christian Concern (ICC)."""
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
    parse_html_news_listing,
    strip_html,
    write_json,
    write_status,
)

ensure_fetched_dir()

ICC_NEWS_URL = "https://www.persecution.org/news/"
ICC_WP_JSON = "https://www.persecution.org/wp-json/wp/v2/posts?per_page=20"
OUTPUT = FETCHED / "icc.json"


def parse_articles(html: str) -> list[dict]:
    return parse_html_news_listing(
        html,
        source_label="International Christian Concern",
        absolute_link_re=r'href="(https?://www\.persecution\.org/news/[^"]+)"',
        relative_link_re=r'href="(/news/[^"]+)"',
        link_base="https://www.persecution.org",
        fallback_link_re=(
            r'<a[^>]*href="(https?://www\.persecution\.org/news/[^"]+)"[^>]*>(.*?)</a>'
        ),
    )


def parse_wp_json(payload: str) -> tuple[list[dict], str | None]:
    articles: list[dict] = []
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        return articles, f"JSONDecodeError: {e}"
    if not isinstance(data, list):
        return articles, "WP JSON root is not a list"
    for post in data:
        title = strip_html((post.get("title") or {}).get("rendered") or "")
        url = post.get("link") or ""
        date = post.get("date") or post.get("date_gmt") or ""
        excerpt = strip_html((post.get("excerpt") or {}).get("rendered") or "")
        if not is_christian_persecution(title=title, description=excerpt):
            continue
        countries = countries_for_article(title, excerpt)
        articles.append({
            "title": title,
            "url": url,
            "date": normalize_date(date) or date,
            "description": excerpt[:300],
            "countries": countries,
            "source": "International Christian Concern",
        })
    return articles, None


def main():
    print("Fetching International Christian Concern news...")
    cached = load_json_cache(OUTPUT)
    articles: list[dict] = []
    wp_err: str | None = None

    # Prefer WP JSON (less bot-blocked than RSS); fall back to HTML scrape.
    wp_text, wp_fetch_err = fetch_text(ICC_WP_JSON, user_agent=USER_AGENT)
    if wp_text:
        articles, wp_err = parse_wp_json(wp_text)
        print(f"  WP JSON: {len(articles)} articles" + (f" ({wp_err})" if wp_err else ""))
    elif wp_fetch_err:
        print(f"  WP JSON fetch failed: {wp_fetch_err}")

    if not articles:
        html, err = fetch_text(ICC_NEWS_URL, user_agent=USER_AGENT)
        if html is None:
            if cached:
                print("  fetch failed, using cached data")
                cached["status"] = "cached"
                write_json(OUTPUT, cached)
                write_status("icc", "cached", "fetch failed, using cache")
                exit_for_status("cached")
            result = build_news_result(
                source="International Christian Concern",
                source_url=ICC_NEWS_URL,
                status="fetch_failed",
                articles=[],
            )
            write_json(OUTPUT, result)
            msg = err or wp_err or wp_fetch_err or "fetch failed, no cache"
            write_status("icc", "failed", msg)
            exit_for_status("failed")
        articles = parse_articles(html)

    print(f"  found {len(articles)} persecution-related articles")
    result = build_news_result(
        source="International Christian Concern",
        source_url=ICC_NEWS_URL,
        status="ok",
        articles=articles,
        previous=cached,
    )
    write_json(OUTPUT, result)
    print(f"  wrote {OUTPUT} ({result['total_articles']} accumulated)")
    write_status("icc", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
