import json
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import (
    FETCHED as FETCHED_ROOT,
    USER_AGENT,
    ensure_fetched_dir,
    exit_for_status,
    fetch_text,
    write_status,
)
from urls import http_url

ensure_fetched_dir()
FETCHED = FETCHED_ROOT / "uscirf"
FETCHED.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.uscirf.gov"
RECOMMENDATIONS_URL = f"{BASE_URL}/countries/2026-recommendations"

COUNTRIES = [
    # Existing project countries that have USCIRF pages
    {"title": "Afghanistan", "slug": "afghanistan", "project_slug": "afghanistan"},
    {"title": "Algeria", "slug": "algeria", "project_slug": "algeria"},
    {"title": "Central African Republic", "slug": "central-african-republic", "project_slug": "central-african-republic"},
    {"title": "China", "slug": "china", "project_slug": "china"},
    {"title": "Cuba", "slug": "cuba", "project_slug": "cuba"},
    {"title": "Egypt", "slug": "egypt", "project_slug": "egypt"},
    {"title": "Eritrea", "slug": "eritrea", "project_slug": "eritrea"},
    {"title": "India", "slug": "india", "project_slug": "india"},
    {"title": "Indonesia", "slug": "indonesia", "project_slug": "indonesia"},
    {"title": "Iran", "slug": "iran", "project_slug": "iran"},
    {"title": "Iraq", "slug": "iraq", "project_slug": "iraq"},
    {"title": "Laos", "slug": "laos", "project_slug": "laos"},
    {"title": "Libya", "slug": "libya", "project_slug": "libya"},
    {"title": "Malaysia", "slug": "malaysia", "project_slug": "malaysia"},
    {"title": "Nicaragua", "slug": "nicaragua", "project_slug": "nicaragua"},
    {"title": "Nigeria", "slug": "nigeria", "project_slug": "nigeria"},
    {"title": "North Korea", "slug": "north-korea", "project_slug": "north-korea"},
    {"title": "Pakistan", "slug": "pakistan", "project_slug": "pakistan"},
    {"title": "Saudi Arabia", "slug": "saudi-arabia", "project_slug": "saudi-arabia"},
    {"title": "Sudan", "slug": "sudan", "project_slug": "sudan"},
    {"title": "Syria", "slug": "syria", "project_slug": "syria"},
    {"title": "Turkey", "slug": "turkey", "project_slug": "turkey"},
    {"title": "Vietnam", "slug": "vietnam", "project_slug": "vietnam"},
    # Myanmar uses "burma" slug on USCIRF
    {"title": "Myanmar", "slug": "burma", "project_slug": "myanmar"},
    # New countries to add (USCIRF has pages for these)
    {"title": "Azerbaijan", "slug": "azerbaijan", "project_slug": "azerbaijan"},
    {"title": "Bahrain", "slug": "bahrain", "project_slug": "bahrain"},
    {"title": "Bangladesh", "slug": "bangladesh", "project_slug": "bangladesh"},
    {"title": "Kazakhstan", "slug": "kazakhstan", "project_slug": "kazakhstan"},
    {"title": "Kyrgyzstan", "slug": "kyrgyzstan", "project_slug": "kyrgyzstan"},
    {"title": "Qatar", "slug": "qatar", "project_slug": "qatar"},
    {"title": "Russia", "slug": "russia", "project_slug": "russia"},
    {"title": "Sri Lanka", "slug": "sri-lanka", "project_slug": "sri-lanka"},
    {"title": "Tajikistan", "slug": "tajikistan", "project_slug": "tajikistan"},
    {"title": "Turkmenistan", "slug": "turkmenistan", "project_slug": "turkmenistan"},
    {"title": "Uzbekistan", "slug": "uzbekistan", "project_slug": "uzbekistan"},
]


def fetch_url(url, timeout=20):
    text, err = fetch_text(url, timeout=timeout, user_agent=USER_AGENT)
    if text is None:
        raise OSError(err or "fetch failed")
    return text


