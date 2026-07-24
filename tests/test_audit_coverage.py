"""Targeted tests for audit gaps: parsers, enrich helpers, fetch retry, urls."""
from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from archive_text import store_summary  # noqa: E402
from collect_data import country_polygons_from_geojson  # noqa: E402
from collect_enrich import split_country_news  # noqa: E402
from country_registry import resolve_country_name  # noqa: E402
from fetch_common import (  # noqa: E402
    contained_path,
    fetch_bytes,
    merge_articles,
    normalize_date,
    wiki_cache_key,
)
from fetch_gcr_stats import extract_number, parse_global_stats  # noqa: E402
from fetch_state_dept import (  # noqa: E402
    extract_executive_summary,
    extract_sections,
    strip_tags,
)
from fetch_uscirf import (  # noqa: E402
    ContentExtractor,
    detect_designation,
    extract_key_findings,
    normalize_name,
)
from generate_website_data import render_data_fields  # noqa: E402
from urls import http_url, is_safe_url, safe_url  # noqa: E402
from christian_persecution import is_christian_persecution  # noqa: E402


class TestNormalizeDate(unittest.TestCase):
    def test_none_empty_malformed(self):
        self.assertEqual(normalize_date(None), "")
        self.assertEqual(normalize_date(""), "")
        self.assertEqual(normalize_date("   "), "")
        self.assertEqual(normalize_date("not-a-date"), "not-a-date")

    def test_month_day_year(self):
        self.assertEqual(normalize_date("July 4, 2024"), "2024-07-04")

    def test_gdelt_seendate(self):
        self.assertEqual(normalize_date("20260115T120000Z"), "2026-01-15")


class TestMergeArticlesExtras(unittest.TestCase):
    def test_newest_first_and_url_dedupe(self):
        existing = [
            {"title": "old", "url": "https://ex.com/a", "date": "2024-01-01", "description": "x"},
            {"title": "mid", "url": "https://ex.com/b/", "date": "2024-06-01", "description": "y"},
        ]
        new = [
            {
                "title": "new longer title",
                "url": "https://ex.com/a",
                "date": "2025-01-01",
                "description": "longer description here",
                "countries": ["Nigeria"],
            }
        ]
        merged = merge_articles(existing, new, max_articles=10, max_age_days=0)
        self.assertEqual(merged[0]["date"], "2025-01-01")
        urls = [a["url"].rstrip("/") for a in merged]
        self.assertEqual(len(urls), len(set(urls)))

    def test_max_age_prunes(self):
        arts = [
            {"title": "old", "url": "https://ex.com/old", "date": "2000-01-01", "description": "a"},
            {"title": "new", "url": "https://ex.com/new", "date": date.today().isoformat(), "description": "b"},
        ]
        merged = merge_articles([], arts, max_articles=10, max_age_days=30)
        self.assertEqual(len(merged), 1)
        self.assertIn("new", merged[0]["title"])


class TestSplitCountryNews(unittest.TestCase):
    def test_exact_cutoff_and_empty(self):
        today = date(2026, 7, 24)
        arts = [
            {"title": "on cutoff", "date": "2021-07-24", "url": "https://a"},
            {"title": "stale", "date": "2020-01-01", "url": "https://b"},
        ]
        latest, _older = split_country_news(arts, today=today, latest_cap=5)
        titles = {a["title"] for a in latest}
        self.assertIn("on cutoff", titles)
        latest, older = split_country_news([])
        self.assertEqual(latest, [])
        self.assertEqual(older, [])


class TestUrlsAndPaths(unittest.TestCase):
    def test_safe_url_helpers(self):
        self.assertTrue(is_safe_url("https://example.com/x"))
        self.assertFalse(is_safe_url("javascript:alert(1)"))
        self.assertEqual(safe_url("javascript:x"), "#")
        self.assertEqual(
            http_url("https://www.uscirf.gov", "countries", "nigeria"),
            "https://www.uscirf.gov/countries/nigeria",
        )
        self.assertIsNone(http_url("javascript:evil", "x"))

    def test_contained_path_rejects_escape(self):
        base = ROOT / "data" / "fetched"
        with self.assertRaises(ValueError):
            contained_path(base, "..", "..", "etc", "passwd")

    def test_wiki_cache_key_sanitizes(self):
        key = wiki_cache_key("Foo/Bar Baz")
        self.assertNotIn("/", key)
        self.assertNotIn(" ", key)


