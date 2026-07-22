#!/usr/bin/env python3
"""Fetch Christian persecution incident reports from CSW.

Christian Solidarity Worldwide (CSW) is a UK-based human rights organisation
specialising in freedom of religion or belief. They track persecution
incidents in 20+ countries across Africa, Asia, Latin America and the Middle East.
Source: https://www.csw.org.uk/
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import (
    FETCHED,
    USER_AGENT,
    detect_countries,
    ensure_fetched_dir,
    exit_for_status,
    fetch_text,
    is_persecution_article,
    load_json_cache,
    strip_html,
    write_status,
)

ensure_fetched_dir()

CSW_NEWS_URL = "https://www.csw.org.uk/news"
OUTPUT = FETCHED / "csw.json"


def parse_articles(html):
    """Parse CSW news page for persecution articles."""
    articles = []

    article_pattern = re.compile(
        r'<article[^>]*>(.*?)</article>',
        re.DOTALL | re.IGNORECASE
    )
    for match in article_pattern.finditer(html):
        article_html = match.group(1)
        title_match = re.search(r'<h[23][^>]*>(.*?)</h[23]>', article_html, re.DOTALL | re.IGNORECASE)
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
        p_match = re.search(r'<p[^>]*>(.*?)</p>', article_html, re.DOTALL | re.IGNORECASE)
        if p_match:
            excerpt = strip_html(p_match.group(1)).strip()[:500]

        full_text = f"{title} {excerpt}"
        if not is_persecution_article(full_text):
            continue

        countries = detect_countries(full_text)

        articles.append({
            "title": title,
            "url": url,
            "date": date,
            "description": excerpt[:300],
            "countries": countries,
            "source": "Christian Solidarity Worldwide",
        })

    if not articles:
        link_pattern = re.compile(
            r'<a[^>]*href="(/news/[^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE
        )
        for match in link_pattern.finditer(html):
            url_path = match.group(1)
            title = strip_html(match.group(2)).strip()
            if not title or len(title) < 20:
                continue
            full_url = f"https://www.csw.org.uk{url_path}"
            full_text = title
            if not is_persecution_article(full_text):
                continue
            countries = detect_countries(full_text)
            articles.append({
                "title": title,
                "url": full_url,
                "date": None,
                "description": "",
                "countries": countries,
                "source": "Christian Solidarity Worldwide",
            })

    return articles


def _write_empty(status):
    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Christian Solidarity Worldwide",
        "source_url": CSW_NEWS_URL,
        "status": status,
        "articles": [],
        "countries": {},
        "total_articles": 0,
        "countries_with_articles": 0,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote empty output to {OUTPUT}")


def main():
    print("Fetching Christian Solidarity Worldwide news...")
    cached = load_json_cache(OUTPUT)

    html, err = fetch_text(CSW_NEWS_URL, user_agent=USER_AGENT)
    if html is None:
        if cached:
            print("  fetch failed, using cached data")
            cached["status"] = "cached"
            cached["fetched_at"] = datetime.now(timezone.utc).isoformat()
            OUTPUT.write_text(json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8")
            write_status("csw", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        print("  CSW site unreachable and no cache, writing stub")
        _write_empty("fetch_failed")
        write_status("csw", "failed", "fetch failed, no cache")
        exit_for_status("failed")

    articles = parse_articles(html)
    print(f"  found {len(articles)} persecution-related articles")

    by_country = {}
    for a in articles:
        for country in a["countries"]:
            by_country.setdefault(country, []).append({
                "title": a["title"],
                "url": a["url"],
                "date": a["date"],
                "description": a["description"],
            })

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Christian Solidarity Worldwide",
        "source_url": CSW_NEWS_URL,
        "status": "ok",
        "articles": articles,
        "countries": by_country,
        "total_articles": len(articles),
        "countries_with_articles": len(by_country),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  countries with articles: {len(by_country)}")
    for c in sorted(by_country.keys()):
        print(f"    {c}: {len(by_country[c])} articles")
    print(f"  wrote {OUTPUT}")
    write_status("csw", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
