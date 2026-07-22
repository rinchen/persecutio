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
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
<meta name="theme-color" content="#0b132b" />
<title>{title} | Christian Persecution World Map</title>
<link rel="stylesheet" href="../assets/css/main.css" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet" />
<style>
*,*::before,*::after {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: 'Outfit', system-ui, -apple-system, Segoe UI, Arial, sans-serif;
  background: linear-gradient(180deg, #dbeafe 0%, #f4f8fb 28%, #f4f8fb 100%);
  color: #1a2b3c;
  line-height: 1.55;
  min-height: 100dvh;
  -webkit-tap-highlight-color: transparent;
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }}
}}
.skip-link {{
  position: absolute;
  left: -9999px;
  top: auto;
  width: 1px;
  height: 1px;
  overflow: hidden;
  z-index: 9999;
  padding: 8px 16px;
  background: #0369a1;
  color: #fff;
  font-weight: 600;
  border-radius: 0 0 10px 10px;
  text-decoration: none;
}}
.skip-link:focus {{
  position: fixed;
  left: 16px;
  top: 0;
  width: auto;
  height: auto;
  overflow: visible;
  z-index: 10000;
}}
.sr-only {{
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}}
header {{
  background: rgb(255 255 255 / 94%);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-bottom: 1px solid rgb(197 214 227 / 90%);
  position: sticky;
  top: 0;
  z-index: 100;
  color: #1a2b3c;
}}
header a {{ text-decoration: none; color: inherit; }}
.wrap {{
  max-width: min(92rem, 100%);
  margin: 0 auto;
  padding: 0 clamp(0.75rem, 2.8vw, 2.5rem);
  height: 3.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}}
.brand {{
  font-weight: 700;
  font-size: clamp(0.9rem, 2vw, 1.1rem);
  letter-spacing: -0.01em;
  white-space: nowrap;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}}