class TestFetchRetry(unittest.TestCase):
    def test_retries_then_succeeds(self):
        calls = {"n": 0}

        class FakeResp:
            headers = {}

            def __init__(self):
                self._sent = False

            def read(self, _n):
                if self._sent:
                    return b""
                self._sent = True
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=30):
            calls["n"] += 1
            if calls["n"] < 2:
                raise URLError("timed out")
            return FakeResp()

        with mock.patch("fetch_common.urllib.request.urlopen", side_effect=fake_urlopen):
            with mock.patch("fetch_common.time.sleep"):
                data, err = fetch_bytes("https://example.com/x", retries=3, backoff=0.01)
        self.assertIsNone(err)
        self.assertEqual(data, b"ok")
        self.assertGreaterEqual(calls["n"], 2)


class TestStateDeptParsers(unittest.TestCase):
    def test_extract_executive_summary_from_sections(self):
        html = """
        <div id="report_content">
          <h2>Executive Summary</h2>
          <p>The government restricts religious practice for Christians.</p>
          <h2>Section I</h2>
          <p>Other content.</p>
        </div>
        """
        sections = extract_sections(html)
        summary = extract_executive_summary(sections, html)
        self.assertTrue(summary)
        self.assertIn("restrict", summary.lower())

    def test_strip_tags_entities(self):
        self.assertEqual(strip_tags("<b>A&amp;B</b>"), "A&B")


class TestUscirfParsers(unittest.TestCase):
    def test_normalize_edge(self):
        self.assertEqual(normalize_name(""), "")
        self.assertEqual(normalize_name("Nigeria"), "nigeria")

    def test_content_and_designation(self):
        html = """
        <h1 class="internal-hero-title">Nigeria</h1>
        <div class="full-content"><p>First finding about church attacks.</p>
        <p>Second finding.</p></div>
        """
        findings, ok = extract_key_findings(html)
        self.assertTrue(ok)
        self.assertGreaterEqual(len(findings), 1)
        des, name, _ = detect_designation(html, {"nigeria"}, set())
        self.assertEqual(des, "CPC")
        self.assertIn("Nigeria", name)

    def test_content_extractor_factory(self):
        p = ContentExtractor()
        p.feed('<div class="full-content"><p>Hello world church.</p></div>')
        self.assertTrue(p.get_paragraphs())


class TestGcrParsers(unittest.TestCase):
    def test_extract_number_and_global(self):
        self.assertEqual(extract_number("4,849"), 4849)
        self.assertIsNone(extract_number("abc"))
        html = "Of the 4,849 Christians were killed for their faith. 388 million believers face."
        stats = parse_global_stats(html)
        self.assertEqual(stats.get("total_killed"), 4849)


class TestChristianFilterEdges(unittest.TestCase):
    def test_empty_and_high_trust(self):
        self.assertFalse(is_christian_persecution(title="", description=""))
        self.assertFalse(is_christian_persecution(title=None, description=None))
        self.assertTrue(
            is_christian_persecution(
                title="Pastor kidnapped in Nigeria",
                description="",
                high_trust_source=True,
            )
        )


class TestResolveCountry(unittest.TestCase):
    def test_none_and_gibberish(self):
        self.assertIsNone(resolve_country_name(None))  # type: ignore[arg-type]
        self.assertIsNone(resolve_country_name(""))
        self.assertIsNone(resolve_country_name("   "))
        self.assertIsNone(resolve_country_name("Atlantis"))
        self.assertEqual(resolve_country_name("  nigeria "), "Nigeria")


class TestGeoPolygons(unittest.TestCase):
    def test_multipolygon_and_junk(self):
        geo = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"ADMIN": "Testland", "NAME": "Testland", "ISO_A3": "TST"},
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 0]]]],
                    },
                },
                {"type": "NotFeature"},
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": None,
                },
            ],
        }
        polys = country_polygons_from_geojson(geo)
        self.assertIsInstance(polys, dict)
        self.assertIn("TST", polys)


class TestStoreSummary(unittest.TestCase):
    def test_clips_long_prose(self):
        text = "Sentence one. " * 400
        out = store_summary(text, limit=200)
        self.assertLessEqual(len(out), 220)
        self.assertFalse(out.endswith("…"))


class TestRenderDataFieldsBranches(unittest.TestCase):
    def test_gcr_uscirf_vdem(self):
        country = {
            "title": "Nigeria",
            "slug": "nigeria",
            "metadata": {
                "gcr_killed": 100,
                "uscirf_designation": "CPC",
                "uscirf_url": "https://www.uscirf.gov/countries/nigeria",
                "vdem_year": 2025,
                "vdem_freedom_of_religion": 1.2,
                "vdem_religious_organization_repression": 0.5,
                "state_dept_url": "https://www.state.gov/reports/x/",
            },
        }
        html = render_data_fields(country)
        self.assertIn("GCR Killed", html)
        self.assertIn("USCIRF Designation", html)
        self.assertIn("V-Dem", html)


if __name__ == "__main__":
    unittest.main()
