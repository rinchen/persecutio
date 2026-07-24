#!/usr/bin/env python3
"""Fetch Forum 18 FoRB news; keep Christian-persecution items only."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rss_news_fetcher import run_rss_fetcher

if __name__ == "__main__":
    run_rss_fetcher(name="forum18")
