#!/usr/bin/env python3
"""Fetch Forum 18 FoRB news; keep Christian-persecution items only."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import FETCHED, ensure_fetched_dir
from rss_news_fetcher import run_rss_fetcher

ensure_fetched_dir()

if __name__ == "__main__":
    run_rss_fetcher(
        name="forum18",
        source_label="Forum 18",
        rss_url="https://www.forum18.org/syndication/forum18.xml",
        output=FETCHED / "forum18.json",
        high_trust=False,
    )
