#!/usr/bin/env python3
"""Fetch religious freedom data from Aid to the Church in Need (ACN).

ACN's biennial Religious Freedom Report covers ~196 countries and classifies
each as "persecution" or "discrimination". The public report page is now a
stub that iframes a Nuxt app backed by a Strapi GraphQL API, so the old HTML
scrape matched nothing. Read the country classifications straight from the
API: every CountryMetric carries a Year, a Status (Persecution /
Discrimination / Under_observation / Unclassified) and its Country.

Source: https://acninternational.org/religiousfreedomreport/
API:    https://strapi-rfr-prod.acninternational.org/graphql
"""
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from country_registry import resolve_country_name
from fetch_common import (
    FETCHED,
    USER_AGENT,
    ensure_fetched_dir,
    exit_for_status,
    load_json_cache,
    write_empty_result,
    write_status,
)

ensure_fetched_dir()

GRAPHQL_URL = "https://strapi-rfr-prod.acninternational.org/graphql"
ACN_URL = "https://acninternational.org/religiousfreedomreport/"
OUTPUT = FETCHED / "acn_report.json"

# Strapi enum Status -> the lowercase classification the rest of the pipeline
# expects. "Under_observation" and "Unclassified" are kept verbatim (lowered).
STATUS_MAP = {
    "persecution": "persecution",
    "discrimination": "discrimination",
    "under_observation": "under_observation",
    "unclassified": "unclassified",
}

_QUERY = (
    '{ countryMetrics(pagination:{page:%d,pageSize:250}, sort:"Year:desc")'
    " { Year Status Country { Name Code } } }"
)

# ACN country names that resolve_country_name does not map on its own.
NAME_ALIASES = {
    "Guinea Conakry": "Guinea",
    "Myanmar (Burma)": "Myanmar",
    "United States of America": "United States",
}


def _resolve_name(name: str) -> str | None:
    return resolve_country_name(name) or NAME_ALIASES.get(name)


def _graphql(query: str) -> dict:
    body = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def fetch_metrics() -> list[dict]:
    """Page through CountryMetrics, newest year first, until the latest year ends."""
    rows: list[dict] = []
    latest_year: int | None = None
    for page in range(1, 6):
        payload = _graphql(_QUERY % page)
        if payload.get("errors"):
            raise RuntimeError(f"GraphQL errors: {payload['errors']}")
        page_rows = ((payload.get("data") or {}).get("countryMetrics")) or []
        if not page_rows:
            break
        if latest_year is None:
            latest_year = max(int(r.get("Year") or 0) for r in page_rows)
            rows = [r for r in page_rows if int(r.get("Year") or 0) == latest_year]
            if len(rows) == len(page_rows) and len(page_rows) == 250:
                continue  # latest year may continue on the next page
            break
    return rows


def build_report(rows: list[dict]) -> dict:
    countries: dict[str, dict] = {}
    total_persecution = 0
    total_discrimination = 0
    report_year: int | None = None

    for row in rows:
        year = int(row.get("Year") or 0)
        if report_year is None:
            report_year = year
        status = (row.get("Status") or "").strip()
        if status.lower() == "persecution":
            total_persecution += 1
        elif status.lower() == "discrimination":
            total_discrimination += 1
        name = ((row.get("Country") or {}).get("Name") or "").strip()
        title = _resolve_name(name)
        if not title:
            continue
        countries[title] = {
            "classification": STATUS_MAP.get(status.lower(), status.lower()),
            "mentions": 1,
            "key_findings": [],
        }

    return {
        "report_year": report_year,
        "period": None,
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
    write_empty_result(OUTPUT, result)


def main():
    print("Fetching Aid to the Church in Need report...")
    cached = load_json_cache(OUTPUT)

    try:
        rows = fetch_metrics()
    except (urllib.error.URLError, RuntimeError, ValueError, OSError) as e:
        print(f"  fetch error: {type(e).__name__}: {e}")
        rows = []

    report = build_report(rows)
    countries = report["countries"]
    if not countries:
        if cached:
            print("  parse yielded no countries; keeping cached data")
            cached["status"] = "partial"
            cached["fetched_at"] = datetime.now(timezone.utc).isoformat()
            OUTPUT.write_text(json.dumps(cached, indent=2, ensure_ascii=False), encoding="utf-8")
            write_status("acn", "partial", "fetch/parse yielded no countries")
            exit_for_status("partial")
        _write_empty("fetch_failed")
        write_status("acn", "failed", "fetch/parse yielded no countries")
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
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  report year: {report['report_year']}")
    print(f"  persecution countries: {report['total_persecution_countries']}")
    print(f"  discrimination countries: {report['total_discrimination_countries']}")
    print(f"  countries with data: {len(countries)}")
    for c in sorted(countries.keys()):
        entry = countries[c]
        print(f"    {c}: {entry['classification']}")
    print(f"  wrote {OUTPUT}")
    write_status("acn", "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
