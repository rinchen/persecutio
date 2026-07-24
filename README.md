# Persecutio

Static site documenting Christian persecution by country, served via GitHub Pages and updated automatically by GitHub Actions.

## Architecture

```
scripts/fetch_*.py  →  data/fetched/
        ↓
scripts/collect_data.py (+ collect_enrich.py, country_registry.py)
        →  data/countries.yml, data/sources.yml
        ↓
scripts/generate_website_data.py  →  countries/*.html, assets/data/{geojson,search,meta}.json
        ↓
GitHub Pages (public HTML/CSS/JS only — scrape caches are not published)
```

Curated country narratives live in `scripts/collect_data.py`. Fetch scripts enrich metadata (scores, incidents, news). Helpers in `collect_enrich.py`, `rss_news_fetcher.py`, and `christian_persecution.py` merge feeds, filter articles, and auto-create stub country pages when feeds mention countries not yet curated. The generator builds HTML pages and JSON for the map/search UI.

## Data outputs

- `data/countries.yml` / `data/sources.yml` — structured country and source records
- `assets/data/geojson.json` — map markers
- `assets/data/search.json` — Lunr search index input
- `assets/data/meta.json` — source status chips for the map footer
- `countries/*.html` — per-country pages (~63 curated + auto-tracked stubs)

## Sources

Pipeline sources (status chips on the map footer):

**Primary** (fetch failure aborts generate/deploy): Open Doors (OD), Freedom House (FH), Our World in Data (OWID), USCIRF (UC), U.S. State Dept IRF (SD).

**Secondary** (enrich when available; never abort deploy): GDELT, OHCHR, Morning Star News (MSN), Violent Incidents Database (VID), Global Christian Relief (GCR), Aid to the Church in Need (ACN), Christian Solidarity Worldwide (CSW), International Christian Concern (ICC), Forum 18 (F18), Middle East Concern (MEC), Bitter Winter (BW), Release International (RI).

Also cited on pages / chips: Pew, BBC, Natural Earth (NE). Wikipedia summaries are fetched during collect for enrichment.

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

**GitHub Pages base path:** Generated country pages link to `/persecutio/…` (project site). Serving from the repo root at `http://localhost:8000/` loads the map, but “Back to map” from a country page expects `http://localhost:8000/persecutio/`. Preview options:

```bash
# From the repo parent, with this repo named persecutio:
python3 -m http.server 8000
# open http://localhost:8000/persecutio/
```

Or symlink: `mkdir -p /tmp/site && ln -sfn "$PWD" /tmp/site/persecutio && python3 -m http.server 8000 --directory /tmp/site`.

## Contributing

1. Add or edit a country in `scripts/collect_data.py` (`COUNTRIES_DATA`), including `source_ids`. Feeds can also create auto-tracked stub pages when a known country appears in incident data without a curated entry.
2. Add a source entry in the `sources` dict in the same file (or extend a `scripts/fetch_*.py` / `rss_news_fetcher` wrapper). Enrichment logic lives in `scripts/collect_enrich.py`.
3. Run collect → generate → pytest.
4. Open a PR with the regenerated YAML/HTML/JSON when appropriate.

Prefer `python3 -m pytest tests` over the legacy `scripts/verify.py` helper.

## Workflow

[`.github/workflows/update.yml`](.github/workflows/update.yml) runs **daily** at 06:00 UTC (`cron: '0 6 * * *'`) and on `workflow_dispatch`. It fetches sources, collects, generates, tests, commits data updates to `main` (schedule/dispatch), and deploys the public site to the `gh-pages` branch.

[`.github/workflows/pages.yml`](.github/workflows/pages.yml) redeploys committed public files to `gh-pages` on pushes to `main` that touch site paths (so HTML/docs merges go live without waiting for the daily fetch).

Only **primary** fetch failures abort before generate/deploy. Secondary fetches use `|| true` and never block the job. The Pages artifact is staged from public site files only (`index.html`, `about.html`, `faq.html`, `countries/`, `assets/`) — not `data/fetched/` scrape caches.

**Live site:** https://rinchen.github.io/persecutio/

### PR previews

Same-repo pull requests get a sticky comment with a live preview URL under `/pr-preview/pr-{N}/` (see [`.github/workflows/preview.yml`](.github/workflows/preview.yml)). Previews stage the PR’s public site files, rewrite absolute `/persecutio/…` links for the preview subpath, and are removed when the PR closes. Fork PRs do not get automatic previews — serve locally with `python3 -m http.server`. Preview URLs share the production GitHub Pages origin — treat them as **untrusted** until you review the PR.

**One-time setup** (after the first `gh-pages` deploy succeeds):

1. **Settings → Pages → Build and deployment → Source:** Deploy from a branch → `gh-pages` / `/` (not “GitHub Actions”, and not `main`).
2. **Settings → Actions → General → Workflow permissions:** Read and write permissions.
