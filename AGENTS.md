# Agent notes — persecutio

Short guidance for agents working in this repo. Pipeline details live in [README.md](README.md).

## Source reuse model

Two gates — do not collapse them:

| Gate | Meaning | Bar |
|------|---------|-----|
| **Citation / secondary fetch** | Link + short attributed excerpt on country pages | All-rights-reserved OK if we only cite/link (same tier as Freedom House, Morning Star News) |
| **Archive** (`data/archives/`) | Committed redistributable extracts | Only sources in [data/archives/NOTICE](data/archives/NOTICE): U.S. gov works, Open Doors free-use-with-©, V-Dem **CC BY-SA**. No NC/ND licenses. |

CC BY-NC-ND (e.g. HRW, Amnesty) → citation secondary **yes**, archive **no**.

Corroborating sources that cover the same country or incident are welcome. **Do not reject a lawful FoRB source only because another source already covers it.**

## Quality tiers (A / B / C / Infra / X)

Public definitions also appear on [about.html](about.html). Keep About’s Quality column in sync whenever sources change.

| Tier | Meaning | Action |
|------|---------|--------|
| **A** | Strong Christian-persecution / FoRB fit; reliable fetch; clear link+excerpt (or better) license; high signal for country pages | Prefer; wire first |
| **B** | Useful supporting source (broader indexes, demography, solid but less central FoRB feeds) | Wire after A |
| **C** | Supplementary / noisier (general news, wide aggregators, sparse feeds); still lawful to cite | Wire last; skip only if fetch impossible |
| **Infra** | Not FoRB content (e.g. map boundaries) | Keep; not a content-quality score |
| **X** | Do not use — legal block, defunct/no feed, proprietary data ban, or mission-unfit | About “unused” only; no fetcher |
| **A/B/C on unused** | Content could fit, but not wired (e.g. bot-blocked / no nightly surface) | About “unused” with A/B/C Quality + ops reason; revisit if a feed appears |

**Score on:** mission fit, license gate, fetchability, provenance, coverage usefulness, ops risk.  
**Do not** down-tier to X for overlap alone.

## Checklist — evaluating a new source

1. **Terms** — Find copyright / permissions URL. Decide citation-only vs archive-eligible (NOTICE bar).
2. **Fit** — Christian persecution / FoRB country documentation? Mission-unfit → tier X on About unused.
3. **Fetch surface** — RSS, Atom, HTML listing, or API? Prefer `scripts/rss_news_fetcher.py` or `parse_html_news_listing` patterns under `scripts/fetch_*.py`.
4. **Filter** — Reuse `is_christian_persecution` / high-trust flags so non-FoRB noise stays out.
5. **Citation bucket** — Org-index and news-org homepage ids go in `source_ids.indicators` via `GLOBAL_INDICATOR_SOURCE_IDS` (never the Modern-Day Situation Sources line unless empty-modern fallback). Country dossiers stay in `modern`.
6. **Wire** — Add the source to [`scripts/source_registry.py`](scripts/source_registry.py) (fetch script, RSS, footer chip, quality, tier). Keep `.github/workflows/update.yml` fetch steps and the About used/unused Quality row in sync (registry sync tests cover the Python-side maps). `data/sources.yml` is **generated** by collect — do not hand-edit it as an input.
7. **Populate** — Run the new fetcher(s) + collect/enrich + generate and **commit** `data/countries.yml` / `countries/*.html` / `data/sources.yml` before calling the work done. `data/fetched/` is gitignored.
8. **Unused** — If rejected or not wireable, add an About unused row with Quality (**X** for legal/mission/permanent ops block; **A/B/C** when content fits but fetch is impossible for now) and reason; no fetcher until a surface exists.

## Pointers

- Source registry: [scripts/source_registry.py](scripts/source_registry.py)
- Archive terms: [data/archives/NOTICE](data/archives/NOTICE)
- Used / unused tables: [about.html](about.html)
- Fetch scripts: [scripts/fetch_*.py](scripts/), [scripts/rss_news_fetcher.py](scripts/rss_news_fetcher.py)
- Citation buckets: [scripts/country_registry.py](scripts/country_registry.py) (`attach_citation`, `reconcile_citation_buckets`)
- Primary CI gate: [scripts/check_primary_status.py](scripts/check_primary_status.py)
