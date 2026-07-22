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
for c in countries:
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{c['title']} | Christian Persecution World Map</title><link rel="stylesheet" href="assets/css/main.css"></head><body><header><a href="index.html">Home</a></header><main><h1>{c['title']}</h1><section><h2>Historical Background</h2><p>{c['historical']}</p></section><section><h2>Modern-Day Situation</h2><p>{c['modern']}</p></section><section><h2>Sources</h2><ul>"""
    for s in c.get("sources", []):
        html += f"""<li><a href="{s.get('url','#')}">{s.get('title','')}</a></li>"""
    html += "</ul></section></main></body></html>"
    (COUNTRIES / f"{c['slug']}.html").write_text(html, encoding="utf-8")
    print("wrote", c["slug"])
geo = {"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[c["lng"], c["lat"]]},"properties":{"title":c["title"],"slug":c["slug"],"iso3":(c.get("iso3") or "").upper(),"status":c.get("status","")}} for c in countries]}
(ASSETS / "geojson.json").write_text(json.dumps(geo, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
(COUNTRIES / "geojson.json").write_text((ASSETS / "geojson.json").read_text(encoding="utf-8"), encoding="utf-8")
(ASSETS / "search.json").write_text(json.dumps([{"slug":c["slug"],"title":c["title"],"country":c["title"]} for c in countries], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
(COUNTRIES / "search.json").write_text((ASSETS / "search.json").read_text(encoding="utf-8"), encoding="utf-8")
print("generated plain-static files")