nav {{ display: flex; align-items: center; gap: 14px; flex-shrink: 0; }}
nav a {{ color: #4a5f73; font-size: 0.875rem; }}
@media (hover: hover) and (pointer: fine) {{
  nav a:hover {{ color: #0369a1; }}
}}
main {{
  padding: clamp(0.75rem, 2.5vw, 1.5rem) clamp(0.75rem, 2.8vw, 2.5rem) clamp(1.5rem, 4vw, 2.5rem);
}}
.card {{
  background: rgb(255 255 255 / 94%);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgb(197 214 227 / 90%);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgb(26 43 60 / 8%), 0 4px 16px rgb(26 43 60 / 6%);
  padding: clamp(1rem, 2.5vw, 1.5rem);
  max-width: min(92rem, 100%);
  margin: 0 auto;
}}
.top {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}}
.top h1 {{
  margin: 0;
  font-size: clamp(1.5rem, 3vw, 1.75rem);
  letter-spacing: -0.02em;
  font-weight: 700;
  min-width: 0;
  overflow-wrap: anywhere;
}}
.top a {{
  font-size: 0.8125rem;
  color: #0369a1;
  white-space: nowrap;
  flex-shrink: 0;
}}
@media (hover: hover) and (pointer: fine) {{
  .top a:hover {{ color: #075985; }}
}}
section + section {{ margin-top: 18px; }}
h2 {{
  margin: 0 0 6px;
  font-size: clamp(1rem, 2vw, 1.125rem);
  letter-spacing: -0.01em;
  font-weight: 600;
  color: #1a2b3c;
}}
p {{ margin: 0; line-height: 1.55; color: #1a2b3c; }}
p + p {{ margin-top: 10px; }}
ul {{ margin: 0; padding-left: 18px; }}
li + li {{ margin-top: 6px; }}
a {{ color: #0369a1; word-break: break-word; }}
@media (hover: hover) and (pointer: fine) {{
  a:hover {{ color: #075985; }}
}}
.status-pill {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 0.8125rem;
  border: 1px solid #c5d6e3;
  background: #ffffff;
  margin-top: 8px;
}}
.status-pill .pct {{
  width: 8px;
  height: 8px;
  border-radius: 999px;
  display: inline-block;
}}
.section-sources {{
  margin-top: 8px;
  font-size: 0.8125rem;
  color: #4a5f73;
}}
.section-sources strong {{ color: #1a2b3c; }}
footer {{
  margin-top: 6px;
  border-top: 1px solid rgb(197 214 227 / 90%);
  background: rgb(255 255 255 / 82%);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  font-size: 0.75rem;
  color: #4a5f73;
}}
footer .wrap {{
  display: block;
  max-width: min(92rem, 100%);
  padding: 10px clamp(0.75rem, 2.8vw, 2.5rem);
  height: auto;
}}
.footer-status-line {{ font-size: 0.75rem; }}
.footer-status-line a {{ color: #334155; text-decoration: underline; }}
.data-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(180px, 100%), 1fr));
  gap: 10px;
  margin-top: 14px;
}}
.data-item {{
  background: #e8f1f8;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 0.8125rem;
}}
.data-item .label {{
  color: #4a5f73;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}
.data-item .value {{
  color: #1a2b3c;
  font-weight: 600;
  font-size: 0.9375rem;
  margin-top: 2px;
  font-variant-numeric: tabular-nums;
}}
.incidents-list {{ margin-top: 10px; }}
.incident-item {{
  padding: 8px 0;
  border-bottom: 1px solid #c5d6e3;
  font-size: 0.8125rem;
}}
.incident-item:last-child {{ border-bottom: none; }}
.incident-source {{
  display: inline-block;
  background: #fee2e2;
  color: #991b1b;
  font-size: 0.68rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 6px;
}}
.incident-date {{ color: #94a3b8; font-size: 0.75rem; margin-left: 6px; }}
@media (max-width: 520px) {{
  .brand {{ font-size: 0.875rem; }}
  nav {{ gap: 10px; }}
  nav a {{ font-size: 0.8125rem; }}
}}
:focus-visible {{
  outline: 2px solid #0284c7;
  outline-offset: 2px;
}}
.back-to-top {{
  position: fixed;
  bottom: max(1.5rem, env(safe-area-inset-bottom));
  right: max(1.5rem, env(safe-area-inset-right));
  width: 44px;
  height: 44px;
  border-radius: 999px;
  background: rgb(255 255 255 / 94%);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgb(197 214 227 / 90%);
  box-shadow: 0 1px 3px rgb(26 43 60 / 8%), 0 4px 16px rgb(26 43 60 / 6%);
  color: #1a2b3c;
  font-size: 1.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: translateY(8px);
  transition: opacity 0.2s ease, visibility 0.2s ease, transform 0.2s ease;
  z-index: 90;
}}
.back-to-top.is-visible {{
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
  transform: translateY(0);
}}
</style>
</head>
<body>
<a href="#main-content" class="skip-link">Skip to content</a>
<header>
  <div class="wrap">
    <a class="brand" href="/persecutio/index.html">Christian Persecution World Map</a>
    <nav>
      <a href="/persecutio/index.html">Map</a>
    </nav>
  </div>
</header>
<main id="main-content" tabindex="-1">
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
  <div class="wrap">
    <div class="footer-status-line">
      <strong>Source status:</strong>
      {last_pull_text}
    </div>
  </div>
</footer>
<button id="back-to-top" class="back-to-top" aria-label="Back to top">&uarr;</button>
<script src="../assets/js/back-to-top.js" defer></script>
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

SOURCE_GROUP_DEFS = {
    "uscirf": {"prefixes": ("uscirf",), "label": "UC", "title": "USCIRF Annual Reports"},
    "opendoors": {"prefixes": ("odwwl",), "label": "OD", "title": "Open Doors World Watch List"},
    "pew": {"prefixes": ("pew",), "label": "Pew", "title": "Pew Research"},
    "natural_earth": {"prefixes": ("natural_earth",), "label": "NE", "title": "Natural Earth map boundaries"},
    "freedomhouse": {"prefixes": ("freedomhouse",), "label": "FH", "title": "Freedom House Freedom in the World"},
    "statedepartment": {"prefixes": ("statedepartment",), "label": "SD", "title": "U.S. State Dept IRF Reports"},
    "ohchr": {"prefixes": ("ohchr",), "label": "OHCHR", "title": "OHCHR Universal Human Rights Index"},
    "gdelt": {"prefixes": ("gdelt",), "label": "GDELT", "title": "GDELT Global Database of Events"},
    "owid": {"prefixes": ("owid",), "label": "OWID", "title": "Our World in Data - Religious Composition"},
    "acn": {"prefixes": ("acn",), "label": "ACN", "title": "ACN Persecuted and Forgotten"},
    "bbc": {"prefixes": ("bbc",), "label": "BBC", "title": "BBC News"},
    "morningstarnews": {"prefixes": ("morningstarnews",), "label": "MSN", "title": "Morning Star News"},
    "vid": {"prefixes": ("vid",), "label": "VID", "title": "Violent Incidents Database"},
    "gcr": {"prefixes": ("gcr",), "label": "GCR", "title": "Global Christian Relief"},
    "csw": {"prefixes": ("csw",), "label": "CSW", "title": "Christian Solidarity Worldwide"},
    "icc": {"prefixes": ("icc",), "label": "ICC", "title": "International Christian Concern"},
}

STATUS_PRIORITY = {"error": 0, "failed": 0, "partial": 1, "skipped": 2, "ok": 3, "cached": 4}


def _assign_source_group(sid):
    for group_key, defn in SOURCE_GROUP_DEFS.items():
        for prefix in defn["prefixes"]:
            if sid.startswith(prefix):
                return group_key
    return sid[:8]


fetched_statuses = data.get("fetched", {}).get("source_statuses") or []
status_map = {}
for s in fetched_statuses:
    if isinstance(s, dict) and s.get("name"):
        status_map[s["name"]] = s

source_groups = {}
for sid in all_sources_lookup:
    group_key = _assign_source_group(sid)
    if group_key not in source_groups:
        source_groups[group_key] = []
    source_groups[group_key].append(sid)

STATUS_KEY_MAP = {
    "uscirf": "uscirf",
    "opendoors": "opendoors",
    "pew": None,
    "natural_earth": "natural_earth_110m",
    "freedomhouse": "freedomhouse",
    "statedepartment": "statedepartment",
    "ohchr": "ohchr",
    "gdelt": "gdelt",
    "owid": "owid",
}

# Chip CSS uses --error; fetch scripts report "failed". Map for display.
STATUS_DISPLAY = {"failed": "error"}


meta_sources = []
for group_key, sids in source_groups.items():
    defn = SOURCE_GROUP_DEFS.get(group_key, {"label": group_key[:6].upper(), "title": group_key})
    worst_status = None
    worst_ts = None
    for sid in sids:
        status_key = STATUS_KEY_MAP.get(group_key, sid)
        fs = status_map.get(status_key) if status_key else None
        if not fs:
            fs = status_map.get(sid)
        if fs:
            st = fs.get("status", "skipped")
            if worst_status is None or STATUS_PRIORITY.get(st, 99) < STATUS_PRIORITY.get(worst_status, 99):
                worst_status = st
                worst_ts = fs.get("fetched_at")
    if worst_status is None:
        worst_status = "skipped"
    meta_sources.append({
        "id": group_key,
        "label": defn["label"],
        "title": defn["title"],
        "status": STATUS_DISPLAY.get(worst_status, worst_status),
        "fetchedAt": worst_ts,
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
