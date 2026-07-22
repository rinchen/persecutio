#!/usr/bin/env python3
"""Fetch Christian persecution-related news from GDELT Doc API."""
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from christian_persecution import is_christian_persecution
from fetch_common import (
    FETCHED,
    USER_AGENT,
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

GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
OUTPUT = FETCHED / "gdelt.json"

QUERIES = [
    "church attack christian",
    "christian persecution",
    "church bombing",
    "christian killed",
]


def fetch_gdelt(query: str):
    params = urllib.parse.urlencode({
        "query": query,
        "mode": "artlist",
        "maxrecords": 50,
        "format": "json",
        "timespan": "30d",
    })
    url = f"{GDELT_BASE}?{params}"
    text, err = fetch_text(url, timeout=30, user_agent=USER_AGENT)
    if text is None:
        return {}, url, err
    try:
        return json.loads(text), url, None
    except json.JSONDecodeError as e:
        return {}, url, f"JSONDecodeError: {e}"


def extract_articles(data: dict) -> list[dict]:
    articles = []
    for item in data.get("articles", []):
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        source = item.get("domain") or item.get("source") or ""
        date = item.get("seendate") or item.get("date") or ""
        if not title or not url:
            continue
        if not is_christian_persecution(title=title, description=""):
            continue
        countries = detect_countries(title)
        articles.append({
            "title": title,
            "url": url,
            "source": "GDELT",
            "publisher": source.strip(),
            "date": normalize_date(date) or date.strip(),
            "description": "",
            "countries": countries,
        })
    return articles


def main():
    print("fetching gdelt articles...")
    cached = load_json_cache(OUTPUT)
    all_articles = []
    statuses = []

    for query in QUERIES:
        print(f"  querying: {query}")
        data, url, error = fetch_gdelt(query)
        if error:
            print(f"    FAILED: {error}")
            statuses.append({"query": query, "url": url, "status": "failed", "error": error})
            continue
        articles = extract_articles(data)
        print(f"    got {len(articles)} filtered articles")
        statuses.append({"query": query, "url": url, "status": "ok", "count": len(articles)})
        all_articles.extend(articles)

    result = build_news_result(
        source="GDELT Doc API",
        source_url=GDELT_BASE,
        status="ok",
        articles=all_articles,
        previous=cached,
    )
    result["query_date"] = result["fetched_at"][:10]
    result["queries"] = statuses

    failed_queries = [s for s in statuses if s["status"] == "failed"]
    if statuses and len(failed_queries) == len(statuses):
        final_status = "failed"
        result["status"] = "failed"
        write_json(OUTPUT, result)
        write_status("gdelt", final_status, "all queries failed")
    elif failed_queries:
        final_status = "partial"
        result["status"] = "partial"
        write_json(OUTPUT, result)
        write_status("gdelt", final_status, f"{len(failed_queries)} of {len(statuses)} queries failed")
    else:
        final_status = "ok"
        write_json(OUTPUT, result)
        write_status("gdelt", final_status)

    print(f"\ntotal accumulated: {result['total_articles']}")
    print(f"saved to {OUTPUT}")
    exit_for_status(final_status)


if __name__ == "__main__":
    main()
