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
from country_registry import dedupe_source_ids_by_url
from source_registry import footer_groups, status_key_map

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
  <meta name="theme-color" content="#13327c" />
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
        <a href="/persecutio/act.html">Act</a>
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
      <a class="back-link back-link--top" href="/persecutio/index.html">&larr; Back to map</a>
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
        <div class="prose"><p>{historical}</p></div>
        <div class="section-sources"><strong>Sources:</strong> {historical_sources}</div>
      </section>
      <section>
        <h2>Modern-Day Situation</h2>
        <div class="prose"><p>{modern}</p></div>
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

SOURCE_GROUP_DEFS = footer_groups()

STATUS_PRIORITY = {"error": 0, "failed": 0, "stale": 0, "partial": 1, "skipped": 2, "ok": 3, "cached": 4}

STATUS_KEY_MAP = status_key_map()

# Chip CSS uses --error; fetch scripts report "failed". Map for display.
STATUS_DISPLAY = {"failed": "error", "stale": "error"}


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


def resolve_page_source_ids(slug: str, source_ids: dict) -> tuple[list[str], list[str]]:
    """Return (historical, modern) citation ids for a page, or fail the build.

    A country with an empty section used to fall back to citing every source in the
    repository, producing pages that listed hundreds of unrelated references. Each page
    must carry its own sources instead, so an empty section is a hard error.
    Indicator/org-index cites live in source_ids.indicators and are not required here.
    """
    hist_ids = source_ids.get("historical", []) or []
    mod_ids = source_ids.get("modern", []) or []
    if not hist_ids or not mod_ids:
        raise SystemExit(
            f"Country {slug!r} has empty source_ids "
            f"(historical={len(hist_ids)}, modern={len(mod_ids)}); "
            "every page must cite its own sources"
        )
    return hist_ids, mod_ids


def render_sources(source_ids: list[str], all_sources_lookup: dict) -> str:
    items = []
    for sid in dedupe_source_ids_by_url(list(source_ids), all_sources_lookup):
        s = all_sources_lookup.get(sid)
        if not s:
            continue
        label = esc(s.get("title", sid))
        url = safe_url(s.get("url"))
        date = s.get("date", "")
        prefix = f"({esc(date)}) " if date else ""
        items.append(f'<a href="{url}">{prefix}{label}</a>')
    return "; ".join(items) if items else "Sources will be listed here."


def collect_all_reference_ids(source_ids: dict) -> list[str]:
    """Union of historical, modern, and indicators citation ids (order preserved)."""
    out: list[str] = []
    for bucket in ("historical", "modern", "indicators"):
        for sid in source_ids.get(bucket) or []:
            if sid not in out:
                out.append(sid)
    return out


def linked_data_value(text: str, url: str | None) -> str:
    """Wrap header data in a source link only when a direct http(s) URL exists."""
    href = safe_url(url, fallback="")
    if not href:
        return text
    return f'<a href="{href}" target="_blank" rel="noopener">{text}</a>'


def _lucide_svg(inner: str) -> str:
    return (
        '<svg class="lucide-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
        f"{inner}</svg>"
    )


# Lucide path markup (inline; no JS dependency). Keys match field roles.
ICON_SVGS = {
    "opendoors_score": _lucide_svg(
        '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 '
        '1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
    ),
    "opendoors_ranking": _lucide_svg(
        '<path d="M10 6h11"/><path d="M10 12h11"/><path d="M10 18h11"/>'
        '<path d="M4 6h1v4"/><path d="M4 10h2"/><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"/>'
    ),
    "freedom_house": _lucide_svg(
        '<path d="M10 18v-7"/><path d="M11.12 2.198a2 2 0 0 1 1.76.006l7.866 3.805a1 1 0 0 1 .01 1.794L12.9 10.2a2 2 0 0 1-1.8 0L3.234 7.803a1 1 0 0 1 .01-1.794z"/>'
        '<path d="M14 18v-7"/><path d="M6 18v-5"/><path d="M18 18v-5"/><path d="M2 22h20"/>'
    ),
    "pr_cl": _lucide_svg(
        '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>'
        '<path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>'
        '<path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>'
    ),
    "christian_population": _lucide_svg(
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
    ),
    "acn": _lucide_svg(
        '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>'
        '<line x1="4" x2="4" y1="22" y2="15"/>'
    ),
    "vid_incidents": _lucide_svg(
        '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 '
        '0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>'
    ),
    "vid_killings": _lucide_svg(
        '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 '
        '0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>'
    ),
    "gcr_killed": _lucide_svg(
        '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 '
        '0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>'
    ),
    "gcr_score": _lucide_svg(
        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>'
        '<path d="M12 8v4"/><path d="M12 16h.01"/>'
    ),
    "uscirf": _lucide_svg(
        '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 '
        '4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"/>'
        '<path d="m9 12 2 2 4-4"/>'
    ),
    "state_dept": _lucide_svg(
        '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
        '<path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>'
    ),
    "ohchr": _lucide_svg(
        '<path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 '
        '4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>'
    ),
    "vdem_religion": _lucide_svg(
        '<path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>'
    ),
    "vdem_repression": _lucide_svg(
        '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>'
    ),
    "news_events": _lucide_svg(
        '<path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/>'
        '<path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6Z"/>'
    ),
}

