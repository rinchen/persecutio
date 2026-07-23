#!/usr/bin/env python3
"""One-time download of legally archivable FoRB sources into data/archives/."""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from country_registry import COUNTRY_GEO, KNOWN_COUNTRIES  # noqa: E402
from fetch_common import USER_AGENT, strip_html  # noqa: E402
from fetch_state_dept import (  # noqa: E402
    REPORT_YEAR as IRF_YEAR,
    extract_christian_mentions,
    extract_executive_summary,
    extract_report_body,
    extract_sections,
    strip_tags,
)

# Some country slugs differ between our project and state.gov URLs
# Keep in sync with fetch_state_dept.SLUG_MAP
STATE_SLUG_MAP = {
    "myanmar": "burma",
    "democratic-republic-of-congo": "democratic-republic-of-the-congo",
}

# Open Doors dossier title overrides (project title -> dossier name fragment / PDF stem)
OD_TITLE_MAP = {
    "Russia": "Russian-Federation",
    "North Korea": "North-Korea",
    "Democratic Republic of Congo": "DRC",
    "Central African Republic": "CAR",
    "Saudi Arabia": "Saudi-Arabia",
    "Sri Lanka": "Sri-Lanka",
    "South Sudan": "South-Sudan",
    "Burkina Faso": "Burkina-Faso",
    "United States": None,  # no OD dossier expected
    "United Arab Emirates": "UAE",
}

ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = ROOT / "data" / "archives"
STATE_DIR = ARCHIVES / "state_dept"
USCIRF_DIR = ARCHIVES / "uscirf"
OD_DIR = ARCHIVES / "opendoors"
VDEM_DIR = ARCHIVES / "vdem"
MANIFEST_PATH = ARCHIVES / "manifest.json"

REQUEST_DELAY = 1.2
IRF_BASE = f"https://www.state.gov/reports/{IRF_YEAR}-report-on-international-religious-freedom"
USCIRF_ANNUAL_PDF = (
    "https://www.uscirf.gov/sites/default/files/2025-03/2025%20USCIRF%20Annual%20Report.pdf"
)
USCIRF_COUNTRY_URL = "https://www.uscirf.gov/countries/{slug}"
OD_ARCHIVE_URL = "https://www.opendoors.org/en-US/research-reports/wwl-archive/"
OD_DOSSIER_PREFIX = "https://www.opendoors.org/research-reports/country-dossiers/"
VDEM_ZIP_URL = "https://www.v-dem.net/media/datasets/V-Dem-CY-Core-v16_csv.zip"

# USCIRF country page slug overrides (project slug -> uscirf.gov slug)
USCIRF_SLUG_MAP = {
    "myanmar": "burma",
}


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def site_countries() -> list[dict]:
    """Prefer live countries.yml; fall back to registry geo keys."""
    yml = ROOT / "data" / "countries.yml"
    out: list[dict] = []
    if yml.exists():
        try:
            import yaml

            data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
            countries = data.get("countries") or []
            for c in countries:
                title = c.get("title")
                slug = c.get("slug") or slugify(title or "")
                iso3 = c.get("iso3")
                if title and slug:
                    out.append({"title": title, "slug": slug, "iso3": iso3})
            if out:
                return out
        except Exception as exc:  # noqa: BLE001
            print(f"  warn: could not read countries.yml ({exc}); using registry")
    for title in KNOWN_COUNTRIES:
        geo = COUNTRY_GEO.get(title)
        if not geo:
            continue
        out.append({"title": title, "slug": slugify(title), "iso3": geo[0]})
    return out


