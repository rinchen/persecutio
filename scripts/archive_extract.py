#!/usr/bin/env python3
"""Extract structured enrichment from data/archives/ into extracted/countries.json."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from country_registry import COUNTRY_GEO, KNOWN_COUNTRIES, slugify  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = ROOT / "data" / "archives"
STATE_DIR = ARCHIVES / "state_dept"
USCIRF_DIR = ARCHIVES / "uscirf"
OD_DIR = ARCHIVES / "opendoors"
VDEM_DIR = ARCHIVES / "vdem"
OUT_DIR = ARCHIVES / "extracted"
OUT_PATH = OUT_DIR / "countries.json"

THIN_MODERN_CHARS = 280


def site_countries() -> list[dict]:
    yml = ROOT / "data" / "countries.yml"
    if yml.exists():
        try:
            import yaml

            data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
            countries = data.get("countries") or []
            out = []
            for c in countries:
                title = c.get("title")
                slug = c.get("slug") or slugify(title or "")
                if title and slug:
                    out.append(
                        {
                            "title": title,
                            "slug": slug,
                            "iso3": c.get("iso3"),
                            "modern": c.get("modern") or "",
                            "historical": c.get("historical") or "",
                            "stub": bool((c.get("metadata") or {}).get("stub")),
                        }
                    )
            if out:
                return out
        except Exception as exc:  # noqa: BLE001
            print(f"warn: countries.yml: {exc}")
    return [
        {
            "title": t,
            "slug": slugify(t),
            "iso3": COUNTRY_GEO.get(t, (None,))[0],
            "modern": "",
            "historical": "",
            "stub": False,
        }
        for t in KNOWN_COUNTRIES
        if t in COUNTRY_GEO
    ]


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"warning: could not load JSON {path}: {type(e).__name__}: {e}")
        return None


def first_sentences(text: str, max_chars: int = 520) -> str:
    from archive_text import clean_archive_text, clip_at_sentence

    text = clean_archive_text(re.sub(r"\s+", " ", (text or "")).strip())
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for p in parts:
        p = p.strip()
        if len(p) < 40:
            continue
        out.append(p)
        joined = " ".join(out)
        if len(joined) >= max_chars * 0.7 or len(out) >= 3:
            break
    joined = " ".join(out).strip()
    if len(joined) > max_chars:
        joined, _ = clip_at_sentence(joined, max_chars)
        joined = joined.rstrip("…").rstrip()
    return joined


def build_modern_excerpt(od: dict | None, sd: dict | None, uc: dict | None) -> str:
    bits = []
    if od and od.get("brief_situation"):
        bits.append(first_sentences(od["brief_situation"], 420))
    elif od and od.get("persecution_engines"):
        bits.append(first_sentences(od["persecution_engines"], 320))
    if sd and sd.get("executive_summary"):
        bits.append(first_sentences(sd["executive_summary"], 380))
    if uc and uc.get("key_findings"):
        bits.append(first_sentences(uc["key_findings"][0], 300))
    # Dedupe near-identical
    cleaned = []
    for b in bits:
        if not b:
            continue
        if any(b[:80] in c for c in cleaned):
            continue
        cleaned.append(b)
    return " ".join(cleaned)[:900]


def build_historical_excerpt(sd: dict | None) -> str:
    if not sd:
        return ""
    sections = sd.get("sections") or {}
    for key, val in sections.items():
        if "demograph" in key or "legal framework" in key:
            return first_sentences(val, 400)
    return ""


def format_vdem_score(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return round(float(val), 3)
    except (TypeError, ValueError):
        return None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    countries = site_countries()
    vdem = load_json(VDEM_DIR / "forb_latest.json") or {}
    vdem_by_slug = {}
    for _iso, row in (vdem.get("countries") or {}).items():
        slug = row.get("project_slug")
        if slug:
            vdem_by_slug[slug] = row

    extracted = {}
    enriched = 0
    for c in countries:
        slug = c["slug"]
        od = load_json(OD_DIR / f"{slug}.json")
        sd = load_json(STATE_DIR / f"{slug}.json")
        uc = load_json(USCIRF_DIR / f"{slug}.json")
        vd = vdem_by_slug.get(slug) or {}

        modern_excerpt = build_modern_excerpt(od, sd, uc)
        historical_excerpt = build_historical_excerpt(sd)
        thin = c.get("stub") or len(c.get("modern") or "") < THIN_MODERN_CHARS

        sources = []
        if od:
            sources.append(
                {
                    "id": f"odwwl2025archive{slug.replace('-', '')}",
                    "title": f"Open Doors WWL 2025 Persecution Dynamics — {c['title']}",
                    "url": od.get("url")
                    or "https://www.opendoors.org/en-US/research-reports/",
                    "date": "2025",
                    "attribution": "© Open Doors International",
                }
            )
        if sd:
            sources.append(
                {
                    "id": f"statedepartment{sd.get('report_year', 2023)}archive{slug.replace('-', '')}",
                    "title": f"U.S. State Department IRF Report {sd.get('report_year', 2023)} — {c['title']}",
                    "url": sd.get("url")
                    or "https://www.state.gov/international-religious-freedom-reports/",
                    "date": str(sd.get("report_year") or "2023"),
                }
            )
        if uc:
            sources.append(
                {
                    "id": f"uscirf2025archive{slug.replace('-', '')}",
                    "title": f"USCIRF Country Page — {c['title']}",
                    "url": uc.get("url") or f"https://www.uscirf.gov/countries/{slug}",
                    "date": "2025",
                }
            )
        if vd:
            sources.append(
                {
                    "id": "vdem2025forb",
                    "title": "V-Dem Dataset — Freedom of Religion Indicators (CC BY-SA)",
                    "url": "https://www.v-dem.net/data/the-v-dem-dataset/",
                    "date": str(int(float(vd.get("year") or 2024))),
                }
            )

        record = {
            "title": c["title"],
            "slug": slug,
            "iso3": c.get("iso3"),
            "thin_modern": thin,
            "modern_excerpt": modern_excerpt,
            "historical_excerpt": historical_excerpt,
            "apply_modern": bool(thin and modern_excerpt),
            "apply_historical": bool(
                (c.get("stub") or len(c.get("historical") or "") < 200) and historical_excerpt
            ),
            "opendoors": {
                "brief_situation": (od or {}).get("brief_situation") or "",
                "persecution_engines": (od or {}).get("persecution_engines") or "",
                "ranking": (od or {}).get("ranking"),
                "score": (od or {}).get("score"),
                "url": (od or {}).get("url"),
            }
            if od
            else None,
            "state_dept": {
                "executive_summary": ((sd or {}).get("executive_summary") or "")[:800],
                "url": (sd or {}).get("url"),
                "report_year": (sd or {}).get("report_year"),
                "christian_mention_count": (
                    ((sd or {}).get("christian_mentions") or {}).get("count")
                    if isinstance((sd or {}).get("christian_mentions"), dict)
                    else None
                ),
            }
            if sd
            else None,
            "uscirf": {
                "designation": (uc or {}).get("designation"),
                "key_findings": ((uc or {}).get("key_findings") or [])[:2],
                "url": (uc or {}).get("url"),
            }
            if uc
            else None,
            "vdem": {
                "year": format_vdem_score(vd.get("year")),
                "v2clrelig": format_vdem_score(vd.get("v2clrelig")),
                "v2clrelig_ord": format_vdem_score(vd.get("v2clrelig_ord")),
                "v2csrlgrep": format_vdem_score(vd.get("v2csrlgrep")),
                "v2csrlgrep_ord": format_vdem_score(vd.get("v2csrlgrep_ord")),
            }
            if vd
            else None,
            "source_entries": sources,
        }
        if modern_excerpt or historical_excerpt or vd or od or sd or uc:
            enriched += 1
        extracted[slug] = record

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "country_count": len(extracted),
        "enriched_count": enriched,
        "countries": extracted,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    apply_m = sum(1 for r in extracted.values() if r.get("apply_modern"))
    apply_h = sum(1 for r in extracted.values() if r.get("apply_historical"))
    print(f"Wrote {OUT_PATH} ({enriched}/{len(extracted)} enriched; apply modern={apply_m} historical={apply_h})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
