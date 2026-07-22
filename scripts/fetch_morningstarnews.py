#!/usr/bin/env python3
"""Fetch Christian persecution news from Morning Star News RSS feed."""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from christian_persecution import is_christian_persecution
from fetch_common import (
    FETCHED,
    KNOWN_COUNTRIES,
    build_news_result,
    detect_countries,
    ensure_fetched_dir,
    exit_for_status,
    fetch_text,
    load_json_cache,
    normalize_date,
    write_json,
    write_status,
)

ensure_fetched_dir()

RSS_URL = "https://morningstarnews.org/feed/"
OUTPUT = FETCHED / "morningstarnews.json"


def parse_rss(xml_text: str) -> list[dict]:
    articles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")
        return articles

    channel = root.find("channel")
    if channel is None:
        return articles

    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()
        desc_clean = re.sub(r"<[^>]+>", "", description).strip()

        categories = []
        for cat_elem in item.findall("category"):
            cat_text = (cat_elem.text or "").strip()
            if cat_text:
                categories.append(cat_text)

        if not is_christian_persecution(
            title=title,
            description=desc_clean,
            categories=categories,
            high_trust_source=True,
        ):
            continue

        search_text = f"{title} {desc_clean}"
        countries = detect_countries(search_text)
        for cat in categories:
            if cat in KNOWN_COUNTRIES and cat not in countries:
                countries.append(cat)

        articles.append({
            "title": title,
            "url": link,
            "date": normalize_date(pub_date) or pub_date,
            "description": desc_clean[:500],
            "countries": countries,
            "categories": categories,
            "source": "Morning Star News",
        })

    return articles


def main():
    print("Fetching Morning Star News RSS feed...")
    cached = load_json_cache(OUTPUT)

    xml_text, err = fetch_text(RSS_URL)
    if xml_text is None:
        if cached:
            print("  fetch failed, using cached data")
            cached["status"] = "cached"
            write_json(OUTPUT, cached)
            write_status("morningstarnews", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        result = build_news_result(
            source="Morning Star News RSS",
            source_url=RSS_URL,
            status="fetch_failed",
            articles=[],
        )
        write_json(OUTPUT, result)
        write_status("morningstarnews", "failed", "fetch failed, no cache")
        exit_for_status("failed")

    articles = parse_rss(xml_text)
    print(f"  found {len(articles)} persecution-related articles")
    result = build_news_result(
        source="Morning Star News RSS",
        source_url=RSS_URL,
        status="ok",
        articles=articles,
        previous=cached,
    )
    write_json(OUTPUT, result)
    print(f"  wrote {OUTPUT} ({result['total_articles']} accumulated)")
    write_status("morningstarnews", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
