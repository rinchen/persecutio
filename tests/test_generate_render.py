import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_website_data import (  # noqa: E402
    PAGE,
    STATUS_DISPLAY,
    build_meta_sources,
    esc,
    render_data_fields,
    render_recent_incidents,
    render_sources,
    safe_url,
    valid_slug,
)


class TestEscaping(unittest.TestCase):
    def test_esc_escapes_html(self):
        self.assertEqual(esc('<script>alert(1)</script>'), "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertIn("&quot;", esc('"quoted"'))

    def test_safe_url_allows_https(self):
        self.assertEqual(safe_url("https://example.com/a"), "https://example.com/a")
        self.assertEqual(safe_url("http://example.com/a"), "http://example.com/a")

    def test_safe_url_rejects_javascript(self):
        self.assertEqual(safe_url("javascript:alert(1)"), "#")
        self.assertEqual(safe_url("data:text/html,hi"), "#")
        self.assertEqual(safe_url(""), "#")
        self.assertEqual(safe_url(None), "#")

    def test_valid_slug(self):
        self.assertTrue(valid_slug("north-korea"))
        self.assertFalse(valid_slug("../etc/passwd"))
        self.assertFalse(valid_slug("North_Korea"))
        self.assertFalse(valid_slug(""))


class TestRenderSources(unittest.TestCase):
    def test_escapes_title_and_rejects_bad_url(self):
        lookup = {
            "s1": {"title": '<img src=x onerror=alert(1)>', "url": "javascript:evil", "date": "2024"},
            "s2": {"title": "Safe Source", "url": "https://example.com/report", "date": "2025"},
        }
        html = render_sources(["s1", "s2"], lookup)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;img", html)
        self.assertIn('href="#"', html)
        self.assertIn('href="https://example.com/report"', html)
        self.assertIn("Safe Source", html)

    def test_missing_ids(self):
        self.assertEqual(render_sources(["missing"], {}), "Sources will be listed here.")


class TestRenderIncidents(unittest.TestCase):
    def test_escapes_and_allowlists_urls(self):
        country = {
            "metadata": {
                "morningstarnews_samples": [
                    {
                        "title": '<script>x</script>',
                        "url": "javascript:alert(1)",
                        "date": "2024-01-01",
                    },
                    {
                        "title": "Church attacked in Nigeria",
                        "url": "https://morningstarnews.org/example",
                        "date": "2024-02-01",
                    },
                ]
            }
        }
        html = render_recent_incidents(country)
        self.assertIn("<h2>Latest News</h2>", html)
        self.assertIn("<section>", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn('href="#"', html)
        self.assertIn('href="https://morningstarnews.org/example"', html)

    def test_primary_recent_incidents_path(self):
        country = {
            "metadata": {
                "recent_incidents": [
                    {
                        "title": "Church burned",
                        "url": "https://morningstarnews.org/burned",
                        "date": "2025-03-01",
                        "source": "CSW",
                    },
                    {
                        "title": '<b>Attack</b>',
                        "url": "javascript:evil",
                        "date": "2025-01-02",
                        "source": "Morning Star News",
                    },
                ]
            }
        }
        html = render_recent_incidents(country)
        self.assertIn("<h2>Latest News</h2>", html)
        self.assertIn("&lt;b&gt;Attack&lt;/b&gt;", html)
        self.assertIn('href="#"', html)
        self.assertIn('href="https://morningstarnews.org/burned"', html)
        # Preserves enrich order (newest-first from build_recent_incidents)
        self.assertLess(html.index("Church burned"), html.index("Attack"))

    def test_historical_news_collapsed_details(self):
        country = {
            "metadata": {
                "recent_incidents": [
                    {
                        "title": "Recent attack",
                        "url": "https://morningstarnews.org/recent",
                        "date": "2026-01-01",
                        "source": "MSN",
                    },
                ],
                "historical_incidents": [
                    {
                        "title": "Older attack",
                        "url": "https://morningstarnews.org/old",
                        "date": "2018-01-01",
                        "source": "ICC",
                    },
                ],
            }
        }
        html = render_recent_incidents(country)
        self.assertIn("<h2>Latest News</h2>", html)
        self.assertIn('<details class="historical-news">', html)
        self.assertIn("<summary>Historical News</summary>", html)
        self.assertNotIn(" open", html.split("historical-news")[1][:40])
        self.assertIn("Recent attack", html)
        self.assertIn("Older attack", html)
        self.assertLess(html.index("Latest News"), html.index("Historical News"))
        self.assertLess(html.index("Recent attack"), html.index("Older attack"))

    def test_historical_only_without_latest(self):
        country = {
            "metadata": {
                "historical_incidents": [
                    {
                        "title": "Archive only",
                        "url": "https://example.com/a",
                        "date": "2015-01-01",
                        "source": "CSW",
                    }
                ]
            }
        }
        html = render_recent_incidents(country)
        self.assertNotIn("<h2>Latest News</h2>", html)
        self.assertIn("<summary>Historical News</summary>", html)
        self.assertIn("Archive only", html)

    def test_empty(self):
        self.assertEqual(render_recent_incidents({"metadata": {}}), "")


class TestRenderDataFields(unittest.TestCase):
    def test_escapes_string_fields(self):
        country = {
            "metadata": {
                "freedom_house_status": "<b>Not Free</b>",
                "opendoors_score": 88,
                "opendoors_ranking": 1,
            }
        }
        html = render_data_fields(country)
        self.assertIn("&lt;b&gt;Not Free&lt;/b&gt;", html)
        self.assertIn("88/100", html)
        self.assertIn("#1", html)
        # No direct source URL → leave values unlinked
        self.assertNotIn("<a ", html)

    def test_links_direct_sources_when_available(self):
        country = {
            "metadata": {
                "opendoors_score": 89,
                "opendoors_ranking": 9,
                "archive_od_url": "https://www.opendoors.org/persecution/reports/Afghanistan-Full_Country_Dossier-ODI-2025.pdf",
                "uscirf_designation": "CPC",
                "uscirf_url": "https://www.uscirf.gov/countries/afghanistan",
                "freedom_house_status": "Not Free",
                "state_dept_url": "https://www.state.gov/reports/2023-report-on-international-religious-freedom/afghanistan/",
            }
        }
        html = render_data_fields(country)
        self.assertIn(
            'href="https://www.opendoors.org/persecution/reports/Afghanistan-Full_Country_Dossier-ODI-2025.pdf"',
            html,
        )
        self.assertIn('href="https://www.uscirf.gov/countries/afghanistan"', html)
        self.assertIn(
            'href="https://www.state.gov/reports/2023-report-on-international-religious-freedom/afghanistan/"',
            html,
        )
        # Freedom House has no country-specific URL in metadata → stay plain text
        self.assertIn('<div class="value">Not Free</div>', html)

    def test_empty(self):
        self.assertEqual(render_data_fields({"metadata": {}}), "")


class TestPageSectionOrder(unittest.TestCase):
    def test_page_template_section_order(self):
        hist = PAGE.index("Historical Background")
        modern = PAGE.index("Modern-Day Situation")
        incidents = PAGE.index("{recent_incidents}")
        refs = PAGE.index("All References")
        data = PAGE.index("{data_fields}")
        self.assertLess(data, hist)
        self.assertLess(hist, modern)
        self.assertLess(modern, incidents)
        self.assertLess(incidents, refs)


class TestMetaStatusMapping(unittest.TestCase):
    def test_failed_maps_to_error_and_secondary_keys(self):
        lookup = {
            "acn2024": {"title": "ACN", "url": "https://example.com"},
            "morningstarnews": {"title": "MSN", "url": "https://example.com"},
            "csw": {"title": "CSW", "url": "https://example.com"},
        }
        statuses = [
            {"name": "acn", "status": "failed", "fetched_at": "2024-01-01T00:00:00Z"},
            {"name": "morningstarnews", "status": "ok", "fetched_at": "2024-01-02T00:00:00Z"},
            {"name": "csw", "status": "partial", "fetched_at": "2024-01-03T00:00:00Z"},
        ]
        meta = build_meta_sources(lookup, statuses)
        by_id = {m["id"]: m for m in meta}
        self.assertEqual(by_id["acn"]["status"], STATUS_DISPLAY["failed"])
        self.assertEqual(by_id["morningstarnews"]["status"], "ok")
        self.assertEqual(by_id["csw"]["status"], "partial")


if __name__ == "__main__":
    unittest.main()
