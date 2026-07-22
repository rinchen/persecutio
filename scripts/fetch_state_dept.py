import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import (
    FETCHED,
    USER_AGENT,
    ensure_fetched_dir,
    exit_for_status,
    fetch_text,
    write_status,
)

ensure_fetched_dir()
STATE_DEPT = FETCHED / "state_dept"
STATE_DEPT.mkdir(parents=True, exist_ok=True)

REPORT_YEAR = 2023
BASE_URL = f"https://www.state.gov/reports/{REPORT_YEAR}-report-on-international-religious-freedom"
MAIN_URL = "https://www.state.gov/international-religious-freedom-reports/"
REQUEST_DELAY = 1.5

# Some country slugs differ between our project and state.gov URLs
SLUG_MAP = {
    "myanmar": "burma",
}

TARGET_COUNTRIES = [
    "afghanistan", "algeria", "bangladesh", "central-african-republic",
    "china", "colombia", "cuba", "egypt", "eritrea", "haiti",
    "india", "indonesia", "iran", "iraq", "laos", "libya",
    "malaysia", "mexico", "myanmar", "nicaragua", "nigeria",
    "north-korea", "pakistan", "saudi-arabia", "somalia", "sudan",
    "syria", "turkey", "venezuela", "vietnam", "yemen",
    "united-states", "brazil", "uganda", "zimbabwe",
]


def fetch_url(url, timeout=20):
    text, err = fetch_text(url, timeout=timeout)
    if err:
        raise RuntimeError(err)
    return text


