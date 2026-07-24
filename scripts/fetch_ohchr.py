import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import (
    FETCHED,
    USER_AGENT,
    ensure_fetched_dir,
    exit_for_status,
    fetch_json,
    write_status,
)

ensure_fetched_dir()
OHCHR_DIR = FETCHED / "ohchr"
OHCHR_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "https://uhri.ohchr.org/api/v1"
RECOMMENDATIONS_URL = f"{API_BASE}/measure-recommendations"

RELIGION_KEYWORDS = [
    "religion",
    "religious",
    "belief",
    "faith",
    "worship",
    "church",
    "mosque",
    "synagogue",
    "temple",
    "clergy",
    "pastor",
    "imam",
    "priest",
    "sectarian",
    "blasphemy",
    "apostasy",
    "proselyt",
    "conversion",
]


def is_religion_related(text):
    if not text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in RELIGION_KEYWORDS)


def extract_country_data(recommendations):
    countries = {}
    for rec in recommendations:
        country_name = rec.get("country") or rec.get("countryName") or rec.get("state") or ""
        if not country_name:
            iso = rec.get("iso3") or rec.get("iso") or ""
            country_name = iso
        if not country_name:
            continue
        if country_name not in countries:
            countries[country_name] = {
                "recommendation_count": 0,
                "religion_recommendations": [],
                "latest_date": None,
            }
        entry = countries[country_name]
        entry["recommendation_count"] += 1
        title = rec.get("title") or rec.get("text") or rec.get("recommendation") or ""
        if is_religion_related(title):
            entry["religion_recommendations"].append(title)
        date_str = rec.get("date") or rec.get("sessionDate") or rec.get("session") or ""
        if date_str:
            if entry["latest_date"] is None or date_str > entry["latest_date"]:
                entry["latest_date"] = date_str
    return countries


def build_empty_output():
    return {
        "countries": {},
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": RECOMMENDATIONS_URL,
        "status": "unavailable",
    }


def main():
    raw_path = OHCHR_DIR / "raw_recommendations.json"
    index_path = OHCHR_DIR / "index.json"

    data, status = fetch_json(RECOMMENDATIONS_URL, raw_path, "ohchr_recommendations")

    if not data:
        print("ohchr api unavailable, falling back to cache")
        if index_path.exists():
            try:
                cached = json.loads(index_path.read_text(encoding="utf-8"))
                cached["fetched_at"] = datetime.now(timezone.utc).isoformat()
                cached["status"] = "cached_fallback"
                index_path.write_text(
                    json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                write_status("ohchr", "cached")
                print(f"ohchr used cache: {index_path}")
                exit_for_status("cached")
            except Exception:
                pass
        output = build_empty_output()
        index_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        write_status("ohchr", "failed", "api unavailable, no cache")
        print(f"ohchr wrote empty index: {index_path}")
        exit_for_status("failed")

    recommendations = data
    if isinstance(data, dict):
        for key in ["results", "data", "recommendations", "items"]:
            if key in data and isinstance(data[key], list):
                recommendations = data[key]
                break

    countries = extract_country_data(recommendations)

    output = {
        "countries": countries,
        "total_recommendations": len(recommendations),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": RECOMMENDATIONS_URL,
        "status": status["status"],
        "fetch_status": status,
    }
    index_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    final_status = status["status"]
    write_status("ohchr", final_status)
    print(f"ohchr wrote {len(countries)} countries to {index_path}")
    exit_for_status(final_status)


if __name__ == "__main__":
    main()
