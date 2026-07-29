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

Public definitions also appear on [about.html](about.html). Keep About’s Quality column in sync whenever sources change. Act’s evaluated table uses the same scale.

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

## Research, cite, and document (mandatory)

Before wiring a feed, recommending an org, or asserting a factual claim on FAQ / Act / About / country pages:

1. **Cite every external claim** — Working source URLs in the page’s Sources list (or equivalent). Same honesty bar as [act.html](act.html) “Sources and citations” and [faq.html](faq.html) Sources. Do not invent statistics.
2. **Research candidates against project criteria** — Apply the Source reuse model, Quality tiers, and (for giving / action / org pointers) Act’s “How we chose this short list” / red-flag bar. Do not list orgs or wire feeds from name recognition alone.
3. **Document everything evaluated** — For each candidate considered (wired, linked, deferred, or rejected), record **Quality (A/B/C/Infra/X)** and a short **justification** in the public table that owns that decision:
   - Data / news / FoRB feeds → [about.html](about.html) used or unused
   - Act / giving / civic / org CTAs → [act.html](act.html) listed cards or Evaluated-but-not-listed
   - FAQ reader pointers that are not pipeline sources → list on FAQ; rejected siblings → Act evaluated table
4. Skipping documentation is **not** allowed even when the decision is “do not use.”

## Mission fit — trafficking

Christian or religious persons as trafficking / forced-labor / forced-marriage **victims** is mission-fit FoRB harm (victim-scoped path in [`scripts/christian_persecution.py`](scripts/christian_persecution.py) `is_christian_trafficking_victim`). Church or secular anti-trafficking advocacy without Christian/religious victims is **not** persecution content for the news filter. Do **not** add bare `trafficking` to `HARM_MARKERS` (that would let high-trust feeds pass on trafficking alone and accept advocacy pieces).

## Checklist — evaluating a new source

1. **Terms** — Find copyright / permissions URL. Decide citation-only vs archive-eligible (NOTICE bar).
2. **Fit** — Christian persecution / FoRB country documentation? Mission-unfit → tier X on About unused. Trafficking counts only with Christian/religious **victims** (see above).
3. **Fetch surface** — RSS, Atom, HTML listing, or API? Prefer `scripts/rss_news_fetcher.py` or `parse_html_news_listing` patterns under `scripts/fetch_*.py`.
4. **Filter** — Reuse `is_christian_persecution` / high-trust flags so non-FoRB noise stays out.
5. **Citation bucket** — Org-index and news-org homepage ids go in `source_ids.indicators` via `GLOBAL_INDICATOR_SOURCE_IDS` (never the Modern-Day Situation Sources line unless empty-modern fallback). Country dossiers stay in `modern`.
6. **Wire** — Add the source to [`scripts/source_registry.py`](scripts/source_registry.py) (fetch script, RSS, footer chip, quality, tier). Keep `.github/workflows/update.yml` fetch steps and the About used/unused Quality row in sync (registry sync tests cover the Python-side maps). `data/sources.yml` is **generated** by collect — do not hand-edit it as an input.
7. **Populate** — Run the new fetcher(s) + collect/enrich + generate and **commit** `data/countries.yml` / `countries/*.html` / `data/sources.yml` before calling the work done. `data/fetched/` is gitignored.
8. **Unused / evaluated** — If rejected or not wireable, add the About unused or Act evaluated row with Quality and justification; no fetcher until a surface exists. Documenting the rejection is part of finishing the work.

## Pointers

- Source registry: [scripts/source_registry.py](scripts/source_registry.py)
- Archive terms: [data/archives/NOTICE](data/archives/NOTICE)
- Used / unused tables: [about.html](about.html)
- Act CTAs / evaluated orgs: [act.html](act.html)
- Fetch scripts: [scripts/fetch_*.py](scripts/), [scripts/rss_news_fetcher.py](scripts/rss_news_fetcher.py)
- Citation buckets: [scripts/country_registry.py](scripts/country_registry.py) (`attach_citation`, `reconcile_citation_buckets`)
- Primary CI gate: [scripts/check_primary_status.py](scripts/check_primary_status.py)
