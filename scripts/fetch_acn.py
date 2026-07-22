#!/usr/bin/env python3
"""Fetch religious freedom data from Aid to the Church in Need (ACN).

ACN publishes a biennial Religious Freedom Report covering 196 countries.
The report classifies countries as "persecution" or "discrimination" and
provides detailed analysis of Christian persecution worldwide.
Source: https://acninternational.org/religiousfreedomreport/
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

ACN_URL = "https://acninternational.org/religiousfreedomreport/"
ACN_FACT_SHEET = "https://www.churchinneed.org/wp-content/uploads/2025/10/RELIGIOUS-FREEDOM-REPORT-FACT-SHEET.pdf"
OUTPUT = FETCHED / "acn_report.json"

PERSECUTION_KEYWORDS = [
    "persecution", "persecuted", "violence", "violence against",
    "killed", "murdered", "martyred", "martyrdom", "attack",
    "church burned", "church destroyed", "church closed",
    "imprisoned", "detained", "arrested", "forced conversion",
    "blasphemy", "anti-conversion", "discrimination",
    "harassment", "intimidation", "threat", "kidnapping",
    "abduction", "sexual violence", "forced marriage",
]


def parse_acn_report(html):
    """Parse the ACN Religious Freedom Report page."""
    countries = {}

    text = strip_html(html)

    report_year = None
    year_match = re.search(r'Religious\s+Freedom\s+(?:in\s+the\s+World\s+)?Report\s+(\d{4})', text, re.IGNORECASE)
    if year_match:
        report_year = int(year_match.group(1))

    period_match = re.search(r'(?:covers?|period)\s+(?:from\s+)?(\w+\s+\d{4})\s+(?:to|until)\s+(\w+\s+\d{4})', text, re.IGNORECASE)
    period = None
    if period_match:
        period = f"{period_match.group(1)} to {period_match.group(2)}"

    total_persecution = None
    total_discrimination = None
    p_match = re.search(r'(\d+)\s+countries?\s+(?:classified|marked|designated)\s+(?:as\s+)?"?persecution"?', text, re.IGNORECASE)
    if p_match:
        total_persecution = int(p_match.group(1))
    d_match = re.search(r'(\d+)\s+countries?\s+(?:classified|marked|designated)\s+(?:as\s+)?"?discrimination"?', text, re.IGNORECASE)
    if d_match:
        total_discrimination = int(d_match.group(1))

    if not total_persecution:
        p_match2 = re.search(r'(\d+)\s+(?:of\s+persecution|persecution\s+countries)', text, re.IGNORECASE)
        if p_match2:
            total_persecution = int(p_match2.group(1))
    if not total_discrimination:
        d_match2 = re.search(r'(\d+)\s+(?:of\s+discrimination|discrimination\s+countries)', text, re.IGNORECASE)
        if d_match2:
            total_discrimination = int(d_match2.group(1))

    for country in KNOWN_COUNTRIES:
        escaped = re.escape(country)
        country_pattern = rf'(?:\b{escaped}\b)'
        matches = list(re.finditer(country_pattern, text, re.IGNORECASE))
        if not matches:
            continue

        for m in matches:
            start = max(0, m.start() - 200)
            end = min(len(text), m.end() + 500)
            context = text[start:end]

            has_persecution = any(kw in context.lower() for kw in PERSECUTION_KEYWORDS)
            has_discrimination = "discriminat" in context.lower()

            if has_persecution or has_discrimination:
                classification = "persecution" if has_persecution else "discrimination"
                entry = countries.setdefault(country, {
                    "classification": classification,
                    "mentions": 0,
                    "key_findings": [],
                })
                entry["mentions"] += 1
                if entry["classification"] != "persecution" and has_persecution:
                    entry["classification"] = "persecution"

                snippet = context[:300].strip()
                if snippet and len(snippet) > 50 and len(entry["key_findings"]) < 3:
                    entry["key_findings"].append(snippet)
                break

    return {
        "report_year": report_year,
        "period": period,
        "total_persecution_countries": total_persecution,
        "total_discrimination_countries": total_discrimination,
        "countries": countries,
    }


def _write_empty(status):
    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Aid to the Church in Need - Religious Freedom Report",
        "source_url": ACN_URL,
        "status": status,
        "report_year": None,
        "period": None,
        "total_persecution_countries": None,
        "total_discrimination_countries": None,
        "countries": {},
        "total_countries_with_data": 0,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote empty output to {OUTPUT}")


def main():
    print("Fetching Aid to the Church in Need report...")
    cached = load_json_cache(OUTPUT)

    html, err = fetch_text(ACN_URL, user_agent=USER_AGENT)
    if html is None:
        if cached:
            print("  fetch failed, using cached data")
            cached["status"] = "cached"
            cached["fetched_at"] = datetime.now(timezone.utc).isoformat()
            OUTPUT.write_text(json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8")
            write_status("acn", "cached", "fetch failed, using cache")
            exit_for_status("cached")
        print("  ACN site unreachable and no cache, writing stub")
        _write_empty("fetch_failed")
        write_status("acn", "failed", "fetch failed, no cache")
        exit_for_status("failed")

    report = parse_acn_report(html)

    countries = report["countries"]
    if not countries:
        if cached:
            print("  parse yielded no countries; keeping cached data")
            cached["status"] = "partial"
            cached["fetched_at"] = datetime.now(timezone.utc).isoformat()
            OUTPUT.write_text(json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8")
            write_status("acn", "partial", "parse yielded no countries")
            exit_for_status("partial")
        _write_empty("parse_empty")
        write_status("acn", "failed", "parse yielded no countries")
        exit_for_status("failed")

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Aid to the Church in Need - Religious Freedom Report",
        "source_url": ACN_URL,
        "status": "ok",
        "report_year": report["report_year"],
        "period": report["period"],
        "total_persecution_countries": report["total_persecution_countries"],
        "total_discrimination_countries": report["total_discrimination_countries"],
        "countries": countries,
        "total_countries_with_data": len(countries),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  report year: {report['report_year']}")
    print(f"  persecution countries: {report['total_persecution_countries']}")
    print(f"  discrimination countries: {report['total_discrimination_countries']}")
    print(f"  countries with data: {len(countries)}")
    for c in sorted(countries.keys()):
        entry = countries[c]
        print(f"    {c}: {entry['classification']} ({entry['mentions']} mentions)")
    print(f"  wrote {OUTPUT}")
    write_status("acn", "ok")
    exit_for_status("ok")

if __name__ == "__main__":
    main()
