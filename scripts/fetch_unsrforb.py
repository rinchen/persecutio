#!/usr/bin/env python3
"""Fetch FoRB items from the UN Special Rapporteur on religion or belief hub."""
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

PAGE_URL = "https://www.ohchr.org/en/special-procedures/sr-religion-or-belief"
OUTPUT = FETCHED / "unsrforb.json"
LINK_RE = re.compile(
    r'href="(https://www\.ohchr\.org/en/[^"]+)"[^>]*>(.*?)</a>',
    re.I | re.S,
)
_HUB = "https://www.ohchr.org/en/special-procedures/sr-religion-or-belief"


def _skip(url: str) -> bool:
    if url.rstrip("/") == _HUB.rstrip("/"):
        return True
    return not re.search(
        r"religion|belief|forb|documents|statements|press|news|countries",
        url,
        re.I,
    )


def _extra_ok(title: str, url: str) -> bool:
    return bool(
        re.search(
            r"religion|belief|forb|christian|blasphemy|apostasy",
            f"{title} {url}",
            re.I,
        )
    )


def parse_articles(html: str) -> list[dict]:
    return parse_html_link_listing(
        html,
        link_re=LINK_RE,
        source_label="UN Special Rapporteur on FoRB",
        skip_urls=_skip,
        extra_ok=_extra_ok,
        min_title_len=20,
        high_trust=True,
        limit=40,
    )


def main():
    run_news_fetch(
        "unsrforb",
        PAGE_URL,
        parse_articles,
        source_label="UN Special Rapporteur on FoRB",
        output=OUTPUT,
        found_label="FoRB-related items",
    )


if __name__ == "__main__":
    main()
