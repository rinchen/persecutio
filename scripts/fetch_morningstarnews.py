#!/usr/bin/env python3
"""Fetch Christian persecution news from Morning Star News RSS feed.

Morning Star News is the only independent news service focusing exclusively
on the persecution of Christians. Their RSS feed provides real-time incident
reports with country tags.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import (
    FETCHED,
    KNOWN_COUNTRIES,
    ensure_fetched_dir,
    exit_for_status,
    fetch_text,
    load_json_cache,
    write_status,
)

ensure_fetched_dir()

RSS_URL = "https://morningstarnews.org/feed/"
OUTPUT = FETCHED / "morningstarnews.json"

PERSECUTION_CATEGORIES = {
    "persecution", "religious freedom", "christianity", "apostasy",
    "blasphemy", "forced conversion", "forced marriage", "church attack",
    "martyrdom", "imprisonment", "kidnapping", "sexual assault",
    "church closure", "discrimination", "violence",
}

COUNTRY_ALIASES = {
    "dr congo": "Democratic Republic of Congo",
    "drc": "Democratic Republic of Congo",
    "congo": "Democratic Republic of Congo",
    "democratic republic of the congo": "Democratic Republic of Congo",
    "car": "Central African Republic",
    "myanmar": "Myanmar",
    "burma": "Myanmar",
    "north korea": "North Korea",
    "dprk": "North Korea",
    "south sudan": "Sudan",
    "palestine": None,
    "gaza": None,
    "israel": None,
    "west bank": None,
    "ukraine": None,
    "russia": "Russia",
    "china": "China",
    "india": "India",
    "nigeria": "Nigeria",
    "pakistan": "Pakistan",
    "iran": "Iran",
    "iraq": "Iraq",
    "egypt": "Egypt",
    "sudan": "Sudan",
    "syria": "Syria",
    "somalia": "Somalia",
    "afghanistan": "Afghanistan",
    "ethiopia": "Ethiopia",
    "mali": "Mali",
    "mozambique": "Mozambique",
    "cameroon": "Cameroon",
    "colombia": "Colombia",
    "mexico": "Mexico",
    "nicaragua": "Nicaragua",
    "cuba": "Cuba",
    "venezuela": "Venezuela",
    "haiti": "Haiti",
    "brazil": "Brazil",
    "united states": "United States",
    "usa": "United States",
    "us": "United States",
    "indonesia": "Indonesia",
    "philippines": "Philippines",
    "malaysia": "Malaysia",
    "laos": "Laos",
    "vietnam": "Vietnam",
    "uzbekistan": "Uzbekistan",
    "turkmenistan": "Turkmenistan",
    "tajikistan": "Tajikistan",
    "kazakhstan": "Kazakhstan",
    "kyrgyzstan": "Kyrgyzstan",
    "azerbaijan": "Azerbaijan",
    "algeria": "Algeria",
    "morocco": "Morocco",
    "tunisia": "Tunisia",
    "libya": "Libya",
    "eritrea": "Eritrea",
    "niger": "Niger",
    "burkina faso": "Burkina Faso",
    "central african republic": "Central African Republic",
    "uganda": "Uganda",
    "kenya": None,
    "tanzania": None,
    "zimbabwe": "Zimbabwe",
    "south africa": None,
    "bangladesh": "Bangladesh",
    "sri lanka": "Sri Lanka",
    "maldives": "Maldives",
    "bhutan": "Bhutan",
    "nepal": None,
    "jordan": "Jordan",
    "lebanon": None,
    "saudi arabia": "Saudi Arabia",
    "yemen": "Yemen",
    "oman": "Oman",
    "bahrain": "Bahrain",
    "qatar": "Qatar",
    "uae": None,
    "united arab emirates": None,
    "kuwait": None,
    "turkey": "Turkey",
}


def fetch_rss(url):
    """Fetch and parse RSS feed."""
    text, err = fetch_text(url)
    if err:
        return None
    return text


def detect_countries(text):
    """Detect country names from article text (title + description)."""
    found = set()
    text_lower = text.lower()
    for alias, canonical in COUNTRY_ALIASES.items():
        if canonical is None:
            continue
        pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(pattern, text_lower):
            found.add(canonical)
    return sorted(found)


def is_persecution_by_categories(categories):
    """Check if article categories indicate Christian persecution content."""
    cats_lower = {c.lower().strip() for c in categories}
    if cats_lower & PERSECUTION_CATEGORIES:
        return True
    for cat in cats_lower:
        for kw in PERSECUTION_CATEGORIES:
            if kw in cat:
                return True
    return False


def parse_rss(xml_text):
    """Parse RSS XML and extract articles."""
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
        desc_clean = re.sub(r'<[^>]+>', '', description).strip()

        categories = []
        for cat_elem in item.findall("category"):
            cat_text = (cat_elem.text or "").strip()
            if cat_text:
                categories.append(cat_text)

        if not is_persecution_by_categories(categories):
            continue

        search_text = f"{title} {desc_clean}"
        countries = detect_countries(search_text)

        for cat in categories:
            if cat in KNOWN_COUNTRIES:
                if cat not in countries:
                    countries.append(cat)

        articles.append({
            "title": title,
            "url": link,
            "date": pub_date,
            "description": desc_clean[:500],
            "countries": countries,
            "categories": categories,
            "source": "Morning Star News",
        })

    return articles


def _write_empty(status):
    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Morning Star News RSS",
        "source_url": RSS_URL,
        "status": status,
        "articles": [],
        "countries": {},
        "total_articles": 0,
        "countries_with_articles": 0,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote empty output to {OUTPUT}")


def main():
    print("Fetching Morning Star News RSS feed...")
    cached = load_json_cache(OUTPUT)

    xml_text = fetch_rss(RSS_URL)
    if xml_text is None:
        if cached:
            print("  fetch failed, using cached data")
            cached["status"] = "cached"
            OUTPUT.write_text(json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8")
            write_status("morningstarnews", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        print("  no cache available, writing empty output")
        _write_empty("fetch_failed")
        write_status("morningstarnews", "failed", "fetch failed, no cache")
        exit_for_status("failed")

    articles = parse_rss(xml_text)
    print(f"  found {len(articles)} persecution-related articles")

    by_country = {}
    for a in articles:
        for country in a["countries"]:
            by_country.setdefault(country, []).append({
                "title": a["title"],
                "url": a["url"],
                "date": a["date"],
                "description": a["description"][:200],
            })

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Morning Star News RSS",
        "source_url": RSS_URL,
        "status": "ok",
        "articles": articles,
        "countries": by_country,
        "total_articles": len(articles),
        "countries_with_articles": len(by_country),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {OUTPUT}")
    print(f"  countries with articles: {len(by_country)}")
    for c in sorted(by_country.keys()):
        print(f"    {c}: {len(by_country[c])} articles")
    write_status("morningstarnews", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
