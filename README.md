# Persecutio

Static site documenting Christian persecution by country, served via GitHub Pages and updated automatically by GitHub Actions.

## Data

Country content lives in `scripts/collect_data.py` and generated pages/data are written to:
- `data/countries.yml`
- `data/sources.yml`
- `assets/data/geojson.json`
- `assets/data/search.json`
- `countries/*.html`
- `countries/search.json`

## Sources

Current site sources: Open Doors World Watch List, USCIRF, Pew Research Center, and Wikipedia.

## Local development

```bash
python3 scripts/collect_data.py
python3 scripts/generate_website_data.py
```

Then open `index.html` and `countries/<slug>.html` locally.

## Workflow

`.github/workflows/update.yml` runs twice monthly on the 1st and 15th.
