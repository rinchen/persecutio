#!/usr/bin/env python3
"""Fetch Christian persecution statistics from Global Christian Relief.

GCR publishes annual statistics on Christian persecution worldwide including
killings, displacement, abuse, and country-level data from the World Watch List.
Source: https://globalchristianrelief.org/stories/christian-persecution-statistics
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import (
    FETCHED,
    KNOWN_COUNTRIES,
    USER_AGENT,
    ensure_fetched_dir,
    exit_for_status,
    fetch_text,
    load_json_cache,
    strip_html,
    write_status,
)

ensure_fetched_dir()

STATS_URL = "https://globalchristianrelief.org/stories/christian-persecution-statistics"
OUTPUT = FETCHED / "gcr_stats.json"


def extract_number(text):
    """Extract a number from text, handling commas and dots."""
    clean = re.sub(r'[^\d]', '', text)
    return int(clean) if clean else None


def parse_global_stats(html):
    """Extract global persecution statistics from the page."""
    stats = {}

    patterns = [
        (r'([\d,]+)\s*(?:Christians?\s+)?(?:were\s+)?killed', "total_killed"),
        (r'([\d,]+)\s*(?:Christians?\s+)?(?:were\s+)?(?:displaced|became\s+refugees)', "total_displaced"),
        (r'([\d,]+)\s*(?:cases?\s+of\s+)?(?:physical|mental)\s+(?:and\s+)?(?:mental\s+)?abuse', "total_abused"),
        (r'([\d,]+)\s*(?:million\s+)?Christians\s+(?:face|face\s+high\s+levels)', "total_persecuted_text"),
        (r'([\d,]+)\s*million\s+believers', "total_persecuted"),
        (r'([\d,]+)\s*(?:Christians?\s+)?(?:were\s+)?(?:arrested|detained|imprisoned)', "total_arrested"),
        (r'([\d,]+)\s*(?:Christians?\s+)?(?:were\s+)?(?:abducted|kidnapped)', "total_abducted"),
        (r'([\d,]+)\s*(?:churches?\s+)?(?:were\s+)?(?:attacked|destroyed)', "total_church_attacks"),
    ]

    for pattern, key in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            val = extract_number(match.group(1))
            if val:
                stats[key] = val

    million_match = re.search(r'([\d,]+)\s*(?:million\s+)?(?:believers|Christians)\s+(?:now\s+)?face', html, re.IGNORECASE)
    if million_match:
        num = extract_number(million_match.group(1))
        if num and num < 1000:
            stats["total_persecuted"] = num * 1_000_000
        elif num:
            stats["total_persecuted"] = num

    return stats


def parse_country_stats(html):
    """Extract country-specific persecution data."""
    countries = {}

    for country in KNOWN_COUNTRIES:
        country_section = None
        escaped = re.escape(country)
        section_match = re.search(
            rf'(?:###?\s*)?\*?\*?{escaped}\*?\*?\s*[\—\-–]?\s*(.*?)(?=###?\s*\*?\*?[A-Z]|\Z)',
            html, re.DOTALL | re.IGNORECASE
        )
        if section_match:
            country_section = section_match.group(1)[:2000]
        else:
            bullet_match = re.search(
                rf'\*?\*?{escaped}\*?\*?\s*[\—\-–]?\s*(.*?)(?=\n\s*\*|\n\s*###|\Z)',
                html, re.DOTALL | re.IGNORECASE
            )
            if bullet_match:
                country_section = bullet_match.group(1)[:2000]

        if not country_section:
            continue

        entry = {}
        kill_match = re.search(r'([\d,]+)\s*(?:of\s+)?(?:the\s+)?(?:believers\s+)?killed', country_section, re.IGNORECASE)
        if kill_match:
            entry["killed"] = extract_number(kill_match.group(1))

        score_match = re.search(r'(?:score|persecution\s+score)[\s:]*(\d+)', country_section, re.IGNORECASE)
        if score_match:
            entry["persecution_score"] = int(score_match.group(1))

        rank_match = re.search(r'(?:No\.?\s*|rank(?:ed)?\s*|#)(\d+)', country_section, re.IGNORECASE)
        if rank_match:
            entry["wwl_ranking"] = int(rank_match.group(1))

        notes = strip_html(country_section)[:500]
        if notes:
            entry["notes"] = notes

        if entry:
            countries[country] = entry

    return countries


def _write_empty(status):
    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Global Christian Relief - Christian Persecution Statistics",
        "source_url": STATS_URL,
        "status": status,
        "global_stats": {},
        "countries": {},
        "total_countries_with_data": 0,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote empty output to {OUTPUT}")


def main():
    print("Fetching Global Christian Relief statistics...")
    cached = load_json_cache(OUTPUT)

    html, err = fetch_text(STATS_URL, user_agent=USER_AGENT)
    if html is None:
        if cached:
            print("  fetch failed, using cached data")
            cached["status"] = "cached"
            cached["fetched_at"] = datetime.now(timezone.utc).isoformat()
            OUTPUT.write_text(json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8")
            write_status("gcr", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        print("  GCR site unreachable and no cache, writing stub")
        _write_empty("fetch_failed")
        write_status("gcr", "failed", "fetch failed, no cache")
        exit_for_status("failed")

    global_stats = parse_global_stats(html)
    country_stats = parse_country_stats(html)

    text = strip_html(html)

    for country in KNOWN_COUNTRIES:
        if country not in country_stats:
            pattern = rf'{re.escape(country)}\s*[\—\-–]\s*(.*?)(?=[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*[\—\-–]|\Z)'
            match = re.search(pattern, text)
            if match:
                snippet = match.group(1)[:300]
                entry = {}
                kill_m = re.search(r'([\d,]+)\s*killed', snippet, re.IGNORECASE)
                if kill_m:
                    entry["killed"] = extract_number(kill_m.group(1))
                if snippet.strip():
                    entry["notes"] = snippet.strip()[:200]
                if entry:
                    country_stats[country] = entry

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Global Christian Relief - Christian Persecution Statistics",
        "source_url": STATS_URL,
        "status": "ok",
        "global_stats": global_stats,
        "countries": country_stats,
        "total_countries_with_data": len(country_stats),
    }
    if not country_stats and not global_stats:
        if cached:
            print("  parse yielded no stats; keeping cached data")
            cached["status"] = "partial"
            cached["fetched_at"] = datetime.now(timezone.utc).isoformat()
            OUTPUT.write_text(json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8")
            write_status("gcr", "partial", "parse yielded no stats")
            exit_for_status("partial")
        _write_empty("parse_empty")
        write_status("gcr", "failed", "parse yielded no stats")
        exit_for_status("failed")

    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  global stats: {json.dumps(global_stats, indent=4)}")
    print(f"  countries with data: {len(country_stats)}")
    for c in sorted(country_stats.keys()):
        print(f"    {c}: {country_stats[c]}")
    print(f"  wrote {OUTPUT}")
    write_status("gcr", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
