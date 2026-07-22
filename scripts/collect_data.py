from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
(DATA / "countries.yml").write_text("countries:\n  - title: China\n    slug: china\n    iso3: CHN\n    status: severe\n    persecution_level: Very High\n    lat: 35.86\n    lng: 104.19\n    modern: |\n      China ranks among the world’s most restrictive environments for Christians...\n    historical: |\n      Christianity entered China in the Tang dynasty through Nestorian missionaries...\n    sources:\n      - title: Open Doors World Watch List 2024\n        url: https://www.opendoorsusa.org/christian-persecution/world-watch-list/\n        date: 2024\n", encoding="utf-8")
print("collect ok")
