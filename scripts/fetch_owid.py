import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FETCHED = ROOT / "data" / "fetched"
FETCHED.mkdir(parents=True, exist_ok=True)

CSV_SHARE = (
    "https://ourworldindata.org/grapher/religious-composition.csv"
    "?v=1&csvType=full&useColumnShortNames=false"
    "&indicator=share&religion=christians"
)
CSV_COUNT = (
    "https://ourworldindata.org/grapher/religious-composition.csv"
    "?v=1&csvType=full&useColumnShortNames=false"
    "&indicator=count_unrounded&religion=christians"
)
META_URL = (
    "https://ourworldindata.org/grapher/religious-composition.metadata.json"
)

CACHE_CSV = FETCHED / "owid_religion.csv"
CACHE_JSON = FETCHED / "owid_religion.json"
STATUS_PATH = FETCHED / "owid_status.json"

SKIP_COUNTRIES = {
    "OWID_WRL", "OWID_AFR", "OWID_ASI", "OWID_EUR",
    "OWID_NAM", "OWID_SAM", "OWID_OCE", "OWID_KOS",
    "PEW_APA", "PEW_EUR", "PEW_LAC", "PEW_MENA",
    "PEW_NAM", "PEW_SSA",
}


def write_status(status, message=None):
    STATUS_PATH.write_text(
        json.dumps({
            "name": "owid",
            "status": status,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "message": message,
        }, indent=2),
        encoding="utf-8",
    )


def fetch_url(url, label):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="ignore"), None
    except Exception as e:
        return None, str(e)


def parse_csv(text):
    rows = {}
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        code = row.get("Code", "").strip()
        if not code or code in SKIP_COUNTRIES:
            continue
        entity = row.get("Entity", "").strip()
        year = int(row.get("Year", 0))
        val = row.get("Share of the population who are Christians") or row.get(
            "Number of people who are Christians"
        )
        if val:
            val = float(val)
        else:
            val = None
        key = (code, year)
        if key not in rows:
            rows[key] = {"entity": entity, "code": code, "year": year}
        col_name = reader.fieldnames[-1] if reader.fieldnames else ""
        if "Share" in col_name:
            rows[key]["share"] = val
        elif "Number" in col_name:
            rows[key]["count"] = val
    return rows


def merge_rows(share_rows, count_rows):
    merged = {}
    all_keys = set(share_rows.keys()) | set(count_rows.keys())
    for key in all_keys:
        s = share_rows.get(key, {})
        c = count_rows.get(key, {})
        entity = s.get("entity") or c.get("entity") or ""
        code = s.get("code") or c.get("code") or ""
        year = s.get("year") or c.get("year") or 0
        if code in SKIP_COUNTRIES:
            continue
        merged[key] = {
            "entity": entity,
            "code": code,
            "year": year,
            "share": s.get("share"),
            "count": c.get("count"),
        }
    return merged


def build_country_map(merged):
    countries = {}
    for (code, year), row in merged.items():
        name = row["entity"]
        if name not in countries or year > countries[name]["year"]:
            pop = row.get("count")
            if pop is not None:
                pop = int(round(pop))
            countries[name] = {
                "christian_population": pop,
                "christian_percentage": round(row["share"], 2)
                if row.get("share") is not None
                else None,
                "year": year,
            }
    return countries


def main():
    print("fetching OWID religious composition metadata...")
    meta_text, meta_err = fetch_url(META_URL, "metadata")
    if meta_err:
        print(f"  metadata fetch failed: {meta_err}")
    else:
        try:
            meta = json.loads(meta_text)
            citation = meta.get("chart", {}).get("citation", "unknown")
            print(f"  citation: {citation}")
        except Exception:
            print("  metadata parsed (non-critical)")

    print("fetching Christian share CSV...")
    share_text, share_err = fetch_url(CSV_SHARE, "share")
    if share_err:
        print(f"  share CSV failed: {share_err}")

    print("fetching Christian count CSV...")
    count_text, count_err = fetch_url(CSV_COUNT, "count")
    if count_err:
        print(f"  count CSV failed: {count_err}")

    if share_text and count_text:
        share_rows = parse_csv(share_text)
        count_rows = parse_csv(count_text)
        merged = merge_rows(share_rows, count_rows)
        countries = build_country_map(merged)

        lines = []
        lines.append("Entity,Code,Year,Christian_Share_Pct,Christian_Count")
        for (code, year) in sorted(merged.keys()):
            row = merged[(code, year)]
            share_val = f"{row['share']:.2f}" if row.get("share") is not None else ""
            count_val = str(int(row["count"])) if row.get("count") is not None else ""
            lines.append(
                f"{row['entity']},{code},{year},{share_val},{count_val}"
            )
        CACHE_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")

        output = {"countries": countries}
        CACHE_JSON.write_text(
            json.dumps(output, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        n = len(countries)
        print(f"  {n} countries written to {CACHE_CSV.name}")
        print(f"  JSON written to {CACHE_JSON.name}")
    else:
        print("fetch failed, trying cache fallback...")
        if CACHE_CSV.exists():
            print(f"  using cached CSV: {CACHE_CSV}")
            raw = CACHE_CSV.read_text(encoding="utf-8")
            reader = csv.DictReader(io.StringIO(raw))
            countries = {}
            for row in reader:
                code = row.get("Code", "").strip()
                if not code:
                    continue
                year = int(row.get("Year", 0))
                share = row.get("Christian_Share_Pct")
                count = row.get("Christian_Count")
                if code not in countries or year > countries[code]["year"]:
                    countries[code] = {
                        "country_name": row.get("Entity", ""),
                        "christian_population": int(count)
                        if count
                        else None,
                        "christian_percentage": float(share)
                        if share
                        else None,
                        "year": year,
                    }
            output = {"countries": countries}
            CACHE_JSON.write_text(
                json.dumps(output, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"  {len(countries)} countries restored from cache")
        else:
            print("  no cache available, exiting")
            write_status("failed", "no data available")
            return

    status = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "share_status": "ok" if not share_err else f"failed: {share_err}",
        "count_status": "ok" if not count_err else f"failed: {count_err}",
        "countries": len(countries),
    }
    print(json.dumps(status, indent=2))

    used_cache = bool((share_err or count_err) and countries)
    if share_err and count_err and not countries:
        write_status("failed", "both share and count CSVs failed")
    elif share_err and count_err and used_cache:
        write_status("cached", "both CSVs failed, restored from cache")
    elif share_err or count_err:
        write_status("partial", f"share={'ok' if not share_err else 'failed'}, count={'ok' if not count_err else 'failed'}")
    else:
        write_status("ok")
    print("done")


if __name__ == "__main__":
    main()
