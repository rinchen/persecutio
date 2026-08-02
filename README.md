# Persecutio

Static site documenting Christian persecution by country, served via GitHub Pages (and mirrored on Nostr via nsite) and updated automatically by GitHub Actions.

## Architecture

```
scripts/fetch_*.py           →  data/fetched/            (recurring feeds, gitignored)
scripts/archive_download.py  →  data/archives/           (one-time report snapshot)
scripts/archive_extract.py   →  data/archives/extracted/countries.json
        ↓
scripts/collect_data.py (+ collect_enrich.py, country_registry.py)
        →  data/countries.yml, data/sources.yml
        ↓
scripts/generate_website_data.py  →  countries/*.html, assets/data/{geojson,search,meta}.json
        ↓
GitHub Pages (public HTML/CSS/JS only — scrape caches are not published)
        ↓
Nostr / nsite (same public files, after successful Pages deploy)
```

`scripts/country_registry.py` is the canonical list of tracked countries: display titles, aliases used to match free text, ISO3 codes, and map coordinates. Fetchers derive their target lists from it (for example `fetch_state_dept.py`) instead of keeping hand-maintained subsets.

Curated country narratives live in `scripts/collect_data.py` (`COUNTRIES_DATA`, currently one entry per registry country). Fetch scripts enrich metadata (scores, incidents, news). Helpers in `collect_enrich.py`, `rss_news_fetcher.py`, and `christian_persecution.py` merge feeds, filter articles, and auto-create stub country pages when feeds mention a registry country without a curated entry. `scripts/urls.py` allowlists http(s) URLs for both fetch construction and HTML rendering. The generator builds HTML pages and JSON for the map/search UI.

## Data outputs

- `data/countries.yml` / `data/sources.yml` — structured country and source records
- `data/archives/extracted/countries.json` — excerpts and indicators derived from archived reports
- `assets/data/geojson.json` — map markers
- `assets/data/search.json` — Lunr search index input
- `assets/data/meta.json` — source status chips for the map footer
- `countries/*.html` — per-country pages (70, one per registry country)

Collect and generate keep the five most recent `.bak-*` snapshots of `data/countries.yml` and the `assets/data/*.json` files. They are gitignored and stripped from the published site.

## Sources

Pipeline sources (status chips on the map footer):

**Primary** (fetch failure aborts generate/deploy): Open Doors (OD), Freedom House (FH), Our World in Data (OWID), USCIRF (UC), U.S. State Dept IRF (SD).

**Secondary** (enrich when available; never abort deploy): Morning Star News, GDELT, OHCHR, VID, GCR, ACN, CSW, ICC, Forum 18, MEC, Bitter Winter, Release International, VOM, ChinaAid, Info Chrétienne, OSCE/ODIHR, UNSR FoRB, HRW, Amnesty, Barnabas Aid, CSI, CNA, Fides, ACI Prensa, HRWF, ADF, WEA, Jubilee Campaign, IPPFoRB. Full quality tiers and links: [about.html](about.html).

**Archived** (snapshotted once, not fetched by the daily job): V-Dem FoRB indicators (VD), plus State Dept IRF, USCIRF, and Open Doors report text under `data/archives/`.

Also cited on pages / chips: Pew, BBC, Natural Earth (NE). Wikipedia summaries are fetched during collect for enrichment.

Quality tiers (A / B / C / Infra / X) are defined in [AGENTS.md](AGENTS.md) and on the About page.

## Archived reports

`data/archives/` holds a one-time snapshot of legally redistributable source material. `collect_enrich.py` reads `extracted/countries.json` from it to fill thin or stub narratives with short excerpts and to attach V-Dem freedom-of-religion indicators.

Large binaries (report PDFs, HTML mirrors, the V-Dem zip) are gitignored. Committed artifacts are `NOTICE`, `manifest.json`, per-country JSON extracts, `extracted/countries.json`, and the V-Dem FoRB CSV/JSON subset. Rebuild the ignored inputs with:

```bash
python3 scripts/archive_download.py
python3 scripts/archive_extract.py
```

Per-source redistribution terms are recorded in [`data/archives/NOTICE`](data/archives/NOTICE).

## Requirements

Python **3.12+** (CI runs 3.12). Dependencies are pinned in `requirements.txt`: `pyyaml`, `openpyxl` (Freedom House workbooks), `pypdf` (archived report PDFs), `defusedxml` (RSS), and `pytest`.