HIGH_SEVERITY_STATUSES = frozenset({"severe", "warning", "persecution"})


def _od_score_bar(score) -> str:
    try:
        pct = max(0.0, min(100.0, float(score)))
    except (TypeError, ValueError):
        return ""
    width = int(round(pct))
    return f'<div class="score-bar" role="presentation"><span style="width:{width}%"></span></div>'


def _data_item(icon_key: str, label_html: str, value_html: str, extra: str = "") -> str:
    icon = ICON_SVGS.get(icon_key, "")
    return (
        f'<div class="data-item">'
        f'<div class="label">{icon}{label_html}</div>'
        f'<div class="value">{value_html}</div>'
        f"{extra}"
        f"</div>"
    )


def _data_group(title: str, items: list[str]) -> str:
    if not items:
        return ""
    joined = "\n            ".join(items)
    return (
        f'<div class="data-group">\n'
        f'          <div class="data-group-label">{esc(title)}</div>\n'
        f'          <div class="data-grid">\n            {joined}\n          </div>\n'
        f"        </div>"
    )


def render_data_fields(country: dict) -> str:
    meta = country.get("metadata", {})
    # Direct country-specific source URLs only (leave fields unlinked when absent).
    od_url = meta.get("archive_od_url")
    uscirf_url = meta.get("uscirf_url")

    severity: list[str] = []
    liberties: list[str] = []
    demographics: list[str] = []
    incidents: list[str] = []

    od_score = meta.get("opendoors_score")
    od_rank = meta.get("opendoors_ranking")
    if od_score is not None:
        severity.append(
            _data_item(
                "opendoors_score",
                "Open Doors Score",
                linked_data_value(f"{esc(od_score)}/100", od_url),
                _od_score_bar(od_score),
            )
        )
    if od_rank is not None:
        severity.append(
            _data_item(
                "opendoors_ranking",
                "WWL Ranking",
                linked_data_value(f"#{esc(od_rank)}", od_url),
            )
        )
    gcr_score = meta.get("gcr_persecution_score")
    if gcr_score:
        severity.append(_data_item("gcr_score", "GCR Persecution Score", esc(gcr_score)))
    acn_class = meta.get("acn_classification")
    if acn_class:
        severity.append(_data_item("acn", "ACN Classification", esc(acn_class)))
    uscirf_des = meta.get("uscirf_designation")
    if uscirf_des:
        severity.append(
            _data_item(
                "uscirf",
                "USCIRF Designation",
                linked_data_value(esc(uscirf_des), uscirf_url),
            )
        )

    fh_status = meta.get("freedom_house_status")
    if fh_status:
        liberties.append(_data_item("freedom_house", "Freedom House", esc(fh_status)))
    fh_pr = meta.get("freedom_house_pr")
    fh_cl = meta.get("freedom_house_cl")
    if fh_pr is not None and fh_cl is not None:
        liberties.append(
            _data_item("pr_cl", "PR / CL Score", f"{esc(fh_pr)} / {esc(fh_cl)}")
        )
    vdem_relig = meta.get("vdem_freedom_of_religion")
    if vdem_relig is not None:
        year = meta.get("vdem_year")
        year_s = f" ({int(year)})" if isinstance(year, (int, float)) else ""
        liberties.append(
            _data_item(
                "vdem_religion",
                f"V-Dem Freedom of Religion{esc(year_s)}",
                esc(vdem_relig),
            )
        )
    vdem_repr = meta.get("vdem_religious_org_repression")
    if vdem_repr is not None:
        liberties.append(
            _data_item("vdem_repression", "V-Dem Rel. Org. Repression", esc(vdem_repr))
        )
    ohchr_count = meta.get("ohchr_recommendation_count")
    if ohchr_count is not None:
        liberties.append(
            _data_item("ohchr", "OHCHR Recommendations", esc(ohchr_count))
        )
    if meta.get("state_dept_url"):
        liberties.append(
            _data_item(
                "state_dept",
                "U.S. State Dept IRF",
                f'<a href="{safe_url(meta.get("state_dept_url"))}" '
                f'target="_blank" rel="noopener">Report</a>',
            )
        )

    christ_pop = meta.get("christian_population")
    christ_pct = meta.get("christian_percentage")
    if christ_pop is not None:
        pop_str = f"{christ_pop:,}" if isinstance(christ_pop, (int, float)) else str(christ_pop)
        pct_str = f" ({christ_pct:.1f}%)" if isinstance(christ_pct, (int, float)) else ""
        demographics.append(
            _data_item(
                "christian_population",
                "Christian Population",
                f"{esc(pop_str)}{esc(pct_str)}",
            )
        )

    vid_total = meta.get("vid_incidents_total")
    if vid_total is not None:
        incidents.append(_data_item("vid_incidents", "VID Incidents", esc(vid_total)))
    vid_killings = meta.get("vid_killings")
    if vid_killings is not None:
        incidents.append(_data_item("vid_killings", "VID Killings", esc(vid_killings)))
    gcr_killed = meta.get("gcr_killed")
    if gcr_killed:
        incidents.append(_data_item("gcr_killed", "GCR Killed", esc(gcr_killed)))
    gdelt_count = meta.get("gdelt_recent_articles")
    if gdelt_count is not None:
        incidents.append(
            _data_item("news_events", "Recent News Events", esc(gdelt_count))
        )

    groups = [
        _data_group("Persecution severity", severity),
        _data_group("Civil liberties", liberties),
        _data_group("Demographics", demographics),
        _data_group("Incidents", incidents),
    ]
    groups = [g for g in groups if g]
    if not groups:
        return ""
    joined = "\n        ".join(groups)
    return f'<div class="data-groups">\n        {joined}\n        </div>'


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


