"""Unit tests for collect_enrich helpers."""
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from collect_enrich import (  # noqa: E402
    LATEST_NEWS_CAP,
    build_country_news,
    build_recent_incidents,
    create_stub_countries,
    derive_status_from_signals,
    enrich_country,
    load_uscirf_index,
    split_country_news,
)
from country_registry import reconcile_citation_buckets  # noqa: E402


class TestDeriveStatus(unittest.TestCase):
    def test_opendoors_score_bands(self):
        od = {"countries": {"Nigeria": {"score": 85}}}
        self.assertEqual(
            derive_status_from_signals("Nigeria", od, {}, {}),
            ("severe", "Extreme"),
        )
        od["countries"]["Nigeria"]["score"] = 65
        self.assertEqual(
            derive_status_from_signals("Nigeria", od, {}, {}),
            ("severe", "Very High"),
        )
        od["countries"]["Nigeria"]["score"] = 45
        self.assertEqual(
            derive_status_from_signals("Nigeria", od, {}, {}),
            ("warning", "High"),
        )
        od["countries"]["Nigeria"]["score"] = 25
        self.assertEqual(
            derive_status_from_signals("Nigeria", od, {}, {}),
            ("warning", "Moderate"),
        )

    def test_uscirf_and_acn_fallbacks(self):
        uscirf = {"Egypt": {"designation": "CPC"}}
        self.assertEqual(
            derive_status_from_signals("Egypt", {}, uscirf, {}),
            ("severe", "Extreme"),
        )
        uscirf = {"Egypt": {"designation": "SWL"}}
        self.assertEqual(
            derive_status_from_signals("Egypt", {}, uscirf, {}),
            ("warning", "High"),
        )
        acn = {"countries": {"Egypt": {"classification": "Persecution"}}}
        self.assertEqual(
            derive_status_from_signals("Egypt", {}, {}, acn),
            ("persecution", "High"),
        )


class TestSplitCountryNews(unittest.TestCase):
    def test_fresh_overflow_goes_to_historical(self):
        today = date(2026, 7, 23)
        articles = [
            {
                "title": f"Fresh {i}",
                "url": f"https://example.com/f{i}",
                "date": f"2025-{(i % 12) + 1:02d}-01",
            }
            for i in range(25)
        ]
        # Newest-first as merge_articles would return
        articles.sort(key=lambda a: a["date"], reverse=True)
        latest, historical = split_country_news(articles, today=today)
        self.assertEqual(len(latest), LATEST_NEWS_CAP)
        self.assertEqual(len(historical), 5)
        self.assertTrue(all(a["date"] >= "2021-07-23" for a in latest))
        self.assertLess(latest[0]["date"], "2027-01-01")

    def test_pads_with_stale_into_historical(self):
        today = date(2026, 7, 23)
        fresh = [
            {"title": f"Fresh {i}", "url": f"https://example.com/n{i}", "date": f"2025-0{i+1}-01"}
            for i in range(5)
        ]
        stale = [
            {
                "title": f"Stale {i}",
                "url": f"https://example.com/s{i}",
                "date": f"2018-{(i % 12) + 1:02d}-01",
            }
            for i in range(10)
        ]
        articles = sorted(fresh + stale, key=lambda a: a["date"], reverse=True)
        latest, historical = split_country_news(articles, today=today)
        self.assertEqual(len(latest), 5)
        self.assertEqual(len(historical), 10)
        self.assertTrue(all("Fresh" in a["title"] for a in latest))
        self.assertTrue(all("Stale" in a["title"] for a in historical))

    def test_few_fresh_no_stale_has_no_historical(self):
        today = date(2026, 7, 23)
        articles = [
            {"title": f"Fresh {i}", "url": f"https://example.com/x{i}", "date": f"2024-0{i+1}-01"}
            for i in range(3)
        ]
        latest, historical = split_country_news(articles, today=today)
        self.assertEqual(len(latest), 3)
        self.assertEqual(historical, [])

    def test_undated_counts_as_fresh(self):
        today = date(2026, 7, 23)
        articles = [
            {"title": "No date", "url": "https://example.com/u", "date": ""},
            {"title": "Old", "url": "https://example.com/o", "date": "2015-01-01"},
        ]
        latest, historical = split_country_news(articles, today=today)
        self.assertEqual(len(latest), 1)
        self.assertEqual(latest[0]["title"], "No date")
        self.assertEqual(len(historical), 1)


