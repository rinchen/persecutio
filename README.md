# Persecutio

Static site documenting Christian persecution by country, served via GitHub Pages and updated automatically by GitHub Actions.

## Architecture

```
scripts/fetch_*.py  →  data/fetched/
        ↓
scripts/collect_data.py  →  data/countries.yml, data/sources.yml
        ↓
scripts/generate_website_data.py  →  countries/*.html, assets/data/{geojson,search,meta}.json
        ↓
GitHub Pages
```

Curated country narratives live in `scripts/collect_data.py`. Fetch scripts enrich metadata (scores, incidents, news). The generator builds HTML pages and JSON for the map/search UI.

## Data outputs

- `data/countries.yml` / `data/sources.yml` — structured country and source records
- `assets/data/geojson.json` — map markers
- `assets/data/search.json` — Lunr search index input
- `assets/data/meta.json` — source status chips for the map footer
- `countries/*.html` — per-country pages (~63)

## Sources

Pipeline sources (status chips on the map footer): Open Doors (OD), USCIRF (UC), Freedom House (FH), U.S. State Dept IRF (SD), OHCHR, GDELT, Our World in Data (OWID), Morning Star News (MSN), Violent Incidents Database (VID), Global Christian Relief (GCR), Aid to the Church in Need (ACN), Christian Solidarity Worldwide (CSW), International Christian Concern (ICC), Pew, BBC, Natural Earth (NE). Wikipedia summaries are fetched during collect for enrichment.

## Requirements

Python **3.12+**. Install deps:

```bash
python3 -m pip install -r requirements.txt
```

## Local development

```bash
# Optional: refresh external feeds (writes data/fetched/)
python3 scripts/fetch_opendoors.py
# ...or run any scripts/fetch_*.py

python3 scripts/collect_data.py
python3 scripts/generate_website_data.py
python3 -m pytest tests

# Serve locally (map/search fetch JSON relative to the site root)
python3 -m http.server 8000
# open http://localhost:8000/
```

Opening `index.html` via `file://` will not load JSON correctly; use a local HTTP server.

## Contributing

1. Add or edit a country in `scripts/collect_data.py` (`COUNTRIES_DATA`), including `source_ids`.
2. Add a source entry in the `sources` dict in the same file (or extend a `scripts/fetch_*.py` fetcher).
3. Run collect → generate → pytest.
4. Open a PR with the regenerated YAML/HTML/JSON when appropriate.

## Workflow

[`.github/workflows/update.yml`](.github/workflows/update.yml) runs **daily** at 06:00 UTC (`cron: '0 6 * * *'`) and on `workflow_dispatch`. It fetches sources, collects, generates, tests, deploys GitHub Pages, and on schedule commits data updates to `main`. Fetch failures abort before generate/deploy.
