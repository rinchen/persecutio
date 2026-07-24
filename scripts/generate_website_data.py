import html
import json
import re
from pathlib import Path

import yaml

from archive_text import (
    DEFAULT_IRF_LIMIT,
    DEFAULT_OD_LIMIT,
    DEFAULT_USCIRF_LIMIT,
    clean_archive_text,
    clip_at_sentence,
    is_usable_archive_excerpt,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
COUNTRIES = ROOT / "countries"
ASSETS = ROOT / "assets" / "data"
DATA.mkdir(parents=True, exist_ok=True)
COUNTRIES.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

SLUG_RE = re.compile(r"^[a-z0-9-]+$")

PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="theme-color" content="#0b132b" />
  <title>{title} | Christian Persecution World Map</title>
  <link rel="icon" href="/persecutio/assets/img/favicon.svg" type="image/svg+xml" />
  <link rel="icon" href="/persecutio/assets/img/favicon-32x32.png" type="image/png" sizes="32x32" />
  <link rel="stylesheet" href="../assets/css/main.css" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'" />
  <meta http-equiv="X-Content-Type-Options" content="nosniff" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to content</a>
  <header>
    <div class="wrap">
      <a class="brand" href="/persecutio/index.html">Christian Persecution World Map</a>
      <nav>
        <a href="/persecutio/index.html">Map</a>
        <a href="/persecutio/faq.html">FAQ</a>
        <a href="/persecutio/about.html">About</a>
        <a
          class="site-nav-github"
          href="https://github.com/rinchen/persecutio"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Persecutio on GitHub (opens in new tab)"
        >
          <svg
            class="site-nav-github-icon"
            viewBox="0 0 16 16"
            width="18"
            height="18"
            aria-hidden="true"
            focusable="false"
          >
            <path
              fill="currentColor"
              d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8"
            />
          </svg>
        </a>
      </nav>
    </div>
  </header>
  <main id="main-content" tabindex="-1">
    <div class="card">
      <div class="country-hero" data-status="{status_key}">
        <div class="top">
          <h1>{title}</h1>
        </div>
        <div class="status-pill">
          <span class="pct" style="background:{status_color}"></span>
          <span>{persecution_level} · {status_label}</span>
        </div>{stub_note}
        {data_fields}
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
      {archive_notes}
      {recent_incidents}
      <section>
        <h2>All References</h2>
        <ul>
          {all_sources}
        </ul>
      </section>
    </div>
  </main>
  <footer class="site-footer">
    <p id="data-updated">Loading data freshness…</p>
    <div id="data-sources" class="site-footer__sources" hidden></div>
  </footer>
  <button id="back-to-top" class="back-to-top" aria-label="Back to top">&uarr;</button>
  <script src="../assets/js/sources.js" defer data-meta="../assets/data/meta.json"></script>
  <script src="../assets/js/back-to-top.js" defer></script>
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

SOURCE_GROUP_DEFS = {
    "uscirf": {"prefixes": ("uscirf",), "label": "UC", "title": "USCIRF Annual Reports"},
    "opendoors": {"prefixes": ("odwwl",), "label": "OD", "title": "Open Doors World Watch List"},
    "pew": {"prefixes": ("pew",), "label": "Pew", "title": "Pew Research"},
    "natural_earth": {"prefixes": ("natural_earth",), "label": "NE", "title": "Natural Earth map boundaries"},
    "freedomhouse": {"prefixes": ("freedomhouse",), "label": "FH", "title": "Freedom House Freedom in the World"},
    "statedepartment": {"prefixes": ("statedepartment",), "label": "SD", "title": "U.S. State Dept IRF Reports"},
    "ohchr": {"prefixes": ("ohchr",), "label": "OHCHR", "title": "OHCHR Universal Human Rights Index"},
    "vdem": {"prefixes": ("vdem",), "label": "VD", "title": "V-Dem FoRB Indicators"},
    "gdelt": {"prefixes": ("gdelt",), "label": "GDELT", "title": "GDELT Global Database of Events"},
    "owid": {"prefixes": ("owid",), "label": "OWID", "title": "Our World in Data - Religious Composition"},
    "acn": {"prefixes": ("acn",), "label": "ACN", "title": "ACN Persecuted and Forgotten"},
    "bbc": {"prefixes": ("bbc",), "label": "BBC", "title": "BBC News"},
    "morningstarnews": {"prefixes": ("morningstarnews",), "label": "MSN", "title": "Morning Star News"},
    "vid": {"prefixes": ("vid",), "label": "VID", "title": "Violent Incidents Database"},
    "gcr": {"prefixes": ("gcr",), "label": "GCR", "title": "Global Christian Relief"},
    "csw": {"prefixes": ("csw",), "label": "CSW", "title": "Christian Solidarity Worldwide"},
    "icc": {"prefixes": ("icc",), "label": "ICC", "title": "International Christian Concern"},
    "forum18": {"prefixes": ("forum18",), "label": "F18", "title": "Forum 18"},
    "mec": {"prefixes": ("mec",), "label": "MEC", "title": "Middle East Concern"},
    "bitterwinter": {"prefixes": ("bitterwinter",), "label": "BW", "title": "Bitter Winter"},
    "releaseintl": {"prefixes": ("releaseintl",), "label": "RI", "title": "Release International"},
}

STATUS_PRIORITY = {"error": 0, "failed": 0, "partial": 1, "skipped": 2, "ok": 3, "cached": 4}

STATUS_KEY_MAP = {
    "uscirf": "uscirf",
    "opendoors": "opendoors",
    "pew": None,
    "natural_earth": "natural_earth_110m",
    "freedomhouse": "freedomhouse",
    "statedepartment": "statedepartment",
    "ohchr": "ohchr",
    "gdelt": "gdelt",
    "owid": "owid",
    "acn": "acn",
    "morningstarnews": "morningstarnews",
    "vid": "vid",
    "gcr": "gcr",
    "csw": "csw",
    "icc": "icc",
    "forum18": "forum18",
    "mec": "mec",
    "bitterwinter": "bitterwinter",
    "releaseintl": "releaseintl",
    "bbc": None,
}

# Chip CSS uses --error; fetch scripts report "failed". Map for display.
STATUS_DISPLAY = {"failed": "error"}


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def clip_text(text: str, limit: int) -> tuple[str, bool]:
    """Truncate at a sentence boundary; fall back to a word boundary + ellipsis."""
    return clip_at_sentence(text, limit)


def render_archive_more(url: str | None, label: str) -> str:
    href = safe_url(url, fallback="")
    if not href:
        return ""
    return (
        f' <a class="archive-more" href="{href}" target="_blank" rel="noopener">'
        f"{esc(label)}</a>"
    )


def render_archive_notes(country: dict) -> str:
    """Short excerpts from archived IRF/OD/USCIRF reports (not full republication)."""
    meta = country.get("metadata") or {}
    bits = []
    modern = country.get("modern") or ""

    od_brief = clean_archive_text(meta.get("archive_od_brief") or "")
    if od_brief and is_usable_archive_excerpt(od_brief) and od_brief[:80] not in modern:
        excerpt, truncated = clip_text(od_brief, DEFAULT_OD_LIMIT)
        more = ""
        if truncated or meta.get("archive_od_url"):
            more = render_archive_more(
                meta.get("archive_od_url"), "Read full Open Doors dossier"
            )
        bits.append(
            "<p><strong>Open Doors research note:</strong> "
            f"{esc(excerpt)}"
            f"{more}"
            ' <span class="archive-attr">(© Open Doors International)</span></p>'
        )

    sd = clean_archive_text(meta.get("state_dept_executive_summary") or "")
    if sd and is_usable_archive_excerpt(sd) and sd[:80] not in modern and len(bits) < 2:
        excerpt, truncated = clip_text(sd, DEFAULT_IRF_LIMIT)
        more = ""
        if truncated or meta.get("state_dept_url"):
            more = render_archive_more(meta.get("state_dept_url"), "Read full IRF report")
        bits.append(
            "<p><strong>U.S. State Department IRF excerpt:</strong> "
            f"{esc(excerpt)}{more}</p>"
        )

    findings = meta.get("uscirf_key_findings") or []
    if findings and len(bits) < 2:
        first = clean_archive_text(str(findings[0]))
        if first and is_usable_archive_excerpt(first) and first[:80] not in modern:
            excerpt, truncated = clip_text(first, DEFAULT_USCIRF_LIMIT)
            more = ""
            if truncated or meta.get("uscirf_url"):
                more = render_archive_more(
                    meta.get("uscirf_url"), "Read USCIRF country page"
                )
            bits.append(
                f"<p><strong>USCIRF finding:</strong> {esc(excerpt)}{more}</p>"
            )
    if not bits:
        return ""
    body = "\n        ".join(bits)
    return (
        '<section class="archive-notes">\n'
        "        <h2>From archived reports</h2>\n"
        f"        {body}\n"
        "      </section>"
    )


def safe_url(url: str | None, fallback: str = "#") -> str:
    """Allow only http(s) URLs; reject javascript:/data:/etc. HTML-escaped for attributes."""
    from urls import safe_url as _safe

    return esc(_safe(url, fallback))


def valid_slug(slug: str) -> bool:
    return bool(slug) and bool(SLUG_RE.fullmatch(slug))


def render_sources(source_ids: list[str], all_sources_lookup: dict) -> str:
    items = []
    for sid in source_ids:
        s = all_sources_lookup.get(sid)
        if not s:
            continue
        label = esc(s.get("title", sid))
        url = safe_url(s.get("url"))
        date = s.get("date", "")
        prefix = f"({esc(date)}) " if date else ""
        items.append(f'<a href="{url}">{prefix}{label}</a>')
    return "; ".join(items) if items else "Sources will be listed here."


def linked_data_value(text: str, url: str | None) -> str:
    """Wrap header data in a source link only when a direct http(s) URL exists."""
    href = safe_url(url, fallback="")
    if not href:
        return text
    return f'<a href="{href}" target="_blank" rel="noopener">{text}</a>'


def render_data_fields(country: dict) -> str:
    meta = country.get("metadata", {})
    items = []
    # Direct country-specific source URLs only (leave fields unlinked when absent).
    od_url = meta.get("archive_od_url")
    uscirf_url = meta.get("uscirf_url")
    od_score = meta.get("opendoors_score")
    od_rank = meta.get("opendoors_ranking")
    if od_score is not None:
        items.append(
            f'<div class="data-item"><div class="label">Open Doors Score</div>'
            f'<div class="value">{linked_data_value(f"{esc(od_score)}/100", od_url)}</div></div>'
        )
    if od_rank is not None:
        items.append(
            f'<div class="data-item"><div class="label">WWL Ranking</div>'
            f'<div class="value">{linked_data_value(f"#{esc(od_rank)}", od_url)}</div></div>'
        )
    fh_status = meta.get("freedom_house_status")
    if fh_status:
        items.append(
            f'<div class="data-item"><div class="label">Freedom House</div>'
            f'<div class="value">{esc(fh_status)}</div></div>'
        )
    fh_pr = meta.get("freedom_house_pr")
    fh_cl = meta.get("freedom_house_cl")
    if fh_pr is not None and fh_cl is not None:
        items.append(
            f'<div class="data-item"><div class="label">PR / CL Score</div>'
            f'<div class="value">{esc(fh_pr)} / {esc(fh_cl)}</div></div>'
        )
    christ_pop = meta.get("christian_population")
    christ_pct = meta.get("christian_percentage")
    if christ_pop is not None:
        pop_str = f"{christ_pop:,}" if isinstance(christ_pop, (int, float)) else str(christ_pop)
        pct_str = f" ({christ_pct:.1f}%)" if isinstance(christ_pct, (int, float)) else ""
        items.append(
            f'<div class="data-item"><div class="label">Christian Population</div>'
            f'<div class="value">{esc(pop_str)}{esc(pct_str)}</div></div>'
        )
    gdelt_count = meta.get("gdelt_recent_articles")
    if gdelt_count is not None:
        items.append(
            f'<div class="data-item"><div class="label">Recent News Events</div>'
            f'<div class="value">{esc(gdelt_count)}</div></div>'
        )
    acn_class = meta.get("acn_classification")
    if acn_class:
        items.append(
            f'<div class="data-item"><div class="label">ACN Classification</div>'
            f'<div class="value">{esc(acn_class)}</div></div>'
        )
    vid_total = meta.get("vid_incidents_total")
    if vid_total is not None:
        items.append(
            f'<div class="data-item"><div class="label">VID Incidents</div>'
            f'<div class="value">{esc(vid_total)}</div></div>'
        )
    vid_killings = meta.get("vid_killings")
    if vid_killings is not None:
        items.append(
            f'<div class="data-item"><div class="label">VID Killings</div>'
            f'<div class="value">{esc(vid_killings)}</div></div>'
        )
    gcr_killed = meta.get("gcr_killed")
    if gcr_killed:
        items.append(
            f'<div class="data-item"><div class="label">GCR Killed</div>'
            f'<div class="value">{esc(gcr_killed)}</div></div>'
        )
    gcr_score = meta.get("gcr_persecution_score")
    if gcr_score:
        items.append(
            f'<div class="data-item"><div class="label">GCR Persecution Score</div>'
            f'<div class="value">{esc(gcr_score)}</div></div>'
        )
    uscirf_des = meta.get("uscirf_designation")
    if uscirf_des:
        items.append(
            f'<div class="data-item"><div class="label">USCIRF Designation</div>'
            f'<div class="value">{linked_data_value(esc(uscirf_des), uscirf_url)}</div></div>'
        )
    if meta.get("state_dept_url"):
        items.append(
            f'<div class="data-item"><div class="label">U.S. State Dept IRF</div>'
            f'<div class="value"><a href="{safe_url(meta.get("state_dept_url"))}" '
            f'target="_blank" rel="noopener">Report</a></div></div>'
        )
    ohchr_count = meta.get("ohchr_recommendation_count")
    if ohchr_count is not None:
        items.append(
            f'<div class="data-item"><div class="label">OHCHR Recommendations</div>'
            f'<div class="value">{esc(ohchr_count)}</div></div>'
        )
    vdem_relig = meta.get("vdem_freedom_of_religion")
    if vdem_relig is not None:
        year = meta.get("vdem_year")
        year_s = f" ({int(year)})" if isinstance(year, (int, float)) else ""
        items.append(
            f'<div class="data-item"><div class="label">V-Dem Freedom of Religion{esc(year_s)}</div>'
            f'<div class="value">{esc(vdem_relig)}</div></div>'
        )
    vdem_repr = meta.get("vdem_religious_org_repression")
    if vdem_repr is not None:
        items.append(
            f'<div class="data-item"><div class="label">V-Dem Rel. Org. Repression</div>'
            f'<div class="value">{esc(vdem_repr)}</div></div>'
        )
    if not items:
        return ""
    joined = "\n          ".join(items)
    return f'<div class="data-grid">\n          {joined}\n        </div>'


def render_stub_note(country: dict) -> str:
    meta = country.get("metadata") or {}
    if not meta.get("stub"):
        return ""
    return (
        '\n        <p class="stub-note"><em>Auto-tracked</em> — this country page was created from '
        "nightly Christian persecution feeds. Editorial narrative is pending; "
        "indicators and incident links reflect ingested sources.</p>"
    )


def _incident_rows(articles: list[dict]) -> str:
    rows = []
    for a in articles:
        href = safe_url(a.get("url"))
        title = esc(a.get("title") or "Report")
        src = esc(a.get("source", ""))
        date = esc(a.get("date", ""))
        rows.append(
            f'<div class="incident-item">'
            f'<span class="incident-source">{src}</span> '
            f'<a href="{href}" target="_blank" rel="noopener">{title}</a> '
            f'<span class="incident-date">{date}</span>'
            f"</div>"
        )
    return "\n          ".join(rows)


def render_recent_incidents(country: dict) -> str:
    meta = country.get("metadata", {})
    articles = list(meta.get("recent_incidents") or [])
    historical = list(meta.get("historical_incidents") or [])
    if not articles:
        # Legacy fallback for older YAML
        for sample_key, label in [
            ("morningstarnews_samples", "Morning Star News"),
            ("csw_samples", "CSW"),
            ("icc_samples", "ICC"),
            ("forum18_samples", "Forum 18"),
            ("mec_samples", "Middle East Concern"),
            ("bitterwinter_samples", "Bitter Winter"),
            ("releaseintl_samples", "Release International"),
        ]:
            for a in meta.get(sample_key, []) or []:
                articles.append({
                    "source": label,
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "date": a.get("date", ""),
                })
    if not articles and not historical:
        return ""

    parts: list[str] = []
    if articles:
        joined = _incident_rows(articles)
        parts.append(
            "<section>\n"
            "        <h2>Latest News</h2>\n"
            f'        <div class="incidents-list">\n          {joined}\n        </div>\n'
            "      </section>"
        )
    if historical:
        joined = _incident_rows(historical)
        parts.append(
            '<details class="historical-news">\n'
            "        <summary>Historical News</summary>\n"
            f'        <div class="incidents-list">\n          {joined}\n        </div>\n'
            "      </details>"
        )
    return "\n      ".join(parts)


def assign_source_group(sid: str) -> str:
    for group_key, defn in SOURCE_GROUP_DEFS.items():
        for prefix in defn["prefixes"]:
            if sid.startswith(prefix):
                return group_key
    return sid[:8]


def build_meta_sources(all_sources_lookup: dict, fetched_statuses: list) -> list:
    status_map = {}
    for s in fetched_statuses:
        if isinstance(s, dict) and s.get("name"):
            status_map[s["name"]] = s

    source_groups: dict[str, list[str]] = {}
    for sid in all_sources_lookup:
        group_key = assign_source_group(sid)
        source_groups.setdefault(group_key, []).append(sid)

    meta_sources = []
    for group_key, sids in source_groups.items():
        defn = SOURCE_GROUP_DEFS.get(group_key, {"label": group_key[:6].upper(), "title": group_key})
        worst_status = None
        worst_ts = None
        for sid in sids:
            status_key = STATUS_KEY_MAP.get(group_key, sid)
            fs = status_map.get(status_key) if status_key else None
            if not fs:
                fs = status_map.get(sid)
            if fs:
                st = fs.get("status", "skipped")
                if worst_status is None or STATUS_PRIORITY.get(st, 99) < STATUS_PRIORITY.get(worst_status, 99):
                    worst_status = st
                    worst_ts = fs.get("fetched_at")
        if worst_status is None:
            worst_status = "skipped"
        meta_sources.append({
            "id": group_key,
            "label": defn["label"],
            "title": defn["title"],
            "status": STATUS_DISPLAY.get(worst_status, worst_status),
            "fetchedAt": worst_ts,
        })
    return meta_sources


def main():
    with (DATA / "countries.yml").open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    countries = data.get("countries")
    if not countries:
        raise SystemExit("data/countries.yml is missing or has no 'countries' list")

    source_statuses = data.get("fetched", {}).get("source_statuses") or []

    with (DATA / "sources.yml").open("r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}
    all_sources_lookup = loaded.get("sources") or {}
    if not all_sources_lookup:
        raise SystemExit("data/sources.yml is missing or has no 'sources' mapping")

    meta_sources = build_meta_sources(all_sources_lookup, source_statuses)
    meta = {
        "generatedAt": data.get("fetched", {}).get("generated_at"),
        "sources": meta_sources,
    }
    (ASSETS / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for c in countries:
        if not isinstance(c, dict):
            raise SystemExit("countries.yml contains an invalid non-object country entry")
        title = c.get("title")
        slug = c.get("slug")
        iso3 = str(c.get("iso3", "") or "").upper()
        if not title or not slug or not iso3:
            raise SystemExit(f"Invalid country entry missing title/slug/iso3: {c}")
        if not valid_slug(slug):
            raise SystemExit(f"Invalid country slug (must match [a-z0-9-]+): {slug!r}")
        out_path = (COUNTRIES / f"{slug}.html").resolve()
        if out_path.parent != COUNTRIES.resolve():
            raise SystemExit(f"Refusing to write outside countries/: {out_path}")

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
        all_sources_items = []
        for s in all_sources_lookup.keys():
            if s not in {*hist_ids, *mod_ids}:
                continue
            src = all_sources_lookup[s]
            href = safe_url(src.get("url"))
            src_title = esc(src.get("title", s))
            date = src.get("date", "")
            date_suffix = f" ({esc(date)})" if date else ""
            all_sources_items.append(f'<li><a href="{href}">{src_title}</a>{date_suffix}</li>')
        if not all_sources_items:
            all_sources_items = ["<li>Sources will be listed here.</li>"]

        page_html = PAGE.format(
            title=esc(title),
            historical=esc(c.get("historical", "")),
            modern=esc(c.get("modern", "")),
            historical_sources=historical_sources,
            modern_sources=modern_sources,
            all_sources="\n          ".join(all_sources_items),
            persecution_level=esc(c.get("persecution_level", "")),
            status_key=esc(status or "unknown"),
            status_label=esc(label),
            status_color=esc(color),
            stub_note=render_stub_note(c),
            data_fields=render_data_fields(c),
            archive_notes=render_archive_notes(c),
            recent_incidents=render_recent_incidents(c),
        )
        out_path.write_text(page_html, encoding="utf-8")
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
    (ASSETS / "search.json").write_text(
        json.dumps(
            [{"slug": c["slug"], "title": c["title"], "country": c["title"]} for c in countries],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("generated plain-static files")


if __name__ == "__main__":
    main()