class TestBuildRecentIncidents(unittest.TestCase):
    def test_cap_and_newest_first(self):
        news = {
            "morningstarnews": {
                "countries": {
                    "Nigeria": [
                        {
                            "title": "Older church attack in Nigeria",
                            "url": "https://example.com/old",
                            "date": "2024-01-01",
                            "description": "Christians attacked",
                            "source": "Morning Star News",
                        },
                        {
                            "title": "Newer church attack in Nigeria",
                            "url": "https://example.com/new",
                            "date": "2025-06-01",
                            "description": "Christians attacked",
                            "source": "Morning Star News",
                        },
                    ]
                }
            }
        }
        for i in range(LATEST_NEWS_CAP + 5):
            news["morningstarnews"]["countries"]["Nigeria"].append({
                "title": f"Incident {i} in Nigeria",
                "url": f"https://example.com/i{i}",
                "date": f"2024-02-{(i % 28) + 1:02d}",
                "description": "Church destroyed",
                "source": "Morning Star News",
            })
        latest, historical = build_country_news("Nigeria", news)
        self.assertEqual(len(latest), LATEST_NEWS_CAP)
        self.assertEqual(latest[0]["title"], "Newer church attack in Nigeria")
        self.assertEqual(len(latest) + len(historical), LATEST_NEWS_CAP + 7)
        self.assertEqual(len(historical), 7)
        # Back-compat wrapper returns latest only
        self.assertEqual(build_recent_incidents("Nigeria", news), latest)

    def test_drops_misbucketed_articles(self):
        news = {
            "forum18": {
                "countries": {
                    "United States": [
                        {
                            "title": (
                                'RUSSIA: "Without any investigation, they\'re already '
                                'presuming us guilty", says pastor'
                            ),
                            "url": "https://example.com/ru",
                            "date": "2026-01-01",
                            "description": "Prosecutions in Bryansk",
                            "source": "Forum 18",
                        }
                    ]
                }
            }
        }
        incidents = build_recent_incidents("United States", news)
        self.assertEqual(incidents, [])


class TestCreateStubCountries(unittest.TestCase):
    def test_creates_stub_for_known_geo_only(self):
        stubs = create_stub_countries(
            existing=[{"title": "Nigeria"}],
            sources={},
            feed_titles={"Kenya", "Nigeria", "NotARealPlaceXYZ"},
            opendoors_data={},
            uscirf_by_title={},
            acn_data={},
            news_blobs={
                "morningstarnews": {
                    "countries": {
                        "Kenya": [{
                            "title": "Church burned in Kenya",
                            "url": "https://example.com/k",
                            "date": "2025-01-01",
                            "description": "Christians attacked",
                            "source": "Morning Star News",
                        }]
                    }
                }
            },
            freedom_house={},
            owid_data={},
            vid_data={},
            gcr_data={},
            state_dept_by_title={},
            ohchr_by_title={},
            country_polygons={},
        )
        titles = {s["title"] for s in stubs}
        self.assertIn("Kenya", titles)
        self.assertNotIn("Nigeria", titles)
        kenya = next(s for s in stubs if s["title"] == "Kenya")
        self.assertEqual(kenya["slug"], "kenya")
        self.assertIn("Auto-tracked", kenya["historical"])

    def test_score_only_stub_has_nonempty_sections(self):
        """A stub discovered from score data alone (no news) must still cite sources
        in both historical and modern, never leaving a section empty."""
        sources = {
            "odwwl2024": {
                "title": "Open Doors World Watch List 2024",
                "url": "https://www.opendoors.org/en-US/persecution/countries/",
                "date": "2024",
            }
        }
        stubs = create_stub_countries(
            existing=[],
            sources=sources,
            feed_titles={"Kenya"},
            opendoors_data={"countries": {"Kenya": {"ranking": 40, "score": 55}}},
            uscirf_by_title={},
            acn_data={},
            news_blobs={},
            freedom_house={},
            owid_data={},
            vid_data={},
            gcr_data={},
            state_dept_by_title={},
            ohchr_by_title={},
            country_polygons={},
        )
        kenya = next(s for s in stubs if s["title"] == "Kenya")
        hist = kenya["source_ids"]["historical"]
        mod = kenya["source_ids"]["modern"]
        indicators = kenya["source_ids"].get("indicators") or []
        self.assertTrue(hist, "historical must not be empty")
        self.assertTrue(mod, "modern must not be empty")
        self.assertIn("odwwl2024", hist)
        # Generic OD index is an indicator cite; thin stubs may also keep it as a
        # modern fallback so the section Sources line is never empty.
        self.assertIn("odwwl2024", mod)
        self.assertTrue(
            "odwwl2024" in indicators or "odwwl2024" in mod,
            "odwwl2024 should be cited in indicators and/or modern fallback",
        )
        # Every seeded id must resolve to a real source (no cite-everything fallback).
        self.assertTrue(all(sid in sources for sid in hist))
        self.assertTrue(all(sid in sources for sid in mod))
        self.assertTrue(all(sid in sources for sid in indicators))


