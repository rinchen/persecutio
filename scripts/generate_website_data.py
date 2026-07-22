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
    data = yaml.safe_load(f)
countries = data["countries"]

PAGE = """<!DOCTYPE html>
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
      <a href="/">Back to map</a>
    </div>
    <div class="status-pill">
      <span class="pct" style="background:{status_color}"></span>
      <span>{persecution_level} · {status_label}</span>
    </div>
    <section>
      <h2>Historical Background</h2>
      <p>{historical}</p>
    </section>
    <section>
      <h2>Modern-Day Situation</h2>
      <p>{modern}</p>
    </section>
    <section>
      <h2>Sources</h2>
      <ul>
        {sources}
      </ul>
    </section>
  </div>
</main>
<footer>
  <div class="wrap" style="padding:14px 16px;">
    <a href="/persecutio/index.html">Map</a> · <a href="/persecutio/about.html">About</a>
    <div style="margin-top:6px">Data updated automatically via GitHub Actions.</div>
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
    "persecution": "#ef4444"
}

LABELS = {
    "severe": "Severe",
    "warning": "Warning",
    "restricted": "Restricted",
    "open": "Open",
    "persecution": "Active Persecution",
}

for c in countries:
    status = c.get("status", "")
    color = COLORS.get(status, "#94a3b8")
    label = LABELS.get(status, status.title())
    sources_html = "".join(
        f"""<li><a href="{s.get('url','#')}">{s.get('title','')}</a>{" ("+s.get('date','')+")" if s.get('date') else ""}</li>"""
        for s in c.get("sources", [])
    ) or '<li>Sources will be listed here.</li>'
    html = PAGE.format(
        title=c['title'],
        historical=c['historical'],
        modern=c['modern'],
        sources=sources_html,
        persecution_level=c.get('persecution_level', ''),
        status_label=label,
        status_color=color,
    )
    (COUNTRIES / f"{c['slug']}.html").write_text(html, encoding="utf-8")
    print("wrote", c["slug"])
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
