import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FETCHED = DATA / "fetched"
FETCHED.mkdir(parents=True, exist_ok=True)

GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

QUERIES = [
    "church attack christian",
    "christian persecution",
    "church bombing",
    "christian killed",
]

ARTICLE_KEYS = {"title", "url", "source", "date"}


def fetch_gdelt(query):
    params = urllib.parse.urlencode({
        "query": query,
        "mode": "artlist",
        "maxrecords": 50,
        "format": "json",
        "timespan": "30d",
    })
    url = f"{GDELT_BASE}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "persecutio/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8", errors="ignore")), url, None
    except Exception as e:
        return {}, url, str(e)


def extract_articles(data):
    articles = []
    for item in data.get("articles", []):
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()
        source = item.get("domain", "") or item.get("source", "") or ""
        date = item.get("seendate", "") or item.get("date", "") or ""
        if not title or not url:
            continue
        articles.append({
            "title": title,
            "url": url,
            "source": source.strip(),
            "date": date.strip(),
        })
    return articles


def guess_country(article):
    title = article.get("title", "").lower()
    known_countries = [
        "nigeria", "india", "pakistan", "china", "iran", "iraq", "syria",
        "egypt", "north korea", "north korea", "myanmar", "sudan", "somalia",
        "eritrea", "yemen", "cuba", "laos", "vietnam", "nicaragua", "colombia",
        "mexico", "indonesia", "saudi arabia", "turkey", "algeria",
        "bangladesh", "central african republic", "haiti", "libya", "malaysia",
        "venezuela", "zimbabwe", "afghanistan", "uganda", "iraq",
    ]
    for country in known_countries:
        if country in title:
            return country.title()
    return "Unknown"


def group_by_country(articles):
    grouped = {}
    for article in articles:
        country = guess_country(article)
        grouped.setdefault(country, []).append(article)
    return grouped


def main():
    print("fetching gdelt articles...")
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
        print(f"    got {len(articles)} articles")
        statuses.append({"query": query, "url": url, "status": "ok", "count": len(articles)})
        all_articles.extend(articles)

    seen_urls = set()
    unique_articles = []
    for a in all_articles:
        if a["url"] not in seen_urls:
            seen_urls.add(a["url"])
            unique_articles.append(a)
    print(f"\ntotal unique articles: {len(unique_articles)}")

    countries = group_by_country(unique_articles)
    print(f"countries found: {len(countries)}")
    for country, arts in sorted(countries.items(), key=lambda x: -len(x[1])):
        print(f"  {country}: {len(arts)}")

    result = {
        "query_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "countries": countries,
        "total_articles": len(unique_articles),
        "queries": statuses,
    }

    out_path = FETCHED / "gdelt.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nsaved to {out_path}")


if __name__ == "__main__":
    main()