def _dated_incident_count(articles: list[dict]) -> int:
    return sum(1 for a in articles if str(a.get("date") or "").strip())


def _incidents_list_html(articles: list[dict]) -> str:
    joined = _incident_rows(articles)
    classes = "incidents-list"
    if _dated_incident_count(articles) >= 2:
        classes += " timeline"
    return f'<div class="{classes}">\n          {joined}\n        </div>'


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
            ("vom_samples", "Voice of the Martyrs"),
            ("chinaaid_samples", "ChinaAid"),
            ("infochretienne_samples", "Info Chrétienne"),
            ("osce_samples", "OSCE / ODIHR"),
            ("unsrforb_samples", "UN Special Rapporteur on FoRB"),
            ("hrw_samples", "Human Rights Watch"),
            ("amnesty_samples", "Amnesty International"),
            ("barnabas_samples", "Barnabas Aid"),
            ("csi_samples", "Christian Solidarity International"),
            ("cna_samples", "Catholic News Agency"),
            ("fides_samples", "Agenzia Fides"),
            ("aciprensa_samples", "ACI Prensa"),
            ("hrwf_samples", "Human Rights Without Frontiers"),
            ("adf_samples", "ADF International"),
            ("wea_samples", "WEA"),
            ("jubilee_samples", "Jubilee Campaign"),
            ("ippforb_samples", "IPPFoRB"),
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
        parts.append(
            "<section>\n"
            "        <h2>Latest News</h2>\n"
            f"        {_incidents_list_html(articles)}\n"
            "      </section>"
        )
    if historical:
        parts.append(
            '<details class="historical-news">\n'
            "        <summary>Historical News</summary>\n"
            f"        {_incidents_list_html(historical)}\n"
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
    high_severity = sum(
        1 for c in countries if isinstance(c, dict) and c.get("status") in HIGH_SEVERITY_STATUSES
    )
    meta = {
        "generatedAt": data.get("fetched", {}).get("generated_at"),
        "sources": meta_sources,
        "countryCount": len(countries),
        "highSeverityCount": high_severity,
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
        hist_ids, mod_ids = resolve_page_source_ids(slug, source_ids)

        historical_sources = render_sources(hist_ids, all_sources_lookup)
        modern_sources = render_sources(mod_ids, all_sources_lookup)
        all_ref_ids = dedupe_source_ids_by_url(
            collect_all_reference_ids(source_ids), all_sources_lookup
        )
        all_sources_items = []
        for s in all_ref_ids:
            src = all_sources_lookup.get(s)
            if not src:
                continue
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
        "features": [],
    }
    for c in countries:
        props = {
            "title": c["title"],
            "slug": c["slug"],
            "iso3": (c.get("iso3") or "").upper(),
            "status": c.get("status", ""),
            "level": c.get("persecution_level", ""),
        }
        od_score = (c.get("metadata") or {}).get("opendoors_score")
        if od_score is not None:
            props["opendoors_score"] = od_score
        geo["features"].append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [c["lng"], c["lat"]]},
                "properties": props,
            }
        )
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
