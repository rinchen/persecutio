#!/usr/bin/env python3
"""Fetch FoRB items from the UN Special Rapporteur on religion or belief hub."""
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

PAGE_URL = "https://www.ohchr.org/en/special-procedures/sr-religion-or-belief"
OUTPUT = FETCHED / "unsrforb.json"
LINK_RE = re.compile(
    r'href="(https://www\.ohchr\.org/en/[^"]+)"[^>]*>(.*?)</a>',
    re.I | re.S,
)


def parse_articles(html: str) -> list[dict]:
    articles: list[dict] = []
    seen: set[str] = set()
    for match in LINK_RE.finditer(html):
        url = match.group(1).split("#")[0]
        title = strip_html(match.group(2)).strip()
        if len(title) < 20 or url in seen:
            continue
        if "/special-procedures/sr-religion-or-belief" == url.rstrip("/").split("ohchr.org")[-1]:
            continue
        if not is_christian_persecution(
            title=title, description=url, high_trust_source=True
        ) and not re.search(
            r"religion|belief|forb|christian|blasphemy|apostasy",
            f"{title} {url}",
            re.I,
        ):
            continue
        # Keep SR-relevant paths
        if not re.search(
            r"religion|belief|forb|documents|statements|press|news|countries",
            url,
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
            "source": "UN Special Rapporteur on FoRB",
        })
    return articles[:40]


def main():
    print("Fetching UN Special Rapporteur on FoRB hub...")
    cached = load_json_cache(OUTPUT)
    html, err = fetch_text(PAGE_URL, user_agent=USER_AGENT)
    if html is None:
        if cached:
            cached["status"] = "cached"
            write_json(OUTPUT, cached)
            write_status("unsrforb", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        result = build_news_result(
            source="UN Special Rapporteur on FoRB",
            source_url=PAGE_URL,
            status="fetch_failed",
            articles=[],
        )
        write_json(OUTPUT, result)
        write_status("unsrforb", "failed", f"fetch failed: {err}")
        exit_for_status("failed")

    articles = parse_articles(html)
    print(f"  found {len(articles)} FoRB-related items")
    result = build_news_result(
        source="UN Special Rapporteur on FoRB",
        source_url=PAGE_URL,
        status="ok",
        articles=articles,
        previous=cached,
    )
    write_json(OUTPUT, result)
    print(f"  wrote {OUTPUT} ({result['total_articles']} accumulated)")
    write_status("unsrforb", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
