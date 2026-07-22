"""Canonical country titles, aliases, ISO3, and map coordinates for fetchers/collect."""
from __future__ import annotations

import re
from typing import Any

# Canonical display titles used across the project.
KNOWN_COUNTRIES = [
    "Afghanistan", "Algeria", "Azerbaijan", "Bahrain", "Bangladesh",
    "Bhutan", "Brazil", "Brunei", "Burkina Faso", "Cameroon",
    "Central African Republic", "China", "Colombia", "Comoros", "Cuba",
    "Democratic Republic of Congo", "Egypt", "Eritrea", "Ethiopia",
    "Guinea", "Haiti", "India", "Indonesia", "Iran", "Iraq", "Jordan",
    "Kazakhstan", "Kenya", "Kuwait", "Kyrgyzstan", "Laos", "Lebanon",
    "Libya", "Malaysia", "Maldives", "Mali", "Mauritania", "Mexico",
    "Morocco", "Mozambique", "Myanmar", "Nepal", "Nicaragua", "Niger",
    "Nigeria", "North Korea", "Oman", "Pakistan", "Philippines", "Qatar",
    "Russia", "Saudi Arabia", "Somalia", "South Sudan", "Sri Lanka",
    "Sudan", "Syria", "Tajikistan", "Tanzania", "Tunisia", "Turkey",
    "Turkmenistan", "Uganda", "United Arab Emirates", "United States",
    "Uzbekistan", "Venezuela", "Vietnam", "Yemen", "Zimbabwe",
]

# alias (lowercase) -> canonical title, or None to ignore.
# Short forms that collide with English words (us, car) are NOT scanned in
# free text — see EXACT_ALIASES and CASE_SENSITIVE_ALIASES.
COUNTRY_ALIASES: dict[str, str | None] = {
    "dr congo": "Democratic Republic of Congo",
    "drc": "Democratic Republic of Congo",
    "congo": "Democratic Republic of Congo",
    "democratic republic of the congo": "Democratic Republic of Congo",
    "burma": "Myanmar",
    "dprk": "North Korea",
    "usa": "United States",
    "u.s.a.": "United States",
    "uae": "United Arab Emirates",
    "emirates": "United Arab Emirates",
    "palestine": None,
    "gaza": None,
    "israel": None,
    "west bank": None,
    "chinese": "China",
    "indian": "India",
    "nigerian": "Nigeria",
    "pakistani": "Pakistan",
    "iranian": "Iran",
    "egyptian": "Egypt",
    "palestinian": None,
    "israeli": None,
}

# Whole-string aliases for categories / resolve_country_name only (not free text).
EXACT_ALIASES: dict[str, str | None] = {
    "us": "United States",
    "u.s.": "United States",
    "car": "Central African Republic",
}

# Matched case-sensitively in original text so "us"/"car" pronouns/nouns
# are not treated as United States / Central African Republic.
CASE_SENSITIVE_ALIASES: dict[str, str] = {
    "US": "United States",
    "U.S.": "United States",
    "U.S.A.": "United States",
    "CAR": "Central African Republic",
}

