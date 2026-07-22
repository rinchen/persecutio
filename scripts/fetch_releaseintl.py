#!/usr/bin/env python3
"""Fetch Release International news; keep Christian-persecution items only."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import FETCHED, ensure_fetched_dir
from rss_news_fetcher import run_rss_fetcher

ensure_fetched_dir()

if __name__ == "__main__":
    run_rss_fetcher(
        name="releaseintl",
        source_label="Release International",
        rss_url="https://releaseinternational.org/feed/",
        output=FETCHED / "releaseintl.json",
        high_trust=True,
    )
