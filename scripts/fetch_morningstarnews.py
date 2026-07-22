#!/usr/bin/env python3
"""Fetch Christian persecution news from Morning Star News RSS feed."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import FETCHED, ensure_fetched_dir
from rss_news_fetcher import run_rss_fetcher

ensure_fetched_dir()

if __name__ == "__main__":
    run_rss_fetcher(
        name="morningstarnews",
        source_label="Morning Star News",
        rss_url="https://morningstarnews.org/feed/",
        output=FETCHED / "morningstarnews.json",
        high_trust=True,
    )
