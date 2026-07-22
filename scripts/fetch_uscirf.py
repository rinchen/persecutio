import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FETCHED = DATA / "fetched" / "uscirf"
FETCHED.mkdir(parents=True, exist_ok=True)
STATUS_PATH = DATA / "fetched" / "uscirf_status.json"

BASE_URL = "https://www.uscirf.gov"
RECOMMENDATIONS_URL = f"{BASE_URL}/countries/2026-recommendations"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def write_status(status, message=None):
    STATUS_PATH.write_text(
        json.dumps({
            "name": "uscirf",
            "status": status,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "message": message,
        }, indent=2),
        encoding="utf-8",
    )


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
    req = Request(url, headers={"User-Agent": USER_AGENT})
    resp = urlopen(req, timeout=timeout)
    return resp.read().decode("utf-8", errors="ignore")


class ContentExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_full_content = False
        self._depth = 0
        self._in_p = False
        self._paragraphs = []
        self._current = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if tag == "div" and "full-content" in cls:
            self._in_full_content = True
            self._depth = 0
        if self._in_full_content and tag == "div":
            self._depth += 1
        if self._in_full_content and tag == "p":
            self._in_p = True
            self._current = []

    def handle_endtag(self, tag):
        if self._in_full_content and tag == "p" and self._in_p:
            self._in_p = False
            text = " ".join("".join(self._current).split()).strip()
            if text:
                self._paragraphs.append(text)
            self._current = []
        if self._in_full_content and tag == "div":
            self._depth -= 1
            if self._depth <= 0:
                self._in_full_content = False

    def handle_data(self, data):
        if self._in_p:
            self._current.append(data)

    def get_paragraphs(self):
        return self._paragraphs


class TitleExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_hero_title = False
        self._text = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if tag == "h1" and "internal-hero-title" in cls:
            self._in_hero_title = True

    def handle_endtag(self, tag):
        if tag == "h1" and self._in_hero_title:
            self._in_hero_title = False

    def handle_data(self, data):
        if self._in_hero_title:
            self._text.append(data.strip())

    def get_title(self):
        return " ".join(self._text).strip()


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
    cache_path = FETCHED / "recommendations_2026.json"
    try:
        html = fetch_url(RECOMMENDATIONS_URL)
        cache_path.write_text(html, encoding="utf-8")
    except Exception as e:
        print(f"  Warning: could not fetch recommendations page: {e}")
        if cache_path.exists():
            html = cache_path.read_text(encoding="utf-8")
        else:
            return [], []

    parser = RecommendationParser()
    parser.feed(html)

    cpc = [normalize_name(c) for c in parser.cpc_countries]
    swl = [normalize_name(s) for s in parser.swl_countries]
    return cpc, swl


def normalize_name(name):
    return re.sub(r"\s+", " ", name).strip().lower()


def detect_designation(page_html, cpc_names, swl_names):
    title_extractor = TitleExtractor()
    try:
        title_extractor.feed(page_html)
    except Exception:
        pass
    country_name = title_extractor.get_title()
    norm = normalize_name(country_name)

    if norm in cpc_names:
        return "CPC", country_name
    if norm in swl_names:
        return "SWL", country_name

    text_lower = page_html.lower()
    if "countries of particular concern" in text_lower:
        return "CPC", country_name
    if "special watch list" in text_lower:
        return "SWL", country_name

    return "none", country_name


def extract_key_findings(page_html):
    parser = ContentExtractor()
    try:
        parser.feed(page_html)
    except Exception:
        pass
    paragraphs = parser.get_paragraphs()
    return paragraphs[:3]


def fetch_country(country):
    slug = country["slug"]
    title = country["title"]
    cache_path = FETCHED / f"{slug}.json"
    url = f"{BASE_URL}/countries/{slug}"

    cached = None
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
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
            return cached, f"fallback to cache: {e}"
        return None, str(e)


def main():
    print("Fetching USCIRF 2026 recommendations...")
    cpc_names, swl_names = fetch_recommendations()
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
        designation, detected_name = detect_designation(page_html, cpc_names, swl_names)
        findings = extract_key_findings(page_html)

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

    if failed == len(unique_countries):
        write_status("failed", "all countries failed")
    elif failed > 0:
        write_status("partial", f"{failed} of {len(unique_countries)} failed")
    else:
        write_status("ok")


if __name__ == "__main__":
    main()
