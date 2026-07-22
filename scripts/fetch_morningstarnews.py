#!/usr/bin/env python3
"""Fetch Christian persecution news from Morning Star News RSS feed.

Morning Star News is the only independent news service focusing exclusively
on the persecution of Christians. Their RSS feed provides real-time incident
reports with country tags.
"""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FETCHED = DATA / "fetched"
FETCHED.mkdir(parents=True, exist_ok=True)

RSS_URL = "https://morningstarnews.org/feed/"
OUTPUT = FETCHED / "morningstarnews.json"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

KNOWN_COUNTRIES = [
    "Afghanistan", "Algeria", "Azerbaijan", "Bahrain", "Bangladesh",
    "Bhutan", "Brazil", "Brunei", "Burkina Faso", "Cameroon",
    "Central African Republic", "China", "Colombia", "Comoros", "Cuba",
    "Democratic Republic of Congo", "Egypt", "Eritrea", "Ethiopia",
    "Guinea", "Haiti", "India", "Indonesia", "Iran", "Iraq", "Jordan",
    "Kazakhstan", "Kyrgyzstan", "Laos", "Libya", "Malaysia", "Maldives",
    "Mali", "Mauritania", "Mexico", "Morocco", "Mozambique", "Myanmar",
    "Nicaragua", "Niger", "Nigeria", "North Korea", "Oman", "Pakistan",
    "Philippines", "Qatar", "Russia", "Saudi Arabia", "Somalia",
    "Sri Lanka", "Sudan", "Syria", "Tajikistan", "Tunisia", "Turkey",
    "Turkmenistan", "Uganda", "United States", "Uzbekistan", "Venezuela",
    "Vietnam", "Yemen", "Zimbabwe",
]

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
    "myanmar": "Myanmar",
    "laos": "Laos",
    "vietnam": "Vietnam",
    "china": "China",
    "north korea": "North Korea",
    "uzbekistan": "Uzbekistan",
    "turkmenistan": "Turkmenistan",
    "tajikistan": "Tajikistan",
    "kazakhstan": "Kazakhstan",
    "kyrgyzstan": "Kyrgyzstan",
    "azerbaijan": "Azerbaijan",
    "russia": "Russia",
    "algeria": "Algeria",
    "morocco": "Morocco",
    "tunisia": "Tunisia",
    "libya": "Libya",
    "egypt": "Egypt",
    "sudan": "Sudan",
    "somalia": "Somalia",
    "eritrea": "Eritrea",
    "ethiopia": "Ethiopia",
    "nigeria": "Nigeria",
    "niger": "Niger",
    "burkina faso": "Burkina Faso",
    "mali": "Mali",
    "cameroon": "Cameroon",
    "central african republic": "Central African Republic",
    "dr congo": "Democratic Republic of Congo",
    "mozambique": "Mozambique",
    "uganda": "Uganda",
    "kenya": None,
    "tanzania": None,
    "zimbabwe": "Zimbabwe",
    "south africa": None,
    "bangladesh": "Bangladesh",
    "sri lanka": "Sri Lanka",
    "maldives": "Maldives",
    "bhutan": "Bhutan",
    "pakistan": "Pakistan",
    "india": "India",
    "nepal": None,
    "afghanistan": "Afghanistan",
    "iran": "Iran",
    "iraq": "Iraq",
    "syria": "Syria",
    "jordan": "Jordan",
    "lebanon": None,
    "israel": None,
    "palestine": None,
    "saudi arabia": "Saudi Arabia",
    "yemen": "Yemen",
    "oman": "Oman",
    "bahrain": "Bahrain",
    "qatar": "Qatar",
    "uae": None,
    "united arab emirates": None,
    "kuwait": None,
    "turkey": "Turkey",
    "azerbaijan": "Azerbaijan",
}


def fetch_rss(url):
    """Fetch and parse RSS feed."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  fetch error: {e}")
        return None


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


def is_persecution_article(categories):
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

        if not is_persecution_article(categories):
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


def main():
    print("Fetching Morning Star News RSS feed...")
    cached = {}
    if OUTPUT.exists():
        try:
            cached = json.loads(OUTPUT.read_text(encoding="utf-8"))
        except Exception:
            pass

    xml_text = fetch_rss(RSS_URL)
    if xml_text is None:
        if cached:
            print("  fetch failed, using cached data")
            cached["status"] = "cached"
            OUTPUT.write_text(json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8")
            return
        print("  no cache available, writing empty output")
        _write_empty("fetch_failed")
        return

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


if __name__ == "__main__":
    main()