def fetch_bytes(url: str, timeout: int = 60) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_text(url: str, timeout: int = 45) -> str:
    return fetch_bytes(url, timeout=timeout).decode("utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def download_state_dept(countries: list[dict], manifest: dict) -> None:
    print("Archiving U.S. State Department IRF chapters...")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for c in countries:
        slug = c["slug"]
        state_slug = STATE_SLUG_MAP.get(slug, slug)
        url = f"{IRF_BASE}/{state_slug}/"
        out_html = STATE_DIR / f"{slug}.html"
        out_json = STATE_DIR / f"{slug}.json"
        entry = {
            "slug": slug,
            "title": c["title"],
            "url": url,
            "status": "failed",
            "path": str(out_html.relative_to(ROOT)),
        }
        try:
            html = fetch_text(url)
            if len(html) < 2000 or "404" in html[:500].lower():
                raise RuntimeError("short or missing page")
            write_text(out_html, html)
            body = extract_report_body(html) or html
            sections = extract_sections(html)
            summary = extract_executive_summary(sections, html)
            plain = strip_tags(body)
            mentions = extract_christian_mentions(plain)
            payload = {
                "title": c["title"],
                "slug": slug,
                "url": url,
                "report_year": IRF_YEAR,
                "executive_summary": (summary or "")[:5000],
                "christian_mentions": mentions,
                "sections": {k: v[:3000] for k, v in list(sections.items())[:12]},
                "text_excerpt": plain[:8000],
                "archived_at": datetime.now(timezone.utc).isoformat(),
            }
            write_text(out_json, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
            entry["status"] = "ok"
            entry["summary_chars"] = len(payload["executive_summary"])
            print(f"  OK  {slug} ({entry['summary_chars']} summary chars)")
        except Exception as exc:  # noqa: BLE001
            entry["message"] = str(exc)
            print(f"  FAIL {slug}: {exc}")
        results.append(entry)
        time.sleep(REQUEST_DELAY)
    manifest["state_dept"] = {
        "source": "U.S. State Department IRF",
        "report_year": IRF_YEAR,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "countries": results,
    }


def download_uscirf(countries: list[dict], manifest: dict) -> None:
    print("Archiving USCIRF annual report + country pages...")
    USCIRF_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = USCIRF_DIR / "USCIRF_2025_Annual_Report.pdf"
    annual = {"url": USCIRF_ANNUAL_PDF, "status": "failed", "path": str(pdf_path.relative_to(ROOT))}
    try:
        data = fetch_bytes(USCIRF_ANNUAL_PDF, timeout=180)
        if not data.startswith(b"%PDF"):
            raise RuntimeError("not a PDF")
        write_bytes(pdf_path, data)
        annual["status"] = "ok"
        annual["bytes"] = len(data)
        print(f"  OK  annual PDF ({len(data):,} bytes)")
    except Exception as exc:  # noqa: BLE001
        annual["message"] = str(exc)
        print(f"  FAIL annual PDF: {exc}")

    results = []
    for c in countries:
        slug = c["slug"]
        uscirf_slug = USCIRF_SLUG_MAP.get(slug, slug)
        url = USCIRF_COUNTRY_URL.format(slug=uscirf_slug)
        out_html = USCIRF_DIR / f"{slug}.html"
        out_json = USCIRF_DIR / f"{slug}.json"
        entry = {
            "slug": slug,
            "title": c["title"],
            "url": url,
            "status": "failed",
            "path": str(out_html.relative_to(ROOT)),
        }
        try:
            html = fetch_text(url)
            if len(html) < 1500:
                raise RuntimeError("short page")
            # Heuristic: country pages usually mention CPC/SWL/EPC or Key Findings
            lower = html.lower()
            if "page not found" in lower or "404" in html[:400].lower():
                raise RuntimeError("not found")
            write_text(out_html, html)
            plain = strip_html(html)
            # Do not invent CPC/SWL/EPC from boilerplate page chrome; leave unset
            # unless an explicit country-status phrase appears near the title area.
            designation = None
            head = plain[:1500]
            if re.search(r"Country of Particular Concern|\bCPC recommendation\b", head, re.I):
                designation = "CPC"
            elif re.search(r"Special Watch List|\bSWL recommendation\b", head, re.I):
                designation = "SWL"
            elif re.search(r"Entity of Particular Concern|\bEPC recommendation\b", head, re.I):
                designation = "EPC"
            findings = []
            for pat in (
                r"Key Findings?\s*(.{80,900}?)(?:Recommendations|Background|$)",
                r"USCIRF recommends(.{80,600})",
            ):
                fm = re.search(pat, plain, re.IGNORECASE | re.DOTALL)
                if fm:
                    chunk = re.sub(r"\s+", " ", fm.group(1)).strip()
                    if chunk:
                        findings.append(chunk[:700])
                    break
            # Paragraph-ish excerpts mentioning Christian
            for sent in re.split(r"(?<=[.!?])\s+", plain):
                if "christian" in sent.lower() and 60 < len(sent) < 400:
                    findings.append(sent.strip())
                    if len(findings) >= 3:
                        break
            payload = {
                "title": c["title"],
                "slug": slug,
                "url": url,
                "designation": designation,
                "key_findings": findings[:3],
                "text_excerpt": plain[:8000],
                "archived_at": datetime.now(timezone.utc).isoformat(),
            }
            write_text(out_json, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
            entry["status"] = "ok"
            entry["designation"] = designation
            print(f"  OK  {slug} ({designation or 'no designation'})")
        except Exception as exc:  # noqa: BLE001
            entry["message"] = str(exc)
            print(f"  skip {slug}: {exc}")
        results.append(entry)
        time.sleep(REQUEST_DELAY)
    manifest["uscirf"] = {
        "source": "USCIRF",
        "annual_report": annual,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "countries": results,
    }


def pdf_to_text(data: bytes, max_pages: int = 12) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required to extract Open Doors PDFs") from exc
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages[:max_pages]:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def parse_od_fields(plain: str) -> dict:
    from archive_text import clean_archive_text, is_usable_archive_excerpt

    # Drop TOC-style dotted leaders
    lines = []
    for line in (plain or "").splitlines():
        if re.search(r"\.{6,}", line):
            continue
        if re.match(r"^\s*\d+\s*$", line):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    compact = re.sub(r"\s+", " ", cleaned)

    def _score_brief(cand: str) -> int:
        """Prefer real prose paragraphs over TOC/copyright leftovers."""
        if not cand or "...." in cand:
            return -1
        cand = clean_archive_text(cand)
        if not is_usable_archive_excerpt(cand, min_len=80):
            return -1
        score = len(cand)
        if "christian" in cand.lower():
            score += 500
        if cand[0].isupper() or cand[0] in '"“':
            score += 100
        # Penalize page-header fragments
        if re.search(r"Persecution Dynamics\s*[–—-]", cand) and len(cand) < 160:
            score -= 400
        return score

    brief = ""
    best_score = -1
    for pat in (
        r"Brief description of the persecution situation\s*(.{80,1200}?)(?:Summary of|Position on the World Watch List|Persecution engines|Dominant persecution|Specific examples|$)",
        r"Brief description of the persecution situation\s*(.{80,1200})",
    ):
        for m in re.finditer(pat, compact, re.IGNORECASE | re.DOTALL):
            cand = re.sub(r"\s+", " ", m.group(1)).strip()[:1200]
            sc = _score_brief(cand)
            if sc > best_score:
                best_score = sc
                brief = clean_archive_text(cand)[:1200]

    engines = ""
    m = re.search(
        r"Dominant persecution engines and drivers\s*(.{40,800}?)(?:Brief description|Summary of|Position on|$)",
        compact,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        cand = re.sub(r"\s+", " ", m.group(1)).strip()
        if "...." not in cand:
            engines = clean_archive_text(cand)[:800]

    if not brief:
        for sent in re.split(r"(?<=[.!?])\s+", compact):
            s = clean_archive_text(sent.strip())
            if "...." in s:
                continue
            if "christian" in s.lower() and is_usable_archive_excerpt(s, min_len=90) and len(s) < 450:
                brief = s
                break

    rank = None
    score = None
    rm = re.search(r"Rank[:\s]+(\d+)", compact, re.IGNORECASE)
    if rm:
        rank = int(rm.group(1))
    sm = re.search(
        r"(?:Score|WWL[^\d]{0,20})(\d{2,3}(?:\.\d+)?)\s*/?\s*100",
        compact,
        re.IGNORECASE,
    )
    if sm:
        try:
            score = float(sm.group(1))
        except ValueError:
            score = None
    return {
        "brief_situation": brief,
        "persecution_engines": engines,
        "ranking": rank,
        "score": score,
    }


def discover_od_dossiers() -> dict[str, dict]:
    """Map normalized country keys -> {url, kind} from the WWL archive page."""
    html = fetch_text(OD_ARCHIVE_URL, timeout=60)
    found: dict[str, dict] = {}

    def add(key: str, url: str, kind: str) -> None:
        key = key.lower().strip()
        if not key:
            return
        found[key] = {"url": url, "kind": kind}
        found[key.replace(" ", "-")] = {"url": url, "kind": kind}
        found[key.replace("-", " ")] = {"url": url, "kind": kind}

    # Top 50: PDFs under /persecution/reports/
    for m in re.finditer(
        r'href="(/persecution/reports/([^"/]+?)-Full_Country_Dossier-ODI-2025\.pdf)"',
        html,
    ):
        path, stem = m.group(1), m.group(2)
        url = "https://www.opendoors.org" + path
        add(stem.replace("-", " "), url, "pdf")
        add(stem, url, "pdf")
        # Friendly aliases
        if stem == "CAR":
            add("central african republic", url, "pdf")
        if stem == "DRC":
            add("democratic republic of congo", url, "pdf")
            add("congo dr", url, "pdf")
        if stem == "North-Korea":
            add("north korea", url, "pdf")

    # Ranks 51–78: HTML persecution-dynamics pages
    for m in re.finditer(
        r'href="(/research-reports/country-dossiers/(WWL-2025-[^"]+?)-Persecution-Dynamics)"',
        html,
    ):
        path, name = m.group(1), m.group(2)
        country = name.replace("WWL-2025-", "").replace("-", " ")
        url = "https://www.opendoors.org" + path
        add(country, url, "html")
        if "Russian Federation" in country or country.lower() == "russian federation":
            add("russia", url, "html")
        if country.upper() == "UAE" or "United Arab Emirates" in country:
            add("united arab emirates", url, "html")
            add("uae", url, "html")
    return found


def download_opendoors(countries: list[dict], manifest: dict) -> None:
    print("Archiving Open Doors WWL persecution-dynamics dossiers...")
    OD_DIR.mkdir(parents=True, exist_ok=True)
    try:
        dossier_index = discover_od_dossiers()
        print(f"  discovered {len(dossier_index)} dossier index keys")
    except Exception as exc:  # noqa: BLE001
        print(f"  FAIL dossier index: {exc}")
        dossier_index = {}

    results = []
    for c in countries:
        slug = c["slug"]
        title = c["title"]
        mapped = OD_TITLE_MAP.get(title, title.replace(" ", "-"))
        entry = {
            "slug": slug,
            "title": title,
            "status": "skipped",
            "url": None,
        }
        if mapped is None:
            entry["message"] = "no OD dossier expected"
            results.append(entry)
            continue

        hit = None
        for key in (
            mapped.lower(),
            mapped.replace("-", " ").lower(),
            title.lower(),
            title.replace(" ", "-").lower(),
            slug.replace("-", " "),
            slug,
        ):
            if key in dossier_index:
                hit = dossier_index[key]
                break
        if not hit:
            # Construct PDF URL as fallback for Top-50 style names
            stem = mapped
            hit = {
                "url": f"https://www.opendoors.org/persecution/reports/{stem}-Full_Country_Dossier-ODI-2025.pdf",
                "kind": "pdf",
            }

        url = hit["url"]
        kind = hit["kind"]
        entry["url"] = url
        out_json = OD_DIR / f"{slug}.json"
        try:
            if kind == "pdf":
                out_pdf = OD_DIR / f"{slug}.pdf"
                entry["path"] = str(out_pdf.relative_to(ROOT))
                data = fetch_bytes(url, timeout=120)
                if not data.startswith(b"%PDF"):
                    raise RuntimeError("not a PDF")
                write_bytes(out_pdf, data)
                plain = pdf_to_text(data)
            else:
                out_html = OD_DIR / f"{slug}.html"
                entry["path"] = str(out_html.relative_to(ROOT))
                html = fetch_text(url)
                plain = strip_html(html)
                if len(plain) < 800 or "page not found" in plain.lower():
                    raise RuntimeError("dossier not found")
                write_text(out_html, html)

            fields = parse_od_fields(plain)
            payload = {
                "title": title,
                "slug": slug,
                "url": url,
                "year": 2025,
                "format": kind,
                "attribution": "© Open Doors International",
                "brief_situation": fields["brief_situation"],
                "persecution_engines": fields["persecution_engines"],
                "ranking": fields["ranking"],
                "score": fields["score"],
                "text_excerpt": re.sub(r"\s+", " ", plain)[:10000],
                "archived_at": datetime.now(timezone.utc).isoformat(),
            }
            write_text(out_json, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
            entry["status"] = "ok"
            print(f"  OK  {slug} ({kind})")
        except Exception as exc:  # noqa: BLE001
            entry["status"] = "failed"
            entry["message"] = str(exc)
            print(f"  skip {slug}: {exc}")
        results.append(entry)
        time.sleep(REQUEST_DELAY)
    manifest["opendoors"] = {
        "source": "Open Doors World Watch Research",
        "attribution": "© Open Doors International",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "countries": results,
    }


def _iso_map(countries: list[dict]) -> dict[str, dict]:
    return {str(c.get("iso3") or "").upper(): c for c in countries if c.get("iso3")}


def download_vdem(countries: list[dict], manifest: dict) -> None:
    print("Archiving V-Dem FoRB indicator subset (CC BY-SA)...")
    VDEM_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = VDEM_DIR / "V-Dem-CY-Core-v16_csv.zip"
    subset_path = VDEM_DIR / "forb_subset.csv"
    entry: dict = {
        "source": "V-Dem Country-Year Core v16",
        "license": "CC BY-SA",
        "url": VDEM_ZIP_URL,
        "status": "failed",
    }
    try:
        if not zip_path.exists() or zip_path.stat().st_size < 1_000_000:
            print("  downloading Core CSV zip (~16MB)...")
            data = fetch_bytes(VDEM_ZIP_URL, timeout=300)
            write_bytes(zip_path, data)
        else:
            print("  using cached zip")
        with zipfile.ZipFile(zip_path) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not names:
                raise RuntimeError("no CSV in zip")
            # Prefer the main country-year file
            names.sort(key=lambda n: (0 if "V-Dem-CY-Core" in n or "vdem" in n.lower() else 1, len(n)))
            csv_name = names[0]
            print(f"  reading {csv_name}")
            raw = zf.read(csv_name)
        # Detect columns
        text = raw.decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(text))
        fields = reader.fieldnames or []
        # Core may or may not include these; pick what exists
        want = []
        for col in (
            "country_name",
            "country_text_id",
            "country_id",
            "year",
            "v2clrelig",
            "v2clrelig_ord",
            "v2csrlgrep",
            "v2csrlgrep_ord",
            "v2clrelig_osp",
            "v2xcl_rol",  # rule of law related fallback sometimes present
        ):
            if col in fields:
                want.append(col)
        if "year" not in want or ("country_text_id" not in want and "country_name" not in want):
            raise RuntimeError(f"unexpected columns: {fields[:20]}")
        iso_map = _iso_map(countries)
        # Also map by name
        name_map = {c["title"].lower(): c for c in countries}
        rows_out = []
        latest_by_iso: dict[str, dict] = {}
        for row in reader:
            try:
                year = int(float(row.get("year") or 0))
            except ValueError:
                continue
            if year < 2000:
                continue
            iso = (row.get("country_text_id") or "").upper()
            cname = (row.get("country_name") or "").strip()
            target = iso_map.get(iso) or name_map.get(cname.lower())
            if not target:
                # fuzzy: Russian Federation -> Russia
                if cname.lower().startswith("russia"):
                    target = name_map.get("russia")
                elif cname.lower() in ("burma/myanmar", "myanmar"):
                    target = name_map.get("myanmar")
                elif "korea" in cname.lower() and "north" in cname.lower():
                    target = name_map.get("north korea")
                elif "congo" in cname.lower() and "democratic" in cname.lower():
                    target = name_map.get("democratic republic of congo")
            if not target:
                continue
            key = str(target.get("iso3") or target["slug"]).upper()
            trimmed = {k: row.get(k) for k in want}
            trimmed["project_slug"] = target["slug"]
            trimmed["project_title"] = target["title"]
            prev = latest_by_iso.get(key)
            if not prev or year >= int(float(prev.get("year") or 0)):
                # Prefer most recent year with any FoRB value
                latest_by_iso[key] = trimmed
            rows_out.append(trimmed)
        # Write full multi-year subset for site countries + latest snapshot JSON
        with subset_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(want) + ["project_slug", "project_title"])
            w.writeheader()
            for r in sorted(rows_out, key=lambda x: (x.get("project_slug") or "", int(float(x.get("year") or 0)))):
                w.writerow(r)
        latest_path = VDEM_DIR / "forb_latest.json"
        write_text(
            latest_path,
            json.dumps(
                {
                    "license": "CC BY-SA",
                    "version": "v16",
                    "source_url": VDEM_ZIP_URL,
                    "indicators": [c for c in want if c.startswith("v2")],
                    "countries": latest_by_iso,
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
        )
        entry.update(
            {
                "status": "ok",
                "zip_path": str(zip_path.relative_to(ROOT)),
                "subset_path": str(subset_path.relative_to(ROOT)),
                "latest_path": str(latest_path.relative_to(ROOT)),
                "countries": len(latest_by_iso),
                "rows": len(rows_out),
                "indicators": [c for c in want if c.startswith("v2")],
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        print(f"  OK  subset {len(rows_out)} rows / {len(latest_by_iso)} countries; indicators={entry['indicators']}")
        # Do not keep the full zip in git if large — leave on disk but note in manifest.
        # Prefer committing only the subset CSV + latest JSON.
    except Exception as exc:  # noqa: BLE001
        entry["message"] = str(exc)
        print(f"  FAIL V-Dem: {exc}")
    manifest["vdem"] = entry


def main() -> int:
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    countries = site_countries()
    print(f"Archiving sources for {len(countries)} countries → {ARCHIVES}")
    manifest: dict = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "country_count": len(countries),
    }
    download_state_dept(countries, manifest)
    download_uscirf(countries, manifest)
    download_opendoors(countries, manifest)
    download_vdem(countries, manifest)
    write_text(MANIFEST_PATH, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