class ClassScopedTextCollector(HTMLParser):
    """Collect text from tags inside an element whose class contains ``scope_class``.

    Used for USCIRF full-content paragraphs and hero titles.
    """

    def __init__(
        self,
        *,
        scope_tag: str,
        scope_class: str,
        collect_tag: str | None = None,
        collect_as_paragraphs: bool = True,
    ):
        super().__init__()
        self.scope_tag = scope_tag
        self.scope_class = scope_class
        self.collect_tag = collect_tag
        self.collect_as_paragraphs = collect_as_paragraphs
        self._in_scope = False
        self._depth = 0
        self._in_collect = False
        self._paragraphs: list[str] = []
        self._current: list[str] = []
        self._flat: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if tag == self.scope_tag and self.scope_class in cls:
            self._in_scope = True
            self._depth = 0
        if self._in_scope and tag == self.scope_tag:
            self._depth += 1
        if self._in_scope and self.collect_tag and tag == self.collect_tag:
            self._in_collect = True
            self._current = []
        elif self._in_scope and not self.collect_tag:
            # Title-style: collect all text in scope
            pass

    def handle_endtag(self, tag):
        if self._in_collect and self.collect_tag and tag == self.collect_tag:
            self._in_collect = False
            text = " ".join("".join(self._current).split()).strip()
            if text:
                self._paragraphs.append(text)
            self._current = []
        if self._in_scope and tag == self.scope_tag:
            self._depth -= 1
            if self._depth <= 0:
                self._in_scope = False

    def handle_data(self, data):
        if self._in_collect:
            self._current.append(data)
        elif self._in_scope and not self.collect_tag:
            self._flat.append(data.strip())

    def get_paragraphs(self):
        return self._paragraphs

    def get_title(self):
        return " ".join(t for t in self._flat if t).strip()


def ContentExtractor():
    return ClassScopedTextCollector(
        scope_tag="div",
        scope_class="full-content",
        collect_tag="p",
        collect_as_paragraphs=True,
    )


def TitleExtractor():
    return ClassScopedTextCollector(
        scope_tag="h1",
        scope_class="internal-hero-title",
        collect_tag=None,
        collect_as_paragraphs=False,
    )


class RecommendationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_view_content = False
        self._in_h3 = False
        self._in_link = False
        self._h3_text = []
        self._link_text = []
        self.cpc_countries = []
        self.swl_countries = []
        self._section = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if tag == "div" and "view-content" in cls:
            self._in_view_content = True
        if self._in_view_content and tag == "h3":
            self._in_h3 = True
            self._h3_text = []
        if self._in_view_content and tag == "a":
            href = attrs_dict.get("href", "")
            if href.startswith("/countries/"):
                self._in_link = True
                self._link_text = []

    def handle_endtag(self, tag):
        if self._in_h3 and tag == "h3":
            self._in_h3 = False
            text = "".join(self._h3_text).strip()
            if "Countries of Particular Concern" in text:
                self._section = "cpc"
            elif "Special Watch List" in text:
                self._section = "swl"
        if self._in_link and tag == "a":
            self._in_link = False
            text = " ".join("".join(self._link_text).split()).strip()
            if text and self._section:
                target = self.cpc_countries if self._section == "cpc" else self.swl_countries
                target.append(text)

    def handle_data(self, data):
        if self._in_h3:
            self._h3_text.append(data)
        if self._in_link:
            self._link_text.append(data)


def fetch_recommendations():
    """Return (cpc_names, swl_names) or None if the recommendations source is unavailable."""
    cache_path = FETCHED / "recommendations_2026.json"
    try:
        html = fetch_url(RECOMMENDATIONS_URL)
        cache_path.write_text(html, encoding="utf-8")
    except Exception as e:
        print(f"  Warning: could not fetch recommendations page: {e}")
        if cache_path.exists():
            html = cache_path.read_text(encoding="utf-8")
        else:
            return None

    parser = RecommendationParser()
    parser.feed(html)

    cpc = [normalize_name(c) for c in parser.cpc_countries]
    swl = [normalize_name(s) for s in parser.swl_countries]
    if not cpc and not swl:
        print("  Warning: recommendations page yielded empty CPC/SWL lists")
        return None
    return cpc, swl


def normalize_name(name):
    return re.sub(r"\s+", " ", name).strip().lower()


def detect_designation(page_html, cpc_names, swl_names):
    title_extractor = TitleExtractor()
    parse_ok = True
    try:
        title_extractor.feed(page_html)
    except Exception as e:
        print(f"  Warning: title parse error: {type(e).__name__}: {e}")
        parse_ok = False
    country_name = title_extractor.get_title()
    norm = normalize_name(country_name)

    if norm in cpc_names:
        return "CPC", country_name, parse_ok
    if norm in swl_names:
        return "SWL", country_name, parse_ok

    # Only use list membership — do not invent CPC/SWL from boilerplate page text
    # when the recommendations lists are the source of truth.
    return "none", country_name, parse_ok


def extract_key_findings(page_html):
    parser = ContentExtractor()
    try:
        parser.feed(page_html)
    except Exception as e:
        print(f"  Warning: content parse error: {type(e).__name__}: {e}")
        return [], False
    paragraphs = parser.get_paragraphs()
    return paragraphs[:3], True


