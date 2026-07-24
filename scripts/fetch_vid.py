#!/usr/bin/env python3
"""Fetch violent incident counts from the Violent Incidents Database (VID).

The VID is maintained by the International Institute for Religious Freedom (IIRF)
and Global Christian Relief. It tracks 600,000+ incidents of religious freedom
violations worldwide since 2022. The public version provides incident counts
by country. We filter to Christian-specific incidents only.
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
    write_empty_result,
    write_status,
)

ensure_fetched_dir()

VID_URL = "https://iirf.global/vid/"
OUTPUT = FETCHED / "vid.json"


def try_api_endpoints():
    """Try various API endpoints the VID might expose."""
    api_urls = [
        "https://iirf.global/vid/",
        "https://violentincidents.com/",
    ]
    for url in api_urls:
        text, err = fetch_text(url, timeout=15, user_agent=USER_AGENT)
        if err or not text:
            continue
        if text.strip().startswith(("{", "[")):
            try:
                return json.loads(text), url
            except json.JSONDecodeError:
                continue
    return None, None


def parse_country_counts(html):
    """Try to extract country-level incident counts from VID HTML."""
    countries = {}
    country_pattern = re.compile(
        r'(?:(?:country|location|nation)[^>]*>)\s*([A-Z][a-zA-Z\s]+?)(?:</(?:td|span|div|a)>)\s*'
        r'(?:.*?(?:count|incidents?|events?|total)[^>]*>)\s*(\d[\d,]*)',
        re.IGNORECASE | re.DOTALL
    )
    for match in country_pattern.finditer(html):
        name = match.group(1).strip()
        count = int(match.group(2).replace(",", ""))
        if name in KNOWN_COUNTRIES or any(name.lower() == c.lower() for c in KNOWN_COUNTRIES):
            canonical = next((c for c in KNOWN_COUNTRIES if c.lower() == name.lower()), name)
            countries[canonical] = {"total_incidents": count}

    table_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
    cell_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
    for table_match in table_pattern.finditer(html):
        row = table_match.group(1)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cell_pattern.findall(row)]
        if len(cells) >= 2:
            name = cells[0]
            for cell in cells[1:]:
                clean = cell.replace(",", "").strip()
                if clean.isdigit():
                    canonical = next((c for c in KNOWN_COUNTRIES if c.lower() == name.lower()), None)
                    if canonical:
                        countries[canonical] = {"total_incidents": int(clean)}
                    break

    return countries


def process_api_data(data):
    """Process VID API response into our standard format."""
    countries = {}
    incidents = data if isinstance(data, list) else data.get("incidents", data.get("results", []))
    if isinstance(incidents, dict):
        incidents = list(incidents.values()) if incidents else []

    for inc in incidents:
        if not isinstance(inc, dict):
            continue
        religion = str(inc.get("religion", "")).lower()
        if "christian" not in religion and religion not in ("", "all"):
            continue
        country = inc.get("country", inc.get("location", ""))
        if not country:
            continue
        entry = countries.setdefault(country, {
            "total_incidents": 0,
            "killings": 0,
            "abductions": 0,
            "arrests": 0,
            "church_attacks": 0,
            "forced_marriages": 0,
        })
        entry["total_incidents"] += 1
        inc_type = str(inc.get("type", inc.get("incident_type", ""))).lower()
        if "kill" in inc_type or "murder" in inc_type or "martyr" in inc_type:
            entry["killings"] += 1
        elif "abduct" in inc_type or "kidnap" in inc_type:
            entry["abductions"] += 1
        elif "arrest" in inc_type or "detain" in inc_type or "imprison" in inc_type:
            entry["arrests"] += 1
        elif "church" in inc_type or "attack" in inc_type:
            entry["church_attacks"] += 1
        elif "marriage" in inc_type or "forced" in inc_type:
            entry["forced_marriages"] += 1

    total = sum(e["total_incidents"] for e in countries.values())
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Violent Incidents Database (IIRF/GCR)",
        "source_url": VID_URL,
        "status": "ok",
        "countries": countries,
        "total_incidents": total,
        "total_countries": len(countries),
    }


def _write_empty(status):
    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Violent Incidents Database (IIRF/GCR)",
        "source_url": VID_URL,
        "status": status,
        "countries": {},
        "total_incidents": 0,
        "total_countries": 0,
    }
    write_empty_result(OUTPUT, result)


def main():
    print("Fetching Violent Incidents Database (VID)...")
    cached = load_json_cache(OUTPUT)

    api_data, api_url = try_api_endpoints()
    if api_data:
        print(f"  got API response from {api_url}")
        result = process_api_data(api_data)
        OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  wrote {OUTPUT}")
        write_status("vid", "ok")
        exit_for_status("ok")

    html, err = fetch_text(VID_URL, user_agent=USER_AGENT)
    if html is None:
        if cached:
            print("  fetch failed, using cached data")
            cached["status"] = "cached"
            cached["fetched_at"] = datetime.now(timezone.utc).isoformat()
            OUTPUT.write_text(json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8")
            write_status("vid", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        print("  VID site unreachable and no cache, writing stub")
        _write_empty("unavailable")
        write_status("vid", "failed", "unavailable, no cache")
        exit_for_status("failed")

    countries = parse_country_counts(html)

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Violent Incidents Database (IIRF/GCR)",
        "source_url": VID_URL,
        "status": "partial" if countries else "parse_limited",
        "note": "Public VID shows aggregate counts only. Detailed records require subscription.",
        "countries": countries,
        "total_countries": len(countries),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  parsed {len(countries)} countries from VID page")
    print(f"  wrote {OUTPUT}")
    # Page fetched successfully even if parse is limited
    final_status = "ok" if countries else "partial"
    write_status("vid", final_status, result["status"])
    exit_for_status(final_status)


if __name__ == "__main__":
    main()
