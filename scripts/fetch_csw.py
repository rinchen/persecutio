#!/usr/bin/env python3
"""Fetch Christian persecution incident reports from CSW.

Christian Solidarity Worldwide (CSW) is a UK-based human rights organisation
specialising in freedom of religion or belief. They track persecution
incidents in 20+ countries across Africa, Asia, Latin America and the Middle East.
Source: https://www.csw.org.uk/
"""
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FETCHED = DATA / "fetched"
FETCHED.mkdir(parents=True, exist_ok=True)

CSW_NEWS_URL = "https://www.csw.org.uk/news"
OUTPUT = FETCHED / "csw.json"

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

PERSECUTION_KEYWORDS = [
    "persecution", "persecuted", "religious freedom", "freedom of religion",
    "christian", "church", "pastor", "believer", "faith",
    "violence", "attack", "killed", "murdered", "martyr",
    "imprisoned", "detained", "arrested", "sentenced",
    "harassment", "intimidation", "threat", "discrimination",
    "blasphemy", "anti-conversion", "forced conversion",
    "church closure", "church demolition", "church attack",
    "kidnapping", "abduction", "sexual violence", "forced marriage",
    "burned", "burnt", "destroyed", "vandalism",
]


def fetch_page(url):
    """Fetch HTML page."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  fetch error: {e}")
        return None


def strip_html(html):
    """Remove HTML tags and normalize whitespace."""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def detect_countries(text):
    """Detect country names from text."""
    found = []
    text_lower = text.lower()
    for country in KNOWN_COUNTRIES:
        if re.search(r'\b' + re.escape(country.lower()) + r'\b', text_lower):
            found.append(country)
    return found


def is_persecution_article(text):
    """Check if article text is about Christian persecution."""
    text_lower = text.lower()
    christian_terms = ["christian", "church", "pastor", "believer", "faith",
                       "evangelical", "catholic", "protestant", "orthodox",
                       "gospel", "jesus", "christ", "bible", "worship"]
    persecution_terms = ["persecution", "persecuted", "violence", "attack",
                         "killed", "murdered", "imprisoned", "detained",
                         "arrested", "harassment", "intimidation", "threat",
                         "discrimination", "blasphemy", "forced conversion",
                         "church closure", "church demolition", "church attack",
                         "burned", "burnt", "destroyed", "vandalism",
                         "religious freedom", "freedom of religion"]
    has_christian = any(t in text_lower for t in christian_terms)
    has_persecution = any(t in text_lower for t in persecution_terms)
    return has_christian and has_persecution


def parse_articles(html):
    """Parse CSW news page for persecution articles."""
    articles = []

    article_pattern = re.compile(
        r'<article[^>]*>(.*?)</article>',
        re.DOTALL | re.IGNORECASE
    )
    for match in article_pattern.finditer(html):
        article_html = match.group(1)
        title_match = re.search(r'<h[23][^>]*>(.*?)</h[23]>', article_html, re.DOTALL | re.IGNORECASE)
        if not title_match:
            continue
        title = strip_html(title_match.group(1)).strip()
        if not title:
            continue

        link_match = re.search(r'href="(/news/[^"]+)"', article_html)
        url = f"https://www.csw.org.uk{link_match.group(1)}" if link_match else None

        date_match = re.search(r'<time[^>]*datetime="([^"]+)"', article_html)
        date = date_match.group(1) if date_match else None

        excerpt = ""
        p_match = re.search(r'<p[^>]*>(.*?)</p>', article_html, re.DOTALL | re.IGNORECASE)
        if p_match:
            excerpt = strip_html(p_match.group(1)).strip()[:500]

        full_text = f"{title} {excerpt}"
        if not is_persecution_article(full_text):
            continue

        countries = detect_countries(full_text)

        articles.append({
            "title": title,
            "url": url,
            "date": date,
            "description": excerpt[:300],
            "countries": countries,
            "source": "Christian Solidarity Worldwide",
        })

    if not articles:
        link_pattern = re.compile(
            r'<a[^>]*href="(/news/[^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE
        )
        for match in link_pattern.finditer(html):
            url_path = match.group(1)
            title = strip_html(match.group(2)).strip()
            if not title or len(title) < 20:
                continue
            full_url = f"https://www.csw.org.uk{url_path}"
            full_text = title
            if not is_persecution_article(full_text):
                continue
            countries = detect_countries(full_text)
            articles.append({
                "title": title,
                "url": full_url,
                "date": None,
                "description": "",
                "countries": countries,
                "source": "Christian Solidarity Worldwide",
            })

    return articles


def main():
    print("Fetching Christian Solidarity Worldwide news...")
    cached = {}
    if OUTPUT.exists():
        try:
            cached = json.loads(OUTPUT.read_text(encoding="utf-8"))
        except Exception:
            pass

    html = fetch_page(CSW_NEWS_URL)
    if html is None:
        if cached:
            print("  fetch failed, using cached data")
            cached["status"] = "cached"
            cached["fetched_at"] = datetime.now(timezone.utc).isoformat()
            OUTPUT.write_text(json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8")
            return
        print("  CSW site unreachable and no cache, writing stub")
        _write_empty("fetch_failed")
        return

    articles = parse_articles(html)
    print(f"  found {len(articles)} persecution-related articles")

    by_country = {}
    for a in articles:
        for country in a["countries"]:
            by_country.setdefault(country, []).append({
                "title": a["title"],
                "url": a["url"],
                "date": a["date"],
                "description": a["description"],
            })

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Christian Solidarity Worldwide",
        "source_url": CSW_NEWS_URL,
        "status": "ok",
        "articles": articles,
        "countries": by_country,
        "total_articles": len(articles),
        "countries_with_articles": len(by_country),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  countries with articles: {len(by_country)}")
    for c in sorted(by_country.keys()):
        print(f"    {c}: {len(by_country[c])} articles")
    print(f"  wrote {OUTPUT}")


def _write_empty(status):
    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Christian Solidarity Worldwide",
        "source_url": CSW_NEWS_URL,
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