def fetch_country(country):
    slug = country["slug"]
    title = country["title"]
    cache_path = FETCHED / f"{slug}.json"
    url = http_url(BASE_URL, "countries", slug)
    if not url:
        return None, f"unsafe USCIRF URL for slug={slug!r}"

    cached = None
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  warning: corrupt USCIRF cache {cache_path.name}: {type(e).__name__}: {e}")
            cached = None

    try:
        html = fetch_url(url)
        result = {
            "title": title,
            "slug": slug,
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "html": html,
        }
        cache_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result, None
    except Exception as e:
        if cached:
            return cached, f"fallback to cache: {type(e).__name__}: {e}"
        return None, f"{type(e).__name__}: {e}"


def main():
    print("Fetching USCIRF 2026 recommendations...")
    rec = fetch_recommendations()
    if rec is None:
        print("  ERROR: CPC/SWL recommendations unavailable — aborting")
        write_status("uscirf", "failed", "recommendations page unavailable or empty CPC/SWL")
        exit_for_status("failed")
    cpc_names, swl_names = rec
    print(f"  CPC countries ({len(cpc_names)}): {', '.join(cpc_names)}")
    print(f"  SWL countries ({len(swl_names)}): {', '.join(swl_names)}")
    print()

    seen_slugs = set()
    unique_countries = []
    for c in COUNTRIES:
        if c["slug"] not in seen_slugs:
            seen_slugs.add(c["slug"])
            unique_countries.append(c)

    results = []
    ok = 0
    failed = 0
    cached_count = 0
    parse_issues = 0

    for i, country in enumerate(unique_countries):
        slug = country["slug"]
        title = country["title"]
        print(f"[{i + 1}/{len(unique_countries)}] {title} ({slug})...", end=" ", flush=True)

        data, err = fetch_country(country)
        if data is None:
            print(f"FAILED: {err}")
            failed += 1
            results.append({
                "title": title,
                "slug": slug,
                "project_slug": country["project_slug"],
                "status": "failed",
                "error": err,
                "designation": "unknown",
                "key_findings": [],
            })
            continue

        if err:
            print(f"(cached fallback)")
            cached_count += 1
        else:
            print("ok")

        page_html = data.get("html", "")
        designation, detected_name, title_ok = detect_designation(page_html, cpc_names, swl_names)
        findings, findings_ok = extract_key_findings(page_html)
        if not title_ok or not findings_ok:
            parse_issues += 1

        results.append({
            "title": title,
            "slug": slug,
            "project_slug": country["project_slug"],
            "uscirf_name": detected_name,
            "designation": designation,
            "key_findings": findings,
            "url": data.get("url", f"{BASE_URL}/countries/{slug}"),
            "fetched_at": data.get("fetched_at"),
            "status": "ok" if not err else "cached",
        })
        ok += 1

        if i < len(unique_countries) - 1:
            time.sleep(1)

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": RECOMMENDATIONS_URL,
        "summary": {
            "total": len(results),
            "ok": ok,
            "cached": cached_count,
            "failed": failed,
            "parse_issues": parse_issues,
            "cpc_count": len(cpc_names),
            "swl_count": len(swl_names),
        },
        "cpc_recommended": cpc_names,
        "swl_recommended": swl_names,
        "countries": results,
    }

    index_path = FETCHED / "index.json"
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print()
    print(f"Done. {ok} ok, {cached_count} cached, {failed} failed.")
    print(f"Index written to {index_path}")

    cpc_found = [r for r in results if r["designation"] == "CPC"]
    swl_found = [r for r in results if r["designation"] == "SWL"]
    none_found = [r for r in results if r["designation"] == "none"]
    print(f"Designations: {len(cpc_found)} CPC, {len(swl_found)} SWL, {len(none_found)} none")
    if parse_issues:
        print(f"Parse issues: {parse_issues}")

    if failed == len(unique_countries):
        final_status = "failed"
        write_status("uscirf", final_status, "all countries failed")
    elif failed > 0 or parse_issues > 0:
        final_status = "partial"
        parts = []
        if failed > 0:
            parts.append(f"{failed} of {len(unique_countries)} failed")
        if parse_issues > 0:
            parts.append(f"{parse_issues} parse issues")
        write_status("uscirf", final_status, "; ".join(parts))
    else:
        final_status = "ok"
        write_status("uscirf", final_status)
    exit_for_status(final_status)


if __name__ == "__main__":
    main()
