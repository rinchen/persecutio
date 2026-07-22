import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_website_data import (  # noqa: E402
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
        self.assertIn("Recent Incidents", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn('href="#"', html)
        self.assertIn('href="https://morningstarnews.org/example"', html)

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

    def test_empty(self):
        self.assertEqual(render_data_fields({"metadata": {}}), "")


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
