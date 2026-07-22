#!/usr/bin/env python3
"""Fetch Bitter Winter FoRB news; keep Christian-persecution items only."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import FETCHED, ensure_fetched_dir
from rss_news_fetcher import run_rss_fetcher

ensure_fetched_dir()

if __name__ == "__main__":
    run_rss_fetcher(
        name="bitterwinter",
        source_label="Bitter Winter",
        rss_url="https://bitterwinter.org/feed/",
        output=FETCHED / "bitterwinter.json",
        high_trust=False,
    )
