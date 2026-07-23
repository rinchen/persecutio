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
    load_uscirf_index,
    split_country_news,
)


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
