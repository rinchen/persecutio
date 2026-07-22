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
    <div style="margin-top:6px">Data updated automatically via GitHub Actions. Last generated: {generated_at}</div>
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


all_sources_lookup = {}
with (DATA / "sources.yml").open("r", encoding="utf-8") as f:
    loaded = yaml.safe_load(f) or {}
all_sources_lookup = loaded.get("sources") or {}
if not all_sources_lookup:
    raise SystemExit("data/sources.yml is missing or has no 'sources' mapping")

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
