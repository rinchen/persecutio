"""Enrich countries with fetched metadata, citations, incidents, and stubs."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from christian_persecution import is_christian_persecution
from country_registry import (
    attach_citation,
    ensure_source,
    geo_for,
    resolve_country_name,
    slugify,
)
from fetch_common import merge_articles, normalize_date

NEWS_SOURCES = [
    ("morningstarnews", "Morning Star News", "morningstarnews2026"),
    ("csw", "CSW", "csw2026"),
    ("icc", "ICC", "icc2026"),
    ("forum18", "Forum 18", "forum18"),
    ("mec", "Middle East Concern", "mec"),
    ("bitterwinter", "Bitter Winter", "bitterwinter"),
    ("releaseintl", "Release International", "releaseintl"),
    ("gdelt", "GDELT", "gdelt2025"),
]

INCIDENT_DISPLAY_CAP = 12


def load_fetched_json(fetched: Path, filename: str) -> dict:
    path = fetched / filename
    if path.exists():
        try:
            import json
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"warning: corrupt fetched file {filename}: {type(e).__name__}: {e}")
    return {}


def load_uscirf_index(fetched: Path) -> dict[str, dict]:
    import json
    path = fetched / "uscirf" / "index.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, dict] = {}
    for entry in data.get("countries") or []:
        if not isinstance(entry, dict):
            continue
        title = resolve_country_name(entry.get("title") or "") or entry.get("title")
        if title:
            out[title] = entry
    return out


def load_state_dept_index(fetched: Path) -> dict[str, dict]:
    import json
    path = fetched / "state_dept" / "index.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, dict] = {}
    year = str(data.get("report_year") or "2023")
    for name, entry in (data.get("countries") or {}).items():
        title = resolve_country_name(name) or name
        if isinstance(entry, dict):
            entry = dict(entry)
            entry["_report_year"] = year
            out[title] = entry
    return out


def load_ohchr_index(fetched: Path) -> dict[str, dict]:
    import json
    path = fetched / "ohchr" / "index.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, dict] = {}
    for name, entry in (data.get("countries") or {}).items():
        title = resolve_country_name(name)
        if not title:
            continue
        if isinstance(entry, dict):
            out[title] = entry
    return out


def _article_samples(articles: list[dict], limit: int = 3) -> list[dict]:
    return [
        {
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "date": normalize_date(a.get("date")) or a.get("date") or "",
            "description": a.get("description", ""),
            "source": a.get("source", ""),
        }
        for a in (articles or [])[:limit]
    ]


def build_recent_incidents(country_title: str, news_blobs: dict[str, dict]) -> list[dict]:
    combined: list[dict] = []
    for key, label, _sid in NEWS_SOURCES:
        blob = news_blobs.get(key) or {}
        countries = blob.get("countries") or {}
        arts = countries.get(country_title) or []
        for a in arts:
            title = a.get("title") or ""
            desc = a.get("description") or ""
            # GDELT/others may already be filtered at fetch; re-check for safety
            if key in ("forum18", "bitterwinter", "gdelt"):
                if not is_christian_persecution(title=title, description=desc):
                    continue
            combined.append({
                "title": title,
                "url": a.get("url", ""),
                "date": normalize_date(a.get("date")) or a.get("date") or "",
                "description": desc,
                "source": a.get("source") or label,
            })
    merged = merge_articles([], combined)
    return merged[:INCIDENT_DISPLAY_CAP]


def enrich_country(
    c: dict,
    *,
    sources: dict,
    country_polygons: dict,
    wiki: dict | None,
    freedom_house: dict,
    opendoors_data: dict,
    owid_data: dict,
    vid_data: dict,
    gcr_data: dict,
    acn_data: dict,
    uscirf_by_title: dict,
    state_dept_by_title: dict,
    ohchr_by_title: dict,
    news_blobs: dict[str, dict],
) -> None:
    iso = str(c.get("iso3", "")).upper()
    title = c.get("title", "")
    c.setdefault("source_ids", {})
    modern = list(c["source_ids"].get("modern") or [])
    c["source_ids"]["modern"] = [sid for sid in modern if sid in sources]

    c.setdefault("metadata", {})
    meta = c["metadata"]
    meta["shape_geo"] = country_polygons.get(iso)
    meta["wiki_url"] = (
        wiki.get("content_urls", {}).get("desktop", {}).get("page")
        if isinstance(wiki, dict)
        else None
    )
    meta["wiki_extract"] = wiki.get("extract") if isinstance(wiki, dict) else None
    meta["country_polygon"] = bool(iso in country_polygons)

    # Re-sync citations from handwritten ids first
    for sid in list(c["source_ids"].get("modern") or []):
        attach_citation(c, sid, sources)

    fh = (freedom_house.get("countries") or {}).get(title, {})
    if fh:
        meta["freedom_house_status"] = fh.get("status")
        meta["freedom_house_pr"] = fh.get("pr_score")
        meta["freedom_house_cl"] = fh.get("cl_score")
        attach_citation(c, "freedomhouse2024", sources)

    od = (opendoors_data.get("countries") or {}).get(title, {})
    if od:
        meta["opendoors_ranking"] = od.get("ranking")
        meta["opendoors_score"] = od.get("score")
        # Prefer newer WWL citation when present
        od_sid = "odwwl2026" if "odwwl2026" in sources else "odwwl2024"
        attach_citation(c, od_sid, sources)

    owid = (owid_data.get("countries") or {}).get(title, {})
    if owid:
        meta["christian_population"] = owid.get("christian_population")
        meta["christian_percentage"] = owid.get("christian_percentage")
        attach_citation(c, "owid2024", sources)

    vid_entry = (vid_data.get("countries") or {}).get(title, {})
    if vid_entry:
        meta["vid_incidents_total"] = vid_entry.get("total_incidents")
        meta["vid_killings"] = vid_entry.get("killings")
        meta["vid_breakdown"] = {
            k: v for k, v in vid_entry.items() if k != "total_incidents" and v
        }
        attach_citation(c, "vid2026", sources)

    gcr_entry = (gcr_data.get("countries") or {}).get(title, {})
    if gcr_entry:
        if gcr_entry.get("killed"):
            meta["gcr_killed"] = gcr_entry["killed"]
        if gcr_entry.get("persecution_score"):
            meta["gcr_persecution_score"] = gcr_entry["persecution_score"]
        if gcr_entry.get("notes"):
            meta["gcr_notes"] = gcr_entry["notes"]
        attach_citation(c, "gcr2026", sources)

    acn_entry = (acn_data.get("countries") or {}).get(title, {})
    if acn_entry:
        meta["acn_classification"] = acn_entry.get("classification")
        if acn_entry.get("key_findings"):
            meta["acn_key_findings"] = acn_entry["key_findings"][:2]
        attach_citation(c, "acn2025" if "acn2025" in sources else "acn2024", sources)

    # News feeds
    for key, _label, sid in NEWS_SOURCES:
        blob = news_blobs.get(key) or {}
        arts = (blob.get("countries") or {}).get(title) or []
        if not arts:
            continue
        meta[f"{key}_articles"] = len(arts)
        meta[f"{key}_samples"] = _article_samples(arts, 3)
        if key == "gdelt":
            meta["gdelt_recent_articles"] = len(arts)
            meta["gdelt_sample_urls"] = [a.get("url", "") for a in arts[:3]]
        attach_citation(c, sid, sources)

    # USCIRF
    uscirf = uscirf_by_title.get(title)
    if uscirf and uscirf.get("status") in ("ok", "cached"):
        meta["uscirf_designation"] = uscirf.get("designation")
        findings = uscirf.get("key_findings") or []
        if findings:
            meta["uscirf_key_findings"] = findings[:2]
        url = uscirf.get("url") or ""
        meta["uscirf_url"] = url
        slug = uscirf.get("project_slug") or slugify(title)
        year = "2026"
        sid = f"uscirf{year}{slug.replace('-', '')}"
        # Prefer existing handwritten ids when present
        existing = None
        for cand in sources:
            if cand.startswith("uscirf") and slug.replace("-", "") in cand.replace("-", ""):
                if title.lower().replace(" ", "") in sources[cand]["title"].lower().replace(" ", ""):
                    existing = cand
                    break
        if existing:
            attach_citation(c, existing, sources)
        else:
            ensure_source(
                sources,
                sid,
                f"USCIRF Annual Report - {title}",
                url or f"https://www.uscirf.gov/countries/{slug}",
                year,
            )
            attach_citation(c, sid, sources)

    # State Dept IRF
    sd = state_dept_by_title.get(title)
    if sd and sd.get("has_report"):
        meta["state_dept_url"] = sd.get("url") or ""
        summary = (sd.get("executive_summary") or "")[:600]
        if summary:
            meta["state_dept_executive_summary"] = summary
        mentions = sd.get("christian_mentions")
        if isinstance(mentions, dict):
            meta["state_dept_christian_mentions"] = mentions.get("count") or len(
                mentions.get("excerpts") or mentions.get("mentions") or []
            ) or bool(mentions)
        elif mentions:
            meta["state_dept_christian_mentions"] = mentions
        year = sd.get("_report_year") or "2023"
        slug = slugify(title)
        sid = f"statedepartment{year}{slug.replace('-', '')}"
        ensure_source(
            sources,
            sid,
            f"U.S. State Department IRF Report {year} - {title}",
            sd.get("url") or "https://www.state.gov/international-religious-freedom-reports/",
            year,
        )
        attach_citation(c, sid, sources)
        attach_citation(c, "statedepartment2023", sources)

    # OHCHR
    ohchr = ohchr_by_title.get(title)
    if ohchr:
        count = ohchr.get("recommendation_count") or 0
        religion_recs = ohchr.get("religion_recommendations") or []
        # Prefer Christian-relevant samples when possible
        christian_samples = [
            r for r in religion_recs
            if is_christian_persecution(title=r, description="")
            or any(t in (r or "").lower() for t in ("christian", "church", "bible"))
        ]
        samples = christian_samples[:2] or religion_recs[:2]
        if count or samples:
            meta["ohchr_recommendation_count"] = count
            if samples:
                meta["ohchr_samples"] = samples[:2]
            attach_citation(c, "ohchr2024", sources)

    incidents = build_recent_incidents(title, news_blobs)
    if incidents:
        meta["recent_incidents"] = incidents


def derive_status_from_signals(
    title: str,
    opendoors_data: dict,
    uscirf_by_title: dict,
    acn_data: dict,
) -> tuple[str, str]:
    od = (opendoors_data.get("countries") or {}).get(title, {})
    score = od.get("score")
    if isinstance(score, (int, float)):
        if score >= 80:
            return "severe", "Extreme"
        if score >= 60:
            return "severe", "Very High"
        if score >= 40:
            return "warning", "High"
        if score >= 20:
            return "warning", "Moderate"
    uscirf = uscirf_by_title.get(title) or {}
    des = (uscirf.get("designation") or "").upper()
    if des == "CPC":
        return "severe", "Extreme"
    if des == "SWL":
        return "warning", "High"
    acn = (acn_data.get("countries") or {}).get(title, {})
    classification = (acn.get("classification") or "").lower()
    if "persecution" in classification:
        return "persecution", "High"
    if "discrimination" in classification:
        return "restricted", "Moderate"
    return "warning", "Moderate"


def collect_feed_titles(news_blobs: dict[str, dict], score_blobs: list[dict]) -> set[str]:
    titles: set[str] = set()
    for blob in news_blobs.values():
        for name in (blob.get("countries") or {}):
            resolved = resolve_country_name(name) or name
            if geo_for(resolved):
                titles.add(resolved)
    for blob in score_blobs:
        for name in (blob.get("countries") or {}):
            resolved = resolve_country_name(name)
            if resolved and geo_for(resolved):
                titles.add(resolved)
    return titles


def create_stub_countries(
    existing: list[dict],
    *,
    sources: dict,
    feed_titles: set[str],
    opendoors_data: dict,
    uscirf_by_title: dict,
    acn_data: dict,
    news_blobs: dict[str, dict],
    freedom_house: dict,
    owid_data: dict,
    vid_data: dict,
    gcr_data: dict,
    state_dept_by_title: dict,
    ohchr_by_title: dict,
    country_polygons: dict,
) -> list[dict]:
    existing_titles = {c.get("title") for c in existing}
    stubs: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()

    for title in sorted(feed_titles):
        if title in existing_titles:
            continue
        geo = geo_for(title)
        if not geo:
            continue
        status, level = derive_status_from_signals(
            title, opendoors_data, uscirf_by_title, acn_data
        )
        discovering = []
        for key, label, sid in NEWS_SOURCES:
            arts = ((news_blobs.get(key) or {}).get("countries") or {}).get(title) or []
            if arts:
                discovering.append(sid)
        stub = {
            "title": geo["title"],
            "slug": geo["slug"],
            "iso3": geo["iso3"],
            "status": status,
            "persecution_level": level,
            "lat": geo["lat"],
            "lng": geo["lng"],
            "historical": (
                f"Auto-tracked country page for {title}. Historical narrative has not "
                f"been curated yet; see Recent Incidents and referenced sources for "
                f"current Christian persecution reporting."
            ),
            "modern": (
                f"This page was auto-created from nightly Christian persecution feeds. "
                f"Editorial narrative is pending; indicators and incident links below "
                f"reflect the latest ingested sources."
            ),
            "source_ids": {
                "historical": list(dict.fromkeys(discovering)),
                "modern": list(dict.fromkeys(discovering)),
            },
            "pew_slug": "",
            "metadata": {
                "stub": True,
                "auto_created_at": now,
            },
        }
        enrich_country(
            stub,
            sources=sources,
            country_polygons=country_polygons,
            wiki=None,
            freedom_house=freedom_house,
            opendoors_data=opendoors_data,
            owid_data=owid_data,
            vid_data=vid_data,
            gcr_data=gcr_data,
            acn_data=acn_data,
            uscirf_by_title=uscirf_by_title,
            state_dept_by_title=state_dept_by_title,
            ohchr_by_title=ohchr_by_title,
            news_blobs=news_blobs,
        )
        # Ensure stub flag survives enrich
        stub["metadata"]["stub"] = True
        stub["metadata"]["auto_created_at"] = now
        stubs.append(stub)
    return stubs


def register_org_sources(sources: dict) -> None:
    ensure_source(
        sources,
        "forum18",
        "Forum 18 - Freedom of Religion or Belief News",
        "https://www.forum18.org/",
        "2026",
    )
    ensure_source(
        sources,
        "mec",
        "Middle East Concern - News",
        "https://www.meconcern.org/",
        "2026",
    )
    ensure_source(
        sources,
        "bitterwinter",
        "Bitter Winter - A Magazine on Religious Liberty and Human Rights",
        "https://bitterwinter.org/",
        "2026",
    )
    ensure_source(
        sources,
        "releaseintl",
        "Release International - Serving the Persecuted Church",
        "https://releaseinternational.org/",
        "2026",
    )
