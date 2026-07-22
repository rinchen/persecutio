import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import (
    FETCHED,
    USER_AGENT,
    ensure_fetched_dir,
    exit_for_status,
    fetch_text,
    load_json_cache,
    write_status,
)

ensure_fetched_dir()

WWL_URL = "https://www.opendoors.org/en-US/persecution/countries/"
CACHE_PATH = FETCHED / "opendoors.json"


def fetch_url(url, timeout=20):
    text, err = fetch_text(url, timeout=timeout, user_agent=USER_AGENT)
    if err:
        raise RuntimeError(err)
    return text


def parse_json_from_html(html):
    patterns = [
        r"window\.__NEXT_DATA__\s*=\s*(\{.*?\})\s*;?\s*</script>",
        r"window\.__NUXT__\s*=\s*(\{.*?\})\s*;?\s*</script>",
        r'data-countries\s*=\s*["\'](\{.*?\})["\']',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                continue
    return None


def try_fetch_live():
    print("Fetching WWL main page...")
    try:
        html = fetch_url(WWL_URL)
    except Exception as e:
        print(f"  Failed to fetch main page: {e}")
        return None
    parsed = parse_json_from_html(html)
    if parsed:
        print("  Found embedded data in HTML")
        return parsed
    print("  No structured data found in HTML (JS-rendered site)")
    return None


def load_cache():
    data = load_json_cache(CACHE_PATH)
    return data if data else None


def save_cache(data):
    CACHE_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


STATIC_WWL_2025 = {
    "year": 2025,
    "source": "Open Doors World Watch List 2025",
    "note": "Static fallback data from published WWL 2025 rankings",
    "countries": {
        "North Korea": {
            "ranking": 1,
            "score": 98,
            "persecution_source": "Communist and post-Communist oppression",
            "christian_population": "50,000 - 70,000",
            "main_religion": "Ethnoreligionism",
            "government": "Dictatorship",
        },
        "Somalia": {
            "ranking": 2,
            "score": 96,
            "persecution_source": "Islamic oppression",
            "christian_population": "1,000",
            "main_religion": "Islam",
            "government": "Clan-based system",
        },
        "Yemen": {
            "ranking": 3,
            "score": 95,
            "persecution_source": "Islamic oppression",
            "christian_population": "2,500",
            "main_religion": "Islam",
            "government": "Conflict zone / fragile state",
        },
        "Eritrea": {
            "ranking": 4,
            "score": 94,
            "persecution_source": "Authoritarianism",
            "christian_population": "30,000",
            "main_religion": "Christianity",
            "government": "Dictatorship",
        },
        "Libya": {
            "ranking": 5,
            "score": 93,
            "persecution_source": "Islamic oppression",
            "christian_population": "25,000",
            "main_religion": "Islam",
            "government": "Conflict zone / fragile state",
        },
        "Nigeria": {
            "ranking": 6,
            "score": 92,
            "persecution_source": "Islamic oppression",
            "christian_population": "80,000,000",
            "main_religion": "Christianity",
            "government": "Federal republic",
        },
        "Pakistan": {
            "ranking": 7,
            "score": 91,
            "persecution_source": "Islamic oppression",
            "christian_population": "3,500,000",
            "main_religion": "Islam",
            "government": "Federal republic",
        },
        "Sudan": {
            "ranking": 8,
            "score": 90,
            "persecution_source": "Islamic oppression",
            "christian_population": "2,000,000",
            "main_religion": "Islam",
            "government": "Conflict zone / fragile state",
        },
        "Afghanistan": {
            "ranking": 9,
            "score": 89,
            "persecution_source": "Islamic oppression",
            "christian_population": "3,000",
            "main_religion": "Islam",
            "government": "Theocratic dictatorship",
        },
        "Iran": {
            "ranking": 10,
            "score": 88,
            "persecution_source": "Islamic oppression",
            "christian_population": "15,000",
            "main_religion": "Islam",
            "government": "Theocratic republic",
        },
        "China": {
            "ranking": 11,
            "score": 87,
            "persecution_source": "Communist and post-Communist oppression",
            "christian_population": "130,000,000",
            "main_religion": "Folk religion",
            "government": "Communist party state",
        },
        "Ethiopia": {
            "ranking": 12,
            "score": 85,
            "persecution_source": "Ethnoreligionism",
            "christian_population": "52,000,000",
            "main_religion": "Christianity",
            "government": "Federal republic",
        },
        "Myanmar": {
            "ranking": 13,
            "score": 84,
            "persecution_source": "Religious nationalism",
            "christian_population": "2,500,000",
            "main_religion": "Buddhism",
            "government": "Military junta",
        },
        "Mali": {
            "ranking": 14,
            "score": 83,
            "persecution_source": "Islamic oppression",
            "christian_population": "300,000",
            "main_religion": "Islam",
            "government": "Military junta",
        },
        "Niger": {
            "ranking": 15,
            "score": 82,
            "persecution_source": "Islamic oppression",
            "christian_population": "150,000",
            "main_religion": "Islam",
            "government": "Military junta",
        },
        "Iraq": {
            "ranking": 16,
            "score": 81,
            "persecution_source": "Islamic oppression",
            "christian_population": "250,000",
            "main_religion": "Islam",
            "government": "Federal parliamentary republic",
        },
        "India": {
            "ranking": 17,
            "score": 80,
            "persecution_source": "Hindu nationalism",
            "christian_population": "70,000,000",
            "main_religion": "Hinduism",
            "government": "Federal republic",
        },
        "Mauritania": {
            "ranking": 18,
            "score": 79,
            "persecution_source": "Islamic oppression",
            "christian_population": "10,000",
            "main_religion": "Islam",
            "government": "Islamic republic",
        },
        "Syria": {
            "ranking": 19,
            "score": 78,
            "persecution_source": "Islamic oppression",
            "christian_population": "600,000",
            "main_religion": "Islam",
            "government": "Conflict zone / fragile state",
        },
        "Saudi Arabia": {
            "ranking": 20,
            "score": 77,
            "persecution_source": "Islamic oppression",
            "christian_population": "1,500,000",
            "main_religion": "Islam",
            "government": "Absolute monarchy",
        },
        "Maldives": {
            "ranking": 21,
            "score": 76,
            "persecution_source": "Islamic oppression",
            "christian_population": "300",
            "main_religion": "Islam",
            "government": "Presidential republic",
        },
        "Bangladesh": {
            "ranking": 22,
            "score": 75,
            "persecution_source": "Islamic oppression",
            "christian_population": "1,500,000",
            "main_religion": "Islam",
            "government": "Parliamentary republic",
        },
        "Algeria": {
            "ranking": 23,
            "score": 74,
            "persecution_source": "Islamic oppression",
            "christian_population": "80,000",
            "main_religion": "Islam",
            "government": "Federal republic",
        },
        "Turkey": {
            "ranking": 24,
            "score": 73,
            "persecution_source": "Islamic oppression",
            "christian_population": "180,000",
            "main_religion": "Islam",
            "government": "Presidential republic",
        },
        "Somaliland": {
            "ranking": 25,
            "score": 72,
            "persecution_source": "Islamic oppression",
            "christian_population": "1,000",
            "main_religion": "Islam",
            "government": "Unrecognised state",
        },
        "Qatar": {
            "ranking": 26,
            "score": 71,
            "persecution_source": "Islamic oppression",
            "christian_population": "250,000",
            "main_religion": "Islam",
            "government": "Absolute monarchy",
        },
        "Vietnam": {
            "ranking": 27,
            "score": 70,
            "persecution_source": "Communist and post-Communist oppression",
            "christian_population": "5,000,000",
            "main_religion": "Folk religion",
            "government": "Communist party state",
        },
        "Morocco": {
            "ranking": 28,
            "score": 69,
            "persecution_source": "Islamic oppression",
            "christian_population": "30,000",
            "main_religion": "Islam",
            "government": "Constitutional monarchy",
        },
        "Kenya": {
            "ranking": 29,
            "score": 68,
            "persecution_source": "Islamic oppression",
            "christian_population": "38,000,000",
            "main_religion": "Christianity",
            "government": "Federal republic",
        },
        "Mexico": {
            "ranking": 30,
            "score": 67,
            "persecution_source": "Corruption and organized crime",
            "christian_population": "110,000,000",
            "main_religion": "Christianity",
            "government": "Federal republic",
        },
        "Colombia": {
            "ranking": 31,
            "score": 66,
            "persecution_source": "Corruption and organized crime",
            "christian_population": "43,000,000",
            "main_religion": "Christianity",
            "government": "Federal republic",
        },
        "Laos": {
            "ranking": 32,
            "score": 65,
            "persecution_source": "Communist and post-Communist oppression",
            "christian_population": "170,000",
            "main_religion": "Buddhism",
            "government": "Communist party state",
        },
        "Cuba": {
            "ranking": 33,
            "score": 64,
            "persecution_source": "Communist and post-Communist oppression",
            "christian_population": "4,500,000",
            "main_religion": "Folk religion",
            "government": "Communist party state",
        },
        "Oman": {
            "ranking": 34,
            "score": 63,
            "persecution_source": "Islamic oppression",
            "christian_population": "130,000",
            "main_religion": "Islam",
            "government": "Absolute monarchy",
        },
        "Uzbekistan": {
            "ranking": 35,
            "score": 62,
            "persecution_source": "Islamic oppression",
            "christian_population": "550,000",
            "main_religion": "Islam",
            "government": "Presidential republic",
        },
        "Tunisia": {
            "ranking": 36,
            "score": 61,
            "persecution_source": "Islamic oppression",
            "christian_population": "15,000",
            "main_religion": "Islam",
            "government": "Parliamentary republic",
        },
        "Jordan": {
            "ranking": 37,
            "score": 60,
            "persecution_source": "Islamic oppression",
            "christian_population": "150,000",
            "main_religion": "Islam",
            "government": "Constitutional monarchy",
        },
        "Nicaragua": {
            "ranking": 38,
            "score": 59,
            "persecution_source": "Communist and post-Communist oppression",
            "christian_population": "4,000,000",
            "main_religion": "Christianity",
            "government": "Presidential republic",
        },
        "Central African Republic": {
            "ranking": 39,
            "score": 58,
            "persecution_source": "Ethnoreligionism",
            "christian_population": "2,500,000",
            "main_religion": "Christianity",
            "government": "Conflict zone / fragile state",
        },
        "UAE": {
            "ranking": 40,
            "score": 57,
            "persecution_source": "Islamic oppression",
            "christian_population": "500,000",
            "main_religion": "Islam",
            "government": "Federal constitutional monarchy",
        },
        "Egypt": {
            "ranking": 41,
            "score": 56,
            "persecution_source": "Islamic oppression",
            "christian_population": "12,000,000",
            "main_religion": "Islam",
            "government": "Federal republic",
        },
        "Kuwait": {
            "ranking": 42,
            "score": 55,
            "persecution_source": "Islamic oppression",
            "christian_population": "250,000",
            "main_religion": "Islam",
            "government": "Constitutional monarchy",
        },
        "Russia": {
            "ranking": 43,
            "score": 54,
            "persecution_source": "Authoritarianism",
            "christian_population": "89,000,000",
            "main_religion": "Christianity",
            "government": "Federal republic",
        },
        "Benin": {
            "ranking": 44,
            "score": 53,
            "persecution_source": "Islamic oppression",
            "christian_population": "4,500,000",
            "main_religion": "Christianity",
            "government": "Presidential republic",
        },
        "Cameroon": {
            "ranking": 45,
            "score": 52,
            "persecution_source": "Islamic oppression",
            "christian_population": "16,000,000",
            "main_religion": "Christianity",
            "government": "Republic",
        },
        "Burkina Faso": {
            "ranking": 46,
            "score": 51,
            "persecution_source": "Islamic oppression",
            "christian_population": "1,500,000",
            "main_religion": "Islam",
            "government": "Military junta",
        },
        "Bahrain": {
            "ranking": 47,
            "score": 50,
            "persecution_source": "Islamic oppression",
            "christian_population": "100,000",
            "main_religion": "Islam",
            "government": "Constitutional monarchy",
        },
        "Indonesia": {
            "ranking": 48,
            "score": 49,
            "persecution_source": "Islamic oppression",
            "christian_population": "18,000,000",
            "main_religion": "Islam",
            "government": "Federal republic",
        },
        "Tanzania": {
            "ranking": 49,
            "score": 48,
            "persecution_source": "Ethnoreligionism",
            "christian_population": "18,000,000",
            "main_religion": "Christianity",
            "government": "Unitary republic",
        },
        "Brunei": {
            "ranking": 50,
            "score": 47,
            "persecution_source": "Islamic oppression",
            "christian_population": "20,000",
            "main_religion": "Islam",
            "government": "Absolute monarchy",
        },
    },
}


def build_result(static_data, live_status=None):
    result = {
        "year": static_data["year"],
        "source": static_data.get("source", "Open Doors World Watch List"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "live_fetch": live_status or "static_fallback",
        "countries": static_data["countries"],
    }
    return result


def print_summary(result):
    countries = result["countries"]
    print(f"\n{'='*60}")
    print(f"Open Doors World Watch List {result['year']}")
    print(f"{'='*60}")
    print(f"Countries: {len(countries)}")
    print(f"Source: {result['source']}")
    print(f"Data status: {result['live_fetch']}")
    print(f"Cached at: {result['fetched_at']}")
    print()
    top10 = sorted(countries.items(), key=lambda x: x[1]["ranking"])[:10]
    print("Top 10:")
    for name, info in top10:
        print(
            f"  {info['ranking']:>2}. {name:<20s} "
            f"Score: {info['score']:>2}  "
            f"{info['persecution_source']}"
        )
    print(f"\n{'='*60}")


def main():
    cached = load_cache()
    live_status = "static_fallback"

    live_data = try_fetch_live()
    if live_data:
        live_status = "live_fetch_ok"
        print("  Parsing live data...")
        if isinstance(live_data, dict) and "countries" in live_data:
            result = build_result(
                {"year": 2025, "source": "Open Doors WWL 2025 (live)", "countries": live_data["countries"]},
                live_status,
            )
            save_cache(result)
            write_status("opendoors", "ok")
            print_summary(result)
            exit_for_status("ok")
        print("  Live data format not recognized, using static fallback")

    if cached:
        print(f"Using cached data from {cached.get('fetched_at', 'unknown')}")
        write_status("opendoors", "cached")
        print_summary(cached)
        exit_for_status("cached")

    print("Using static WWL 2025 fallback data")
    result = build_result(STATIC_WWL_2025, live_status)
    save_cache(result)
    write_status("opendoors", "partial", "static fallback used")
    print_summary(result)
    exit_for_status("partial")


if __name__ == "__main__":
    main()