# title -> (iso3, lat, lng)
COUNTRY_GEO: dict[str, tuple[str, float, float]] = {
    "Afghanistan": ("AFG", 33.93, 67.71),
    "Algeria": ("DZA", 28.03, 1.66),
    "Azerbaijan": ("AZE", 40.14, 47.58),
    "Bahrain": ("BHR", 26.07, 50.55),
    "Bangladesh": ("BGD", 23.68, 90.36),
    "Bhutan": ("BTN", 27.51, 90.43),
    "Brazil": ("BRA", -14.24, -51.93),
    "Brunei": ("BRN", 4.54, 114.73),
    "Burkina Faso": ("BFA", 12.24, -1.56),
    "Cameroon": ("CMR", 7.37, 12.35),
    "Central African Republic": ("CAF", 6.61, 20.94),
    "China": ("CHN", 35.86, 104.20),
    "Colombia": ("COL", 4.57, -74.30),
    "Comoros": ("COM", -11.65, 43.33),
    "Cuba": ("CUB", 21.52, -77.78),
    "Democratic Republic of Congo": ("COD", -4.04, 21.76),
    "Egypt": ("EGY", 26.82, 30.80),
    "Eritrea": ("ERI", 15.18, 39.78),
    "Ethiopia": ("ETH", 9.15, 40.49),
    "Guinea": ("GIN", 9.95, -9.70),
    "Haiti": ("HTI", 18.97, -72.29),
    "India": ("IND", 20.59, 78.96),
    "Indonesia": ("IDN", -0.79, 113.92),
    "Iran": ("IRN", 32.43, 53.69),
    "Iraq": ("IRQ", 33.22, 43.68),
    "Jordan": ("JOR", 30.59, 36.24),
    "Kazakhstan": ("KAZ", 48.02, 66.92),
    "Kenya": ("KEN", -0.02, 37.91),
    "Kuwait": ("KWT", 29.31, 47.48),
    "Kyrgyzstan": ("KGZ", 41.20, 74.77),
    "Laos": ("LAO", 19.86, 102.50),
    "Lebanon": ("LBN", 33.85, 35.86),
    "Libya": ("LBY", 26.34, 17.23),
    "Malaysia": ("MYS", 4.21, 101.98),
    "Maldives": ("MDV", 3.20, 73.22),
    "Mali": ("MLI", 17.57, -4.00),
    "Mauritania": ("MRT", 21.01, -10.94),
    "Mexico": ("MEX", 23.63, -102.55),
    "Morocco": ("MAR", 31.79, -7.09),
    "Mozambique": ("MOZ", -18.67, 35.53),
    "Myanmar": ("MMR", 21.91, 95.96),
    "Nepal": ("NPL", 28.39, 84.12),
    "Nicaragua": ("NIC", 12.87, -85.21),
    "Niger": ("NER", 17.61, 8.08),
    "Nigeria": ("NGA", 9.08, 8.68),
    "North Korea": ("PRK", 40.34, 127.51),
    "Oman": ("OMN", 21.51, 55.92),
    "Pakistan": ("PAK", 30.38, 69.35),
    "Philippines": ("PHL", 12.88, 121.77),
    "Qatar": ("QAT", 25.35, 51.18),
    "Russia": ("RUS", 61.52, 105.32),
    "Saudi Arabia": ("SAU", 23.89, 45.08),
    "Somalia": ("SOM", 5.15, 46.20),
    "South Sudan": ("SSD", 6.88, 31.31),
    "Sri Lanka": ("LKA", 7.87, 80.77),
    "Sudan": ("SDN", 12.86, 30.22),
    "Syria": ("SYR", 34.80, 39.00),
    "Tajikistan": ("TJK", 38.86, 71.28),
    "Tanzania": ("TZA", -6.37, 34.89),
    "Tunisia": ("TUN", 33.89, 9.54),
    "Turkey": ("TUR", 38.96, 35.24),
    "Turkmenistan": ("TKM", 38.97, 59.56),
    "Uganda": ("UGA", 1.37, 32.29),
    "United Arab Emirates": ("ARE", 23.42, 53.85),
    "United States": ("USA", 37.09, -95.71),
    "Uzbekistan": ("UZB", 41.38, 64.59),
    "Venezuela": ("VEN", 6.42, -66.59),
    "Vietnam": ("VNM", 14.06, 108.28),
    "Yemen": ("YEM", 15.55, 48.52),
    "Zimbabwe": ("ZWE", -19.02, 29.15),
}


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def resolve_country_name(name: str) -> str | None:
    """Map free-text country name to canonical title, or None if excluded/unknown."""
    if not name or not isinstance(name, str):
        return None
    raw = name.strip()
    if raw in COUNTRY_GEO:
        return raw
    lower = raw.lower()
    if lower in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[lower]
    if lower in EXACT_ALIASES:
        return EXACT_ALIASES[lower]
    for title in KNOWN_COUNTRIES:
        if title.lower() == lower:
            return title
    # Title-case slug forms: "north-korea" / "North Korea"
    spaced = lower.replace("-", " ").replace("_", " ")
    if spaced in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[spaced]
    if spaced in EXACT_ALIASES:
        return EXACT_ALIASES[spaced]
    for title in KNOWN_COUNTRIES:
        if title.lower() == spaced:
            return title
    return None