class TestReconcileCitationBuckets(unittest.TestCase):
    def test_moves_globals_to_indicators_and_drops_url_twins(self):
        sources = {
            "freedomhouse2024": {
                "title": "Freedom House",
                "url": "https://freedomhouse.org/report/freedom-world",
                "date": "2024",
            },
            "statedepartment2023brunei": {
                "title": "IRF Brunei",
                "url": "https://www.state.gov/reports/brunei/",
                "date": "2023",
            },
            "statedepartment2023archivebrunei": {
                "title": "IRF Brunei archive",
                "url": "https://www.state.gov/reports/brunei/",
                "date": "2023",
            },
            "statedepartment2023": {
                "title": "IRF index",
                "url": "https://www.state.gov/international-religious-freedom-reports/",
                "date": "2023",
            },
            "odwwl2025archivebrunei": {
                "title": "OD Brunei",
                "url": "https://www.opendoors.org/brunei.pdf",
                "date": "2025",
            },
        }
        country = {
            "source_ids": {
                "historical": ["statedepartment2023brunei"],
                "modern": [
                    "freedomhouse2024",
                    "statedepartment2023brunei",
                    "statedepartment2023archivebrunei",
                    "statedepartment2023",
                    "odwwl2025archivebrunei",
                ],
                "indicators": [],
            },
            "metadata": {},
        }
        reconcile_citation_buckets(country, sources)
        modern = country["source_ids"]["modern"]
        indicators = country["source_ids"]["indicators"]
        self.assertNotIn("freedomhouse2024", modern)
        self.assertIn("freedomhouse2024", indicators)
        self.assertIn("statedepartment2023brunei", modern)
        self.assertNotIn("statedepartment2023archivebrunei", modern)
        self.assertNotIn("statedepartment2023", modern)
        self.assertNotIn("statedepartment2023", indicators)
        self.assertIn("odwwl2025archivebrunei", modern)

    def test_enrich_routes_indicators_away_from_modern(self):
        sources = {
            "freedomhouse2024": {
                "title": "Freedom House",
                "url": "https://freedomhouse.org/report/freedom-world",
                "date": "2024",
            },
            "owid2024": {
                "title": "OWID",
                "url": "https://ourworldindata.org/grapher/religious-composition",
                "date": "2024",
            },
            "odwwl2026": {
                "title": "OD WWL",
                "url": "https://www.opendoors.org/en-US/persecution/countries/",
                "date": "2026",
            },
            "statedepartment2023": {
                "title": "IRF index",
                "url": "https://www.state.gov/international-religious-freedom-reports/",
                "date": "2023",
            },
        }
        country = {
            "title": "Kenya",
            "slug": "kenya",
            "iso3": "KEN",
            "source_ids": {"historical": ["odwwl2026"], "modern": ["odwwl2026"]},
            "metadata": {},
        }
        enrich_country(
            country,
            sources=sources,
            country_polygons={},
            wiki=None,
            freedom_house={"countries": {"Kenya": {"status": "Partly Free", "pr_score": 4, "cl_score": 4}}},
            opendoors_data={"countries": {"Kenya": {"ranking": 40, "score": 55}}},
            owid_data={"countries": {"Kenya": {"christian_population": 1, "christian_percentage": 80}}},
            vid_data={},
            gcr_data={},
            acn_data={},
            uscirf_by_title={},
            state_dept_by_title={
                "Kenya": {
                    "has_report": True,
                    "url": "https://www.state.gov/reports/kenya/",
                    "_report_year": "2023",
                    "executive_summary": "Summary.",
                }
            },
            ohchr_by_title={},
            news_blobs={},
        )
        modern = country["source_ids"]["modern"]
        indicators = country["source_ids"]["indicators"]
        self.assertIn("statedepartment2023kenya", modern)
        self.assertNotIn("freedomhouse2024", modern)
        self.assertIn("freedomhouse2024", indicators)
        self.assertIn("owid2024", indicators)
        self.assertNotIn("statedepartment2023", indicators)


class TestLoadUscirfIndex(unittest.TestCase):
    def test_corrupt_index_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            uscirf = root / "uscirf"
            uscirf.mkdir()
            (uscirf / "index.json").write_text("{not-json", encoding="utf-8")
            self.assertEqual(load_uscirf_index(root), {})


if __name__ == "__main__":
    unittest.main()
