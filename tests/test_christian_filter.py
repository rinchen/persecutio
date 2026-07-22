"""Tests for Christian persecution filter, date merge, and citation helpers."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from christian_persecution import is_christian_persecution  # noqa: E402
from country_registry import attach_citation, ensure_source, resolve_country_name  # noqa: E402
from fetch_common import merge_articles, normalize_date  # noqa: E402
from rss_news_fetcher import countries_for_article  # noqa: E402


class TestChristianFilter(unittest.TestCase):
    def test_accepts_christian_persecution(self):
        self.assertTrue(
            is_christian_persecution(
                title="Pastor killed after church attack in Nigeria",
                description="Gunmen stormed a Christian congregation",
            )
        )

    def test_rejects_sports(self):
        self.assertFalse(
            is_christian_persecution(
                title="Football scores from yesterday",
                description="Local derby results",
            )
        )

    def test_rejects_other_faith_only(self):
        self.assertFalse(
            is_christian_persecution(
                title="Mosque closed by authorities",
                description="Muslim worshippers face new restrictions",
            )
        )

    def test_high_trust_categories(self):
        self.assertTrue(
            is_christian_persecution(
                title="Believers face new pressure",
                description="",
                categories=["Persecution", "Christianity"],
                high_trust_source=True,
            )
        )


class TestMergeOrder(unittest.TestCase):
    def test_normalize_date(self):
        self.assertEqual(normalize_date("2026-07-01T12:00:00Z"), "2026-07-01")
        self.assertEqual(normalize_date("20260715T120000Z")[:10], "2026-07-15")

    def test_newest_first_and_dedupe(self):
        existing = [
            {
                "title": "Older",
                "url": "https://example.com/a",
                "date": "2026-01-01",
                "source": "MSN",
            }
        ]
        new = [
            {
                "title": "Newer",
                "url": "https://example.com/b",
                "date": "2026-06-01",
                "source": "ICC",
            },
            {
                "title": "Older updated",
                "url": "https://example.com/a",
                "date": "2026-01-01",
                "description": "longer description here",
                "source": "MSN",
            },
        ]
        merged = merge_articles(existing, new)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["url"], "https://example.com/b")
        self.assertEqual(merged[1]["url"], "https://example.com/a")
        self.assertIn("longer", merged[1].get("description", ""))


class TestCitations(unittest.TestCase):
    def test_attach_citation(self):
        sources = {}
        ensure_source(sources, "odwwl2024", "Open Doors", "https://example.com", "2024")
        country = {"title": "Nigeria", "source_ids": {"modern": []}, "metadata": {}}
        attach_citation(country, "odwwl2024", sources)
        self.assertIn("odwwl2024", country["source_ids"]["modern"])
        self.assertEqual(country["metadata"]["source_ids"], ["odwwl2024"])

    def test_resolve_country(self):
        self.assertEqual(resolve_country_name("burma"), "Myanmar")
        self.assertIsNone(resolve_country_name("israel"))
        self.assertEqual(resolve_country_name("us"), "United States")
        self.assertEqual(resolve_country_name("US"), "United States")
        self.assertEqual(resolve_country_name("car"), "Central African Republic")


class TestCountriesForArticle(unittest.TestCase):
    def test_prefers_title_over_wp_description_noise(self):
        countries = countries_for_article(
            "Police stand aside as Indian pastor beaten",
            "Crackdown on churches in China. The post Police stand aside as Indian pastor beaten appeared first on Release International.",
            ["India", "Christian Persecution"],
        )
        self.assertEqual(countries, ["India"])
        self.assertNotIn("China", countries)

    def test_ignores_secondary_us_mention_in_description(self):
        countries = countries_for_article(
            "Tensions Inflamed by Blasphemy Accusation in Pakistan",
            "allegations of blasphemy against a pastor living in the United States triggered fears",
            ["Pakistan", "blasphemy"],
        )
        self.assertEqual(countries, ["Pakistan"])
        self.assertNotIn("United States", countries)

    def test_ignores_pronoun_us_in_title(self):
        countries = countries_for_article(
            'RUSSIA: "Without any investigation, they\'re already presuming us guilty", says pastor',
            "Prosecutions for religious organisations in Bryansk",
            [],
        )
        self.assertEqual(countries, ["Russia"])
        self.assertNotIn("United States", countries)

    def test_excluded_israel_does_not_fall_through_to_pronoun_us(self):
        countries = countries_for_article(
            "Israel: Catholic nun comments on her attack in Jerusalem",
            "comments that make us complicit in the conflict",
            ["Israel"],
        )
        self.assertEqual(countries, [])
        self.assertNotIn("United States", countries)


if __name__ == "__main__":
    unittest.main()