```bash
python3 -m pip install -r requirements.txt
```

Or create/refresh a local virtualenv at `.venv`:

```bash
./scripts/update_deps.sh
```

Vendored Leaflet/Lunr versions: [`assets/vendor/VERSIONS`](assets/vendor/VERSIONS).
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

1. Register the country in `scripts/country_registry.py` (`KNOWN_COUNTRIES`, aliases, `COUNTRY_GEO`) if it is not already tracked.
2. Add or edit the country in `scripts/collect_data.py` (`COUNTRIES_DATA`), including `source_ids`.
3. Add the source to `scripts/source_registry.py` (fetch script, RSS, footer chip, quality tier, primary/secondary). Wire the fetcher under `scripts/fetch_*.py` if it is not a thin RSS wrapper.
4. Update `.github/workflows/update.yml` fetch list if the registry does not yet drive CI steps, and add an About used/unused row (keep Quality in sync).
5. Run collect → generate → pytest. Note: `data/sources.yml` is **generated** by collect (not hand-edited).
6. Open a PR with the regenerated YAML/HTML/JSON when appropriate.

See [AGENTS.md](AGENTS.md) for the full source-evaluation checklist.

Prefer `python3 -m pytest tests` (also runs on pull requests via `.github/workflows/test.yml`).

## Workflow

[`.github/workflows/update.yml`](.github/workflows/update.yml) runs **daily** at 06:00 UTC (`cron: '0 6 * * *'`) and on `workflow_dispatch`. It fetches sources, collects, generates, tests, commits data updates to `main` (schedule/dispatch), and deploys the public site to the `gh-pages` branch.

[`.github/workflows/pages.yml`](.github/workflows/pages.yml) redeploys committed public files to `gh-pages` on pushes to `main` that touch site paths (so HTML/docs merges go live without waiting for the daily fetch).

Only **primary** fetch failures abort before generate/deploy. Secondary fetches use `|| true` and never block the job. After generate, the job also enforces structural checks: the country page count must equal the geojson feature count, and every page must carry Historical Background, Modern-Day Situation, an All References section, and at least one source link. The Pages artifact is staged from public site files only (`index.html`, `about.html`, `faq.html`, `LICENSE`, `countries/`, `assets/`) — not `data/fetched/` scrape caches or `.bak-*` snapshots.

**Live site:** https://rinchen.github.io/persecutio/

**Nostr / nsite mirror** (same content; republished after successful Pages deploys via [`.github/workflows/nostr-deploy.yml`](.github/workflows/nostr-deploy.yml)):

- Gateway: https://2vu4veopeh8g2tkli0pmbu2gtrmcicht56a5k9edx63jy6l7tcpersecutio.nsite.lol/
- NIP-05A address (clients with nsite support): `naddr1qvzqqqyf8qpzqua6pgsfdufl97frsalzalnedutx94revzz4m47pgd2qtq28txxsqq98qetjwdjkxat5d9hs2c44ed`
- Signing uses a NIP-46 bunker via repo secret `NBUNK_SECRET` (`nbunksec1…` from `nsyte ci`). Keep the bunker app awake and connected to the relays embedded in that credential. The workflow diagnoses the secret (non-secret hygiene + bunker relay probes), then retries transient bunker/network timeouts for up to ~15 minutes (nsyte’s NIP-46 connect wait is a hard 30s per attempt). Flaky bunker relays may deliver the request to the bunker while dropping or delaying the response — the bunker app can show the request even when CI times out. Permanent credential errors fail fast. Manual republish: Actions → **Deploy to Nostr** → Run workflow.

### PR previews

Same-repo pull requests get a sticky comment with a live preview URL under `/pr-preview/pr-{N}/` (see [`.github/workflows/preview.yml`](.github/workflows/preview.yml)). Previews stage the PR’s public site files, rewrite absolute `/persecutio/…` links for the preview subpath, and are removed when the PR closes. Fork PRs do not get automatic previews — serve locally with `python3 -m http.server`. Preview URLs share the production GitHub Pages origin — treat them as **untrusted** until you review the PR.

**One-time setup** (after the first `gh-pages` deploy succeeds):

1. **Settings → Pages → Build and deployment → Source:** Deploy from a branch → `gh-pages` / `/` (not “GitHub Actions”, and not `main`).
2. **Settings → Actions → General → Workflow permissions:** Read and write permissions.