def strip_tags(html):
    """Remove HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_report_body(html):
    """Extract the main report content area from the HTML."""
    # The report content is inside div#report_content
    match = re.search(
        r'<div\s+id="report_content"[^>]*>(.*?)</div>\s*(?:</div>|<div\s+class="report)',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1)

    # Fallback: try report__content
    match = re.search(
        r'class="report__content">(.*?)<div\s+class="report-appendices"',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1)

    # Fallback: entry-content inside state_report
    match = re.search(
        r'class="report__content__inner\s+entry-content">(.*?)</section>\s*</div>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1)

    return ""


def extract_title(html):
    """Extract the report title."""
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
    if match:
        return strip_tags(match.group(1))
    match = re.search(
        r"Report on International Religious Freedom[:\s]+(\w[\w\s]+)",
        html,
        re.IGNORECASE,
    )
    if match:
        return match.group(0).strip()
    return ""


def extract_sections(html):
    """Extract report sections using regex patterns from the report body."""
    body = extract_report_body(html)
    if not body:
        body = html

    sections = {}

    # Pattern 1: <strong>BOLD HEADING</strong> followed by content
    # Many reports use <strong> or <b> for section headings within entry-content
    strong_pattern = re.compile(
        r"<(?:strong|b)>\s*(.*?)\s*</(?:strong|b)>\s*(.*?)(?=<(?:strong|b)>|<h[23]|$)",
        re.DOTALL | re.IGNORECASE,
    )
    for match in strong_pattern.finditer(body):
        heading = strip_tags(match.group(1)).strip()
        content = strip_tags(match.group(2)).strip()
        if heading and content and len(content) > 30:
            key = heading.lower().rstrip(":").strip()
            if key not in sections:
                sections[key] = content[:5000]

    # Pattern 2: <h2>, <h3>, <h4> headings (less common but used in some reports)
    heading_pattern = re.compile(
        r"<h[234][^>]*>\s*(.*?)\s*</h[234]>\s*(.*?)(?=<h[234]|$)",
        re.DOTALL | re.IGNORECASE,
    )
    for match in heading_pattern.finditer(body):
        heading = strip_tags(match.group(1)).strip()
        content = strip_tags(match.group(2)).strip()
        if heading and content and len(content) > 30:
            key = heading.lower().rstrip(":").strip()
            if key not in sections:
                sections[key] = content[:5000]

    # Pattern 3: text that starts with section-like headings (all caps or title case
    # followed by content in the raw text)
    plain_text = strip_tags(body)
    section_headings_re = re.compile(
        r"(?:^|\s)((?:Section\s+[IVX]+\.?\s+)?"
        r"(?:Executive Summary|Religious Demograph[y]?|Legal Framework|"
        r"Status of (?:Respect|Societal Respect) for Religious Freedom|"
        r"U\.?S\.? Government (?:Policy|Policy and Engagement)|"
        r"(?:Abuses|Restrictions) (?:of|on|involving|limiting) Religious (?:Freedom|Belief)|"
        r"Government Practices|"
        r"Status of Societal (?:Respect|Violence) for Religious Freedom|"
        r"Overview))"
        r"\s*(.*?)(?=(?:Section\s+[IVX]+|Executive Summary|Religious Demograph|"
        r"Legal Framework|Status of|U\.?S\.? Government|"
        r"Abuses|Restrictions|Government Practices|Overview)|$)",
        re.DOTALL | re.IGNORECASE,
    )
    for match in section_headings_re.finditer(plain_text):
        heading = match.group(1).strip()
        content = match.group(2).strip()
        if heading and content and len(content) > 30:
            key = heading.lower().rstrip(":").strip()
            if key not in sections:
                sections[key] = content[:5000]

    return sections


def extract_executive_summary(sections, html):
    """Get the executive summary section."""
    for key in sections:
        if "executive" in key and "summary" in key:
            return sections[key]
    # Try to find it in raw HTML
    match = re.search(
        r"Executive\s+Summary\s*</(?:strong|b|h\d)>\s*(.*?)(?=<strong|<h[23]|Section I)",
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return strip_tags(match.group(1))[:5000]
    return ""


def extract_christian_mentions(full_text):
    """Find mentions of Christian persecution keywords in text."""
    keywords = [
        "christian", "church", "cross", "bible", "worship",
        "proselytiz", "proselyt", "convert", "evangelic",
        "protestant", "catholic", "orthodox", "denomination",
        "pastor", "clergy", "priest", "congregat",
        "persecut", "religious minority", "discrimin",
    ]
    mentions = {}
    lower = full_text.lower()
    for kw in keywords:
        hits = []
        idx = 0
        while len(hits) < 3:
            pos = lower.find(kw, idx)
            if pos == -1:
                break
            start = max(0, pos - 120)
            end = min(len(full_text), pos + 180)
            snippet = full_text[start:end].strip()
            hits.append(snippet)
            idx = pos + len(kw)
        if hits:
            mentions[kw] = hits
    return mentions


def fetch_country_report(slug, skip=False):
    """Fetch and parse a single country's IRF report."""
    state_slug = SLUG_MAP.get(slug, slug)
    cache_path = STATE_DEPT / f"{slug}.json"

    if skip and cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            data["_cached"] = True
            return data
        except Exception:
            pass

    urls_to_try = [
        f"{BASE_URL}/{state_slug}/",
        f"{BASE_URL}/{slug}/",
    ]

    html = None
    final_url = None
    for url in urls_to_try:
        try:
            html = fetch_url(url)
            final_url = url
            break
        except Exception:
            continue

    if html is None:
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text(encoding="utf-8"))
                data["_cached"] = True
                data["_error"] = "fetch_failed_using_cache"
                return data
            except Exception:
                pass
        return {
            "slug": slug,
            "has_report": False,
            "url": None,
            "error": "could_not_fetch",
            "sections": {},
            "executive_summary": "",
            "christian_mentions": {},
        }

    title = extract_title(html)
    sections = extract_sections(html)
    exec_summary = extract_executive_summary(sections, html)

    all_text = " ".join(sections.values())
    if not all_text:
        all_text = strip_tags(html)
    christian_info = extract_christian_mentions(all_text)

    report_data = {
        "slug": slug,
        "has_report": True,
        "url": final_url,
        "title": title,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sections": {k: v[:5000] for k, v in sections.items()},
        "executive_summary": exec_summary[:5000],
        "christian_mentions": christian_info,
        "section_count": len(sections),
    }

    cache_path.write_text(
        json.dumps(report_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return report_data


def main():
    print(f"Fetching State Dept IRF Reports ({REPORT_YEAR})...")
    print(f"Target: {len(TARGET_COUNTRIES)} countries")
    print(f"Cache dir: {STATE_DEPT}")
    print()

    index = {"countries": {}, "fetched_at": None, "report_year": REPORT_YEAR}

    succeeded = 0
    failed = 0
    cached = 0

    for i, slug in enumerate(TARGET_COUNTRIES):
        print(f"[{i + 1}/{len(TARGET_COUNTRIES)}] {slug}...", end=" ", flush=True)

        result = fetch_country_report(slug, skip=False)

        is_cached = result.get("_cached", False)
        has_report = result.get("has_report", False)

        if is_cached:
            cached += 1
            print("(cached)")
        elif has_report:
            succeeded += 1
            section_count = result.get("section_count", 0)
            exec_len = len(result.get("executive_summary", ""))
            print(f"OK ({section_count} sections, exec: {exec_len} chars)")
        else:
            failed += 1
            print(f"FAILED: {result.get('error', 'unknown')}")

        country_name = slug.replace("-", " ").title()
        index["countries"][country_name] = {
            "has_report": has_report,
            "executive_summary": result.get("executive_summary", ""),
            "url": result.get("url", ""),
            "sections": list(result.get("sections", {}).keys()),
            "section_count": result.get("section_count", 0),
            "christian_mentions": bool(result.get("christian_mentions")),
        }

        time.sleep(REQUEST_DELAY)

    index["fetched_at"] = datetime.now(timezone.utc).isoformat()
    index["summary"] = {
        "total": len(TARGET_COUNTRIES),
        "succeeded": succeeded,
        "cached": cached,
        "failed": failed,
    }

    index_path = STATE_DEPT / "index.json"
    index_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print(f"Done: {succeeded} fetched, {cached} cached, {failed} failed")
    print(f"Index written to: {index_path}")

    if failed == len(TARGET_COUNTRIES):
        final_status = "failed"
        write_status("statedepartment", final_status, "all countries failed")
    elif failed > 0:
        final_status = "partial"
        write_status("statedepartment", final_status, f"{failed} of {len(TARGET_COUNTRIES)} failed")
    else:
        final_status = "ok"
        write_status("statedepartment", final_status)
    exit_for_status(final_status)


if __name__ == "__main__":
    main()
