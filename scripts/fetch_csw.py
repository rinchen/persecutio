#!/usr/bin/env python3
"""Fetch Christian persecution news from Christian Solidarity Worldwide (CSW)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from christian_persecution import is_christian_persecution
from fetch_common import (
    FETCHED,
    USER_AGENT,
    build_news_result,
    detect_countries,
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

CSW_NEWS_URL = "https://www.csw.org.uk/news"
OUTPUT = FETCHED / "csw.json"


def parse_articles(html: str) -> list[dict]:
    articles = []

    article_pattern = re.compile(r"<article[^>]*>(.*?)</article>", re.DOTALL | re.IGNORECASE)
    for match in article_pattern.finditer(html):
        article_html = match.group(1)
        title_match = re.search(r"<h[23][^>]*>(.*?)</h[23]>", article_html, re.DOTALL | re.IGNORECASE)
        if not title_match:
            continue
        title = strip_html(title_match.group(1)).strip()
        if not title:
            continue

        link_match = re.search(r'href="(/news/[^"]+)"', article_html)
        url = f"https://www.csw.org.uk{link_match.group(1)}" if link_match else None

        date_match = re.search(r'<time[^>]*datetime="([^"]+)"', article_html)
        date = date_match.group(1) if date_match else None

        excerpt = ""
        p_match = re.search(r"<p[^>]*>(.*?)</p>", article_html, re.DOTALL | re.IGNORECASE)
        if p_match:
            excerpt = strip_html(p_match.group(1)).strip()[:500]

        if not is_christian_persecution(title=title, description=excerpt):
            continue

        countries = detect_countries(f"{title} {excerpt}")
        articles.append({
            "title": title,
            "url": url,
            "date": normalize_date(date) or date,
            "description": excerpt[:300],
            "countries": countries,
            "source": "Christian Solidarity Worldwide",
        })

    if not articles:
        link_pattern = re.compile(
            r'<a[^>]*href="(/news/[^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )
        for match in link_pattern.finditer(html):
            url_path = match.group(1)
            title = strip_html(match.group(2)).strip()
            if not title or len(title) < 20:
                continue
            if not is_christian_persecution(title=title, description=""):
                continue
            countries = detect_countries(title)
            articles.append({
                "title": title,
                "url": f"https://www.csw.org.uk{url_path}",
                "date": None,
                "description": "",
                "countries": countries,
                "source": "Christian Solidarity Worldwide",
            })

    return articles


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
