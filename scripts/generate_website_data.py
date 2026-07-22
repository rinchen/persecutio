import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
COUNTRIES = ROOT / "countries"
ASSETS = ROOT / "assets" / "data"
DATA.mkdir(parents=True, exist_ok=True)
COUNTRIES.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

with (DATA / "countries.yml").open("r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}
countries = data.get("countries")
if not countries:
    raise SystemExit("data/countries.yml is missing or has no 'countries' list")

source_statuses = data.get("fetched", {}).get("source_statuses") or []


def format_source_status(statuses):
    if not statuses:
        return "no source pull data"
    ok = []
    failed = []
    cached = []
    partial = []
    unknown = []
    for s in statuses:
        name = s.get("name") if isinstance(s, dict) else None
        state = ((s or {}).get("status") or "unknown")
        stamp = ((s or {}).get("fetched_at") or "")
        label = name or "source"
        if state == "ok":
            ok.append(f"{label} fetched {stamp}")
        elif state == "cached":
            cached.append(f"{label} cached {stamp}")
        elif state == "partial":
            partial.append(f"{label} partial")
        elif state == "failed":
            failed.append(f"{label} failed")
        else:
            unknown.append(f"{label} {state}")
    parts = []
    if ok:
        parts.append("; ".join(sorted(ok)[:2]))
    if partial:
        parts.append("partial: " + ", ".join(sorted(partial)[:2]))
    if cached:
        parts.append("cached: " + ", ".join(sorted(cached)[:2]))
    if failed or unknown:
        parts.append("failed/unknown: " + ", ".join(sorted(failed + unknown)[:2]))
    return "last pull: " + ("; ".join(parts) if parts else "unknown")


last_pull_text = format_source_status(source_statuses)

PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} | Christian Persecution World Map</title>
<link rel="stylesheet" href="../assets/css/main.css" />
<style>
*,*::before,*::after {{ box-sizing: border-box; }}
body {{ margin:0; font-family: system-ui,-apple-system,Segoe UI,Arial,sans-serif; background:#f8fafc; color:#0f172a; }}
header {{ background:#0b132b; color:#fff; }}
header a {{ text-decoration:none; color:inherit; }}
.wrap {{ max-width:1100px; margin:0 auto; padding:16px; display:flex; align-items:center; justify-content:space-between; }}
.brand {{ font-weight:700; letter-spacing:0.3px; }}
nav a {{ color:#cbd5e1; }}
nav a:hover {{ color:#fff; }}
main {{ padding:24px 16px; }}
.card {{ background:#fff; border:1px solid #e5e7eb; border-radius:12px; box-shadow:0 1px 2px rgba(0,0,0,0.03); padding:16px; }}
.top {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }}
.top h1 {{ margin:0; font-size:22px; }}
.top a {{ font-size:13px; color:#2563eb; text-decoration:underline; }}
section + section {{ margin-top:18px; }}
h2 {{ margin:0 0 6px; font-size:16px; color:#0b132b; }}
p {{ margin:0; line-height:1.6; color:#1e293b; }}
ul {{ margin:0; padding-left:18px; }}
li + li {{ margin-top:6px; }}
a {{ color:#2563eb; word-break:break-word; }}
.status-pill {{ display:inline-flex; align-items:center; gap:8px; padding:6px 10px; border-radius:999px; font-size:12px; border:1px solid #e5e7eb; background:#f8fafc; }}
.status-pill .pct {{ width:8px; height:8px; border-radius:999px; display:inline-block; }}
.section-sources {{ margin-top:8px; font-size:13px; color:#475569; }}
.section-sources strong {{ color:#0f172a; }}
footer {{ margin-top:24px; padding:14px 16px; border-top:1px solid #e5e7eb; font-size:13px; color:#64748b; background:#fff; }}
footer a {{ color:#334155; text-decoration: underline; }}
.data-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:10px; margin-top:14px; }}
.data-item {{ background:#f1f5f9; border-radius:8px; padding:10px 12px; font-size:13px; }}
.data-item .label {{ color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; }}
.data-item .value {{ color:#0f172a; font-weight:600; font-size:15px; margin-top:2px; }}
.incidents-list {{ margin-top:10px; }}
.incident-item {{ padding:8px 0; border-bottom:1px solid #e5e7eb; font-size:13px; }}
.incident-item:last-child {{ border-bottom:none; }}
.incident-source {{ display:inline-block; background:#fee2e2; color:#991b1b; font-size:11px; font-weight:600; padding:2px 6px; border-radius:4px; margin-right:6px; }}
.incident-date {{ color:#94a3b8; font-size:12px; margin-left:6px; }}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <a class="brand" href="/persecutio/index.html">Christian Persecution World Map</a>
    <nav>
      <a href="/persecutio/index.html">Map</a>
    </nav>
  </div>
</header>
<main>
  <div class="card">
    <div class="top">
      <h1>{title}</h1>
      <a href="/persecutio/index.html">Back to map</a>
    </div>
    <div class="status-pill">
      <span class="pct" style="background:{status_color}"></span>
      <span>{persecution_level} · {status_label}</span>
    </div>
    {data_fields}
    {recent_incidents}
    <section>
      <h2>Historical Background</h2>
      <p>{historical}</p>
      <div class="section-sources"><strong>Sources:</strong> {historical_sources}</div>
    </section>
    <section>
      <h2>Modern-Day Situation</h2>
      <p>{modern}</p>
      <div class="section-sources"><strong>Sources:</strong> {modern_sources}</div>
    </section>
    <section>
      <h2>All References</h2>
      <ul>
        {all_sources}
      </ul>
    </section>
  </div>
</main>
<footer>
  <div class="wrap" style="padding:14px 16px;">
    <div class="footer-status-line">
      <strong>Source status:</strong>
      {last_pull_text}
    </div>
  </div>
</footer>
</body>
</html>
"""

COLORS = {
    "severe": "#dc2626",
    "warning": "#f97316",
    "restricted": "#facc15",
    "open": "#3b82f6",
    "persecution": "#ef4444",
}

LABELS = {
    "severe": "Severe",
    "warning": "Warning",
    "restricted": "Restricted",
    "open": "Open",
    "persecution": "Active Persecution",
}

generated_at = __import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')


def render_sources(source_ids: list[str], all_sources_lookup: dict) -> str:
    items = []
    for sid in source_ids:
        s = all_sources_lookup.get(sid)
        if not s:
            continue
        label = s.get("title", sid)
        url = s.get("url", "#")
        date = s.get("date", "")
        prefix = f"({date}) " if date else ""
        items.append(f'<a href="{url}">{prefix}{label}</a>')
    return "; ".join(items) if items else "Sources will be listed here."


def render_data_fields(country: dict) -> str:
    meta = country.get("metadata", {})
    items = []
    od_score = meta.get("opendoors_score")
    od_rank = meta.get("opendoors_ranking")
    if od_score is not None:
        items.append(f'<div class="data-item"><div class="label">Open Doors Score</div><div class="value">{od_score}/100</div></div>')
    if od_rank is not None:
        items.append(f'<div class="data-item"><div class="label">WWL Ranking</div><div class="value">#{od_rank}</div></div>')
    fh_status = meta.get("freedom_house_status")
    if fh_status:
        items.append(f'<div class="data-item"><div class="label">Freedom House</div><div class="value">{fh_status}</div></div>')
    fh_pr = meta.get("freedom_house_pr")
    fh_cl = meta.get("freedom_house_cl")
    if fh_pr is not None and fh_cl is not None:
        items.append(f'<div class="data-item"><div class="label">PR / CL Score</div><div class="value">{fh_pr} / {fh_cl}</div></div>')
    christ_pop = meta.get("christian_population")
    christ_pct = meta.get("christian_percentage")
    if christ_pop is not None:
        pop_str = f"{christ_pop:,}" if isinstance(christ_pop, (int, float)) else str(christ_pop)
        pct_str = f" ({christ_pct:.1f}%)" if christ_pct else ""
        items.append(f'<div class="data-item"><div class="label">Christian Population</div><div class="value">{pop_str}{pct_str}</div></div>')
    gdelt_count = meta.get("gdelt_recent_articles")
    if gdelt_count is not None:
        items.append(f'<div class="data-item"><div class="label">Recent News Events</div><div class="value">{gdelt_count}</div></div>')
    acn_class = meta.get("acn_classification")
    if acn_class:
        items.append(f'<div class="data-item"><div class="label">ACN Classification</div><div class="value">{acn_class}</div></div>')
    vid_total = meta.get("vid_incidents_total")
    if vid_total is not None:
        items.append(f'<div class="data-item"><div class="label">VID Incidents</div><div class="value">{vid_total}</div></div>')
    vid_killings = meta.get("vid_killings")
    if vid_killings is not None:
        items.append(f'<div class="data-item"><div class="label">VID Killings</div><div class="value">{vid_killings}</div></div>')
    gcr_killed = meta.get("gcr_killed")
    if gcr_killed:
        items.append(f'<div class="data-item"><div class="label">GCR Killed</div><div class="value">{gcr_killed}</div></div>')
    gcr_score = meta.get("gcr_persecution_score")
    if gcr_score:
        items.append(f'<div class="data-item"><div class="label">GCR Persecution Score</div><div class="value">{gcr_score}</div></div>')
    if not items:
        return ""
    return '<div class="data-grid">' + "\n      ".join(items) + "\n    </div>"


def render_recent_incidents(country: dict) -> str:
    meta = country.get("metadata", {})
    articles = []
    for src_key, count_key, sample_key, label in [
        ("morningstarnews_articles", "morningstarnews_articles", "morningstarnews_samples", "Morning Star News"),
        ("csw_articles", "csw_articles", "csw_samples", "CSW"),
        ("icc_articles", "icc_articles", "icc_samples", "ICC"),
    ]:
        samples = meta.get(sample_key, [])
        for a in samples:
            articles.append({"source": label, "title": a.get("title", ""), "url": a.get("url", ""), "date": a.get("date", "")})
    if not articles:
        return ""
    rows = []
    for a in articles[:6]:
        href = a.get("url", "#")
        title = html.escape(a.get("title", "Report"))
        src = html.escape(a.get("source", ""))
        date = html.escape(a.get("date", ""))
        rows.append(f'<div class="incident-item"><span class="incident-source">{src}</span> <a href="{href}" target="_blank" rel="noopener">{title}</a> <span class="incident-date">{date}</span></div>')
    return '<h3>Recent Incidents</h3>\n<div class="incidents-list">' + "\n    ".join(rows) + "\n    </div>"


all_sources_lookup = {}
with (DATA / "sources.yml").open("r", encoding="utf-8") as f:
    loaded = yaml.safe_load(f) or {}
all_sources_lookup = loaded.get("sources") or {}
if not all_sources_lookup:
    raise SystemExit("data/sources.yml is missing or has no 'sources' mapping")

SOURCE_LABELS = {
    "natural_earth_110m": "NE",
    "odwwl2024": "OD",
    "acn2024": "ACN",
    "pew2023america": "Pew",
    "pew2023china": "Pew",
    "bbc2021": "BBC",
}
SOURCE_TITLES = {
    "natural_earth_110m": "Natural Earth map boundaries",
    "odwwl2024": "Open Doors World Watch List 2024",
    "acn2024": "ACN Persecuted and Forgotten 2024",
    "pew2023america": "Pew Research — Religion in America",
    "pew2023china": "Pew Research — Religion in China",
    "bbc2021": "BBC News — Afghanistan Christians 2021",
}

def _source_label(sid):
    if sid in SOURCE_LABELS:
        return SOURCE_LABELS[sid]
    if sid.startswith("uscirf"):
        return "UC"
    return sid[:6].upper()

def _source_title(sid):
    if sid in SOURCE_TITLES:
        return SOURCE_TITLES[sid]
    s = all_sources_lookup.get(sid)
    if s and s.get("title"):
        return s["title"]
    return sid

fetched_statuses = data.get("fetched", {}).get("source_statuses") or []
status_map = {}
for s in fetched_statuses:
    if isinstance(s, dict) and s.get("name"):
        status_map[s["name"]] = s

meta_sources = []
for sid in all_sources_lookup:
    fs = status_map.get(sid)
    meta_sources.append({
        "id": sid,
        "label": _source_label(sid),
        "title": _source_title(sid),
        "status": fs.get("status", "skipped") if fs else "skipped",
        "fetchedAt": fs.get("fetched_at") if fs else None,
    })
fs_ne = status_map.get("natural_earth_110m")
if fs_ne:
    meta_sources.append({
        "id": "natural_earth_110m",
        "label": "NE",
        "title": "Natural Earth map boundaries",
        "status": fs_ne.get("status", "ok"),
        "fetchedAt": fs_ne.get("fetched_at"),
    })

meta = {
    "generatedAt": data.get("fetched", {}).get("generated_at"),
    "sources": meta_sources,
}
(ASSETS / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(COUNTRIES / "meta.json").write_text((ASSETS / "meta.json").read_text(encoding="utf-8"), encoding="utf-8")

for c in countries:
    if not isinstance(c, dict):
        raise SystemExit("countries.yml contains an invalid non-object country entry")
    title = c.get("title")
    slug = c.get("slug")
    iso3 = str(c.get("iso3", "") or "").upper()
    if not title or not slug or not iso3:
        raise SystemExit(f"Invalid country entry missing title/slug/iso3: {c}")

    status = c.get("status", "")
    color = COLORS.get(status, "#94a3b8")
    label = LABELS.get(status, status.title() if status else "Unknown")
    source_ids = c.get("source_ids") or {}

    hist_ids = source_ids.get("historical", []) or []
    mod_ids = source_ids.get("modern", []) or []
    if not hist_ids:
        hist_ids = list(all_sources_lookup.keys())
    if not mod_ids:
        mod_ids = list(all_sources_lookup.keys())

    historical_sources = render_sources(hist_ids, all_sources_lookup)
    modern_sources = render_sources(mod_ids, all_sources_lookup)
    all_sources_items = [
        f"""<li><a href="{all_sources_lookup[s].get('url','#')}">{all_sources_lookup[s].get('title', s)}</a>{" ("+all_sources_lookup[s].get('date','')+")" if all_sources_lookup[s].get('date') else ""}</li>"""
        for s in all_sources_lookup.keys()
        if s in {*hist_ids, *mod_ids}
    ] or ['<li>Sources will be listed here.</li>']

    page_html = PAGE.format(
        title=title,
        historical=c.get("historical", ""),
        modern=c.get("modern", ""),
        historical_sources=historical_sources,
        modern_sources=modern_sources,
        all_sources="\n        ".join(all_sources_items),
        persecution_level=c.get("persecution_level", ""),
        status_label=label,
        status_color=color,
        generated_at=generated_at,
        last_pull_text=last_pull_text,
        data_fields=render_data_fields(c),
        recent_incidents=render_recent_incidents(c),
    )
    (COUNTRIES / f"{slug}.html").write_text(page_html, encoding="utf-8")
    print("wrote", slug)


geo = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [c["lng"], c["lat"]]},
            "properties": {
                "title": c["title"],
                "slug": c["slug"],
                "iso3": (c.get("iso3") or "").upper(),
                "status": c.get("status", ""),
                "level": c.get("persecution_level", ""),
            },
        }
        for c in countries
    ],
}
(ASSETS / "geojson.json").write_text(json.dumps(geo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(COUNTRIES / "geojson.json").write_text((ASSETS / "geojson.json").read_text(encoding="utf-8"), encoding="utf-8")
(ASSETS / "search.json").write_text(
    json.dumps(
        [{"slug": c["slug"], "title": c["title"], "country": c["title"]} for c in countries],
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)
(COUNTRIES / "search.json").write_text((ASSETS / "search.json").read_text(encoding="utf-8"), encoding="utf-8")
print("generated plain-static files")
