#!/usr/bin/env python3
"""Fetch Christian persecution news from Barnabas Aid."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import (
    FETCHED,
    ensure_fetched_dir,
    parse_html_link_listing,
    run_news_fetch,
)

ensure_fetched_dir()

NEWS_URL = "https://www.barnabasaid.org/us/news/"
OUTPUT = FETCHED / "barnabas.json"
LINK_RE = re.compile(
    r'href="(https://www\.barnabasaid\.org/us/news/[a-z0-9][^"]+/)"[^>]*>(.*?)</a>',
    re.I | re.S,
)


def parse_articles(html: str) -> list[dict]:
    return parse_html_link_listing(
        html,
        link_re=LINK_RE,
        source_label="Barnabas Aid",
        skip_urls=lambda url: url.rstrip("/").endswith("/us/news") or "/page/" in url,
        min_title_len=20,
        high_trust=True,
    )


def main():
    run_news_fetch(
        "barnabas",
        NEWS_URL,
        parse_articles,
        source_label="Barnabas Aid",
        output=OUTPUT,
        found_label="persecution-related articles",
    )


if __name__ == "__main__":
    main()