def _alias_in_text(alias: str, text: str, *, ignore_case: bool = True) -> bool:
    """Word-boundary match; trailing-period aliases use a non-word lookahead."""
    flags = re.IGNORECASE if ignore_case else 0
    if alias.endswith("."):
        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
    else:
        pattern = r"\b" + re.escape(alias) + r"\b"
    return re.search(pattern, text or "", flags) is not None


def detect_countries(text: str) -> list[str]:
    """Detect canonical country names mentioned in text.

    Ambiguous short tokens (us, car) are ignored unless they appear as
    case-sensitive country codes (US, U.S., CAR) so English pronouns/nouns
    do not falsely tag United States or Central African Republic.
    """
    found: set[str] = set()
    raw = text or ""
    text_lower = raw.lower()

    for alias, canonical in CASE_SENSITIVE_ALIASES.items():
        if _alias_in_text(alias, raw, ignore_case=False):
            found.add(canonical)

    # Longer aliases first to prefer specific matches
    alias_items = sorted(
        [(a, c) for a, c in COUNTRY_ALIASES.items() if c],
        key=lambda x: -len(x[0]),
    )
    for alias, canonical in alias_items:
        if _alias_in_text(alias, text_lower, ignore_case=False):
            found.add(canonical)

    for title in KNOWN_COUNTRIES:
        if _alias_in_text(title.lower(), text_lower, ignore_case=False):
            found.add(title)

    return sorted(found)


def countries_for_article(
    title: str,
    description: str,
    categories: list[str] | None = None,
) -> list[str]:
    """Prefer title + category tags; only fall back to description body.

    WordPress feeds often append unrelated 'related post' blurbs in descriptions.
    Secondary mentions (e.g. 'pastor living in the United States' in a Pakistan
    story) must not pull the article onto that country's page.
    """
    found: list[str] = []
    for name in detect_countries(title or ""):
        if name not in found:
            found.append(name)
    for cat in categories or []:
        resolved = resolve_country_name(cat)
        if resolved and resolved not in found:
            found.append(resolved)
    if found:
        return found
    desc = description or ""
    # Drop common WP footer / related-post noise
    desc = re.split(r"\s+The post\s+", desc, maxsplit=1)[0]
    desc = re.split(r"\s+appeared first on\s+", desc, maxsplit=1)[0]
    for name in detect_countries(desc):
        if name not in found:
            found.append(name)
    return found


def geo_for(title: str) -> dict[str, Any] | None:
    resolved = resolve_country_name(title)
    if not resolved or resolved not in COUNTRY_GEO:
        return None
    iso3, lat, lng = COUNTRY_GEO[resolved]
    return {
        "title": resolved,
        "slug": slugify(resolved),
        "iso3": iso3,
        "lat": lat,
        "lng": lng,
    }


def ensure_source(
    sources: dict[str, dict],
    sid: str,
    title: str,
    url: str,
    date: str,
) -> str:
    if sid not in sources:
        sources[sid] = {"title": title, "url": url, "date": str(date)}
    elif url and sources[sid].get("url") != url:
        sources[sid]["url"] = url
        if title:
            sources[sid]["title"] = title
        if date:
            sources[sid]["date"] = str(date)
    return sid


def attach_citation(country: dict, sid: str, sources: dict[str, dict]) -> None:
    """Attach a citation id to country source_ids.modern and refresh metadata lists."""
    if sid not in sources:
        return
    country.setdefault("source_ids", {})
    modern = list(country["source_ids"].get("modern") or [])
    if sid not in modern:
        modern.append(sid)
    country["source_ids"]["modern"] = modern
    country.setdefault("metadata", {})
    resolved = [s for s in modern if s in sources]
    country["metadata"]["source_ids"] = resolved
    country["metadata"]["sources"] = [sources[s] for s in resolved]
