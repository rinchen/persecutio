#!/usr/bin/env python3
"""Fetch FoRB-related resources from OSCE/ODIHR."""
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

PAGE_URL = "https://www.osce.org/odihr/freedom-of-religion-or-belief"
OUTPUT = FETCHED / "osce.json"
# Resource links on the FoRB hub page
LINK_RE = re.compile(
    r'href="((?:https://(?:www\.)?osce\.org|https://odihr\.osce\.org)?/odihr/\d+)"[^>]*>(.*?)</a>',
    re.I | re.S,
)


def parse_articles(html: str) -> list[dict]:
    return parse_html_link_listing(
        html,
        link_re=LINK_RE,
        source_label="OSCE / ODIHR",
        base_url="https://www.osce.org",
        min_title_len=12,
        high_trust=False,
        extra_ok=lambda title, _url: bool(
            re.search(r"religion|belief|forb|christian|church|hate.?crime", title, re.I)
        ),
    )


def main():
    run_news_fetch(
        "osce",
        PAGE_URL,
        parse_articles,
        source_label="OSCE / ODIHR",
        output=OUTPUT,
        found_label="FoRB-related items",
    )


if __name__ == "__main__":
    main()
