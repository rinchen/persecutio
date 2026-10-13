#!/usr/bin/env python3
"""Fetch UN human rights recommendations for religion from OHCHR's UHRI.

The old UHRI JSON API (``uhri.ohchr.org/api/v1/measure-recommendations``) is
gone: the host now serves a Next.js single-page app whose only data surface is
an unauthenticated proxy under ``/api/uhri/``. This fetcher:

1. Reads the country (UUID) directory that the UHRI app ships in its own
   JavaScript bundle (``/_next/static/chunks/8165-*.js``).
2. Counts all recommendations per country via ``POST api/search``.
3. Collects freedom-of-religion recommendation texts from the Special
   Rapporteur on FoRB mechanism via ``POST api/search/mechanism_result``.

Everything is best-effort: if the app or API changes shape the fetcher falls
back to the previous cached index instead of failing the run.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from country_registry import COUNTRY_GEO, resolve_country_name
from fetch_common import (
    FETCHED,
    USER_AGENT,
    ensure_fetched_dir,
    exit_for_status,
    write_status,
)

ensure_fetched_dir()
OHCHR_DIR = FETCHED / "ohchr"
OHCHR_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = OHCHR_DIR / "index.json"

UHRI_BASE = "https://uhri.ohchr.org/api/uhri/"
APP_URL = "https://uhri.ohchr.org/en/search-human-rights-recommendations"
SOURCE_URL = "https://uhri.ohchr.org/"
REQUEST_DELAY = 0.15

# Project country title -> the name OHCHR uses, for names it renders differently.
NAME_ALIASES = {
    "Brunei": "Brunei Darussalam",
    "Democratic Republic of Congo": "Democratic Republic of the Congo",
    "Iran": "Iran (Islamic Republic of)",
    "Laos": "Lao People's Democratic Republic",
    "North Korea": "Democratic People's Republic of Korea",
    "South Korea": "Republic of Korea",
    "Russia": "Russian Federation",
    "Syria": "Syrian Arab Republic",
    "Tanzania": "United Republic of Tanzania",
    "Turkey": "Türkiye",
    "United States": "United States of America",
    "Venezuela": "Venezuela (Bolivarian Republic of)",
    "Vietnam": "Viet Nam",
}

# Same keyword set the previous fetcher used to flag religion-related text.
RELIGION_KEYWORDS = (
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
)

_COUNTRY_OBJ_RE = re.compile(
    r'\{id:"([0-9a-f-]{36})",text:"([^"]+)",selectable:!?[01],'
    r'heading:!?[01],parentId:null,secondText:"([^"]*)"\}'
)

_SEARCH_BODY = {
    "affectedPersons": [],
    "countries": [],
    "documentCodes": [],
    "documentTypes": [],
    "fromDate": None,
    "mechanisms": [],
    "regions": [],
    "sdgs": [],
    "searchText": "",
    "themes": [],
    "toDate": None,
    "uprCycles": [],
    "uprPositions": [],
    "uprRegions": [],
    "uprSessions": [],
    "uprStates": [],
}


def _get(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _js_unescape(value: str) -> str:
    """Decode the \\xNN / \\uNNNN escapes webpack uses inside string literals."""
    value = re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), value)
    value = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), value)
    return value


def _post(path: str, body: dict, timeout: int = 60) -> dict:
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        UHRI_BASE + path,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def fetch_country_directory() -> tuple[dict[str, str], dict[str, str]]:
    """Return (name -> uuid, uuid -> name) parsed from the UHRI app bundle."""
    page = _get(APP_URL)
    chunks = sorted(set(re.findall(r'/_next/static/chunks/[A-Za-z0-9%_/.-]+\.js', page)))
    if not chunks:
        raise RuntimeError("no JS chunks found on UHRI app page")
    # The country list lives in chunk 8165; try it first, then scan the rest.
    ordered = [c for c in chunks if "/8165-" in c] + [c for c in chunks if "/8165-" not in c]
    for chunk in ordered:
        try:
            js = _get("https://uhri.ohchr.org" + chunk)
        except (urllib.error.URLError, OSError):
            continue
        rows = _COUNTRY_OBJ_RE.findall(js)
        if len(rows) >= 150:
            name_to_uuid = {_js_unescape(name): uuid for uuid, name, _iso in rows}
            uuid_to_name = {uuid: _js_unescape(name) for uuid, name, _iso in rows}
            return name_to_uuid, uuid_to_name
    raise RuntimeError("UHRI country directory not found in app bundle")


def _uuid_for(title: str, name_to_uuid: dict[str, str]) -> str | None:
    for candidate in (title, NAME_ALIASES.get(title), resolve_country_name(title)):
        if candidate and candidate in name_to_uuid:
            return name_to_uuid[candidate]
    return None


def fetch_recommendation_counts(name_to_uuid: dict[str, str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for title in COUNTRY_GEO:
        uuid = _uuid_for(title, name_to_uuid)
        if not uuid:
            continue
        body = dict(_SEARCH_BODY)
        body["countries"] = [uuid]
        try:
            payload = _post("api/search?culture=en", body)
        except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
            print(f"  warning: OHCHR search failed for {title}: {type(e).__name__}")
            continue
        count = ((payload.get("countResult") or {}).get("countRecommendations")) or 0
        counts[title] = int(count)
        time.sleep(REQUEST_DELAY)
    return counts


def _is_religion_related(text: str) -> bool:
    low = (text or "").lower()
    return any(kw in low for kw in RELIGION_KEYWORDS)


def fetch_religion_samples(uuid_to_name: dict[str, str]) -> dict[str, list[str]]:
    """Religion-related recommendation texts grouped by project country.

    ``search/mechanism_result`` is capped at 40 records and requires a
    mechanism id, so sweep every mechanism and keep keyword-matching texts.
    """
    try:
        listing = _post("api/search?culture=en", dict(_SEARCH_BODY))
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        print(f"  warning: OHCHR mechanism list failed: {type(e).__name__}")
        return {}

    mechanisms = [
        m.get("body") for m in (listing.get("mechanismsList") or []) if m.get("body")
    ]
    samples: dict[str, list[str]] = {}
    for mechanism_id in mechanisms:
        body = dict(_SEARCH_BODY)
        body["mechanismId"] = mechanism_id
        try:
            payload = _post("api/search/mechanism_result?culture=en", body)
        except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
            print(f"  warning: OHCHR mechanism query failed: {type(e).__name__}")
            time.sleep(REQUEST_DELAY)
            continue
        for rec in payload.get("listOfRecommendations") or []:
            text = (rec.get("text") or "").strip()
            if not text or not _is_religion_related(text):
                continue
            for cid in rec.get("countryIds") or []:
                title = resolve_country_name(uuid_to_name.get(cid, ""))
                if not title:
                    continue
                bucket = samples.setdefault(title, [])
                if len(bucket) < 5:
                    bucket.append(text)
        time.sleep(REQUEST_DELAY)
    return samples


def build_empty_output(status: str = "unavailable") -> dict:
    return {
        "countries": {},
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE_URL,
        "status": status,
    }


def _use_cache(reason: str) -> None:
    if INDEX_PATH.exists():
        try:
            cached = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            cached["fetched_at"] = datetime.now(timezone.utc).isoformat()
            cached["status"] = "cached_fallback"
            INDEX_PATH.write_text(
                json.dumps(cached, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            write_status("ohchr", "cached", reason)
            print(f"ohchr used cache: {INDEX_PATH}")
            exit_for_status("cached")
            return
        except Exception as e:  # noqa: BLE001 - corrupt cache should not abort
            print(f"  warning: corrupt ohchr cache ({type(e).__name__}: {e})")
    INDEX_PATH.write_text(
        json.dumps(build_empty_output(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_status("ohchr", "failed", reason)
    print(f"ohchr wrote empty index: {INDEX_PATH}")
    exit_for_status("failed")


def main():
    print("Fetching OHCHR Universal Human Rights Index...")
    try:
        name_to_uuid, uuid_to_name = fetch_country_directory()
    except (urllib.error.URLError, RuntimeError, OSError) as e:
        print(f"  OHCHR directory unavailable: {type(e).__name__}: {e}")
        _use_cache(f"UHRI directory unavailable: {type(e).__name__}")
        return

    counts = fetch_recommendation_counts(name_to_uuid)
    if not counts:
        _use_cache("UHRI returned no country counts")
        return

    samples = fetch_religion_samples(uuid_to_name)

    countries: dict[str, dict] = {}
    for title, count in counts.items():
        countries[title] = {
            "recommendation_count": count,
            "religion_recommendations": samples.get(title, []),
            "latest_date": None,
        }

    output = {
        "countries": countries,
        "total_recommendations": sum(counts.values()),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE_URL,
        "status": "ok",
    }
    INDEX_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_status("ohchr", "ok")
    print(f"ohchr wrote {len(countries)} countries to {INDEX_PATH}")
    exit_for_status("ok")


if __name__ == "__main__":
    main()
